import random
from enum import Enum

from src.model.attribs import CharacterAttrib
from src.model.effects import EffectEnum
from src.model.entity import Entity, EntityCategory
from src.utils import print_debug


class EnemyEnum(str,Enum):
    SKELETON = "skeleton"
    BANDIT = "bandit"
    ZOMBIE = "zombie"
    ANGRY_VILLAGER = "angry_villager"




class Zombie(Entity):
    def __init__(self):
        super().__init__("zombie.png", "Zombie", 15, 0, 8, 10,type=EnemyEnum.ZOMBIE,category=EntityCategory.UNDEAD,attributes=self._get_attribs())

    def die(self, target, damage: float,combat=None):
        result = random.randint(1,20)
        print_debug(f"Zumbi tentou reviver e tirou {result} precisando tirar {8 + damage}")
        if result <= 8 + damage:
            super().die(target, damage,combat)
        else:
            self.heal(5 + int(damage))
        self.apply_effect(EffectEnum.STUNNED,1)
        if combat:
            combat.print_text(f"{self.name} revives")
    def _get_attribs(self):
        return {
            CharacterAttrib.STRENGTH: 10,
            CharacterAttrib.DEXTERITY: 8,
            CharacterAttrib.CONSTITUTION: 14,
            CharacterAttrib.INTELLIGENCE: 6,
            CharacterAttrib.WISDOM: 8,
            CharacterAttrib.CHARISMA: 6
        }

ENEMY_FACTORY = {
    EnemyEnum.SKELETON: Entity(
        name="Skeleton",
        health=10,
        armor=0,
        dodge=10,
        base_damage=10,
        image_str="skeleton.png",
        type=EnemyEnum.SKELETON,
        attributes={
            CharacterAttrib.STRENGTH: 8,
            CharacterAttrib.DEXTERITY: 12,
            CharacterAttrib.CONSTITUTION: 8,
            CharacterAttrib.INTELLIGENCE: 10,
            CharacterAttrib.WISDOM: 10,
            CharacterAttrib.CHARISMA: 6
        }
    ),
    EnemyEnum.BANDIT: Entity(
        name="Bandit",
        health=6,
        armor=5,
        dodge=12,
        base_damage=15,
        image_str="bandit.png",
        type=EnemyEnum.BANDIT,
        attributes={
            CharacterAttrib.DEXTERITY: 14,
            CharacterAttrib.CHARISMA: 12
        }
    ),
    EnemyEnum.ZOMBIE: Zombie(),
    EnemyEnum.ANGRY_VILLAGER: Entity(
        name="Angry Villager",
        health=6,
        armor=0,
        dodge=10,
        base_damage=5,
        image_str="villager.png",
        type=EnemyEnum.ANGRY_VILLAGER,
        attributes={}
    )
}
