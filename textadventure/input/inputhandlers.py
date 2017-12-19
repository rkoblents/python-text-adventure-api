from typing import List

from textadventure.clientside.outputs import StreamOutput
from textadventure.handler import Handler
from textadventure.input.inputhandling import InputHandler, InputObject, InputHandleType, InputHandle
from textadventure.message import Message, MessageType
from textadventure.player import Player


class SettingsHandler(InputHandler):
    def __init__(self, allowed_player: Player):
        """
        :param allowed_player: The only player that this will react to
        """
        self.allowed_player = allowed_player

    def on_input(self, handler: Handler, player: Player, player_input: InputObject):
        command = player_input.get_command().lower()
        if player != self.allowed_player or (command != "setting" and not command.startswith(":")):
                # or type(player.player_output) is not StreamOutput:
            return None

        output = player.player_output

        def handle_function(already_handled: List[InputHandleType]) -> InputHandleType:
            arg_index = 1
            arg = None
            if command.startswith(":"):  # the player is typing the argument as the command
                arg = command.replace(":", "")
                arg_index = 0
            elif len(player_input.get_arg(1)) != 0:
                arg = player_input.get_arg(0)[0].lower()

            # TODO, fix this code with : and setting and this is terrible
            if arg is not None:
                if arg == "speed":
                    speed = player_input.get_arg(arg_index + 0)[0].lower()  # remember, arg 0 is the second word
                    if speed == "fast":
                        output.wait_multiplier = 0.4
                        player.send_message("Set speed to fast.")
                        return InputHandleType.HANDLED_AND_DONE
                    elif speed == "normal":
                        output.wait_multiplier = 1
                        player.send_message("Set speed to normal")
                        return InputHandleType.HANDLED_AND_DONE

            player.send_message(Message("Help for setting command: \n"
                                        "\tspeed: setting speed <fast:normal>", MessageType.IMMEDIATE))
            return InputHandleType.HANDLED_AND_DONE

        return InputHandle(0, handle_function, self)