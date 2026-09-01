import os
import pygame
from typing import List
from src.engine.scene.Scene import Scene
from src.engine.scene.SceneElement import SceneElement
from src.engine.ui.Button import Button
from src.engine.ui.SimpleText import SimpleText
from src.utils import get_center_x

class SaveSelectionScene(Scene):
    def build_scene(self, game) -> List[SceneElement]:
        self.game = game
        sw = self.screen.get_width()
        
        elements = [
            SimpleText("Select Adventure to Continue", 48, (get_center_x(self.screen, 500), 50))
        ]
        
        saves = []
        if os.path.exists("saves"):
            saves = [f for f in os.listdir("saves") if f.endswith(".json")]
        
        # Add legacy save if exists
        if os.path.exists("save_game.json"):
            saves.append("save_game.json")

        y_offset = 150
        for save_file in saves:
            elements.append(Button(
                image=None,
                text=SimpleText(save_file, 20, (0, 0), (200, 200, 255)),
                position=(sw // 2 - 150, y_offset),
                click_function=lambda f=save_file: self.game.load_session(f)
            ))
            y_offset += 50

        elements.append(Button(
            image=None,
            text=SimpleText("Back", 24, (0, 0), (255, 255, 255)),
            position=(sw // 2 - 50, self.screen.get_height() - 100),
            click_function=lambda: self.game.main_menu()
        ))

        return elements
