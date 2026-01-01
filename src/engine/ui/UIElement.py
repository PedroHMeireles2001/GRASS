from abc import ABC, abstractmethod
from typing import Tuple, Optional
import pygame
from src.engine.scene.SceneElement import SceneElement
from src.utils import print_debug


class UIElement(SceneElement, ABC):
    def __init__(self, image: Optional[pygame.Surface], position: Tuple[int, int]):
        super().__init__()
        self.image = image
        self.position = position
        self.rect = self.image.get_rect(topleft=position) if self.image else None
        self.enabled = True
        self.hovered = False

    def render(self, surface: pygame.Surface):
        if self.visible and self.image is not None:
            self.rect.topleft = self.position
            surface.blit(self.image, self.position)



    def set_image(self, image: pygame.Surface):
        self.image = image
        self.rect = self.image.get_rect(topleft=self.position)

    @abstractmethod
    def update(self,event: pygame.event.Event,mouse_position: Tuple[int, int]):
        pass