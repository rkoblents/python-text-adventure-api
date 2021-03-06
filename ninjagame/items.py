from enum import Enum, unique
from typing import Tuple

from textadventure.battling.weapon import Weapon
from textadventure.entity import Entity
from textadventure.handler import Handler
from textadventure.player import Player
from textadventure.sending.message import Message


@unique
class MaterialType(Enum):
    WOOD = ("wood", 10)
    IRON = ("iron", 20)
    STEEL = ("steel", 30)
    SHINY_STEEL = ("shiny steel", 40)
    CHINESE_STEEL = ("chinese steel", 41)


SwordTypeValue = Tuple[str, MaterialType, int]


@unique
class SwordType(Enum):
    """
    A simple enum where all the members are of the type SwordTypeValue

    The items in this enum represent the different materials a sword is made out of
    """
    WOODEN = ("wooden", MaterialType.WOOD, 5)
    IRON = ("iron", MaterialType.IRON, 8)
    STEEL = ("steel", MaterialType.STEEL, 10)
    SHINY_STEEL = ("shiny steel", MaterialType.SHINY_STEEL, 12)
    CHINESE_STEEL = ("chinese steel", MaterialType.CHINESE_STEEL, 12)  # idk why I added this one


SwordMoveTypeValue = Tuple[str, int]
"""Represents a the value for SwordMoveType where [0] is the string name and [1] is the index used for \
    Tuple[float, float, float]"""


@unique
class SwordMoveType(Enum):
    """
    A simple enum where all the members are of the type SwordTypeValue

    The items in this enum represent the different move types available when attacking with a normal sword
    """
    SLASH = ("slash", 0)
    SLAM = ("slam", 1)
    STAB = ("stab", 2)


class Sword(Weapon):
    def __init__(self, sword_type: SwordType):
        from ninjagame.utils import SwordMoveOption  # to avoid import errors
        super().__init__("{} sword".format(sword_type.value[0]),
                         move_options=[SwordMoveOption(self, move_type, 1) for move_type in SwordMoveType])
        self.sword_type = sword_type

    def see(self, handler: Handler, player: Player):
        player.send_message(Message("You see a nice {}.", named_variables=[self]))

    def can_smell(self, player: Player):
        return True, "You can smell this"

    def smell(self, handler: Handler, player: Player):
        player.send_message("It smells like a sword.")

    def can_feel(self, player: Player):
        return True, "You can feel this"

    def feel(self, handler: Handler, player: Player):
        player.send_message(Message("It feels like a nice, sharp {}.", named_variables=[self]))

    def can_taste(self, player: Player):
        return True, "You can taste this."

    def taste(self, handler: Handler, player: Player):
        player.send_message("It tastes like a... Eww. don't lick your sword.")

    def can_use(self, entity: Entity):
        return True, "You can use this as long as you're in the right place"

    def listen(self, handler: Handler, player: Player):
        raise Exception("Cannot listen to a sword")

