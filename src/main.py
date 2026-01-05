import pygame

from src.constants import DEBUG
from src.engine.Game import Game
from src.model.scenario import DEFAULT_SCENARIO, DEBUG_SCENARIO

if __name__ == "__main__":
    pygame.init()
    game = Game(DEFAULT_SCENARIO if not DEBUG else DEBUG_SCENARIO)
    game.main_menu()
    game.start()