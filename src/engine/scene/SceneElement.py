from abc import abstractmethod, ABC
from typing import Tuple, Optional

import pygame


class SceneElement(ABC):
    def __init__(self):
        self.visible = True

    @abstractmethod
    def render(self, screen: pygame.Surface):
        pass

    @abstractmethod
    def update(self, event: Optional[pygame.event.Event],mouse_position: Tuple[int, int]):
        pass