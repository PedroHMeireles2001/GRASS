from typing import List, Optional, TYPE_CHECKING

import pygame

from src.engine.scene.CharacterCreator import CharacterCreator
from src.engine.scene.Options import Options
from src.engine.scene.Scene import Scene
from src.engine.scene.SceneElement import SceneElement
from src.engine.ui.Button import Button
from src.engine.ui.ImageTransformStrategy import ColorInverter
from src.engine.ui.SimpleText import SimpleText
from src.utils import get_center_x, get_default_font
if TYPE_CHECKING:
    from src.engine.Game import Game

class MainMenu(Scene):

    def __init__(self,background: Optional[pygame.Surface],screen: pygame.Surface,game: "Game"):
        super().__init__(background,screen,game)

    def options_scene(self):
        self.game.change_scene(Options(None,self.screen,self.game))

    def character_creator_scene(self):
        self.game.change_scene(CharacterCreator(None,self.screen,self.game))

    def build_scene(self, game: "Game") -> List[SceneElement]:
        return [
            SimpleText("G.R.A.S.S",48,(get_center_x(self.screen,get_default_font(48).size("G.R.A.S.S")[0]),0)),
            Button(
                image=None,
                position=(get_center_x(self.screen,get_default_font(30).size("New Game!")[0]),90),
                text=SimpleText("New Game!",30,(0,0),(0,0,0)),
                background_color=(255,255,255),
                hover_transform_strategy=ColorInverter(),
                click_function=self.character_creator_scene
            ),
            Button(
                image=None,
                position=(get_center_x(self.screen,get_default_font(30).size("Options!")[0]), 180),
                text=SimpleText("Options!", 30, (0, 0), (0, 0, 0)),
                background_color=(255, 255, 255),
                hover_transform_strategy=ColorInverter(),
                click_function=self.options_scene
            )
        ]