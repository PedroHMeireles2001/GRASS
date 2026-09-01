import os
import json
import pygame
from typing import List, TYPE_CHECKING
from src.engine.scene.Scene import Scene
from src.engine.scene.SceneElement import SceneElement
from src.engine.ui.Button import Button
from src.engine.ui.SimpleText import SimpleText
from src.utils import (
    get_center_x,
    get_default_font,
    play_dungeon_synth_theme,
    stop_dungeon_synth_theme,
)

if TYPE_CHECKING:
    from src.engine.Game import Game

class SurfaceElement(SceneElement):
    """A lightweight wrapper to render custom pygame.Surfaces as a SceneElement."""
    def __init__(self, surface: pygame.Surface, position: tuple):
        super().__init__()
        self.surface = surface
        self.position = position

    def update(self, event=None, mouse_pos=None) -> None:
        """Satisfies the SceneElement abstract interface event signature."""
        pass

    def render(self, screen: pygame.Surface) -> None:
        screen.blit(self.surface, self.position)

class MainMenu(Scene):
    @staticmethod 
    def create_grass_title(text: str = "GRASS RPG", font_size: int = 64) -> pygame.Surface:
        """Generates a stylized text title surface with shadow and outline

        to overlay smoothly above ASCII video backgrounds.
        """
        pygame.font.init()
        font = get_default_font(font_size)
        
        text_color = (192, 192, 192)       # Cromo Escovado (Prata Metálico Claro)
        shadow_color = (15, 15, 18)         # Carbono Negro (Sombra Escura Industrial)
        outline_color = (54, 59, 62)        # Aço Grafite (Contorno Metálico Escuro)


        # Main text & shadow surfaces
        main_surf = font.render(text, True, text_color)
        shadow_surf = font.render(text, True, shadow_color)
        outline_surf = font.render(text, True, outline_color)

        w, h = main_surf.get_size()
        padding = 20
        container = pygame.Surface(
            (w + padding * 2, h + padding * 2), pygame.SRCALPHA
        )

        # Render drop shadow and stroke outline
        offsets = [(-2, -2), (2, -2), (-2, 2), (2, 2), (0, 3)]
        for ox, oy in offsets:
            container.blit(outline_surf, (padding + ox, padding + oy))

        # Drop shadow
        container.blit(shadow_surf, (padding + 5, padding + 5))
        # Foreground text
        container.blit(main_surf, (padding, padding))

        return container

    def build_scene(self, game: "Game") -> List[SceneElement]:
        self.game = game
        screen_w = self.screen.get_width()
        
        # Trigger looping dungeon synth opening theme
        play_dungeon_synth_theme()

        # Optional: TITLE in pure text (uncomment to deactivate; then, comment image section down below)
        # title_surf = self.create_grass_title("GRASS RPG", font_size=64)

        # GRASS image title prefered for splash screen and main menu:
        title_image_path = os.path.join("assets", "GRASStitle.png")
        if os.path.exists(title_image_path):
            img_surf = pygame.image.load(title_image_path).convert_alpha()
            target_w = 450
            aspect_ratio = img_surf.get_height() / img_surf.get_width()
            target_h = int(target_w * aspect_ratio)
            title_surf = pygame.transform.smoothscale(img_surf, (target_w, target_h))

        # Center title horizontally
        title_width = title_surf.get_width()
        title_x = (screen_w - title_width) // 5
        title_y = 50  # Vertical placement offset

        elements = [
            SurfaceElement(title_surf, (title_x, title_y)),
            Button(
                image=None,
                text=SimpleText("New Game", 24, (0, 0), (255, 255, 255)),
                position=(screen_w // 2 - 100, 390),
                click_function=self.character_creator_scene
            )
        ]

        # Check for saves
        has_save = False
        if os.path.exists("save_game.json"): has_save = True
        if os.path.exists("saves") and any(f.endswith(".json") for f in os.listdir("saves")):
            has_save = True

        if has_save:
            elements.append(Button(
                image=None,
                text=SimpleText("Continue", 24, (0, 0), (100, 255, 100)),
                position=(screen_w // 2 - 100, 440),
                click_function=self.load_game_selection
            ))

        elements.append(Button(
            image=None,
            text=SimpleText("Options", 24, (0, 0), (255, 255, 255)),
            position=(screen_w // 2 - 100, 490),
            click_function=self.options_scene
        ))

        return elements

    def render(self, screen: pygame.Surface) -> None:
        """Draws animated ASCII background, circle-blitted vignette, then UI elements."""
        screen_size = screen.get_size()

        # 1. Render animated ASCII background frame
        if hasattr(self.game, 'ascii_player') and self.game.ascii_player and getattr(self.game, 'ascii_loaded', False):
            bg_frame = self.game.ascii_player.get_current_frame(screen_size)
            if bg_frame:
                screen.blit(bg_frame, (0, 0))
            else:
                screen.fill((10, 15, 10))
        elif self.background is not None:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill((10, 15, 10))

        # Optional black sun vignette (Also uncomment block in Game.py) 2. Cache and render Vignette (Default edge dim, switches to Black Sun after 38s)
        """ if not hasattr(self, '_vignette_cache') or self._vignette_cache.get('size') != screen_size:
            self._vignette_cache = {
                'size': screen_size,
                'edge': self.game.create_vignette_surface(screen_size, intensity=180, style="edge"),
                'sun': self.game.create_vignette_surface(screen_size, intensity=180, style="sun")
            }
        
        uptime_seconds = pygame.time.get_ticks() / 1000.0
        vignette_to_use = self._vignette_cache['sun'] if uptime_seconds >= 38.0 else self._vignette_cache['edge']
        screen.blit(vignette_to_use, (0, 0)) """

        # 2. Cache and render Vignette (Interchanges every 38 seconds continuously)
        if not hasattr(self, '_vignette_cache') or self._vignette_cache.get('size') != screen_size:
            self._vignette_cache = {
                'size': screen_size,
                'edge': self.game.create_vignette_surface(screen_size, intensity=180, style="edge"),
                'sun': self.game.create_vignette_surface(screen_size, intensity=180, style="sun")
            }
        
        uptime_seconds = pygame.time.get_ticks() / 1000.0
        cycle_index = int(uptime_seconds // 38.0)
        vignette_to_use = self._vignette_cache['sun'] if (cycle_index % 2 == 1) else self._vignette_cache['edge']
        
        screen.blit(vignette_to_use, (0, 0))

        # 3. Render Title & Buttons over top
        for element in self.elements:
            element.render(screen)

    def load_game_scene(self):
        stop_dungeon_synth_theme()
        from src.engine.scene.ChatScene import ChatScene
        self.game.load_session("save_game.json")
        self.game.change_scene(ChatScene(self.screen, self, self.game.scenario))

    def load_game_selection(self):
        from src.engine.scene.SaveSelectionScene import SaveSelectionScene
        self.game.change_scene(SaveSelectionScene(None, self.screen, self.game))

    def options_scene(self):
        from src.engine.scene.Options import Options
        self.game.change_scene(Options(None, self.screen, self.game))

    def character_creator_scene(self):
        stop_dungeon_synth_theme()
        from src.engine.scene.CharacterCreator import CharacterCreator
        self.game.change_scene(CharacterCreator(None, self.screen, self.game))