from typing import Tuple, Optional, List

import pygame

from src.engine.ui.UIElement import UIElement
from src.utils import get_default_font


class TextAreaShow(UIElement):

    def __init__(self, position: Tuple[int, int],width:int,height:int,text:str="",text_size:int = 12,padding:int = 12,background_color:Tuple[int,int,int] = (0,0,0),border_color:Tuple[int,int,int] = (255,255,255),text_color:Tuple[int,int,int]= (255,255,255)):
        super().__init__(None, position)
        self.width = width
        self.height = height
        self.padding = padding
        self.background_color = background_color
        self.border_color = border_color
        self.rect = pygame.rect.Rect(self.position[0],self.position[1],self.width,self.height)
        self.text = text
        self.text_color = text_color
        self.font = get_default_font(text_size)
        self.scroll_offset = 0
        self.focused = False

    def _wrap_text(self) -> List[str]:
        lines: List[str] = []
        for paragraph in self.text.split("\n"):
            words = paragraph.split(" ")
            current_line = ""

            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if self.font.size(test_line)[0] <= self.width - 2 * self.padding:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word

            lines.append(current_line)

        return lines

    def render(self, surface: pygame.Surface):
        if not self.visible:
            return
        # Fundo
        pygame.draw.rect(surface, self.background_color, self.rect)

        # Borda
        pygame.draw.rect(surface, self.border_color, self.rect, 2)

        # Texto
        lines = self._wrap_text()
        line_height = self.font.get_height()

        max_visible_lines = (self.height - 2 * self.padding) // line_height
        visible_lines = lines[self.scroll_offset:self.scroll_offset + max_visible_lines]

        y = self.rect.y + self.padding
        for line in visible_lines:
            text_surf = self.font.render(line, True, self.text_color)
            surface.blit(text_surf, (self.rect.x + self.padding, y))
            y += line_height

    def update(self, event: pygame.event.Event, mouse_position: Tuple[int, int]):
        if event is None:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            self.focused = self.rect.collidepoint(mouse_position)

        if not self.focused:
            return



        if event.type == pygame.MOUSEWHEEL:
            lines = self._wrap_text()
            total_lines = len(lines)
            line_height = self.font.get_height()
            visible_lines = (self.height - 2 * self.padding) // line_height
            max_scroll_offset = max(0, total_lines - visible_lines)
            if event.y == 1:
                if self.scroll_offset < max_scroll_offset:
                    self.scroll_offset+=1
            elif event.y == -1:
                if self.scroll_offset > 0:
                    self.scroll_offset -= 1