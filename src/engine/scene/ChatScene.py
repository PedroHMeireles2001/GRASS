import threading
import time
from typing import List

from src.engine.scene.CombatScene import CombatScene
from src.engine.scene.Scene import Scene
from src.engine.scene.SceneElement import SceneElement
from src.engine.ui.Button import Button
from src.engine.ui.ImageTransformStrategy import ColorInverter
from src.engine.ui.SimpleText import SimpleText
from src.engine.ui.StaticImage import StaticImage
from src.engine.ui.TextArea import TextAreaShow
from src.engine.ui.TextInput import TextInput
from src.model.scenario import Scenario
from src.utils import get_center_x, print_debug, get_default_font


class ChatScene(Scene):
    def __init__(self,screen,game,scenario: Scenario):



        self.actual_text:TextAreaShow = TextAreaShow(
            text=scenario.initial_message,
            position=(20,screen.get_height()//2),
            width=screen.get_width() - 20 - 12,
            height=(screen.get_height()//2) - 75
        )
        self.player_input: TextInput = TextInput(
                position=(24,screen.get_height()-50),
                width=screen.get_width() - 300,
                on_change=self._on_change,
                on_submit=self._submit
        )



        self.submit_button = Button(
                position=(screen.get_width() - 200,screen.get_height()-50),
                text=SimpleText("Submit!",24,(0,0),(0,0,0)),
                background_color=(255,255,255),
                image=None,
                hover_transform_strategy=ColorInverter(),
                click_function=lambda : self._submit(self.player_input.text.text)
        )

        self.combat_button = Button(
            position=(get_center_x(screen,get_default_font(24).size("Enter Combat!")[0]),screen.get_height() - 50),
            text = SimpleText("Enter Combat!", 24, (0, 0), (0, 0, 0)),
            background_color=(255, 255, 255),
            image=None,
            hover_transform_strategy=ColorInverter(),
            click_function=self._submit_combat
        )
        self.combat_button.visible = False
        self.combat_button.enabled = False
        self.eminent_combat = None

        super().__init__(None, screen, game)


        self.loading = False

    def build_scene(self, game: "Game") -> List[SceneElement]:
        return [
            StaticImage(
                relative_path="chat.png",
                size=(400,400),
                position=(get_center_x(self.screen,400),0),
                circle_radius=200
            ),


        ] + [self.submit_button,self.player_input,self.actual_text,self.combat_button]


    def wait_combat_confirm(self,combat):
        self._hide_input()
        self.combat_button.visible = True
        self.combat_button.enabled = True
        self.eminent_combat = combat

    def _submit_combat(self):
        if self.eminent_combat is None:
            return

        self.game.scene = CombatScene(
            game=self.game,
            screen=self.screen,
            combat=self.eminent_combat
        )

    def _hide_input(self):
        self.submit_button.visible = False
        self.submit_button.enabled = False
        self.player_input.visible = False
        self.player_input.enabled = False

    def _show_input(self):
        if self.eminent_combat is not None:
            return
        self.submit_button.visible = True
        self.submit_button.enabled = True
        self.player_input.visible = True
        self.player_input.enabled = True

    def _put_text(self,text):
        self.actual_text.text = self.actual_text.text + text


    def _submit(self,text):
        self.player_input.text.text = ""
        self._put_text(f"\n{self.game.player.name}:\n{text}\nDM:\n")
        self._hide_input()
        self.loading = True
        for token in self.game.chat.submit(text):
            self._put_text(token)
        self.loading = False
        self._show_input()



    def _on_change(self,text):
        self.player_input.text.text = text

