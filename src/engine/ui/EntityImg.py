from typing import Tuple

import pygame

from src.engine.ui.Bar import Bar
from src.engine.ui.UIElement import UIElement



class EntityImg(UIElement):
    def __init__(self,entity,position,on_click):
        super().__init__(entity.image,position)
        self.entity = entity
        self.previous_life = entity.health
        self.on_click = on_click
        self.life_bar = Bar(
            position=self.rect.midbottom,
            max_progress=entity.max_health,
            initial_progress=entity.health,
            label_str=f"{self.entity.name} {self.entity.health}/{self.entity.max_health}",
            label_top=False,
            width=100,
        )
        self.targeted = False
    def update(self,event: pygame.event.Event,mouse_position: Tuple[int, int]):
        super().update(event,mouse_position)
        if self.previous_life != self.entity.health:
            self.previous_life = self.entity.health
            self._update_life()
        if event is None:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(mouse_position) and not self.entity.dead:
            if self.on_click:
                self.on_click(self.entity)

    def render(self, surface: pygame.Surface):
        super().render(surface)
        self.life_bar.render(surface)
        if self.targeted:
            pygame.draw.rect(surface,(255,255,255),self.rect,width=1)
        if self.entity.dead:
            pygame.draw.rect(surface,(255,0,0),self.rect,width=1)


    def _update_life(self):
        self.life_bar.change_label(f"{self.entity.name} {self.entity.health}/{self.entity.max_health}",False)
        self.life_bar.progress = self.entity.health