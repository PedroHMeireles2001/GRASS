from typing import Tuple

import pygame

from src.engine.ui.UIElement import UIElement
from src.utils import get_default_font


class SimpleText(UIElement):
    def update(self, event: pygame.event.Event, mouse_position: Tuple[int, int]):
        pass

    def __init__(self,text: str,size: int,position: Tuple[int,int],text_color: Tuple[int,int,int] = (255,255,255)):
        self.font = get_default_font(size)
        self.text = text
        self.text_color = text_color
        self.image = self.font.render(self.text, True, self.text_color)
        self.position = position
        super().__init__(self.image, self.position)

    def render(self,surface):
        surface.blit(self.image,self.position)

    def change_text(self,text: str):
        self.text = text
        self.image = self.font.render(text, True, self.text_color)
