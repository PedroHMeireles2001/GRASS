import os
import sys
import json
import pygame

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def init_dummy_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    pygame.init()
    pygame.font.init()

def test_chat_scene_thread_safety_and_null_guard():
    print("Testing ChatScene thread-safe queue & null payload guard...")
    init_dummy_pygame()
    
    from src.engine.Game import Game
    from src.model.scenario import Scenario
    from src.engine.scene.ChatScene import ChatScene

    dummy_scenario = Scenario(system_prompt="Test DM Prompt", initial_message="Welcome!")
    screen = pygame.display.set_mode((1024, 768))
    game = Game(dummy_scenario)

    chat_scene = ChatScene(screen, game, dummy_scenario)

    # 1. Simulate thread-safe response pushing
    chat_scene._on_chat_response("Found items: ```json\n{\"inventory\": {\"1\": 2}}\n```")
    assert not chat_scene._ui_queue.empty()

    # 2. Process queue in main thread loop update()
    chat_scene.update()
    assert chat_scene._ui_queue.empty()

    # 3. Verify null / empty response safeguard
    chat_scene._on_chat_response(None)
    chat_scene.update()
    
    # Text area buffer should receive typewriter updates safely
    assert "[O Mestre permaneceu em silêncio...]" in chat_scene.actual_text.text or chat_scene.active_typewriter is not None
    print("ChatScene queue & null guard test passed!\n")

def test_skill_raw_d20_propagation():
    print("Testing Skill.execute raw_d20 physical dice propagation...")
    from src.model.skills import Skill, SKILL_FACTORY, SkillEnum
    from src.model.entity import Entity, DamageType
    from src.model.attribs import CharacterAttrib

    attrs = {
        CharacterAttrib.STRENGTH: 10,
        CharacterAttrib.DEXTERITY: 14,
        CharacterAttrib.CONSTITUTION: 10,
        CharacterAttrib.INTELLIGENCE: 16, # +3 spell mod
        CharacterAttrib.WISDOM: 10,
        CharacterAttrib.CHARISMA: 10,
    }

    mage = Entity(None, "Mage", health=20, armor=0, dodge=12, base_damage=2, attributes=attrs)
    target = Entity(None, "Orc", health=30, armor=0, dodge=15, base_damage=4, attributes=attrs)

    skill = SKILL_FACTORY[SkillEnum.MAGIC_MISSILE]

    # 1. Low roll test (raw 2 + intelligence mod 3 = 5 < dodge 15) -> Miss
    target_hp_before = target.health
    skill.execute(mage, target, combat=None, raw_d20=2)
    assert target.health == target_hp_before

    # 2. High roll test (raw 15 + intelligence mod 3 = 18 >= dodge 15) -> Hit
    skill.execute(mage, target, combat=None, raw_d20=15)
    assert target.health < target_hp_before

    print("Skill raw_d20 propagation test passed!\n")

def test_text_area_show_brace_deserialization():
    print("Testing TextAreaShow raw brace-matching and JSON card wrapping...")
    init_dummy_pygame()
    
    from src.engine.ui.TextArea import TextAreaShow

    area = TextAreaShow(
        position=(0, 0),
        width=400,
        height=300,
        text="The enemy appears: {\"inimigos\": [{\"nome\": \"Goblin\", \"quantidade\": 2}]}"
    )

    # Verify cached line types contain the parsed JSON payload card
    card_lines = [item for item in area._cached_lines if item[1] == 'card']
    assert len(card_lines) == 1
    
    payload = card_lines[0][0]
    assert "inimigos" in payload
    assert payload["inimigos"][0]["nome"] == "Goblin"

    print("TextAreaShow brace deserialization test passed!\n")

def test_ui_dynamic_positioning_bounds():
    print("Testing UI component dynamic positioning and bounds...")
    init_dummy_pygame()

    from src.engine.ui.CharacterSheetPanel import CharacterSheetPanel
    from src.model.player import Player
    from src.model.classes import CLASS_FACTORY, CharacterClassEnum
    from src.model.race import CharacterRace
    from src.model.attribs import CharacterAttrib

    attrs = {attr: 10 for attr in CharacterAttrib}
    player = Player("Hero", CLASS_FACTORY[CharacterClassEnum.WARRIOR], CharacterRace.HUMAN, attrs, [], [])
    
    screen = pygame.display.set_mode((1280, 720))
    panel = CharacterSheetPanel(player, (1280, 0), screen)

    # Test closed panel position
    assert panel.target_x == 1280

    # Toggle open
    panel.toggle()
    assert panel.target_x == 1280 - panel.width
    assert panel.target_x < 1280

    print("UI positioning bounds test passed!\n")

if __name__ == "__main__":
    test_chat_scene_thread_safety_and_null_guard()
    test_skill_raw_d20_propagation()
    test_text_area_show_brace_deserialization()
    test_ui_dynamic_positioning_bounds()