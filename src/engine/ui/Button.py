import os.path
from typing import Tuple, Callable, Optional

import pygame

from src.engine.ui.ImageTransformStrategy import ImageTransformStrategy
from src.engine.ui.SimpleText import SimpleText
from src.engine.ui.UIElement import UIElement
from src.utils import get_assets_path


class Button(UIElement):
    def __init__(self, image: Optional[pygame.Surface], position: Tuple[int, int],text: Optional[SimpleText] = None,hover_function: Optional[Callable] = None,click_function: Optional[Callable] = None,hover_transform_strategy: Optional[ImageTransformStrategy] = None,click_transform_strategy: Optional[ImageTransformStrategy] = None,background_color: Optional[Tuple[int, int, int]] = None,padding = (24,12) ,hover_sound="button_hover.mp3",click_sound="button_click.mp3"):
        super().__init__(None, position)
        self.background_color = background_color
        self.padding = padding
        self.text = text
        self.clean_image = image
        self.image = self.get_image(text,image,background_color,padding)
        self.rect = self.image.get_rect()
        self.hover_function = hover_function
        self.click_function = click_function
        self.hover_transform_strategy = hover_transform_strategy
        self.click_transform_strategy = click_transform_strategy
        if click_sound is not None:
            self.click_sound = pygame.mixer.Sound(os.path.join(get_assets_path(),"sfx",click_sound))
        if hover_sound is not None:
            self.hover_sound = pygame.mixer.Sound(os.path.join(get_assets_path(),"sfx",hover_sound))
        self.original_image = self.image.copy()
        self.hover_image = (
            hover_transform_strategy.transform(self.original_image)
            if hover_transform_strategy else self.original_image
        )
        self.click_image = (
            click_transform_strategy.transform(self.original_image)
            if click_transform_strategy else self.original_image
        )

    def update_image(self):
        self.image = self.get_image(self.text, self.clean_image, self.background_color, self.padding)
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect()
        self.hover_image = (
            self.hover_transform_strategy.transform(self.original_image)
            if self.hover_transform_strategy else self.original_image
        )
        self.click_image = (
            self.click_transform_strategy.transform(self.original_image)
            if self.click_transform_strategy else self.original_image
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
            if self.click_sound:
                self.click_sound.play()
            if self.click_function:
                self.click_function()
        else:
            self.set_image(self.original_image)

    def on_hover(self):
        if self.enabled:
            self.set_image(self.hover_image)
            if self.hover_sound:
                self.hover_sound.play()
            if self.hover_function:
                self.hover_function()
        else:
            self.image = self.original_image

    def on_unhover(self):
        self.set_image(self.original_image)

    def check_for_input(self, mause_position: Tuple[int, int]) -> bool:
        if self.enabled:
            if self.rect.collidepoint(mause_position):
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