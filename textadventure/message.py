import sys
import time
from abc import ABC, abstractmethod
from enum import Enum
from threading import Thread
from typing import List


class PlayerInput(ABC):
    @abstractmethod
    def take_input(self):
        """
        @return: a string representing the input or None
        Calling this method should not make the current thread sleep
        """
        pass

    @abstractmethod
    def set_input_prompt(self, message: str):
        """
        Sets the input prompt
        @param message: The string to set the input prompt to
        @return: None
        """
        pass


class PlayerOutput(ABC):
    @abstractmethod
    def send_message(self, message):
        """
        @param message: the message to send
        """
        pass


class StreamOutput(PlayerOutput, Thread):  # extending thread so we can let messages pile up and print them out easily

    """
    This class is a PlayerOutput class that outputs the console by default or another stream if chosen.
    The run method along with the while True loop and everything inside it is pretty much just thrown together\
        with a lot of painful if statements. Of course, if you stare at it long enough, you might be convinced that you\
        have it down. However, there could be side effects of using different things and hopefully this is the only \
        class that has side effects related to the printing of text. Good luck future readers.
    """

    def __init__(self, stream=sys.stdout, is_unix=True):
        super(StreamOutput, self).__init__()
        self.stream = stream
        self.is_unix = is_unix

        self.messages = []
        self.current_messages = []
        self.wait_multiplier = 1
        self.print_immediate = False  # if True, will be set back to False after done printing current_messages

        self.start()

    def send_message(self, message):
        if message is None:
            raise Exception("Cannot add an exception that's None")
        if type(message) is not Message:
            raise Exception("Must be a message")
        self.messages.append(message)  # note that this may cause an issue if it gets reset right after (very unlikely)

    def run(self):
        from colorama import init, AnsiToWin32
        if not self.is_unix:
            init(autoreset=True)
            self.stream = AnsiToWin32(self.stream).stream  # change the stream to one that automatically converts it
        while True:
            if len(self.messages) > 0:
                self.current_messages = self.messages  # no need to clone because we will be resetting self.messages
                self.messages = []
                self.print_immediate = False
                for message in self.current_messages:
                    before_multiplier = 1  # used to make wait messages shorter
                    if self.print_immediate:
                        before_multiplier = 0.3
                    time.sleep(message.wait_in_seconds * before_multiplier)
                    to_print = message.before + message.text + message.ending

                    names: List[str] = []
                    for named in message.named_variables:
                        names.append(str(named))  # named could be a string or something that has an __str__ method
                    to_print = to_print.format(*names)  # tuple is needed or it ends up ['Bob']
                    is_immediate = False  # only used with MessageType.TYPED used for |text| blocks to print immediately
                    # ^ not affected by Message properties, read code in for loop to understand
                    for c in to_print:
                        to_wait = 0  # in seconds # the smaller the faster
                        if not self.print_immediate:
                            if message.message_type == MessageType.TYPED:
                                to_wait = 0.018
                                if c == '|':  # allows a part of the message to be immediate but not all of the message
                                    is_immediate = not is_immediate

                                if is_immediate:
                                    to_wait = 0
                                elif c == '.':
                                    to_wait = 0.05
                                elif c == ' ':
                                    to_wait = 0.03
                                elif not str(c).islower():
                                    to_wait = 0.05
                            elif message.message_type == MessageType.WAIT:
                                to_wait = 0
                            elif message.message_type == MessageType.TYPE_SLOW:
                                to_wait = 0.15

                        to_wait *= self.wait_multiplier

                        if not message.wait_after:
                            time.sleep(to_wait)
                        if c != '|':  # don't print these characters
                            self.stream.write(c)  # print character
                            if self.is_unix:  # if it's windows, this will look terrible
                                self.stream.write("\033[s")  # save position for KeyboardInput
                        if message.message_type != MessageType.IMMEDIATE and message.message_type != MessageType.WAIT \
                                and (message.message_type != MessageType.TYPED or to_wait != 0) and not is_immediate:
                            self.stream.flush()  # flush the stream assuming that we need to
                        if message.message_type == MessageType.WAIT and c == '\n':
                            time.sleep(0.35)
                        if message.wait_after:
                            time.sleep(to_wait)
                    self.stream.flush()


class KeyboardInput(PlayerInput, Thread):
    DEFAULT_INPUT_PROMPT = ""  # because it doesn't look how we want it to

    def __init__(self, stream_output: StreamOutput):
        """

        @param stream_output: The stream output or None if the PlayerOutput object isn't a StreamOutput
        """
        super(KeyboardInput, self).__init__()
        self.inputs: List[str] = []
        self.stream_output = stream_output
        self.__input_prompt: str = self.__class__.DEFAULT_INPUT_PROMPT
        self.start()

    def set_input_prompt(self, message: str):
        self.__input_prompt = message

    def run(self):
        while True:
            inp = str(input(self.__input_prompt))
            self.__input_prompt = self.__class__.DEFAULT_INPUT_PROMPT
            if len(inp) == 0:  # ignore blank lines
                if self.stream_output is not None and self.stream_output.is_unix:
                    # get rid of enter # back to prev: \033[F
                    self.stream_output.stream.write("\033[K\033[u\033[1A")  # gosh, it was worth trying lots of things
                    # K: clear line, u: restore position, 1A: Move up 1 line   # ^ it works!!

                    '''
                    Can we just take a moment to appreciate whatever the heck I created does?
                    All ya gotta do it press enter and this little if statement makes it happen.
                    Fuck this doesn't work on windows. I've been using gitbash. Fuck DOS operating system wtf
                    '''

                    self.stream_output.stream.flush()
                    self.stream_output.print_immediate = True
                continue
            self.inputs.append(inp)

    def take_input(self):
        r = None
        if len(self.inputs) > 0:
            r = self.inputs[0]
            self.inputs.remove(r)

        return r


class MessageType(Enum):
    """
    An enum that represents how the message will be printed out and how it will be shown

    Attributes:
        IMMEDIATE The message will be printed immediately
        TYPED     The message will be typed out at normal speed
        WAIT      The message will be typed out immediately accept when there's a lew line character,
                    it will wait before printing that out. Also should be used when sending a wait between messages
        TYPE_SLOW The message will be typed out slower than the TYPED MessageType

    """

    IMMEDIATE = 1
    TYPED = 2
    WAIT = 3
    TYPE_SLOW = 4


class Message:
    DEFAULT_ENDING = "\n"
    DEFAULT_BEFORE = " "

    def __init__(self, text: str, message_type: MessageType = MessageType.TYPED, ending=DEFAULT_ENDING, before=" ",
                 wait_in_seconds=0, named_variables: List = [], wait_after=False):
        """

        @param message_type: The MessageType
        @param text: The text
        @param ending: the ending defaults to \\n
        @param wait_after: defaults to False. Set to true if you want to wait after a character is printing instead bef
        @param wait_in_seconds: The amount of time in seconds before this prints. Not affected by wait_after
        @param named_variables: A list of variables each overriding __str__ which replaces {} {1} etc\
                                This is recommended because we might want to change the color later.\
                                Note that you shouldn't put a number in {} (don't do {1}) it could be handled weirdly
        """
        self.message_type = message_type
        self.text: str = text
        self.ending: str = ending
        self.wait_after = wait_after
        self.wait_in_seconds = wait_in_seconds
        self.named_variables: List = named_variables
        if (before is self.__class__.DEFAULT_ENDING and ending is not self.__class__.DEFAULT_ENDING
            and len(ending) == 0) or len(text) == 0:  # if you read this if statement, it might make sense
            before = ""  # makes sure that if we are changing the def ending, we don't get a space we don't want unless\
            # we do want it
        elif ending is self.__class__.DEFAULT_ENDING and ending in text:  # adds the before string before a new line
            self.text = self.text.replace(ending, ending + before)
        self.before = before