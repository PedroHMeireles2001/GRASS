import pygame
from src.engine.ui.UIElement import UIElement

class Slider(UIElement):

    def __init__(self, position, width, min_value, max_value, start_value, on_change):
        self.x, self.y = position
        self.width = width
        self.height = 12
        self.min = min_value
        self.max = max_value
        self.value = start_value
        self.dragging = False
        self.on_change = on_change

    def update(self, event, mouse_pos):

        # update de frame (sem evento)
        if event is None:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._mouse_over(mouse_pos):
                self.dragging = True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION and self.dragging:

            mx = mouse_pos[0]

            rel = max(0, min(mx - self.x, self.width))
            self.value = self.min + (rel / self.width) * (self.max - self.min)

            if self.on_change:
                self.on_change(self.value)

    def render(self, screen):

        pygame.draw.rect(
            screen,
            (180,180,180),
            (self.x, self.y, self.width, self.height)
        )

        knob_x = self.x + (self.value - self.min)/(self.max-self.min)*self.width

        pygame.draw.circle(
            screen,
            (255,255,255),
            (int(knob_x), self.y + self.height//2),
            8
        )

    def _mouse_over(self, mouse_pos):

        mx,my = mouse_pos

        return (
            self.x <= mx <= self.x + self.width
            and self.y <= my <= self.y + self.height
        )