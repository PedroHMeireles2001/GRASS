from abc import ABC, abstractmethod

import pygame

from src.utils import print_debug


class ImageTransformStrategy(ABC):
    @abstractmethod
    def transform(self, image: pygame.Surface) -> pygame.Surface:
        pass

class ColorInverter(ImageTransformStrategy):
    def transform(self, image: pygame.Surface) -> pygame.Surface:
        inverted = image.convert_alpha().copy()
        arr = pygame.surfarray.pixels3d(inverted)
        arr[:] = 255 - arr
        del arr
        return inverted


class BrightnessTransform(ImageTransformStrategy):
    def __init__(self, intensity: int):
        """
        intensity: valor entre -1 e 1
        positivo  -> aumenta brilho
        negativo  -> diminui brilho
        """
        self.intensity = intensity * 255

    def transform(self, image: pygame.Surface) -> pygame.Surface:
        new_image = image.copy()

        bright = new_image.convert_alpha()
        width, height = bright.get_size()



        for x in range(width):
            for y in range(height):
                r, g, b, a = bright.get_at((x, y))

                r = max(0, min(255, r + self.intensity))
                g = max(0, min(255, g + self.intensity))
                b = max(0, min(255, b + self.intensity))

                bright.set_at((x, y), (r, g, b, a))

        return bright
