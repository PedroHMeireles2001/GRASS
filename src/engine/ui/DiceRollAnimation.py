import pygame
import os
from src.engine.ui.UIElement import UIElement
from src.engine.ui.SimpleText import SimpleText


class DiceRollAnimation(UIElement):
    def __init__(self, position, duration_ms=1500, scale_factor=0.35):
        super().__init__(None, position)
        self.duration_ms = duration_ms
        self.start_time = pygame.time.get_ticks()
        self.is_rolling = True
        self.result_text = None
        self.is_visible = True          # NEW: control if animation is shown at all

        base_path = "assets/sfx/dice"

        # Configuração exata dos frames e seus tempos (em milissegundos)
        # a, b, d, f = 132ms (66 * 2). c, e = 66ms.
        self.frame_config = [
            ("sptD10a.jpg", 132),
            ("sptD10b.jpg", 132),
            ("sptD10c.jpg", 66),
            ("sptD10d.jpg", 132),
            ("sptD10e.jpg", 66),
            ("sptD10f.jpg", 132),
        ]

        self.frames = []

        color_to_remove = (22, 23, 27)  # #16171b

        # Carrega, redimensiona, remove cor e armazena os frames
        for filename, delay in self.frame_config:
            path = os.path.join(base_path, filename)
            try:
                img = pygame.image.load(path).convert_alpha()  # support alpha
                new_width = int(img.get_width() * scale_factor)
                new_height = int(img.get_height() * scale_factor)
                img = pygame.transform.scale(img, (new_width, new_height))

                # Remove #16171b → transparent
                for y in range(img.get_height()):
                    for x in range(img.get_width()):
                        c = img.get_at((x, y))
                        if c.r == 22 and c.g == 23 and c.b == 27:
                            img.set_at((x, y), (0, 0, 0, 0))  # fully transparent

                self.frames.append({
                    "image": img,
                    "delay": delay,
                })
            except FileNotFoundError:
                print(f"[Aviso] Imagem do dado não encontrada: {path}")
                fallback = pygame.Surface((50, 50), pygame.SRCALPHA)
                fallback.fill((255, 0, 255))  # magenta fallback
                self.frames.append({"image": fallback, "delay": delay})

        self.current_frame_idx = 0
        self.last_frame_update = self.start_time


    def set_result(self, result_string: str):
        # Chamado quando o tempo mock acabar ou a IA responder
        self.result_text = SimpleText(
            text=f"Roll result: {result_string}", 
            size=32, 
            position=self.position,
            text_color=(255, 215, 0),  # dourado
        )
        print("DEBUG: set_result called with:", result_string)   # add this


    def hide_after_3_seconds(self):
        # Called from CharacterCreator when you instantiate the roll animation
        # Records the spawn time so you can hide after 3 seconds
        self.spawn_time = pygame.time.get_ticks()
        self.is_visible = True


    def update(self, event, mouse_pos):
        if not self.frames:
            return

        now = pygame.time.get_ticks()

        # Check if 3 seconds passed → hide the animation
        if hasattr(self, "spawn_time") and now - self.spawn_time >= 3000:
            self.is_visible = False
            return

        if not self.is_rolling:
            return

        # Checa se o tempo total (1500ms) acabou
        if now - self.start_time >= self.duration_ms:
            self.is_rolling = False
            # Force text display when animation stops
            if hasattr(self, "temp_result_str"):   # or pass via set_result
                self.set_result(self.temp_result_str)
            return

        # Pega o delay específico do frame atual
        current_delay = self.frames[self.current_frame_idx]["delay"]

        # Checa se já passou tempo suficiente para pular para o próximo frame
        if now - self.last_frame_update >= current_delay:
            self.current_frame_idx = (self.current_frame_idx + 1) % len(self.frames)
            self.last_frame_update = now


    def render(self, screen):
        if not self.is_visible or not self.frames:
            return

        if self.is_rolling:
            current_image = self.frames[self.current_frame_idx]["image"]
            screen.blit(current_image, self.position)
        else:
            static_image = self.frames[0]["image"]
            screen.blit(static_image, self.position)

            if self.result_text:
                print("DEBUG: Rendering result text")  # <── add this debug print


                text_x = self.position[0] + (static_image.get_width() // 2) - (self.result_text.rect.width // 2)
                text_y = self.position[1] + (static_image.get_height() // 2) - (self.result_text.rect.height // 2)
                self.result_text.position = (text_x, text_y)
                self.result_text.render(screen)
