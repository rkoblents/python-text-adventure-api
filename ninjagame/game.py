from typing import List

from ninjagame.data import EventsObject
from ninjagame.entites import PlayerFriend, OtherPerson, LauraPerson, NinjaDude
from ninjagame.locations import EastCenterSpiderWebForest, CenterSpiderWebForest, EntranceSpiderWebForest, \
    WestInsideEntrance, EastInsideEntrance, InsideEntrance, Entrance
from ninjagame.managing import NinjaGamePropertyManager
from textadventure.customgame import CustomGame
from textadventure.handler import Handler
from textadventure.input.inputhandling import InputHandler
from textadventure.location import Location
from textadventure.manager import Manager
from textadventure.player import Player
from textadventure.saving.savables import PlayerSavable


class NinjaGame(CustomGame):
    def __init__(self):
        super().__init__("Trail of Ninjas")

    def create_custom_input_handlers(self) -> List[InputHandler]:
        return []

    def new_player(self, player: Player):
        # player.send_message("Yay you are a new player!" + str(player.uuid))
        player[PlayerFriend] = PlayerFriend("Friend")  # not used as a magic string
        player[EventsObject] = EventsObject()

    def create_locations(self) -> List[Location]:
        return [Entrance(), InsideEntrance(), EastInsideEntrance(), WestInsideEntrance(),
                EntranceSpiderWebForest(), CenterSpiderWebForest(), EastCenterSpiderWebForest()]

    def create_custom_managers(self) -> List[Manager]:
        return [NinjaGamePropertyManager()]

    def add_other(self, handler: Handler) -> None:
        handler.living_things.extend([OtherPerson(), LauraPerson(), NinjaDude()])
