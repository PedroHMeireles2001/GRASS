from typing import Tuple, Callable, Optional

import pygame

from src.engine.ui.SimpleText import SimpleText
from src.engine.ui.UIElement import UIElement
from src.utils import get_default_font


class TextInput(UIElement):
    def __init__(self, position: Tuple[int,int], width: int,height:int = 24,initial_text:str="", background_color:Tuple[int,int,int] = (255, 255, 255),focus_background_color:Tuple[int,int,int] = (50, 100, 255),text_size:int = 12, text_color:Tuple[int,int,int] = (255, 255, 255), padding: int = 3, border_width = 1,label_str: str = None,label_top: bool=True,label_size:int = 24,on_change: Optional[Callable[[str],None]] = None,on_submit: Optional[Callable[[str],None]] = None):
        super().__init__(None,position)
        self.background_color = background_color
        self.focus_background_color = focus_background_color
        self.focus = False
        self.border_width = border_width
        self.rect = pygame.Rect(position[0], position[1], width + padding, height + padding)
        self.text: SimpleText = SimpleText(
            size=text_size,
            text_color=text_color,
            position=(position[0] + padding, position[1] + padding),
            text=initial_text
        )
        self.on_change = on_change
        self.on_submit = on_submit
        self.label = None
        if label_str:
            self.label = SimpleText(
                size=label_size,
                text_color=text_color,
                position=(position[0], position[1] - height) if label_top else (position[0] - get_default_font(label_size).size(label_str)[0] - 5, position[1]),
                text=label_str
            )

    def _on_change(self):
        if self.on_change:
            self.on_change(self.text.text)

    def render(self, surface: pygame.Surface):
        if not self.visible:
            return
        pygame.draw.rect(surface,self.background_color if not self.focus else self.focus_background_color,self.rect,width=self.border_width)
        self.text.render(surface)
        if self.label:
            self.label.render(surface)

    def update(self, event: pygame.event.Event, mouse_position: Tuple[int, int]):
        if not event:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(mouse_position):
            self.focus = True
            pygame.key.start_text_input()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.focus and not self.rect.collidepoint(mouse_position):
            self.focus = False
            pygame.key.stop_text_input()

        if not self.focus:
            return

        if event.type == pygame.TEXTINPUT:
            self.text.change_text(self.text.text + event.text)
            self._on_change()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text.change_text(self.text.text[:-1])
                self._on_change()
            if event.key == pygame.K_RETURN:
                if self.on_submit:
                    self.on_submit(self.text.text)
