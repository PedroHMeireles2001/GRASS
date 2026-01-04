import json
import os
import sys
from typing import Optional, Dict, Any, TYPE_CHECKING

import pygame

from src.engine.ai.chat import Chat
from src.engine.scene.MainMenu import MainMenu
from src.model.player import Player
from src.model.scenario import Scenario


class Game:
    def __init__(self,scenario:Scenario,start_player=None):
        self.screen = pygame.display.set_mode((0,0),pygame.FULLSCREEN)
        self.scene = None
        self.scenario = scenario
        self.previous_scene = None
        self.running = True
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.options = self.load_options()
        self.player: Optional[Player] = start_player
        self.chat = Chat(
            system_prompt=scenario.system_prompt,
            initial_message=scenario.initial_message,
            api_key=self.options["api_key"],
            gpt_model=self.options["gpt_model"],
            game=self
        ) if self.options["api_key"] else None

    def change_scene(self,new_scene):
        self.previous_scene = self.scene
        self.scene = new_scene

    def save_options(self):
        with open("options.json", "w") as file:
            json.dump(self.options, file)

    def load_options(self) -> Dict[str,Any]:
        if os.path.exists("options.json"):
            with open("options.json", "r") as file:
                return json.load(file)
        return self._get_default_options()

    def _get_default_options(self):
        return {
            "api_key": os.environ["debug_api_key"],
            "gpt_model" : "gpt-4o-mini"
        }

    def start(self):
        while self.running:
            if self.scene is None:
                continue
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self.running = False
                self.scene.handle_event(event)

            self.scene.update()
            self.scene.render()
            pygame.display.flip()
            self.clock.tick(self.fps)

        pygame.quit()
        sys.exit()

    def main_menu(self):
        self.scene = MainMenu(None,self.screen,self)

    def back_scene(self):
        actual_scene = self.scene
        self.scene = self.previous_scene
        self.previous_scene = actual_scene

