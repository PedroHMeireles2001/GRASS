import random
import time
from enum import Enum
from typing import Any, TYPE_CHECKING, List, Dict
import copy
from langchain_core.tools import BaseToolkit, BaseTool, Tool, StructuredTool
from pydantic import BaseModel, PrivateAttr, Field

from src.model.Item import GenericItem, ITEMS, Usable
from src.model.attribs import CharacterAttrib, CharacterExpertise
from src.model.combat import Combat
from src.model.entity import DamageType
from src.model.monster import EnemyEnum, ENEMY_FACTORY
from src.model.skills import SkillEnum, SKILL_FACTORY
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
    damage:int
    damage_type: DamageType

class Heal(BaseModel):
    heal_amount: int
    remove_negative_effects: bool

class AttribSchema(BaseModel):
    character_attribute:CharacterAttrib
    roll_type: RollType

class ExpertiseSchema(BaseModel):
    character_expertise:CharacterExpertise
    roll_type: RollType

class D20Roll(BaseModel):
    modifier: int
    roll_type: RollType

class UseItem(BaseModel):
    item_id: int

class UseSkill(BaseModel):
    skill: SkillEnum

class CombatInitializer(BaseModel):
    enemies:List[EnemyEnum]
    fleeable: bool

class GenericItemModel(BaseModel):
    name:str
    description:str
    value:int
    useless:bool

class GiveItems(BaseModel):
    items_ids: List[int]


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
                func=self.steal_player
            ),StructuredTool(
                name="item_remover",
                description="Remove items",
                args_schema=GiveItems,
                func=self.remove_items
            ),
            StructuredTool(
                name="damage_player",
                description="Damage the player.",
                args_schema=Damage,
                func=self.damage_player
            ),StructuredTool(
                name="heal_player",
                description="Heal the player or clear all effects (or both)",
                args_schema=Damage,
                func=self.heal_player
            ),
            StructuredTool(
                name="create_item",
                description="Create a new item generic item Without. Do not create existing in-game items or coins",
                args_schema=GenericItemModel,
                func=self.create_new_item
            ),
            StructuredTool(
                name="give_items",
                description="Give items to the player",
                args_schema=GiveItems,
                func=self.give_items
            ),
            StructuredTool(
                name="player_use_skill_outside_combat",
                description="run this tool when the player uses a skill out of combat",
                args_schema=UseSkill,
                func=self.player_use_skill_outside_combat
            ),
            StructuredTool(
                name="player_use_item_outside_combat",
                description="run this tool when the player uses an item out of combat",
                args_schema=UseItem,
                func=self.player_use_item_outside_combat
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
            ),
            Tool(
                name="items_consult",
                description="Consult the id/items dict of game",
                func=self.consult_items
            ),
            Tool(
                name="player_consult",
                description="Consult the player status",
                func=self.consult_player
            )
        ]

    # 👇 métodos públicos usados como tools
    def consult_items(self,s):
        items_book = []
        for item_id, item in ITEMS:
            item_text = f"ID: {item_id}, NAME {item.name}"
            items_book.append(item_text)
        return "\n".join(items_book)

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

    def steal_player(self,loss):
        self._game.player.gold = max(0,self._game.player.gold - loss)

    def player_use_item_outside_combat(self,item_id):
        if not self._game.player.has_item(item_id,1):
            return {
                "success": False,
                "message": "Player dont have the item"
            }
        item = ITEMS[item_id]
        if not isinstance(item,Usable):
            return {
                "success": False,
                "message": "This item don´t have a use function. if you want remove a item please use the item_remover tool"
            }
        item.on_use(self._game.player,None)
        self._game.player.remove_item(item_id,1)
        return {
            "success":True,
            "message": "item used and subtracted from inventory"
        }

    def player_use_skill_outside_combat(self,skill):
        if not skill in [skill.enum for skill in self._game.player.skills]:
            return {
                "success": False,
                "message": "Player dont have the skill"
            }
        skill = SKILL_FACTORY[skill]
        if self._game.player.mana < skill.cost:
            return {
                "success": False,
                "message": "Player dont have enought mana"
            }
        skill.execute(self._game.player,None,None)
        self._game.player.mana -= skill.cost
        return {
            "success": True,
            "message": "Skill used and mana subtracted"
        }


    def consult_player(self,aaa):
        return self._game.player.to_text(markdown=True)

    def sell_trash(self,_):
        self._game.player.sell_trash()
        return "All golds have been added to the player's sheet automatically"

    def create_new_item(self,name,description,value,useless):
        new_id = len(ITEMS) + 1
        item = GenericItem(
            id=new_id,
            name=name,
            description=description,
            value=value,
            useless=useless
        )
        ITEMS[new_id] = item
        return f"new item created with ID: {new_id}"

    def give_items(self,items_ids:List[int]):
        for items_id in items_ids:
            self._game.player.give_item(items_id,1)

    def remove_items(self,items_ids:List[int]):
        for items_id in items_ids:
            self._game.player.remove_item(items_id,1)


    def roll_expertise_test(self,character_expertise:CharacterExpertise,roll_type:RollType):
        primary_attribute = character_expertise.get_associated_ability()
        mod = get_mod(self._game.player.attributes[primary_attribute])
        if character_expertise in self._game.player.expertises:
            mod += self._game.player.proficiency
        return self.roll_d20(mod,roll_type)


    def heal_player(self,heal,clear_effects):
        self._game.player.heal(heal)
        if clear_effects:
            self._game.player.clear_negative_effects()

        return {
            "updated_player": self._game.player.to_text()
        }

    def damage_player(self,damage,damage_type):
        self._game.player.apply_damage(None,damage,damage_type,None)


    def reward_player(self,gold,xp):
        if gold < 0 or xp < 0:
            return "Positive values only!"
        self._game.player.gold += gold
        self._game.player.give_xp(xp)

        return {
            "actual_gold": self._game.player.gold,
            "actual_xp": self._game.player.xp
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