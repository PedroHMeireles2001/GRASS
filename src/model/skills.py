import random
from enum import Enum
from typing import List, Optional, Callable, TYPE_CHECKING

from pydantic import BaseModel

from src.model.attribs import CharacterAttrib
from src.model.classes import CharacterClass, CharacterClassEnum
from src.model.combat import Combat
from src.model.effects import EffectEnum
from src.model.entity import Entity, DamageType

class SkillEnum(str, Enum):
    ACCURATE_ATTACK = "accurate_shot",
    RECKLESS_ATTACK = "reckless_attack",
    MAGIC_MISSILE = "magic_missile",
    GUIDED_MAGIC_MISSILE = "guided_magic_missile",
    THUNDER_WAVE = "thunder_wave",
    SLEEP_SONG = "sleep_song",
    HEALING_WORDS = "healing_words",
    CURE_WOUNDS = "cure_wounds",
    DIVINE_SMITH = "divine_smith"

class Skill(BaseModel):
    name: str
    min_level: int
    cost: int
    classes: List[CharacterClassEnum]
    description: str
    enum: SkillEnum
    is_combat: bool = True
    is_targeted: bool = False
    skip_turn: bool = True
    passive: bool = False
    execute: Optional[Callable[[Entity,Entity,Combat],None]] = None




def spell_attack(player,target,combat=None,damage=5,damage_type = DamageType.MAGICAL):
    passed, result, final_damage = player.attack(target, spell=True, spell_damage=damage)
    if passed:
        target.apply_damage(player, final_damage, damage_type, combat)

def thunder_wave(player,target,combat:Combat):
    if not combat:
        return

    base_damage = 5 + player.get_spell_damage_mod()

    for enemy in combat.enemies:
        damage = base_damage
        result = enemy.attrib_test(CharacterAttrib.CONSTITUTION)
        if result >= player.get_spell_difficult_class():
            damage = base_damage // 2
        else:
            enemy.apply_effect(EffectEnum.STUNNED,1)
        enemy.apply_damage(player,damage,DamageType.BLUDGEONING,combat)

def attack(player,target,combat,extra_damage=0,extra_damage_type=None):
    passed, result, damage = player.attack(target)
    if passed:
        target.apply_damage(player,damage,player.get_damage_type(),combat)
        if extra_damage > 0 and extra_damage_type:
            target.apply_damage(player,extra_damage,extra_damage_type,combat)

def sleep_sound(player,target,combat):
    result = random.randint(1,10) + random.randint(1,10)
    if result >= target.health:
        target.apply_effect(EffectEnum.STUNNED,10)

SKILL_FACTORY = {
    SkillEnum.ACCURATE_ATTACK: Skill(
        name="Accurate Attack",
        min_level=1,
        cost=0,
        classes=[CharacterClassEnum.ROGUE,CharacterClassEnum.WARRIOR],
        description="Skip you turn. your next attack has advantage",
        is_combat=True,
        execute=lambda player,target,combat: player.apply_effect(EffectEnum.AIMING,1),
        enum=SkillEnum.ACCURATE_ATTACK
    ),
    SkillEnum.RECKLESS_ATTACK : Skill(
        name="Reckless Attack",
        min_level=1,
        cost=0,
        classes=[CharacterClassEnum.BARBARIAN,CharacterClassEnum.WARRIOR],
        description="Your next attack has advantage, but the enemies too",
        is_combat=True,
        skip_turn=False,
        execute=lambda player,target,combat: player.apply_effect(EffectEnum.RECKLESS,1),
        enum=SkillEnum.RECKLESS_ATTACK
    ),
    SkillEnum.MAGIC_MISSILE: Skill(
        name="Magic Missile",
        min_level=1,
        cost=5,
        classes=[CharacterClassEnum.MAGE],
        description="Make an attack roll against an enemy using the intelligence modifier, if you hit, deal 5 + intelligence modifier damage",
        is_combat=True,
        skip_turn=True,
        execute=lambda player, target,combat: spell_attack(player, target,combat),
        enum=SkillEnum.MAGIC_MISSILE
    ),
    SkillEnum.GUIDED_MAGIC_MISSILE: Skill(
        name="Guided Magic Missile",
        min_level=1,
        cost=5,
        classes=[CharacterClassEnum.MAGE],
        description="Deal 1 + intelligence modifier damage without attack",
        is_combat=True,
        skip_turn=True,
        execute=lambda player, target,combat: target.apply_damage(1+player.get_spell_damage_mod(),DamageType.MAGICAL,combat),
        enum=SkillEnum.GUIDED_MAGIC_MISSILE
    ),
    SkillEnum.HEALING_WORDS: Skill(
        name="Healing Words",
        min_level=1,
        cost=5,
        classes=[CharacterClassEnum.BARD,CharacterClassEnum.CLERIC,CharacterClassEnum.PALADIN],
        is_combat=True,
        description="Cure 20 + spell mod life",
        execute=lambda player, target,combat: player.heal(20 + player.get_spell_damage_mod()),
        enum=SkillEnum.HEALING_WORDS
    ),
    SkillEnum.CURE_WOUNDS: Skill(
        name="Cure wounds",
        min_level=1,
        cost=10,
        classes=[CharacterClassEnum.BARD,CharacterClassEnum.CLERIC,CharacterClassEnum.PALADIN,CharacterClassEnum.MAGE],
        is_combat=True,
        description="Cure 50 + spell mod life. Skips turn",
        execute=lambda player, target,combat: player.heal(50 + player.get_spell_damage_mod()),
        enum=SkillEnum.CURE_WOUNDS
    ),
    SkillEnum.DIVINE_SMITH:Skill(
        name="Divine Smith",
        min_level=1,
        cost=10,
        classes=[CharacterClassEnum.PALADIN],
        description="Attack and Give 5 sacred damage if pass",
        is_combat=True,
        skip_turn=True,
        execute=lambda player,target,combat: attack(player, target, combat,extra_damage=5,extra_damage_type=DamageType.SACRED),
        enum=SkillEnum.DIVINE_SMITH
    ),
    SkillEnum.THUNDER_WAVE : Skill(
        name="Thunder Wave",
        min_level=1,
        cost=10,
        classes=[CharacterClassEnum.MAGE,CharacterClassEnum.BARD],
        description="deal 5 + intelligence modifier damage to all enemies. everyone makes a constitution test, if they fail, they are stunned, if pass, take half of damage",
        is_combat=True,
        skip_turn=True,
        execute=thunder_wave,
        enum=SkillEnum.THUNDER_WAVE
    ),
    SkillEnum.SLEEP_SONG: Skill(
        name="Sleep song",
        min_level=1,
        cost=10,
        classes=[CharacterClassEnum.BARD],
        description="roll two d10s, if the result is greater than or equal to the target's total health, they will be stunned for 10 rounds",
        execute=sleep_sound,
        enum=SkillEnum.SLEEP_SONG
    )
}

