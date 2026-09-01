import pygame
from src.engine.ui.UIElement import UIElement
from src.engine.ui.SimpleText import SimpleText
from src.utils import play_retro_woosh

class HorizontalBar(UIElement):
    def __init__(self, screen_w, screen_h, text, hold_duration_ms=2000):
        super().__init__(None, (0, 0)) # Call parent initialization
        self.screen_w = screen_w
        self.height = 60
        self.y = (screen_h // 2) - (self.height // 2)
        
        self.x = screen_w  # Starts off-screen right
        self.target_center_x = 0  
        
        self.text_elem = SimpleText(text, 28, (0, 0), (255, 255, 255))
        
        self.played_sound = False
        self.state = "ENTER"
        self.hold_duration = hold_duration_ms
        self.hold_start_time = 0
        self.speed = 40
        
        self.flash_timer = 0
        self.is_done = False 
        self.visible = True
        self.image = None

    def update(self, event=None, mouse_pos=None):
        if self.state == "ENTER":
            if not self.played_sound:
                play_retro_woosh()  # FIX: Added parentheses to actually call the function
                self.played_sound = True

            self.x -= self.speed
            if self.x <= 0:
                self.x = 0
                self.state = "HOLD"
                self.hold_start_time = pygame.time.get_ticks()
                
        elif self.state == "HOLD":
            now = pygame.time.get_ticks()
            if now - self.hold_start_time > self.hold_duration:
                self.state = "EXIT"
                
        elif self.state == "EXIT":
            self.x -= self.speed
            if self.x < -self.screen_w:
                self.is_done = True 

    # FIX: Renamed from 'draw' to 'render' to comply with SceneElement ABC
    def render(self, screen: pygame.Surface): 
        if self.is_done: return
        
        # Draw Black Stripe (with alpha)
        stripe_surface = pygame.Surface((self.screen_w, self.height), pygame.SRCALPHA)
        stripe_surface.fill((0, 0, 0, 200)) 
        
        # Flashing borders (Gold/White alternating)
        self.flash_timer += 1
        border_color = (255, 215, 0) if (self.flash_timer // 10) % 2 == 0 else (255, 255, 255)
        pygame.draw.line(stripe_surface, border_color, (0, 0), (self.screen_w, 0), 2)
        pygame.draw.line(stripe_surface, border_color, (0, self.height-2), (self.screen_w, self.height-2), 2)
        
        screen.blit(stripe_surface, (self.x, self.y))
        
        # Draw Text centered inside the stripe
        text_x = self.x + (self.screen_w // 2) - (self.text_elem.font.size(self.text_elem.text)[0] // 2)
        text_y = self.y + 15
        self.text_elem.position = (text_x, text_y)
        
        # FIX: Changed from .draw to .render to match SceneElement structure
        self.text_elem.render(screen)