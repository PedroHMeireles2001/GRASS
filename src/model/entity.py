import os.path
import random
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, TYPE_CHECKING, Dict

import pygame.image

from src.constants import IMAGE_SIZE
from src.model.attribs import CharacterAttrib, fill_missing_attribs
from src.model.effects import EffectEnum, EFFECTS
from src.utils import print_debug, get_mod, get_assets_path

if TYPE_CHECKING:
    from src.model.monster import EnemyEnum

class EntityCategory(str,Enum):
    HUMANOID = "humanoid"
    UNDEAD = "undead"

class DamageType(str,Enum):
    FIRE = "fire",
    COLD = "cold",
    ELECTRIC = "electric"
    POISON = "poison"
    CORROSIVE = "corrosive"
    SLASHING = "slashing"
    BLUDGEONING = "bludgeoning",
    PIERCING = "piercing",
    MAGICAL = "magical"
    PSYCHIC = "psychic"
    SACRED = "sacred",
    PROFANE = "profane",
    TRUE = "true"


class Damageable(ABC):
    @abstractmethod
    def apply_damage(self,target, damage: float,damage_type: DamageType,combat=None) -> int:
        pass
    @abstractmethod
    def die(self, target, damage: float,combat):
        pass

    @abstractmethod
    def heal(self,heal:int):
        pass

class Entity(Damageable):


    def __init__(self, image_str, name: str, health: int, armor: float, dodge: int, base_damage: int,attributes: Dict[CharacterAttrib, int], type:Optional["EnemyEnum"] = None,
                 damage_multiplier=None,category = EntityCategory.HUMANOID,crit_multiplier = 2):
        if damage_multiplier is None:
            damage_multiplier = {}

        self.name = name
        self.crit_multiplier = crit_multiplier
        self.health = health
        self.max_health = health
        self.armor = armor
        self.dodge = dodge
        self.effects = []
        self.damage_multiplier = damage_multiplier
        self.attributes = fill_missing_attribs(attributes)
        self.dead = False
        self.base_damage = base_damage
        self.type = type
        self.category = category
        self.image = None
        if image_str is not None:
            self.image = pygame.transform.scale(pygame.image.load(os.path.join(get_assets_path(),"entities",image_str)), IMAGE_SIZE)

    def get_spell_difficult_class(self):
        return 10 + get_mod(self.attributes[CharacterAttrib.INTELLIGENCE])

    def attrib_test(self,attrib):
        return random.randint(1,20) + get_mod(self.attributes[attrib])

    def die(self, target, damage: float,combat=None):
        self.dead = True

    def heal(self, heal: int):
        self.health = min(self.max_health,self.health + heal)

    def clear_negative_effects(self):
        for effect in [effect for effect in self.effects if not effect.positive]:
            self.effects.remove(effect)

    def get_damage_type(self):
        return DamageType.BLUDGEONING

    def take_turn(self,combat):
        skip = self.dead
        for effect in self.effects:
            canceled = effect.on_new_turn(self)
            if canceled:
                skip = True
            effect.duration -= 1
            if effect.duration <= 0:
                self.effects.remove(effect)

        self.take_turn_impl(combat,skip)

    def take_turn_impl(self,combat,skip):
        if skip:
            return
        combat.print_text(f"{self.name} is attacking {combat.game.player.name}")
        passed, result, damage = self.attack(combat.game.player)
        combat.print_text(f"{self.name} rolled {result}" if result != 20 else f"{self.name} rolled a critical!")
        if passed and damage > 0:
            combat.delayed_action(
                text=f"{self.name} deals {damage} damage to {combat.game.player.name}",
                action=combat.game.player.apply_damage(self, damage,combat)
            )

    def apply_damage(self, target, damage: float,damage_type: DamageType,combat=None):
        if damage_type in self.damage_multiplier.keys():
            damage *= self.damage_multiplier[damage_type]
        if target is not None:
            for effect in self.effects:
                if effect.on_damaged:
                    result_event = effect.on_damaged(effect)
                    if result_event.cancelled:
                        return
                    if result_event.new_result:
                        damage = result_event.new_result

        self.health -= damage
        if self.health <= 0:
            self.die(target, damage,combat)

    def calculate_damage(self,damage):
        damage = damage * (100 / (100 + self.armor))
        return damage

    def apply_effect(self, effect: EffectEnum, duration: int) -> bool:
        # 1️⃣ Verifica se o efeito já existe
        for active_effect in self.effects:
            if active_effect.name == EFFECTS[effect].name:
                if active_effect.stackable:
                    active_effect.duration += duration
                    return True
                return False

        # 2️⃣ Caso não exista, cria nova instância
        base_effect = EFFECTS[effect]
        new_effect = base_effect.copy(deep=True)
        new_effect.duration = duration

        self.effects.append(new_effect)

        # 3️⃣ Aplica efeito
        if new_effect.on_apply:
            new_effect.on_apply(self)

        return True

    def iniciative(self):
        return random.randint(1,20) + get_mod(self.dodge)

    def get_damage(self) -> float:
        return self.base_damage + get_mod(self.attributes[CharacterAttrib.STRENGTH])

    def attacked(self,attacker,passed,result) -> int:
        for effect in self.effects:
            if effect.on_attacked:
                print_debug(f"Efeito: {effect.name} - Attacked {self.name}")
                result_event = effect.on_attacked(attacker,passed,result)
                if result_event.cancelled:
                    return 0
                if result_event.new_result:
                    result = result_event.new_result
        return result

    def get_attack_mod(self,spell=False):
        return get_mod(self.attributes[CharacterAttrib.DEXTERITY if not spell else CharacterAttrib.INTELLIGENCE])

    def get_spell_damage_mod(self):
        return get_mod(self.attributes[CharacterAttrib.INTELLIGENCE])

    def attack(self,target,spell=False,spell_damage=0,spell_damage_type=DamageType.MAGICAL):
        result = random.randint(1,20) + self.get_attack_mod(spell=spell)
        for effect in self.effects:
            if effect.on_attack:
                result_event = effect.on_attack(self,target,result)
                if result_event.cancelled:
                    return False,0,0
                if result_event.new_result:
                    result = result_event.new_result

        passed = result >= target.dodge or result == 20

        result = target.attacked(self,passed,result)
        passed = result >= target.dodge or result == 20
        damage = 0
        if passed:
            damage = (spell_damage + self.get_spell_damage_mod() if spell else self.get_damage()) * (
                self.crit_multiplier if result == 20 else 1)
            damage = target.calculate_damage(damage)
        return passed, result, damage

