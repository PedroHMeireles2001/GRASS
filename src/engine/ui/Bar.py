from typing import Tuple

import pygame

from src.engine.ui.SimpleText import SimpleText
from src.engine.ui.UIElement import UIElement
from src.utils import get_default_font, get_center_x


class Bar(UIElement):
    def update(self, event: pygame.event.Event, mouse_position: Tuple[int, int]):
        pass

    def __init__(self,position:Tuple[int,int],width:int,height:int = 15,bar_color:Tuple[int,int,int] = (255,255,255),initial_progress:int = 100,max_progress: int = 100,label_str:str = None,label_top=True):
        super().__init__(None,position)
        self.progress = initial_progress
        self.max_progress = max_progress
        self.width = width
        self.height = height
        self.bar_color = bar_color
        self.rect = pygame.Rect(position[0],position[1],width,height)
        self.label = None
        if label_str:
            self.label = SimpleText(
                text=label_str,
                position=self._calculate_label_position(label_top, label_str),
                text_color=self.bar_color,
                size=12
            )


    def render(self, surface: pygame.Surface):
        percent = self.progress / self.max_progress
        bar_width = percent * self.width
        bar_rect = pygame.Rect(self.position[0],self.position[1],bar_width,self.height)
        pygame.draw.rect(surface,self.bar_color,bar_rect)
        pygame.draw.rect(surface,self.bar_color,self.rect,width=1)
        if self.label is not None:
            self.label.render(surface)


    def change_label(self,label_str:str,label_top:bool):
        if self.label is not None:
            self.label.change_text(label_str)
            self.label.position = self._calculate_label_position(label_top, label_str)
        else:
            self.label = SimpleText(
                text=label_str,
                position=self._calculate_label_position(label_top, label_str),
                text_color=self.bar_color,
                size=12
            )
        return self.label

    def _calculate_center_label_top(self,label_str:str) -> Tuple[int,int]:
        center_x,center_y = self.rect.center
        fx, fy = get_default_font(12).size(label_str)
        return (center_x - fx // 2), center_y - fy - self.height

    def _calculate_label_position(self,label_top:bool,label_str:str) -> Tuple[int,int]:
        return self._calculate_center_label_top(label_str) if label_top else (self.position[0] - 5 -(get_default_font(12).size(label_str)[0]),self.position[1])