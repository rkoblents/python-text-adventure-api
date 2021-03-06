import math
from typing import TYPE_CHECKING, Optional

from textprint.colors import Color, CLEAR_LINE
from textprint.textutil import length_without_ansi

if TYPE_CHECKING:
    from textprint.section import Section
    from textprint.textprinter import TextPrinter


class Line:
    """
    A class that holds data for a line. Should be created by a Section
    """
    # TODO add a color option
    def __init__(self, contents: str, section: 'Section', line_number: int):
        """

        :param contents: The contents of the line -> What text you want to be displayed on a line.
        :param section: The section that this line is in
        :param line_number: The line number given by section with the lowest value being 0. If a line for whatever \
                reason is deleted, the Section handling the lines should change the value accordingly. Note this is \
                relative to the section, not the whole TextPrinter
        """
        self._contents = contents  # has it's own property and setter
        self.section = section
        self.line_number = line_number

        self._last_length_lines = None  # used by the update method
        self._did_contents_change = True  # used by the update method. Set to False each time

    @property
    def contents(self):
        return self._contents

    @contents.setter
    def contents(self, value):
        if self._contents != value:
            self._did_contents_change = True
        self._contents = value

    def _do_goto(self, text_printer: 'TextPrinter', flush=False, extra_line_number=0):
        """
        Goes to this line

        :param text_printer: The TextPrinter object
        :param flush: By default False, and should be False unless you want the cursor to show at this location on \
                screen
        :param extra_line_number: By default 0. Is used when this line takes up multiple rows. If 1, it will move \
                down 1.
        :return:
        """
        width = text_printer.dimensions[1]
        # length = len(self.section.lines)
        length = 0  # after for loop, will be just like len(self.section.lines) but accounting for extra lines
        for line in self.section.lines:
            length += line.get_rows_taken(width)

        # line_number = self.line_number
        line_number = 0  # after for loop, will be just like self.line_number but accounting for extra lines
        for line in self.section.lines:  # TODO do something with self.line_number
            if line == self:
                break
            line_number += line.get_rows_taken(width)
        if self.line_number < 0:  # for fake lines
            # if we have a line that's fake, we want to
            difference = self.line_number - len(self.section.lines)  # will always be negative
            assert difference < 0
            assert line_number == length, "If this is False, then it's likely this isn't a fake line."
            line_number += difference  # since line_number == length, and difference is a big negative number \
            #       we account for extra lines and get a nice negative number we can use for a fake line
            # assert line_number < 0  we don't need this because of the first assert difference < 0
        rows = length - line_number - 1  # - 1 because we don't want the lowest value of rows as 1

        columns = 0
        return self.section.goto(text_printer, rows - extra_line_number, columns, flush=flush)

    def update(self, text_printer: 'TextPrinter', flush=False, reprint=False):
        """
        Updates the line with self.contents. Note if contents was changed since the last call, and contents overflows\
        to the next line, this will write on the line above it meaning you will need to update all the lines in this\
        section.

        :param text_printer: The text printer object
        :param flush: By default false, set to True if you want to flush the stream
        :param reprint: By default False, when False, makes sure this method only updates if necessary. Set to True,\
                if you are updating all lines. When calling this in a loop, this should be False. If flush is True,\
                changing this does nothing.
        """
        if not flush and not reprint and not self._did_contents_change:
            # Don't reprint if we don't need to
            # assert False, "Hey, we made it"
            return
        self._did_contents_change = False
        columns = text_printer.dimensions[1]

        contents = self.contents
        if str(Color.CLEAR_SECTION) in contents:
            self.section.lines.clear()  # clear all lines. Even this line.
            return
        lines = [""]
        for c in contents:
            index = len(lines) - 1  # define index
            current = lines[index]  # get the current line from lines
            current += c
            lines[index] = current
            if len(current) >= columns and length_without_ansi(current) >= columns:
                # if the first part of if clause if False, the second part won't be tested (what we want)
                lines.append("")
        # show = str(Color.RESET)
        for index, line in enumerate(lines):
            self._do_goto(text_printer, flush=False, extra_line_number=index)
            before = ""
            if index == 0:
                before = str(Color.RESET)
            after = ""
            if index == len(lines) - 1:
                after = str(Color.RESET)
            text_printer.print(CLEAR_LINE + before + line + after, end="", flush=False)

        last_length = self._last_length_lines
        self._last_length_lines = len(lines)
        if last_length is not None and last_length != len(lines):
            # this code is to make sure that if the rows taken by this line changed, other lines are updated so the\
            #   line directly above this line doesn't get erased (Just like how when we add a new line, we update)
            self.section.update_lines(text_printer, flush=False, force_reprint=True)
        if flush:
            text_printer.flush()  # we could do print(flush=False) but eventually, we won't use print
        # if len(lines) > 1:
        #     assert False, "lines: {}, contents: {}".format(lines, contents)

    def get_rows_taken(self, allowed_columns: Optional[int]):
        """
        Usually returns 1 but in the case that the line goes to the next line, it should return 2, or 3, etc.

        Should return the same amount whether or not update has been called first since it uses self.contents and \
        update doesn't change self.contents

        :param allowed_columns: The number of columns that this line is allowed to take up. Usually width of terminal.\
                if None, this will return 1 unless the implementation is changed
        :return: The number of rows that this line is taken, usually 1
        """
        if allowed_columns is None:
            return 1
        length = len(self.contents)
        if length < allowed_columns:  # don't call length_without_ansi until it might be going to the next line
            return 1  # If we go about calculating this, it's going to be 1 anyway
        length = length_without_ansi(self.contents)
        char_count = length + 1  # if we remove + 1, we must account for this being 0
        # assert False, "char_count: {}, allowed_columns: {}".format(char_count, allowed_columns) for debugging

        r = int(math.ceil(char_count / allowed_columns))

        rows = self.section.rows
        if rows is not None and rows < r:
            # this accounts for when the rows in this section don't have enough to fit what we are going to return
            return rows
        return r
