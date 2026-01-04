from typing import List, Optional, TYPE_CHECKING

import pygame
import pyperclip

from src.engine.scene.Scene import Scene
from src.engine.scene.SceneElement import SceneElement
from src.engine.ui.Button import Button
from src.engine.ui.ImageTransformStrategy import ColorInverter
from src.engine.ui.RadioButton import RadioButtonGroup
from src.engine.ui.SimpleText import SimpleText
from src.utils import get_center_x, get_default_font

if TYPE_CHECKING:
    from src.engine.Game import Game

class Options(Scene):

    def __init__(self, background: Optional[pygame.Surface],screen: pygame.Surface,game: "Game"):
        self.api_key = game.options["api_key"]
        self.gpt_model = game.options["gpt_model"]
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

    def set_gpt_model(self,previous,model):
        self.gpt_model = model

    def back(self):
        if self.api_key is not None:
            self.game.options["api_key"] = self.api_key
        self.game.options["gpt_model"] = self.gpt_model
        self.game.save_options()
        self.game.running = False

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
            RadioButtonGroup(
                label_str="GPT Model",
                position=(24,self.screen.get_height() // 2),
                options=[("gpt-5.2-pro","gpt-5.2-pro"),("gpt-5.2","gpt-5.2"),("gpt-5-mini","gpt-5-mini"),("gpt-5-nano","gpt-5-nano"),("gpt-4.1","gpt-4.1"),("gpt-4o-mini","gpt-4o-mini")],
                on_change=self.set_gpt_model
            ),
            Button(
                image=None,
                position=(get_center_x(self.screen, get_default_font(30).size("Reload!")[0]), self.screen.get_height() - 50),
                text=SimpleText("Reload!", 30, (0, 0), (0, 0, 0)),
                background_color=(255, 255, 255),
                hover_transform_strategy=ColorInverter(),
                click_function=self.back
            ),
            self.api_key_text
        ]