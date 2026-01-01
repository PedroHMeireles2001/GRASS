import os.path
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pygame

from src.engine.scene.ChatScene import ChatScene
from src.engine.scene.Scene import Scene
from src.model.attribs import CharacterAttrib
from src.model.classes import CharacterClass
from src.model.combat import Combat
from src.model.entity import Entity
from src.model.player import Player
from src.model.race import CharacterRace
from src.model.scenario import DEBUG_SCENARIO
from src.model.skills import SkillEnum, SKILL_FACTORY
from src.engine.scene.CombatScene import CombatScene
from src.engine.scene.MainMenu import MainMenu
from src.utils import get_assets_path

if TYPE_CHECKING:
    from src.engine.Game import Game

class SceneFactory(ABC):
    @abstractmethod
    def construct(self,game: "Game") -> Scene:
        pass

class MainScene(SceneFactory):
    def construct(self,game: "Game") -> Scene:
        return MainMenu(None, game.screen, game)

class ChatSceneFactory(SceneFactory):
    def construct(self, game: "Game") -> Scene:
        return ChatScene(game.screen,game,scenario=DEBUG_SCENARIO)


class CombatSceneFactory(SceneFactory):
    def construct(self,game: "Game") -> Scene:
        player = Player(
            name="DEBUG",
            race=CharacterRace.ELF,
            clazz=CharacterClass.WARRIOR,
            skills=[SKILL_FACTORY[skillenum] for skillenum in SkillEnum],
            attributes={
                CharacterAttrib.STRENGTH: 10,
                CharacterAttrib.DEXTERITY: 10,
                CharacterAttrib.CONSTITUTION: 10,
                CharacterAttrib.INTELLIGENCE: 10,
                CharacterAttrib.WISDOM: 10,
                CharacterAttrib.CHARISMA: 10
            }
        )
        combat = Combat(
            player=player,
            enemies=[
                Entity(
                    name="DEBUG ENEMY",
                    health=10,
                    dodge=10,
                    armor=0,
                    base_damage=10,
                    image=pygame.image.load(os.path.join(get_assets_path(),"entities","skeleton.png"))
                ),
                Entity(
                    name="DEBUG ENEMY",
                    health=10,
                    dodge=10,
                    armor=0,
                    base_damage=10,
                    image=pygame.image.load(os.path.join(get_assets_path(), "entities", "skeleton.png"))
                )
            ]
        )
        return CombatScene(game.screen,game,combat)