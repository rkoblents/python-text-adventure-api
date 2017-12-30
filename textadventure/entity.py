from abc import ABC, abstractmethod
from typing import Type, List, TYPE_CHECKING
from uuid import UUID, uuid4

from textadventure.action import Action
from textadventure.item.holder import Holder
from textadventure.sending.commandsender import CommandSender
from textadventure.sending.message import Message
from textadventure.utils import MessageConstant, CanDo, are_mostly_equal

if TYPE_CHECKING:
    from textadventure.location import Location


class Identifiable:
    def __init__(self, uuid: UUID = None):
        if uuid is None:
            uuid = uuid4()
        self.uuid = uuid


class Living:
    UNKNOWN_LIVING_NAME = "???"

    """
    A Living object unlike an Entity, doesn't have a location which is the biggest difference.
    This will help with the story so you don't have to worry about teleporting an entity just so they can talk

    Basically an entity that the location manipulates and that isn't controlled by outside sources and it's only state\
        is it's name
    """

    def __init__(self, name):
        self.name = name

    def get_used_name(self, sender: CommandSender) -> str:
        """
        By default, returns self.name but can be overridden to create the effect that someone doesn't know this person

        :param sender: The person that the returned name will be showed to
        :return: The string that represents the name the passed 'living' will be shown
        """
        return self.name

    def tell(self, sender: CommandSender, message: MessageConstant):
        message = CommandSender.get_message(message)
        # if we change the way we do this, like doing this at a later time.
        #   Things could get messed up on the correct name
        message.text = "|" + self.get_used_name(sender) + ":| " + message.text
        sender.send_message(message)

    def is_reference(self, reference: str) -> bool:
        return are_mostly_equal(reference, self.name)

    def __str__(self):
        """Should be used in Message to replace named_variables with"""
        return self.name


class Health:
    def __init__(self, current_health: int, max_health: int):
        self.current_health = current_health
        self.max_health = max_health

    def __str__(self):
        return "{}/{}".format(self.current_health, self.max_health)

    def change_by(self, hp_change: int):
        """
        The recommended way to change the current_health

        :param hp_change:
        :return:
        """
        self.current_health += hp_change
        self.check_range()

    def check_range(self):
        if self.current_health < 0:
            self.current_health = 0
        if self.current_health > self.max_health:
            self.current_health = self.max_health

    def is_fainted(self):
        return self.current_health <= 0

    def is_full(self):
        if self.max_health == 0:
            return False
        return self.current_health == self.max_health


# noinspection PyAbstractClass
class Entity(Living, Holder, Identifiable):
    """
    Represents something that has a location and has health
    """
    def __init__(self, name: str, health: Health, location: 'Location', uuid: UUID = None):
        """
        Creates an Entity the the given parameters

        :param name: The name of the entity
        :param health: The health of the entity
        :param location: The location of the entity.
        :param uuid: The id of the entity or None if you want to create a new id
        """
        super().__init__(name)
        Holder.__init__(self)
        Identifiable.__init__(self, uuid)

        self.health = health

        self.location = location
        """
        The location of the entity. Unless initializing for the first time, you almost should never set this
        by yourself because you probably want to do it with GoAction or something similar that abstracts a few 
        details away.
        """
        if uuid is None:
            uuid = uuid4()
        self.uuid = uuid
        """The id of the entity. You should use this to compare entities but you should assume that an entity\
        created in a custom location may not always have the same id in every instance of a game."""

    # def can_entity_pass(self, entity: 'Entity') -> CanDo:
    #     """ Not going to use this - define in HostileEntity
    #     Called when a entity, usually a player, is trying to go to another location.
    #     This will be called if this entity is in the same location as the entity trying to move to another location
    #     :param entity: The entity trying to move to another location
    #     :return: A CanDo tuple where [0] is a boolean value representing the the entity can pass and if False,\
    #                 [1] is the reason why the entity can't pass. (It will be displayed)
    #     """
    #     return True, "You can pass, a hostile entity might say otherwise, though."

    def can_do_action(self, handler, entity_action: 'EntityActionToEntity') -> CanDo:
        """
        This method should not be called outside of entity.py but may be overridden by any subclass of entity to \
        listen for Actions that are trying to be executed on this entity hence why only EntityActionToEntity \
        are passed

        Note this will be called when try_action is called meaning that it will have been called after all the \
        calls to on_action in each Manager registered in the handler class

        :param handler: The Handler object
        :param entity_action: The action that entity is requesting. asked_entity should be equal to self when called.
        :return: A CanDo where if [0] is False, the message at [1] will be sent to entity_action.entity
        """
        # TODO add more documentation and state in docs whether or not overriding subclasses should cancel the Action\
        #      or do more stuff that may be unwanted or have side effects
        return True, "You have received the default reply from an Entity."


class HostileEntity(Entity):  # abstract

    CANNOT_PASS_STRING = "You can't pass because {} wants to eat you."

    def __init__(self, name: str, health: Health, location):
        super().__init__(name, health, location)

    @abstractmethod
    def can_entity_pass(self, entity: Entity) -> CanDo:
        """
        Will be used by the HostileEntityManager

        :param entity: The entity that is trying to go to another location
        :return: A CanDo
        """
        # return super().can_entity_pass(entity)
        pass


class SimpleHostileEntity(HostileEntity):
    def __init__(self, name: str, health: Health, location, hostile_to_types: List[Type[Entity]]):
        super().__init__(name, health, location)
        self.hostile_to_types = hostile_to_types

        self.hostile_now = True
        self.can_not_pass = False, Message(self.__class__.CANNOT_PASS_STRING, named_variables=[self])

    def _can_pass(self, entity: Entity) -> CanDo:
        """
        Used to be overridden by subclasses where the main implementation is handled in the can_entity_pass method
        By default, this returned self.health.is_fainted()

        The message in the returned value at [1] will never be displayed, but take it seriously in case of needed
        debugging in the future.

        :param entity:
        :return:
        """
        if self.health.is_fainted():
            return True, "I can't fight you because I'm dead."
        return False, "Message shouldn't be displayed. There is no reason to let this entity pass."

    def _is_type_target(self, entity: Entity) -> bool:
        """
        :param entity: The entity to test its type for
        :return: True if the entity's type is a target based upon self.hostile_to_types
        """
        for t in self.hostile_to_types:
            if isinstance(entity, t):
                return True

        return False

    def can_entity_pass(self, entity: Entity):
        if not self.hostile_now:
            return True, "I'm not hostile right now"

        can_pass = self._can_pass(entity)
        if can_pass[0]:  # most of the time, this should be false
            return can_pass

        if self._is_type_target(entity):
            return self.can_not_pass

        return True, "I don't really want to eat you because you aren't of the type of entity I like."

    def send_message(self, message):
        pass


class CommunityHostileEntity(SimpleHostileEntity):
    def __init__(self, name: str, health: Health, location, hostile_to_types: List[Type[Entity]]):
        super().__init__(name, health, location, hostile_to_types)
        self.entities_lost_to = []
        self.entities_won_against = []

    def _can_pass(self, entity: Entity):
        # We aren't going to call super because even if this entity is dead, we want them to fight the entity if\
        #   they haven't beat us yet.

        if entity in self.entities_lost_to:
            return True, "Sure, you can pass, you already beat me."

        return False, "You can't pass since you haven't beaten me yet. - Should not be displayed"


# noinspection PyAbstractClass
class EntityAction(Action):  # abstract
    """
    Used when there's an entity involved in an action (or multiple entities where the entity stored in this class\
        is the one that caused it, usually being the Player (There is no PlayerAction this is it)
    Note that the overridden try_action method sends the entity a message if the returned can_do[0] will be False
    """

    def __init__(self, entity: Entity, send_on_can_not: bool = True):
        """
        :param entity: The main entity involved and the one that is basically requesting to do this action
        :param send_on_can_not: Used to determine if a message should be sent if the returned value at [0] in \
                try_action is False. By default True. Set to False if you will be returning the CanDo returned in \
                try_action. (You would do this so the message wouldn't get sent twice)
        """
        super().__init__()
        self.entity = entity
        self.send_on_can_not = send_on_can_not

    def try_action(self, handler):  # overridden
        can_do = super().try_action(handler)
        if not can_do[0] and self.send_on_can_not and isinstance(self.entity, CommandSender):
            self.entity.send_message(can_do[1])
        return can_do


# noinspection PyAbstractClass
class EntityActionToEntity(EntityAction):  # abstract
    """
    A class that isn't commonly used and only has a few uses in the current textadventure api

    Obviously, this class isn't used by itself, it needs subclasses
    """

    def __init__(self, entity: Entity, asked_entity: Entity):
        """
        :param entity: The main entity causing this action to occur. (The entity that is asking/action on asked_entity)
        :param asked_entity: The entity that entity is asked, challenged, requested of, depending on the action
        """
        super().__init__(entity)
        self.asked_entity = asked_entity
