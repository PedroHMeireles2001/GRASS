import os.path
from typing import Tuple, Callable, Optional
import pygame

from src.engine.ui.ImageTransformStrategy import ImageTransformStrategy
from src.engine.ui.SimpleText import SimpleText
from src.engine.ui.UIElement import UIElement
from src.utils import get_assets_path, play_button_hover, play_button_click

class Button(UIElement):
    def __init__(self, image: Optional[pygame.Surface], position: Tuple[int, int],
                 text: Optional[SimpleText] = None,
                 hover_function: Optional[Callable] = None,
                 click_function: Optional[Callable] = None,
                 hover_transform_strategy: Optional[ImageTransformStrategy] = None,
                 click_transform_strategy: Optional[ImageTransformStrategy] = None,
                 background_color: Optional[Tuple[int, int, int]] = None,
                 padding=(24, 12),
                 hover_sound=True,
                 click_sound=True,
                 tooltip_text: Optional[str] = None):  # NEW: Tooltip parameter
        
        super().__init__(None, position)
        self.background_color = background_color
        self.padding = padding
        self.text = text
        self.clean_image = image
        self.image = self.get_image(text, image, background_color, padding)
        self.rect = self.image.get_rect()
        self.hover_function = hover_function
        self.click_function = click_function
        self.hover_transform_strategy = hover_transform_strategy
        self.click_transform_strategy = click_transform_strategy
        
        # NEW: Tooltip setup
        self.tooltip_text = tooltip_text
        self.tooltip_surface = None
        self.tooltip_rect = None
        self.show_tooltip = False
        self.tooltip_font = pygame.font.Font(None, 24)
        
        # Sounds are played via the shared globals in utils.py so that
        # apply_global_volume() / mute state always applies correctly.
        self.click_sound = click_sound  # True/False sentinel
        self.hover_sound = hover_sound  # True/False sentinel
        
        self.original_image = self.image.copy()
        self.hover_image = (
            hover_transform_strategy.transform(self.original_image)
            if hover_transform_strategy else self.original_image
        )
        self.click_image = (
            click_transform_strategy.transform(self.original_image)
            if click_transform_strategy else self.original_image
        )

    # NEW: Tooltip creation method
    def _create_tooltip(self):
        if self.tooltip_text:
            self.tooltip_surface = self.tooltip_font.render(self.tooltip_text, True, (255, 255, 200))
            self.tooltip_rect = self.tooltip_surface.get_rect()
            # Position tooltip above button
            self.tooltip_rect.midtop = (
                self.position[0] + self.rect.width // 2,
                self.position[1] - 5
            )

    def update_image(self):
        self.image = self.get_image(self.text, self.clean_image, self.background_color, self.padding)
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect()
        # Always re-apply position so callers never need to patch rect.topleft
        # manually after calling this method.
        self.rect.topleft = self.position

        # NEW: Recreate tooltip if rect size changed
        if self.show_tooltip and self.tooltip_surface:
            self._create_tooltip()

        self.hover_image = (
            self.hover_transform_strategy.transform(self.original_image)
            if self.hover_transform_strategy else self.original_image
        )
        self.click_image = (
            self.click_transform_strategy.transform(self.original_image)
            if self.click_transform_strategy else self.original_image
        )

    def get_size(self, text: Optional[SimpleText], image: Optional[pygame.Surface], padding: Tuple[int, int]) -> Tuple[int, int]:
        if image is not None:
            return image.get_size()
        if text is not None:
            w, h = text.image.get_size()
            return w + padding[0], h + padding[1]
        return 100, 100

    def get_image(self, text: Optional[SimpleText], image: Optional[pygame.Surface],
                  background_color: Optional[Tuple[int, int, int]], padding: Tuple[int, int]) -> pygame.Surface:
        bg = pygame.Surface(self.get_size(text, image, padding), pygame.SRCALPHA)
        if background_color is not None:
            bg.fill(background_color)
        if image is not None:
            bg.blit(image, (0, 0))
        if text is not None:
            bg.blit(text.image, (padding[0] // 2, padding[1] // 2))
        return bg

    def on_click(self):
        if self.enabled:
            self.set_image(self.click_image)
            if self.click_sound:
                play_button_click()  # Uses shared global — respects mute/volume
            if self.click_function:
                self.click_function()
        else:
            self.set_image(self.original_image)

    def on_hover(self):
        if self.enabled:
            self.set_image(self.hover_image)
            if self.hover_sound:
                play_button_hover()  # Uses shared global — respects mute/volume
            if self.hover_function:
                self.hover_function()
        else:
            self.image = self.original_image

    def on_unhover(self):
        self.set_image(self.original_image)

    def check_for_input(self, mouse_position: Tuple[int, int]) -> bool:
        if self.enabled:
            if self.rect.collidepoint(mouse_position):
                return True
        return False

    # UPDATED: Added tooltip logic
    def update(self, event: pygame.event.Event, mouse_position: Tuple[int, int]):
        was_hovered = self.hovered
        
        if self.check_for_input(mouse_position):
            if not self.hovered:
                self.hovered = True
                self.on_hover()
                # NEW: Show tooltip on first hover
                if self.tooltip_text and not self.show_tooltip:
                    self.show_tooltip = True
                    self._create_tooltip()
        else:
            if self.hovered:
                self.on_unhover()
            self.hovered = False
            # NEW: Hide tooltip when not hovering
            self.show_tooltip = False
            self.tooltip_surface = None

        if event is not None and event.type == pygame.MOUSEBUTTONDOWN:
            if self.check_for_input(mouse_position):
                self.on_click()

    # ✅ NEW: Override render() method to draw tooltip
    def render(self, surface: pygame.Surface):
        # Draw button normally (parent render)
        super().render(surface)
        
        # ✅ NEW: Draw tooltip if active
        if self.show_tooltip and self.tooltip_surface:
            # Semi-transparent background
            tooltip_bg = pygame.Surface((self.tooltip_rect.width + 12, self.tooltip_rect.height + 8))
            tooltip_bg.set_alpha(220)
            tooltip_bg.fill((20, 20, 20))
            surface.blit(tooltip_bg, self.tooltip_rect.topleft)
            surface.blit(self.tooltip_surface, self.tooltip_rect)

