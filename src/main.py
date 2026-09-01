import sys
import os
import pygame
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  
from src.constants import DEBUG
from src.engine.Game import Game
from src.utils import load_sfx
from src.model.scenario import DEFAULT_SCENARIO, DEBUG_SCENARIO

if __name__ == "__main__":
    pygame.init()
    # pygame.mixer.init()
    game = Game(DEFAULT_SCENARIO if not DEBUG else DEBUG_SCENARIO)
    game.main_menu()
    game.start()
