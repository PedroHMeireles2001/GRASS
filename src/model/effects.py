import random
from enum import Enum
from typing import Optional, Callable

from pydantic import BaseModel

from src.utils import print_debug


class EffectEnum(str, Enum):
    AIMING = "aiming"
    RECKLESS = "reckless"
    STUNNED = "stunned"
    DIVINE_SMITH = "divine_smith"

class CancellableEvent(BaseModel):
    cancelled: bool = True

class OnNewTurnResult(CancellableEvent):
    pass

class OnDieEvent(CancellableEvent):
    pass

class EventResult(BaseModel):
    new_result: int

class OnAttackEvent(BaseModel):
    new_result: int
    cancelled: bool = False



class Effect(BaseModel):
    name: str
    description: str
    duration: int = 1
    positive: bool
    stackable: bool = True
    skip_turn: bool = False

    on_apply: Optional[Callable[[object], None]] = None
    on_unapply: Optional[Callable[[object], None]] = None
    on_attack: Optional[Callable[[object,object,int], OnAttackEvent]] = None
    on_attacked: Optional[Callable[[object,bool,int], OnAttackEvent]] = None
    on_damaged: Optional[Callable[[object,int], OnAttackEvent]] = None
    on_new_turn: Optional[Callable[[object], OnNewTurnResult]] = None
    on_die: Optional[Callable[[object,int],OnDieEvent]] = None

    class Config:
        arbitrary_types_allowed = True

def advantage(_, __, result) -> OnAttackEvent:
    advg_result = random.randint(1, 20)
    new_result = max(advg_result, result)

    print_debug(f"Rolada com vantagem: {result} -> {advg_result} = {new_result}")

    return OnAttackEvent(new_result=new_result)


def desavantage(_, __, result) -> OnAttackEvent:
    advg_result = random.randint(1, 20)
    new_result = min(advg_result, result)

    print_debug(f"Rolada com desvantagem: {result} -> {advg_result} = {new_result}")

    return OnAttackEvent(new_result=new_result)

def skip(_):
    return OnNewTurnResult(cancelled=True)



EFFECTS = {
    EffectEnum.AIMING: Effect(
        name="AIMING",
        description="Aiming",
        duration=1,
        positive=True,
        on_attack=advantage
    ),
    EffectEnum.RECKLESS: Effect(
        name="RECKLESS",
        description="Reckless",
        duration=1,
        positive=True,
        on_attacked=advantage,
        on_attack=advantage
    ),
    EffectEnum.STUNNED: Effect(
        name="STUNNED",
        description="Skips x turns",
        positive=False,
        duration=1,
        on_new_turn=skip
    )
}

