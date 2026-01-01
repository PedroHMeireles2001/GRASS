from typing import Tuple, Callable, Optional

import pygame

from src.engine.ui.ImageTransformStrategy import ImageTransformStrategy
from src.engine.ui.SimpleText import SimpleText
from src.engine.ui.UIElement import UIElement


class Button(UIElement):
    def __init__(self, image: Optional[pygame.Surface], position: Tuple[int, int],text: Optional[SimpleText] = None,hover_function: Optional[Callable] = None,click_function: Optional[Callable] = None,hover_transform_strategy: Optional[ImageTransformStrategy] = None,click_transform_strategy: Optional[ImageTransformStrategy] = None,background_color: Optional[Tuple[int, int, int]] = None,padding = (24,12) ):
        super().__init__(self.get_image(text,image,background_color,padding), position)

        self.hover_function = hover_function
        self.click_function = click_function
        self.hover_transform_strategy = hover_transform_strategy
        self.click_transform_strategy = click_transform_strategy
        self.original_image = self.image.copy()
        self.hover_image = (
            hover_transform_strategy.transform(self.original_image)
            if hover_transform_strategy else self.original_image
        )
        self.click_image = (
            click_transform_strategy.transform(self.original_image)
            if click_transform_strategy else self.original_image
        )

    def get_size(self,text:Optional[SimpleText],image: Optional[pygame.Surface],padding: Tuple[int,int]) -> Tuple[int, int]:
        if image is not None:
            return image.get_size()
        if text is not None:
            w, h = text.image.get_size()
            return w + padding[0], h + padding[1]

        return 100, 100

    def get_image(self,text:Optional[SimpleText],image: Optional[pygame.Surface], background_color: Optional[Tuple[int,int,int]],padding: Tuple[int,int]) -> pygame.Surface:
        bg = pygame.Surface(self.get_size(text,image,padding), pygame.SRCALPHA)
        if background_color is not None:
            bg.fill(background_color)
        if image is not None:
            bg.blit(image, (0, 0))
        if text is not None:
            bg.blit(text.image, (padding[0]//2, padding[1]//2))
        return bg


    def on_click(self):
        if self.enabled:
            self.set_image(self.click_image)
            if self.click_function:
                self.click_function()
        else:
            self.set_image(self.original_image)

    def on_hover(self):
        if self.enabled:
            self.set_image(self.hover_image)
            if self.hover_function:
                self.hover_function()
        else:
            self.image = self.original_image

    def on_unhover(self):
        self.set_image(self.original_image)

    def check_for_input(self, mause_position: Tuple[int, int]) -> bool:
        if self.enabled:
            if mause_position[0] in range(self.rect.left, self.rect.right) and mause_position[1] in range(self.rect.top, self.rect.bottom):
                return True
        return False

    def update(self,event: pygame.event.Event,mouse_position: Tuple[int, int]):
        if self.check_for_input(mouse_position):
            if not self.hovered:
                self.hovered = True
                self.on_hover()
        else:
            if self.hovered:
                self.on_unhover()
            self.hovered = False

        if event is not None and event.type == pygame.MOUSEBUTTONDOWN:
            if self.check_for_input(mouse_position):
                    self.on_click()