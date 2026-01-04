import pygame

from src.engine.Game import Game
from src.model.scenario import DEFAULT_SCENARIO

if __name__ == "__main__":
    pygame.init()
    game = Game(DEFAULT_SCENARIO)
    game.main_menu()
    game.start()