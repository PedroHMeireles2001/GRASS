import glob
import os
import sys
import time
import pygame


class ASCIIBgPlayer:
    """Loads ASCII text frames, pre-renders them to surfaces, and handles

    playback with speed controls (9 FPS base, 2x / 3x slowdown).
    """

    def __init__(self, base_fps: float = 9.0, slowdown: float = 1.0):
        self.base_fps = base_fps
        self.slowdown = max(1.0, float(slowdown))  # 1x, 2x, 3x
        self.effective_fps = self.base_fps / self.slowdown
        self.frame_delay = 1.0 / self.effective_fps

        self.surfaces = []
        self.current_frame_idx = 0
        self.last_frame_time = 0.0

    def load_frames_from_assets(
        self, font_name: str = "consolas", font_size: int = 12
    ):
        """Locates the ASCII frame folder in assets and pre-renders each frame

        into a Pygame Surface for fast, lossless scaling.
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        target_dir = os.path.normpath(os.path.join(script_dir, "../../../assets/ASCIItxt"))
        frame_files = sorted(glob.glob(os.path.join(target_dir, "frame_*.txt")))

        if not frame_files:
            print(f"[ASCII Player] Warning: No frame files found in {target_dir}")
            return False

        print(
            f"[ASCII Player] Loading {len(frame_files)} ASCII frames from {target_dir}..."
        )

        pygame.font.init()
        font = pygame.font.SysFont(font_name, font_size)

        # Color scheme
        char_color = (200, 220, 200)  # Light green/white matrix tint
        bg_color = (10, 15, 10)  # Dark background tint

        self.surfaces = []
        for file_path in frame_files:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = [line.rstrip("\n") for line in f.readlines()]

            if not lines:
                continue

            # Render text lines onto offscreen surface
            line_surfs = [
                font.render(line, True, char_color) for line in lines
            ]
            max_w = max(s.get_width() for s in line_surfs) if line_surfs else 1
            total_h = sum(s.get_height() for s in line_surfs)

            # Create native surface for frame
            frame_surf = pygame.Surface((max_w, total_h))
            frame_surf.fill(bg_color)

            y_off = 0
            for l_surf in line_surfs:
                frame_surf.blit(l_surf, (0, y_off))
                y_off += l_surf.get_height()

            self.surfaces.append(frame_surf)

        print(
            f"[ASCII Player] Successfully pre-rendered {len(self.surfaces)} frames at {self.effective_fps:.2f} FPS."
        )
        return len(self.surfaces) > 0

    def get_current_frame(
        self, target_size: tuple[int, int]
    ) -> pygame.Surface | None:
        """Returns the current animation frame scaled losslessly to the target display resolution."""
        if not self.surfaces:
            return None

        now = time.time()
        if now - self.last_frame_time >= self.frame_delay:
            self.current_frame_idx = (self.current_frame_idx + 1) % len(
                self.surfaces
            )
            self.last_frame_time = now

        raw_surf = self.surfaces[self.current_frame_idx]

        # Smooth scale stretches high-row ASCII output clean and losslessly to target resolution
        return pygame.transform.smoothscale(raw_surf, target_size)