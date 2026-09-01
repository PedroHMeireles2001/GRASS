# src/engine/scene/Scene.py
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING
import pygame

from src.engine.scene.SceneElement import SceneElement

if TYPE_CHECKING:
    from src.engine.Game import Game

class Scene(ABC):
    def __init__(self, background: Optional[pygame.Surface], screen: pygame.Surface, game: "Game"):
        self.game = game
        self.background = background
        self.screen = screen
        # Cache dos elementos para evitar bottlenecks de recriação no loop
        self.elements: List[SceneElement] = self.build_scene(self.game)

    # CORREÇÃO: Adicionado o parâmetro 'screen' para casar com a chamada em Game.py
    def render(self, screen: pygame.Surface):
        # Limpa o frame anterior usando o background ou preto
        if self.background is not None:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill((0, 0, 0))

        # Renderiza os elementos da interface
        for element in self.elements:
            element.render(screen)

    @abstractmethod
    def build_scene(self, game: "Game") -> List[SceneElement]:
        pass

    def handle_events(self, events: List[pygame.event.Event], mouse_pos: tuple):
        for event in events:
            for element in self.elements:
                element.update(event, mouse_pos)

    def update(self, *args, **kwargs):
        # added *args and kwargs
        mouse_position = pygame.mouse.get_pos()
        self.elements = [e for e in self.elements if not getattr(e, 'is_done', False)]
        for element in self.elements:
            element.update(None, mouse_position)
        
