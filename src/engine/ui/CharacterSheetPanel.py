import pygame
from typing import Tuple, List
from src.engine.ui.UIElement import UIElement
from src.engine.ui.SimpleText import SimpleText
from src.model.player import Player
from src.utils import get_default_font

class CharacterSheetPanel(UIElement):
    def __init__(self, player: Player, position: Tuple[int, int], screen: pygame.Surface):
        super().__init__(None, position)
        self.player = player
        self.screen = screen
        self.width = 410
        self.target_x = screen.get_width()
        self.current_x = screen.get_width()
        self.is_open = False
        self.animation_speed = 28
        self.padding = 20
        self.font_large = get_default_font(28)
        self.font_medium = get_default_font(20)
        self.font_small = get_default_font(16)
        
        self.rect = pygame.Rect(self.current_x, 0, self.width, screen.get_height())
        self.visible = True

    def toggle(self):
        self.is_open = not self.is_open
        if self.is_open:
            # Sit flush against the right border
            self.target_x = self.screen.get_width() - self.width
        else:
            self.target_x = self.screen.get_width()

    def update(self, event: pygame.event.Event, mouse_position: Tuple[int, int]):
        if self.current_x != self.target_x:
            if self.current_x < self.target_x:
                self.current_x = min(self.target_x, self.current_x + self.animation_speed)
            else:
                self.current_x = max(self.target_x, self.current_x - self.animation_speed)
            self.rect.x = self.current_x

    def render(self, surface: pygame.Surface):
        if self.current_x >= self.screen.get_width():
            return

        screen_h = self.screen.get_height()

        # Background panel (Dynamic height)
        panel_rect = pygame.Rect(self.current_x, 0, self.width, screen_h)
        pygame.draw.rect(surface, (30, 30, 30, 230), panel_rect)
        pygame.draw.rect(surface, (200, 200, 200), panel_rect, 2)

        x_offset = self.current_x + self.padding
        y_offset = self.padding

        # Name & Title
        title_surf = self.font_large.render(f"{self.player.name}", True, (255, 215, 0))
        surface.blit(title_surf, (x_offset, y_offset))
        y_offset += 40

        class_text = f"{self.player.clazz.name} (Lvl 1)\n- {self.player.race}"
        for line in class_text.split('\n'):
            class_surf = self.font_small.render(line, True, (200, 200, 200))
            surface.blit(class_surf, (x_offset, y_offset))
            y_offset += 20

        y_offset += 20

        # Stats
        stats = [
            (f"HP: {self.player.health}/{self.player.max_health}", (255, 100, 100)),
            (f"Mana: {self.player.mana}/{self.player.max_mana}", (100, 100, 255)),
            (f"Armor: {self.player.armor} | Dodge: {self.player.dodge}", (200, 200, 200)),
            (f"Gold: {self.player.gold}", (255, 255, 100))
        ]

        for text, color in stats:
            surf = self.font_small.render(text, True, color)
            surface.blit(surf, (x_offset, y_offset))
            y_offset += 30
        
        y_offset += 10
        
        # Attributes
        attr_title = self.font_medium.render("Attributes", True, (255, 255, 255))
        surface.blit(attr_title, (x_offset, y_offset))
        y_offset += 25

        for attr, value in self.player.attributes.items():
            from src.utils import get_mod
            mod = get_mod(value)
            mod_str = f"(+{mod})" if mod >= 0 else f"({mod})"
            attr_text = f"{attr.value.title()}: {value} {mod_str}"
            attr_surf = self.font_small.render(attr_text, True, (220, 220, 220))
            surface.blit(attr_surf, (x_offset, y_offset))
            y_offset += 22

        y_offset += 15
        
        # Skills
        skill_title = self.font_medium.render("Skills", True, (255, 255, 255))
        surface.blit(skill_title, (x_offset, y_offset))
        y_offset += 25

        for skill in self.player.skills[:5]:
            skill_text = f"• {skill.name}"
            skill_surf = self.font_small.render(skill_text, True, (180, 255, 180))
            surface.blit(skill_surf, (x_offset, y_offset))
            y_offset += 20
        
        if len(self.player.skills) > 5:
            more_surf = self.font_small.render(f"...and {len(self.player.skills)-5} more", True, (150, 150, 150))
            surface.blit(more_surf, (x_offset, y_offset))