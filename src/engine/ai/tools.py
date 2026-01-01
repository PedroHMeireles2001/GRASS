import random
import time
from enum import Enum
from typing import Any, TYPE_CHECKING, List
import copy
from langchain_core.tools import BaseToolkit, BaseTool, Tool, StructuredTool
from pydantic import BaseModel, PrivateAttr, Field

from src.model.attribs import CharacterAttrib
from src.model.combat import Combat
from src.model.monster import EnemyEnum, ENEMY_FACTORY
from src.utils import get_mod, print_debug

if TYPE_CHECKING:
    from src.engine.Game import Game



class RollType(str,Enum):
    NORMAL = "normal"
    ADVANTAGE = "advantage"
    DESADVANTAGE = "desadvantage"

class REWARDS(BaseModel):
    gold: int
    xp: int

class PUNISH(BaseModel):
    gold_loss: int = Field(ge=1,description="Amount of gold to loss")
    damage: int = Field(ge=1,description="Amount of damage")

class HEAL(BaseModel):
    heal:int = Field(ge=1,description="Cure Amount")

class AttribSchema(BaseModel):
    character_attribute:CharacterAttrib
    roll_type: RollType

class D20Roll(BaseModel):
    modifier: int
    roll_type: RollType

class CombatInitializer(BaseModel):
    enemies:List[EnemyEnum]

class PlayerToolkit(BaseToolkit):
    _game: "Game" = PrivateAttr()

    def __init__(self, game: "Game", **data: Any):
        super().__init__(**data)
        self._game = game

    def get_tools(self) -> list[BaseTool]:
        return [
            StructuredTool(
                name="player_attribute_test",
                description="Roll a pure Attribute Test for player",
                args_schema=AttribSchema,
                func=self.roll_attribute_test
            ),
            StructuredTool(
                name="roll_d20",
                description="Roll a D20",
                args_schema=D20Roll,
                func=self.roll_d20
            ),
            StructuredTool(
                name="initialize_combat",
                description="Initialize a combat",
                args_schema=CombatInitializer,
                func=self.initialize_combat
            ),
            StructuredTool(
                name="reward_player",
                description="Reward the player with gold or xp (or both).POSITIVE VALUES ONLY",
                args_schema=REWARDS,
                func=self.reward_player
            ),
            StructuredTool(
                name="punish_player",
                description="Punish the player with gold loss or damage. POSITIVE VALUE ONLY",
                args_schema=PUNISH,
                func=self.punish_player
            ),
            StructuredTool(
                name="heal_player",
                description="Heal the player. POSITIVE VALUE ONLY",
                args_schema=HEAL,
                func=self.heal_player
            ),
            Tool(
                name="player_rest",
                description="Run this tool every time the player takes a long rest",
                func=self.rest
            )
        ]

    # 👇 métodos públicos usados como tools

    def initialize_combat(self,enemies: List[EnemyEnum]):
        combat = Combat(
            game=self._game,
            enemies=[copy.copy(ENEMY_FACTORY[enemy]) for enemy in enemies]
        )
        self._game.scene.wait_combat_confirm(combat)

        return "event:combat_started"

    def rest(self):
        self._game.player.rest()

    def heal_player(self,heal):
        if heal < 0:
            return "Positive values only!"

        self._game.player.heal(heal)

        return {
            "updated_player": self._game.player.to_markdown()
        }

    def punish_player(self,gold_loss,damage):
        if gold_loss < 0 or damage < 0:
            return "Positive values only!"

        self._game.player.take_gold(gold_loss)
        calculated_damage = self._game.player.calculate_damage(damage)
        self._game.player.apply_damage(None,calculated_damage)

        return {
            "updated_player": self._game.player.to_markdown()
        }


    def reward_player(self,gold,xp):
        if gold < 0 or xp < 0:
            return "Positive values only!"
        self._game.player.gold += gold
        self._game.player.give_xp(xp)

        return {
            "updated_player": self._game.player.to_markdown()
        }

    def roll_attribute_test(
        self,
        character_attribute: CharacterAttrib,
        roll_type: RollType
    ):
        player = self._game.player
        raw_attribute = player.attributes[character_attribute]
        modifier = get_mod(raw_attribute)
        return self.roll_d20(modifier=modifier, roll_type=roll_type)

    def roll_d20(
        self,
        modifier: int,
        roll_type: RollType
    ):
        print_debug(f"Rolling with modifier: {modifier}")
        result = random.randint(1, 20)

        if roll_type != RollType.NORMAL:
            second = random.randint(1, 20)
            result = (
                max(result, second)
                if roll_type == RollType.ADVANTAGE
                else min(result, second)
            )

        return {
            "result_with_modifier": result + modifier,
            "raw_result": result,
            "crit": result == 20
        }