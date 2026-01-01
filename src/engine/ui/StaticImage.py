import os.path
from typing import Tuple

import pygame

from src.engine.ui.UIElement import UIElement
from src.utils import get_assets_path


class StaticImage(UIElement):
    def __init__(self,relative_path,position,size,circle_radius=0):
        super().__init__(pygame.transform.scale(pygame.image.load(os.path.join(get_assets_path(),relative_path)),size),position)
        self.circle_radius = circle_radius

        if self.circle_radius > 0:
            self._apply_circle_mask()

    def _apply_circle_mask(self):
        w, h = self.image.get_size()

        # Surface com alpha
        mask_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        mask_surface.fill((0, 0, 0, 255))  # tudo preto

        # Desenha o círculo transparente (área visível)
        pygame.draw.circle(
            mask_surface,
            (0, 0, 0, 0),  # alpha 0 = transparente
            (w // 2, h // 2),
            self.circle_radius
        )

        # Aplica a máscara
        self.image.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

    def update(self, event: pygame.event.Event, mouse_position: Tuple[int, int]):
        pass