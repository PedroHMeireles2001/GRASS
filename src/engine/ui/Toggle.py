import pygame
from src.engine.ui.UIElement import UIElement
from src.engine.ui.SimpleText import SimpleText

class Toggle(UIElement):
    def __init__(self, x, y, width=60, height=30, is_on=False, on_change=None, text_on=None, text_off=None):
        super().__init__(image=None, position=( x, y ))
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_on = is_on
        self.on_change = on_change
        self.rect = pygame.Rect(x, y, width, height)
        
        # Scale text relative to toggle height
        #self.font_size = max(10, self.height // 2 * 0.72)
        # Scale text relative to toggle height (diminished by 28% and converted to integer)
        self.font_size = int(max(10, (self.height // 2) * 0.72))



    def render(self, screen):
        """This is the method called by Scene.py. We redirect it to our draw logic."""
        if self.visible:
            self.draw(screen)

    def update(self, event=None, mouse_pos=None):
        if event and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_on = not self.is_on
                if self.on_change:
                    self.on_change(self.is_on)

    def draw(self, screen):
        # Track color: green = Mute ON (is_on=True), gray = Sound active (is_on=False)
        track_color = (46, 204, 113) if self.is_on else (100, 100, 100)
        pygame.draw.rect(screen, track_color, self.rect, border_radius=self.height // 2)

        # Label: "ON" = Mute Active (green), "OFF" = Sound Active (gray)
        if self.is_on:
            # Mute is active — show "ON" on the left side of the (right-positioned) handle
            label = SimpleText("ON", self.font_size, (self.x + 6, self.y + (self.height // 4)), (255, 255, 255))
            label.render(screen)
        else:
            # Sound is active — show "OFF" on the right side of the (left-positioned) handle
            label = SimpleText("OFF", self.font_size, (self.x + self.width - 34, self.y + (self.height // 4)), (255, 255, 255))
            label.render(screen)

        # Handle (circle/pill)
        handle_x = self.x + self.width - self.height + 2 if self.is_on else self.x + 2
        handle_rect = pygame.Rect(handle_x, self.y + 2, self.height - 4, self.height - 4)
        pygame.draw.ellipse(screen, (255, 255, 255), handle_rect)

    """ def _mouse_over(self, mouse_pos):

        mx,my = mouse_pos

        return (
            self.x <= mx <= self.x+self.width
            and self.y <= my <= self.y+self.height
        ) """