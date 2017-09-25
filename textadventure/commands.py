from abc import abstractmethod
from typing import List, Optional

from textadventure.command import LocationCommandHandler, SimpleCommandHandler
from textadventure.handler import Handler
from textadventure.input import InputObject, InputHandleType
from textadventure.item import FiveSensesHandler, Item
from textadventure.location import Location
from textadventure.message import Message, MessageType
from textadventure.player import Player
from textadventure.utils import Point, NORTH, EAST, SOUTH, WEST, UP, DOWN, ZERO, CanDo

"""This file holds some nice commands and util methods that help out with it. Most of the commands are essential."""


def get_reference(player: 'Player', string_args: str) -> Optional[Item]:
    """
    Senses command handler has a good code snippet that shows how you should use this method
    Note: Remember, this can return None.
    @param player: the player
    @param string_args: The arguments that the player entered
    @return: The item
    """
    for item in player.location.items:
        if item.is_reference(string_args):
            return item
    for item in player.items:
        if item.is_reference(string_args):
            return item
    return None


def get_point(handler: 'Handler', player: 'Player', string_args: str) -> Optional[Point]:
    """
    Gets the location using the player, and it's string_args
    @param handler: The Handler object
    @param player: The player. Needed for location reference to get location N,E,S,W
    @param string_args: The string arguments
    @return: The point object that represents the point of the new location
    """
    for location in handler.locations:  # we do this first in case there's a location called North <something>
        if location.is_reference(string_args):
            return location.point
    # now we'll check if it's a direction
    string_args = string_args.lower()
    add: Point = None
    if "nor" in string_args:
        add = NORTH
    elif "eas" in string_args or "ast" in string_args:
        add = EAST
    elif "sou" in string_args:
        add = SOUTH
    elif "wes" in string_args:
        add = WEST
    elif "up" in string_args:
        add = UP
    elif "dow" in string_args:
        add = DOWN
    elif "her" in string_args:
        add = ZERO
    else:
        return None
    if add is None:
        raise Exception("Should not have happened")
    return player.location.point + add


class HelpCommandHandler(SimpleCommandHandler):
    def __init__(self):
        super(HelpCommandHandler, self).__init__(["help"], "The help for this command isn't very helpful now it it?")

    def _handle_command(self, handler: 'Handler', player: 'Player', player_input: InputObject) -> InputHandleType:
        message_type = MessageType.WAIT
        player.send_message(Message("Get help for commands: '<command> help'", message_type=message_type))
        player.send_message(
            Message("Useful commands: 'go', 'look', 'listen', 'feel', 'taste', 'smell', 'locate', 'items'"))
        return InputHandleType.HANDLED


"""
The SensesCommandHandler and all the 5 command handler that are subclasses of that are LocationCommandHandlers because\
we want to give the Location as much control over these as possible (that's why they are part of the location's\
field, command_handlers. They should be specific to each location to give it control over these)
"""


class SensesCommandHandler(LocationCommandHandler):
    def __init__(self, command_names: List[str], description: str, location: Location):
        super(SensesCommandHandler, self).__init__(command_names, description, location)

    @abstractmethod
    def sense(self, sense_handler: FiveSensesHandler, handler: 'Handler', player: 'Player'):
        """Should be overridden and should only call the method from """
        pass

    @abstractmethod
    def can_sense(self, item: Item, player: 'Player') -> CanDo:
        pass

    def _handle_command(self, handler: 'Handler', player: 'Player', player_input: InputObject) -> InputHandleType:
        first_arg = player_input.get_arg(0)
        if len(first_arg) != 0:  # thing stuff
            # here to
            referenced_item = get_reference(player, " ".join(first_arg))
            if referenced_item is None:
                player.send_message(Item.CANNOT_SEE[1])
                return InputHandleType.HANDLED
            can_ref = referenced_item.can_reference(player)
            if can_ref[0] is False:
                player.send_message(can_ref[1])
            else:  # here is how you should use get_reference
                can_do_sense = self.can_sense(referenced_item, player)
                if can_do_sense[0]:
                    self.sense(referenced_item, handler, player)
                else:
                    player.send_message(can_do_sense[1])
        else:  # location stuff
            self.sense(player.location, handler, player)
        return InputHandleType.HANDLED


class LookCommandHandler(SensesCommandHandler):
    command_names = ["look", "see", "lok", "find", "se", "ook"]  # yeah I know, magic strings deal with it
    description = """Allows you to see your surroundings. Aliases: look, see, find\nUsage: look [item] """

    def __init__(self, location: Location):
        super(LookCommandHandler, self).__init__(self.__class__.command_names, self.__class__.description, location)

    def sense(self, sense_handler: FiveSensesHandler, handler: 'Handler', player: 'Player'):
        sense_handler.see(handler, player)

    def can_sense(self, item: Item, player: 'Player') -> CanDo:
        return item.can_see(player)


class ListenCommandHandler(SensesCommandHandler):
    command_names = ["listen", "hear", "escucha", "liste", "isten", "hea"]
    description = """Allows you to listen to your surroundings. Aliases: listen, hear\nUsage: feel [item]"""

    def __init__(self, location: Location):
        super(ListenCommandHandler, self).__init__(self.__class__.command_names, self.__class__.description, location)

    def sense(self, sense_handler: FiveSensesHandler, handler: 'Handler', player: 'Player'):
        sense_handler.listen(handler, player)

    def can_sense(self, item: Item, player: 'Player') -> CanDo:
        return item.can_listen(player)


class FeelCommandHandler(SensesCommandHandler):
    command_names = ["feel", "touch", "eel", "fee", "tou", "tuch", "toch"]
    description = """Allows you to feel your surroundings. Aliases: look, touch\nUsage: feel [item]"""

    def __init__(self, location: Location):
        super(FeelCommandHandler, self).__init__(self.__class__.command_names, self.__class__.description, location)

    def sense(self, sense_handler: FiveSensesHandler, handler: 'Handler', player: 'Player'):
        sense_handler.feel(handler, player)

    def can_sense(self, item: Item, player: 'Player'):
        return item.can_feel(player)


class SmellCommandHandler(SensesCommandHandler):
    command_names = ["smell", "nose", "smel", "mell", "nos", "smeel", "smee", "mel"]
    description = """Allows you to smell your surroundings. Aliases: smell, nose\nUsage: feel [item]"""

    def __init__(self, location: Location):
        super(SmellCommandHandler, self).__init__(self.__class__.command_names, self.__class__.description, location)

    def sense(self, sense_handler: FiveSensesHandler, handler: 'Handler', player: 'Player'):
        sense_handler.smell(handler, player)

    def can_sense(self, item: Item, player: 'Player'):
        return item.can_smell(player)


class TasteCommandHandler(SensesCommandHandler):
    command_names = ["taste", "tongue", "aste", "tast"]
    description = """Allows you to taste. Aliases: taste, tongue\nUsage: feel [item]"""

    def __init__(self, location: Location):
        super(TasteCommandHandler, self).__init__(self.__class__.command_names, self.__class__.description, location)

    def sense(self, sense_handler: FiveSensesHandler, handler: 'Handler', player: 'Player'):
        sense_handler.taste(handler, player)

    def can_sense(self, item: Item, player: 'Player'):
        return item.can_taste(player)


class GoCommandHandler(SimpleCommandHandler):  # written on friday with a football game

    command_names = ["go", "move", "mov", "ove", "va", "voy", "walk", "step"]
    description = "Allows you to go to another location usually nearby. Aliases: go, move\n" \
                  "Usage: go <location or direction>"

    def __init__(self):
        super().__init__(self.__class__.command_names, self.__class__.description)

    def _handle_command(self, handler: 'Handler', player: 'Player', player_input: InputObject) -> InputHandleType:
        first_arg = player_input.get_arg(0)
        if len(first_arg) == 0:
            self.send_help(player)
            return InputHandleType.HANDLED
        rest = " ".join(first_arg)
        point = get_point(handler, player, rest)
        if point is None:
            player.send_message("Cannot find location: \"" + rest + "\"")
            return InputHandleType.HANDLED
        new_location = handler.get_point_location(point)
        if new_location == player.location:
            player.send_message("You're already in that location!")
            return InputHandleType.HANDLED

        result: CanDo = player.location.go_to_other_location(handler, new_location, point - player.location.point,
                                                             player)
        if not result[0]:
            player.send_message(result[1])
        return InputHandleType.HANDLED


class TakeCommandHandler(SimpleCommandHandler):
    command_names = ["take", "grab", "tak", "steel", "pick", "pik", "pickup"]
    description = "Allows you to take something from a location or someone. Aliases: take, grab, pickup\n" \
                  "Usage: take <item name>"

    def __init__(self):
        super().__init__(self.__class__.command_names, self.__class__.description)

    def _handle_command(self, handler: 'Handler', player: 'Player', player_input: InputObject):
        first_arg = player_input.get_arg(0)
        if len(first_arg) == 0:
            self.send_help(player)
            return InputHandleType.HANDLED
        item = get_reference(player, " ".join(first_arg))

        if item is None:
            player.send_message(Item.CANNOT_SEE[1])
            return InputHandleType.HANDLED
        can_ref = item.can_reference(player)
        if can_ref[0] is False:
            player.send_message(can_ref[1])
            return InputHandleType.HANDLED
        can_take = item.can_take(player)
        if can_take[0] is False:
            player.send_message(can_take[1])
            return InputHandleType.HANDLED
        previous_holder = item.holder
        if item.change_holder(previous_holder, player) and isinstance(previous_holder, Location):
            previous_holder.on_take(handler, item)
            player.send_message(Message("You took {}.", named_variables=[item]))
        return InputHandleType.HANDLED


class PlaceCommandHandler(SimpleCommandHandler):
    command_names = ["place", "put", "plac", "drop"]
    description = "Allows you to place something in your current location. Aliases: place, put, drop\n" \
                  "Usage: place <item name>"

    def __init__(self):
        super().__init__(self.__class__.command_names, self.__class__.description)

    def _handle_command(self, handler: 'Handler', player: 'Player', player_input: InputObject):
        first_arg = player_input.get_arg(0)
        if len(first_arg) == 0:
            self.send_help(player)
            return InputHandleType.HANDLED
        item = get_reference(player, " ".join(first_arg))

        if item is None:
            player.send_message(Item.CANNOT_SEE[1])
            return InputHandleType.HANDLED
        can_ref = item.can_reference(player)
        if can_ref[0] is False:
            player.send_message(can_ref[1])
            return InputHandleType.HANDLED
        can_put = item.can_put(player)
        if can_put[0] is False:
            player.send_message(can_put[1])
            return InputHandleType.HANDLED
        previous_holder = item.holder
        if item.change_holder(previous_holder, player.location):
            player.location.on_place(handler, item, player)
            player.send_message(Message("You placed {}.", named_variables=[item]))
        return InputHandleType.HANDLED


class YellCommandHandler(SimpleCommandHandler):
    command_names = ["yell", "yel", "grita", "grito", "shout", "holler", "echo"]
    description = "Allows you to yell out something that someone or something may respond to. Use with caution.\n" \
                  "Aliases: yell\nUsage: yell <text to yell>"

    def __init__(self):
        super().__init__(self.__class__.command_names, self.__class__.description)

    def can_yell(self, player: 'Player') -> bool:
        return True

    def _handle_command(self, handler: 'Handler', player: 'Player', player_input: InputObject):
        first_arg = player_input.get_arg(0, False)
        if len(first_arg) == 0:
            self.send_help(player)
            return InputHandleType.HANDLED
        if self.can_yell(player):
            player.location.on_yell(handler, player, player_input)
        else:
            player.send_message("You can't yell right now.")
        return InputHandleType.HANDLED


class UseCommandHandler(SimpleCommandHandler):
    command_names = ["use"]
    description = "Allows you to use an item. Aliases: Use\n" \
                  "Usage: use <item name>"

    def __init__(self):
        super().__init__(self.__class__.command_names, self.__class__.description)

    def _handle_command(self, handler: 'Handler', player: 'Player', player_input: InputObject):
        first_arg = player_input.get_arg(0)
        if len(first_arg) == 0:
            self.send_help(player)
            return InputHandleType.HANDLED
        item = get_reference(player, " ".join(first_arg))
        can_ref = Item.CANNOT_SEE
        if item is not None:
            can_ref = item.can_reference(player)
        if can_ref[0] is False:
            player.send_message(can_ref[1])
            return InputHandleType.HANDLED
        can_use = item.can_use(player)
        if can_use[0] is False:
            player.send_message(can_use[1])
            return InputHandleType.HANDLED
        player.location.on_item_use(handler, player, item)
        return InputHandleType.HANDLED


class NameCommandHandler(SimpleCommandHandler):
    command_names = ["name"]
    description = "Allows you to tell what your own name is.\nUsage: name"

    def __init__(self):
        super().__init__(self.__class__.command_names, self.__class__.description)

    def _handle_command(self, handler: 'Handler', player: 'Player', player_input: InputObject):
        player.send_message(Message("Your name is {}.", named_variables=[player]))
        return InputHandleType.HANDLED


class InventoryCommandHandler(SimpleCommandHandler):
    command_names = ["inv", "inventory", "inve", "items"]
    description = "Allows you to see what's in your inventory"

    def __init__(self):
        super().__init__(self.__class__.command_names, self.__class__.description)

    def _handle_command(self, handler: 'Handler', player: 'Player', player_input: InputObject):
        amount = len(player.items)
        if amount == 0:
            player.send_message("You don't have anything in your inventory")
        elif amount == 1:
            player.send_message(Message("You have {}.", named_variables=player.items))
        names = []
        for i in range(0, amount):
            names.append("{}")

        player.send_message(Message("You  have these items: {}".format(", ".join(names)), named_variables=player.items))

        return InputHandleType.HANDLED


class LocateCommandHandler(SimpleCommandHandler):
    command_names = ["locate", "location", "where", "loc"]
    description = "Allows you to tell where you are"

    def __init__(self):
        super().__init__(self.__class__.command_names, self.__class__.description)

    def _handle_command(self, handler: 'Handler', player: 'Player', player_input: InputObject):
        player.send_message(
            Message("You are at {}, which is '{}'", named_variables=[player.location.point, player.location]))
        return InputHandleType.HANDLED