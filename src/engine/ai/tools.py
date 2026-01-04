import random
import time
from enum import Enum
from typing import Any, TYPE_CHECKING, List, Dict
import copy
from langchain_core.tools import BaseToolkit, BaseTool, Tool, StructuredTool
from pydantic import BaseModel, PrivateAttr, Field

from src.model.Item import GenericItem, UsablesEnum, USABLE_FACTORY
from src.model.attribs import CharacterAttrib, CharacterExpertise
from src.model.combat import Combat
from src.model.monster import EnemyEnum, ENEMY_FACTORY
from src.utils import get_mod, print_debug

if TYPE_CHECKING:
    from src.engine.Game import Game



class RollType(str,Enum):
    NORMAL = "normal"
    ADVANTAGE = "advantage"
    DISADVANTAGE = "disadvantage"

class REWARDS(BaseModel):
    gold: int
    xp: int

class STEAL(BaseModel):
    gold_loss: int = Field(ge=1,description="Amount of gold to loss")

class Damage(BaseModel):
    damage:int = Field(description="Positive value will damage the player.Negative value will heal the player")

class AttribSchema(BaseModel):
    character_attribute:CharacterAttrib
    roll_type: RollType

class ExpertiseSchema(BaseModel):
    character_expertise:CharacterExpertise
    roll_type: RollType

class D20Roll(BaseModel):
    modifier: int
    roll_type: RollType

class CombatInitializer(BaseModel):
    enemies:List[EnemyEnum]
    fleeable: bool

class GenericItemModel(BaseModel):
    name:str
    description:str
    value:int
    quantity:int

class GenericItems(BaseModel):
    items: List[GenericItemModel]

class UsableItems(BaseModel):
    items: List[UsablesEnum]

class PlayerToolkit(BaseToolkit):
    _game: "Game" = PrivateAttr()

    def __init__(self, game: "Game", **data: Any):
        super().__init__(**data)
        self._game = game

    def get_tools(self) -> list[BaseTool]:
        return [
            StructuredTool(
                name="player_attribute_test",
                description="Roll a pure Attribute Test for player. only use if you don't have expertise in the game that fits the test",
                args_schema=AttribSchema,
                func=self.roll_attribute_test
            ),
            StructuredTool(
                name="player_expertise_test",
                description="Roll a Expertise Test for player.",
                args_schema=ExpertiseSchema,
                func=self.roll_expertise_test
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
                name="steal_player",
                description="Steals gold from the player. POSITIVE VALUE ONLY",
                args_schema=STEAL,
                func=self.punish_player
            ),
            StructuredTool(
                name="damage_heal_player",
                description="Damage or Heal the player.",
                args_schema=Damage,
                func=self.heal_player
            ),
            StructuredTool(
                name="give_generic_item",
                description="Give generic items to the player",
                args_schema=GenericItems,
                func=self.give_generic_items
            ),
            StructuredTool(
                name="give_usable_item",
                description="Give usable items to the player",
                args_schema=UsableItems,
                func=self.give_usable_items
            ),
            Tool(
                name="sell_player_trash",
                description="Sell ALL useless items of player",
                func=self.sell_trash
            ),
            Tool(
                name="player_rest",
                description="Run this tool every time the player sleep",
                func=self.rest
            )
        ]

    # 👇 métodos públicos usados como tools

    def initialize_combat(self,enemies: List[EnemyEnum],fleeable):
        combat = Combat(
            game=self._game,
            enemies=[copy.copy(ENEMY_FACTORY[enemy]) for enemy in enemies],
            fleeable=fleeable
        )
        self._game.scene.wait_combat_confirm(combat)

        return {
            "event": "combat_started",
            "instructions": "the game will take care of the combat, you don't need to narrate the combat"
        }

    def rest(self,_):
        self._game.player.rest()

    def sell_trash(self,_):
        self._game.player.sell_trash()
        return "All golds have been added to the player's sheet automatically"

    def give_generic_items(self,items):
        for item in items:
            self._game.player.give_item(GenericItem(
                name=item.name,
                description=item.description,
                value=item.value,
                useless=True
            ),item.quantity)

    def give_usable_items(self, items: List[UsablesEnum]):
        for item in items:
            original_item = USABLE_FACTORY[item]
            cloned_item = copy.copy(original_item)

            self._game.player.give_item(cloned_item, 1)

    def roll_expertise_test(self,character_expertise:CharacterExpertise,roll_type:RollType):
        primary_attribute = character_expertise.get_associated_ability()
        mod = get_mod(self._game.player.attributes[primary_attribute])
        if character_expertise in self._game.player.expertises:
            mod += self._game.player.proficiency
        return self.roll_d20(mod,roll_type)


    def heal_player(self,heal):
        if heal < 0:
            return "Positive values only!"

        self._game.player.heal(heal)

        return {
            "updated_player": self._game.player.to_text()
        }

    def punish_player(self,gold_loss,damage):
        if gold_loss < 0 or damage < 0:
            return "Positive values only!"

        self._game.player.take_gold(gold_loss)
        calculated_damage = self._game.player.calculate_damage(damage)
        self._game.player.apply_damage(None,calculated_damage)

        return {
            "updated_player": self._game.player.to_text()
        }


    def reward_player(self,gold,xp):
        if gold < 0 or xp < 0:
            return "Positive values only!"
        self._game.player.gold += gold
        self._game.player.give_xp(xp)

        return {
            "updated_player": self._game.player.to_text()
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
            "crit": result == 20,
            "crit_fail": result == 1
        }