from enum import Enum
from typing import List, Optional, Callable

from pydantic import BaseModel

from src.model.classes import CharacterClass
from src.model.effects import EffectEnum
from src.model.entity import Entity


class Skill(BaseModel):
    name: str
    min_level: int
    cost: int
    classes: List[CharacterClass]
    description: str
    is_combat: bool
    is_targeted: bool = False
    skip_turn: bool = True
    execute: Optional[Callable[[Entity],None]] = None

class SkillEnum(str, Enum):
    ACCURATE_ATTACK = "accurate_shot",
    RECKLESS_ATTACK = "reckless_attack"

SKILL_FACTORY = {
    SkillEnum.ACCURATE_ATTACK: Skill(
        name="Accurate Attack",
        min_level=1,
        cost=0,
        classes=[CharacterClass.ROGUE,CharacterClass.WARRIOR],
        description="Accurate Attack",
        is_combat=True,
        execute=lambda player: player.apply_effect(EffectEnum.AIMING,1)
    ),
    SkillEnum.RECKLESS_ATTACK : Skill(
        name="Reckless Attack",
        min_level=1,
        cost=0,
        classes=[CharacterClass.BARBARIAN,CharacterClass.WARRIOR],
        description="Reckless Attack",
        is_combat=True,
        skip_turn=False,
        execute=lambda player: player.apply_effect(EffectEnum.RECKLESS,1)
    )
}

