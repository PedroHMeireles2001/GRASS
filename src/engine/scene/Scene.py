from abc import ABC, abstractmethod
from typing import List, Optional

import pygame
from typing import TYPE_CHECKING


from src.engine.scene.SceneElement import SceneElement


if TYPE_CHECKING:
    from src.engine.Game import Game


class Scene(ABC):
    def __init__(self,background: Optional[pygame.Surface],screen: pygame.Surface,game: "Game"):
        self.game = game
        self.background = background
        self.screen = screen
        self.elements :List[SceneElement] = self.build_scene(self.game)


    def render(self):
        #render background
        if self.background is not None:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill((0,0,0))

        #rende elements
        for element in self.elements:
            element.render(self.screen)

    @abstractmethod
    def build_scene(self, game: "Game") -> List[SceneElement]:
        pass

    def handle_event(self, event):
        mouse_position = pygame.mouse.get_pos()
        for element in self.elements:
            element.update(event, mouse_position)


    def update(self):
        mouse_position = pygame.mouse.get_pos()
        for element in self.elements:
            element.update(None, mouse_position)

