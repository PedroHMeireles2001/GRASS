import os.path
from enum import Enum
from typing import Optional, List, Callable, Dict

import pygame.image

from src.model.effects import OnAttackEvent
from src.model.entity import Entity, DamageType
from src.model.player import Player
from src.utils import get_assets_path


class EquipSlot(str, Enum):
    LEFT_HAND = "lhand"
    RIGHT_HAND = "rhand"
    HEAD = "head"
    ARMOR = "armor"
    FEET = "feet"
    RING = "ring"



class GenericItem:
    def __init__(self,id, name, description, value, useless, image=None):
        self.id = id
        self.name = name
        self.description = description
        self.value = value
        self.image = pygame.image.load(os.path.join(get_assets_path(), "items", image)) if image else None
        self.useless = useless
        if self.image is None:
            self.image = pygame.image.load(os.path.join(get_assets_path(), "items", "generic.png"))

    def __eq__(self, other):
        if isinstance(other, GenericItem):
            return self.name == other.name and type(self) == type(other)
        return False

    def __hash__(self):
        return hash((self.name, type(self)))


class Usable(GenericItem):
    def __init__(self, name, description, value, on_use=Optional[Callable[[Player, List[Entity]], None]], image=None,
                 self_use=True, skip_turn=False, area=False, targeted=False):
        super().__init__(name, description, value, False, image)
        self.self_use = self_use
        self.skip_turn = skip_turn
        self.on_use = on_use
        self.area = area
        self.targeted = targeted

    def get_targets(self, player, target, all_enemies):
        targets = []
        if self.self_use:
            targets.append(player)
        if self.area:
            targets = targets + all_enemies
        elif self.targeted:
            targets.append(target)

        return targets


class GenericEquip(GenericItem):
    def __init__(self, name, description, slot, value, image=None, on_equip=Optional[Callable[[Player], None]],
                 on_unequip=Optional[Callable[[Player], None]],
                 on_take_damage=Optional[Callable[[Player, Entity], OnAttackEvent]]):
        super().__init__(name, description, value, False, image)
        self.on_equip = on_equip
        self.on_unequip = on_unequip
        self.on_take_damage = on_take_damage
        self.slot = slot


class GenericWeapon(GenericEquip):
    def __init__(self, name, description, value, image=None, on_equip=Optional[Callable[[Player], None]],
                 on_unequip=Optional[Callable[[Player], None]],
                 on_take_damage=Optional[Callable[[Player, Entity], OnAttackEvent]]):
        super().__init__(name, description, EquipSlot.RIGHT_HAND, value, image, on_equip, on_unequip, on_take_damage)


class HealingPotion(Usable):
    def __init__(self, id, potency,value):
        self.potency = potency
        super().__init__("Healing Potion", "heals 20 to player", value=value, skip_turn=False)

    def _on_use(self, player, targets):
        player.heal(self.potency)


class Bomb(Usable):
    def __init__(self, id,potency,value):
        self.potency = potency
        super().__init__("Bomb", description="Give 10 damage to all enemies", value=value, skip_turn=True, area=True,
                         self_use=False, on_use=self._on_use)

    def _on_use(self, player, targets: List[Entity]):
        for target in targets:
            target.apply_damage(player, self.potency, DamageType.FIRE,None)


ITEMS = {
    1:HealingPotion(1,20,25),
    2:HealingPotion(2,50,50),
    3:Bomb(3,5,25),
    4:Bomb(4,10,50)
}
