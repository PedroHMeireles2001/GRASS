import pygame
from src.engine.ui.SimpleText import SimpleText

class TypewriterManager:
    def __init__(self, text="", font_size=20, color=(255, 255, 255), width=500, speed_ms=25):
        self.full_text = text
        self.displayed_lines = []
        self.current_typing_text = ""
        self.char_index = 0
        self.width = width
        self.font_size = font_size
        self.color = color
        self.last_update = 0
        # self.speed = 25  # ms per char
        self.speed = speed_ms  # Map speed_ms to internal speed
        self.line_height = font_size + 8

    def start_typing(self, text: str):
        """Clears old state and starts a new message."""
        self.full_text = text
        self.char_index = 0
        self.current_typing_text = ""
        self.displayed_lines = []

    @property
    def is_complete(self):
        return self.char_index >= len(self.full_text)
    
    def _needs_wrap(self):
    
    # Simple pixel-based width check using font size approximation
        return len(self.current_typing_text) * (self.font_size // 2) > self.width

    def update(self, fast_forward: bool = False):
        now = pygame.time.get_ticks()
        new_chars = ""  # Track new characters THIS FRAME only
        
        # When fast-forwarding, we allow the loop to process multiple characters 
        # per frame. This smoothly skips the frame delay constraint.
        chars_to_process = 4 if fast_forward else 1
        processed = 0
        
        while self.char_index < len(self.full_text) and processed < chars_to_process:
            # Check delay constraints only if we aren't fast-forwarding
            if not fast_forward and (now - self.last_update <= self.speed):
                break
                
            char = self.full_text[self.char_index]
            self.current_typing_text += char
            new_chars += char  # Only new chars
            self.char_index += 1
            self.last_update = now
            processed += 1
            
            # Line wrapping
            if char == '\n' or (char == ' ' and self._needs_wrap()):
                self.displayed_lines.append(self.current_typing_text.strip())
                self.current_typing_text = ""
        
        # 🔥 CORRECT: Always return new_chars (empty string when done)
        return new_chars  # "", "a", "ab", "abc...", never None!

    def reveal_all(self) -> str:
        """Instantly processes all remaining text in the buffer and returns it."""
        new_chars = ""
        while self.char_index < len(self.full_text):
            char = self.full_text[self.char_index]
            self.current_typing_text += char
            new_chars += char
            self.char_index += 1
            
            # Line wrapping
            if char == '\n' or (char == ' ' and self._needs_wrap()):
                self.displayed_lines.append(self.current_typing_text.strip())
                self.current_typing_text = ""
        return new_chars



    def draw(self, screen, position):
        x, y = position
        
        # Render previously completed lines
        for i, line_text in enumerate(self.displayed_lines):
            line_surface = SimpleText(text=line_text, size=self.font_size, 
                                     position=(x, y + (i * self.line_height)), 
                                     text_color=self.color)
            line_surface.draw(screen)
            
        # Render the line currently being "born"
        if self.current_typing_text:
            current_y = y + (len(self.displayed_lines) * self.line_height)
            typing_surface = SimpleText(text=self.current_typing_text, 
                                       size=self.font_size, 
                                       position=(x, current_y), 
                                       text_color=self.color)
            typing_surface.draw(screen)