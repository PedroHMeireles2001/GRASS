from typing import List, Optional, TYPE_CHECKING

import pygame
import pyperclip

from src.engine.scene.Scene import Scene
from src.engine.scene.SceneElement import SceneElement
from src.engine.ui.Button import Button
from src.engine.ui.ImageTransformStrategy import ColorInverter
from src.engine.ui.SimpleText import SimpleText
from src.utils import get_center_x, get_default_font

if TYPE_CHECKING:
    from src.engine.Game import Game

class Options(Scene):

    def __init__(self, background: Optional[pygame.Surface],screen: pygame.Surface,game: "Game"):
        self.api_key = None
        text = f"API Key: {self.api_key if self.api_key else 'No API Key'}"
        self.api_key_text = self.api_key_text = SimpleText(
            text=text,
            position=(get_center_x(screen,get_default_font(12).size(text)[0]),get_default_font(30).size("Colar")[1] + 110),
            size=12
        )
        super().__init__(background,screen,game)


    def colar(self):
        self.api_key = pyperclip.paste()
        text = f"API Key: {self.api_key if self.api_key else 'No API Key'}"
        self.api_key_text.change_text(text)


    def back(self):
        self.game.back_scene()
        self.game.options["api_key"] = self.api_key
        self.game.save_options()

    def build_scene(self, game: object) -> List[SceneElement]:
        return [
            SimpleText("Options",48,(get_center_x(self.screen,get_default_font(48).size("Options")[0]),0)),
            Button(
                image=None,
                position=(get_center_x(self.screen,get_default_font(30).size("Colar")[0]),90),
                text=SimpleText("Colar API Key", 30, (0, 0), (0, 0, 0)),
                background_color=(255, 255, 255),
                hover_transform_strategy=ColorInverter(),
                click_function=self.colar
            ),
            Button(
                image=None,
                position=(get_center_x(self.screen, get_default_font(30).size("Voltar")[0]), self.screen.get_height() - 50),
                text=SimpleText("Voltar", 30, (0, 0), (0, 0, 0)),
                background_color=(255, 255, 255),
                hover_transform_strategy=ColorInverter(),
                click_function=self.back
            ),
            self.api_key_text
        ]