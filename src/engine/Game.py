import json
import os
import sys
import time
import pygame
import math
from typing import Optional, Dict, Any

from src.engine.ai.chat import Chat
from src.engine.scene.MainMenu import MainMenu
from src.engine.ui.ASCIIBgPlayer import ASCIIBgPlayer
from src.utils import apply_global_volume, load_sfx, play_dungeon_synth_theme
# stop_dungeon_synth_theme is imported in MainMenu.py, not here, so we don't need it in Game.py

class Game:
    def __init__(self, scenario, start_player=None):
        # 1. High-Resolution Setup (1444x800)
        self.screen = pygame.display.set_mode((1444, 800))
        pygame.display.set_caption("GRASS RPG")

        if not pygame.mixer.get_init():
            pygame.mixer.init()

        # 2. State & Options Initialization
        self.scene = None
        self.scenario = scenario
        self.running = True
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.player = start_player
        self.save_path = "saves/current_adventure.dat"

        # ASCII Background Engine Configuration
        # slowdown options: 1.0 = 9 FPS, 2.0 = 4.5 FPS (2x slow), 3.0 = 3 FPS (3x slow)
        self.ascii_slowdown = 2.0
        self.ascii_player = ASCIIBgPlayer(
            base_fps=9.0, slowdown=self.ascii_slowdown
        )
        self.ascii_loaded = self.ascii_player.load_frames_from_assets()

        # Title Stub surface generated using MainMenu's static generator
        self.grass_title_stub = MainMenu.create_grass_title("GRASS RPG", font_size=100)

        # Options Configuration
        self.options = {
            "master_volume": 0.5,
            "is_muted": False,
            "physical_dice_enabled": False,
            "api_key": os.environ.get("debug_api_key", ""),
            "gpt_model": "gemini-1.5-flash",
        }

        self.load_options()
        load_sfx()
        self.apply_volume()

        # 3. Chat System Initialization
        api_key = self.options.get("api_key")
        self.chat = (
            Chat(
                system_prompt=scenario.system_prompt,
                initial_message=scenario.initial_message,
                api_key=api_key,
                game=self,
            )
            if api_key
            else None
        )

    @property
    def physical_dice_enabled(self) -> bool:
        return self.options.get("physical_dice_enabled", False)

    @physical_dice_enabled.setter
    def physical_dice_enabled(self, value: bool):
        self.options["physical_dice_enabled"] = bool(value)

    def get_options_path(self):
        """Helper to guarantee we always hit src/options.json relative to this file."""
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "src",
            "options.json",
        )

    def load_options(self):
        """Loads options from src/options.json and applies audio settings."""
        path = self.get_options_path()
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    file_data = json.load(f)
                    self.options.update(file_data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[Config] Error loading {path}: {e}. Using internal defaults.")
        self.apply_volume()

    def save_options(self):
        """Saves current options dict to src/options.json."""
        path = self.get_options_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                json.dump(self.options, f, indent=4)
        except IOError as e:
            print(f"[Config] Failed to save options: {e}")
        self.apply_volume()

    def apply_volume(self):
        """Dispatches the volume update command to utils without arguments."""
        from src.utils import apply_global_volume
        apply_global_volume()

    def _get_default_options(self):
        return {
            "api_key": os.environ.get("debug_api_key", ""),
            "gpt_model": "gemini-1.5-flash",
        }

    def save_session(self, filename: str = "save_game.json"):
        """Saves the overall state of the adventure to a JSON file."""
        if not os.path.exists("saves"):
            os.makedirs("saves")

        clean_name = filename.strip().replace(" ", "_").lower()
        if not clean_name.endswith(".json"):
            clean_name += ".json"

        path = os.path.join("saves", clean_name)

        save_data = {
            "player": self.player.to_dict() if self.player else None,
            "chat_history": self.chat.history if self.chat else [],
            "scenario": (
                self.scenario.dict()
                if hasattr(self.scenario, "dict")
                else self.scenario
            ),
        }

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Failed to save session to {path}: {e}")
            return False

    def load_session(self, filename: str):
        """Loads the adventure state from a JSON file."""
        path = (
            os.path.join("saves", filename)
            if not os.path.isabs(filename)
            else filename
        )
        if not os.path.exists(path) and not os.path.isabs(filename):
            path = filename

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                from src.model.player import Player

                pd = data.get("player")
                if pd:
                    self.player = Player.from_dict(pd)

                if self.chat and "chat_history" in data:
                    self.chat.history = data["chat_history"]

                from src.engine.scene.ChatScene import ChatScene
                self.change_scene(ChatScene(self.screen, self, self.scenario))
                return True
            except Exception as e:
                print(f"Error loading {path}: {e}")
        return False

    def change_scene(self, new_scene):
        self.previous_scene = self.scene
        self.scene = new_scene
    # def change_scene(self, new_scene):
    #     self.scene = new_scene

    def main_menu(self):
        self.scene = MainMenu(None, self.screen, self)

    def back_scene(self):
        actual_scene = self.scene
        self.scene = self.previous_scene
        self.previous_scene = actual_scene

    def create_vignette_surface(self, size: tuple, intensity: int = 180, style: str = "edge") -> pygame.Surface:
        """Generates a stylized vignette overlay using circle-blitting.
        
        style="edge": Transparent center disk, dark edges/corners (DEFAULT).
        style="sun": Dark center disk (Black Sun), transparent edges (AFTER 38s).
        """
        width, height = size
        cx, cy = width // 2, height // 2
        max_radius = math.hypot(cx, cy)
        
        # 1. Build the layered concentric circle disk ('Black Sun')
        sun_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        num_steps = 30
        for i in range(num_steps, 0, -1):
            factor = i / num_steps
            radius = int(max_radius * factor)
            alpha = int((1.0 - (i / num_steps)) * intensity)
            alpha = max(0, min(255, alpha))
            
            temp_surf = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.circle(temp_surf, (0, 0, 0, alpha), (cx, cy), radius)
            sun_surf.blit(temp_surf, (0, 0))
            
        if style == "sun":
            return sun_surf
            
        # 2. For 'edge' style: subtract the Black Sun from a solid dark fill
        edge_vignette = pygame.Surface((width, height), pygame.SRCALPHA)
        edge_vignette.fill((0, 0, 0, intensity))
        edge_vignette.blit(sun_surf, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        
        return edge_vignette

    def play_splash_screen(self, duration: float = 45.0):
        if not self.ascii_loaded:
            print("[Splash] ASCII frames unavailable. Skipping to main menu.")
            return

        play_dungeon_synth_theme()

        start_time = time.time()
        screen_size = self.screen.get_size()
        title_rect = self.grass_title_stub.get_rect(
            center=(screen_size[0] // 2, screen_size[1] // 3)
        )

        # Pre-render both circle-blitted vignettes
        vignette_default = self.create_vignette_surface(screen_size, intensity=200, style="edge")
        vignette_black_sun = self.create_vignette_surface(screen_size, intensity=180, style="sun")

        showing_splash = True
        while showing_splash and self.running:
            pygame.event.pump()
            now = time.time()
            elapsed = now - start_time

            if elapsed >= duration:
                break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    showing_splash = False
                elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    showing_splash = False

            if not showing_splash:
                break

            # 1. Render ASCII Background Frame
            bg_frame = self.ascii_player.get_current_frame(screen_size)
            if bg_frame:
                self.screen.blit(bg_frame, (0, 0))
            else:
                self.screen.fill((10, 15, 10))
            
            # (Optional: permanent black sun screen vignette) 2. Blit Vignette (Default edge vignette for <38s, then switch to Black Sun)
            """ active_vignette = vignette_black_sun if elapsed >= 38.0 else vignette_default
            self.screen.blit(active_vignette, (0, 0))
             """

            # 2. Interchange every 38 seconds (Even intervals = edge, Odd intervals = sun)
            cycle_index = int(elapsed // 38.0)
            active_vignette = vignette_black_sun if (cycle_index % 2 == 1) else vignette_default
            self.screen.blit(active_vignette, (0, 0))

            # 3. Render Title Stub Overlay
            self.screen.blit(self.grass_title_stub, title_rect)

            pygame.display.flip()
            self.clock.tick(60)

    def start(self):
        # Play ASCII splash screen menu background
        self.play_splash_screen(duration=8.0)

        # Load Main Menu
        self.main_menu()

        while self.running:
            pygame.event.pump()
            self.screen.fill((0, 0, 0))

            mouse_pos = pygame.mouse.get_pos()
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                ):
                    self.running = False

            # Active scene handles events and renders
            if self.scene:
                self.scene.handle_events(events, mouse_pos)
                self.scene.update()
                self.scene.render(self.screen)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()