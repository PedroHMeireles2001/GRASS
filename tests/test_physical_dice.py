import os
import sys
import json
import pygame

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def test_physical_dice_option():
    print("Testing Game physical_dice_enabled option binding...")
    from src.engine.Game import Game
    from src.model.scenario import Scenario

    dummy_scenario = Scenario(system_prompt="Test", initial_message="Hello")
    
    # Initialize Game with dummy scenario
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass
    game = Game(dummy_scenario)

    assert hasattr(game, "physical_dice_enabled")
    initial_val = game.physical_dice_enabled
    
    # Toggle option
    game.physical_dice_enabled = True
    assert game.physical_dice_enabled is True
    assert game.options["physical_dice_enabled"] is True

    game.physical_dice_enabled = False
    assert game.physical_dice_enabled is False

    # Restore initial
    game.physical_dice_enabled = initial_val
    print("Game physical_dice_enabled test passed!\n")

def test_entity_attack_raw_d20():
    print("Testing Entity.attack with raw_d20 parameter...")
    from src.model.entity import Entity, EntityCategory
    from src.model.attribs import CharacterAttrib

    attrs = {
        CharacterAttrib.STRENGTH: 10,
        CharacterAttrib.DEXTERITY: 14, # +2 mod
        CharacterAttrib.CONSTITUTION: 10,
        CharacterAttrib.INTELLIGENCE: 10,
        CharacterAttrib.WISDOM: 10,
        CharacterAttrib.CHARISMA: 10,
    }

    attacker = Entity(None, "Hero", health=20, armor=0, dodge=12, base_damage=5, attributes=attrs)
    defender = Entity(None, "Goblin", health=20, armor=0, dodge=15, base_damage=3, attributes=attrs)

    # 1. Test low roll (raw 2 + mod 2 = 4 < dodge 15) -> Miss
    passed, result, damage = attacker.attack(defender, raw_d20=2)
    assert passed is False
    assert result == 4
    assert damage == 0

    # 2. Test high roll (raw 15 + mod 2 = 17 >= dodge 15) -> Hit
    passed, result, damage = attacker.attack(defender, raw_d20=15)
    assert passed is True
    assert result == 17
    assert damage == 5 # 5 base_damage + 0 str_mod

    # 3. Test natural 20 critical (raw 20 + mod 2 = 22) -> Crit Hit
    passed, result, damage = attacker.attack(defender, raw_d20=20)
    assert passed is True
    assert result == 22
    assert damage == 10 # 5 * crit_multiplier 2

    print("Entity.attack raw_d20 test passed!\n")

def test_character_creator_physical_mode():
    print("Testing CharacterCreator physical dice mode...")
    from src.engine.Game import Game
    from src.model.scenario import Scenario
    from src.engine.scene.CharacterCreator import CharacterCreator

    dummy_scenario = Scenario(system_prompt="Test", initial_message="Hello")
    screen = pygame.display.set_mode((1444, 800))
    game = Game(dummy_scenario)

    game.physical_dice_enabled = True
    creator = CharacterCreator(None, screen, game)

    assert creator.show_physical_modal is True
    assert len(creator.physical_dice_inputs) == 6
    assert len(creator.rolled_atribs) == 6

    # Test changing d6 inputs for roll 0: [6, 6, 6, 1] -> best 3 sum = 18
    for d, val in enumerate(["6", "6", "6", "1"]):
        creator.physical_dice_inputs[0][d].text_str = val
    creator._on_physical_d6_changed(0)
    assert creator.rolled_atribs[0] == 18

    # Close modal
    creator._close_physical_modal()
    assert creator.show_physical_modal is False

    print("CharacterCreator physical dice mode test passed!\n")

if __name__ == "__main__":
    test_physical_dice_option()
    test_entity_attack_raw_d20()
    test_character_creator_physical_mode()
