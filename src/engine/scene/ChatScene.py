import queue
import time
import json
import pygame
import re
from typing import List, Callable, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.engine.Game import Game

from src.engine.ui.TypewriterManager import TypewriterManager
from src.engine.scene.CombatScene import CombatScene
from src.engine.scene.Scene import Scene
from src.engine.scene.SceneElement import SceneElement
from src.engine.ui.Button import Button
from src.engine.ui.ImageTransformStrategy import ColorInverter
from src.engine.ui.SimpleText import SimpleText
from src.engine.ui.StaticImage import StaticImage
from src.engine.ui.TextArea import TextAreaShow
from src.engine.ui.TextInput import TextInput
from src.engine.ui.HorizontalBar import HorizontalBar
from src.model.Item import Usable
from src.model.scenario import Scenario
from src.utils import get_center_x, print_debug, get_default_font, typewriter_sound, log_to_session

class ChatScene(Scene):
    def __init__(self, screen, game: "Game", scenario: Scenario):
        self.game = game
        self.scenario = scenario
        self.screen = screen
        
        self.eminent_combat = None
        self.last_sound_time = 0
        self.sound_cooldown = 0.08
        self.loading = False
        self.active_typewriter = None 
        self._ui_queue = queue.Queue()

        # Inject physical dice mode awareness into Gemini DM context
        if getattr(self.game, "physical_dice_enabled", False):
            if hasattr(self.game, "chat") and hasattr(self.game.chat, "system_prompt"):
                if "Physical Dice Mode" not in self.game.chat.system_prompt:
                    self.game.chat.system_prompt += (
                        "\n\n[SYSTEM DIRECTIVE: Physical Dice Mode is ENABLED. "
                        "The player is using real physical tabletop dice. "
                        "Prompt the player to roll physical dice for attribute checks, skill tests, and saving throws during narrative choices.]"
                    )
        
        initial_text = ""
        if hasattr(self.game, "chat") and self.game.chat and getattr(self.game.chat, "history", None):
            for i, msg in enumerate(self.game.chat.history):
                role = msg.get("role")
                parts = msg.get("parts", [])
                text_content = "".join(part.get("text", "") for part in parts)
                
                if i == 0 and role == "user":
                    initial_text += f"DM:\n{text_content}\n"
                elif role == "user":
                    initial_text += f"{self.game.player.name}:\n{text_content}\n"
                elif role == "model" or role == "assistant":
                    initial_text += f"DM:\n{text_content}\n"
        else:
            initial_text = f"DM:\n{scenario.initial_message}\n"

        self.actual_text = TextAreaShow(
            text=initial_text,
            position=(20, screen.get_height() // 2),
            width=screen.get_width() - 32,
            height=(screen.get_height() // 2) - 75
        )
        
        self.player_input = TextInput(
            position=(24, screen.get_height() - 50),
            width=screen.get_width() - 300,
            on_change=self._on_change,
            on_submit=self._submit
        )

        self.submit_button = Button(
            image=None,
            position=(screen.get_width() - 200, screen.get_height() - 50),
            text=SimpleText("Submit!", 24, (0, 0), (0, 0, 0)),
            background_color=(255, 255, 255),
            hover_transform_strategy=ColorInverter(),
            click_function=lambda: self._submit(self.player_input.text.text)
        )

        self.combat_button = Button(
            image=None,
            position=(get_center_x(screen, get_default_font(24).size("Enter Combat!")[0]), screen.get_height() - 50),
            text=SimpleText("Enter Combat!", 24, (0, 0), (0, 0, 0)),
            background_color=(255, 255, 255),
            hover_transform_strategy=ColorInverter(),
            click_function=self._submit_combat
        )
        self.combat_button.visible = self.combat_button.enabled = False

        btn_save = Button(
            image=None,
            text=SimpleText("Save", 18, (0, 0), (255, 255, 255)),
            background_color=(50, 50, 150),
            position=(screen.get_width() - 100, 20),
            click_function=self._save_game
        )

        btn_options = Button(
            image=None,
            text=SimpleText("Options", 18, (0, 0), (255, 255, 255)),
            background_color=(100, 100, 100),
            position=(screen.get_width() - 250, 20),
            click_function=self._open_options
        )

        btn_sheet = Button(
            image=None,
            text=SimpleText("Sheet", 18, (0, 0), (255, 255, 255)),
            background_color=(150, 50, 50),
            position=(screen.get_width() - 665, 20),
            click_function=self._toggle_char_sheet
        )

        self.commands: Dict[str, Callable[[List[str]], None]] = {
            "save": self._manual_save,
            "get_player_status": self._get_player_attribute,
            "player": lambda args: self._put_text(f"\nSystem:\n{self.game.player.to_text(markdown=False)}"),
            "quit": lambda args: self.game.main_menu(),
            "exit": lambda args: self.game.main_menu()
        }

        self.btn_save = btn_save
        self.btn_options = btn_options
        self.btn_sheet = btn_sheet

        super().__init__(None, screen, game)
        self.player_input.focus = True
        pygame.key.start_text_input()

    def build_scene(self, game: "Game") -> List[SceneElement]:
        from src.engine.ui.CharacterSheetPanel import CharacterSheetPanel
        self.char_sheet = CharacterSheetPanel(self.game.player, (self.screen.get_width(), 0), self.screen)
        
        return [
            StaticImage(
                relative_path="chat.png",
                size=(400, 400),
                position=(get_center_x(self.screen, 400), 0),
                circle_radius=200
            ),
            self.submit_button,
            self.player_input,
            self.actual_text,
            self.combat_button,
            self.btn_save,
            self.btn_options,
            self.btn_sheet,
            self.char_sheet
        ]

    def _open_options(self):
        from src.engine.scene.Options import Options
        self.game.change_scene(Options(None, self.screen, self.game))

    def _toggle_char_sheet(self):
        if hasattr(self, 'char_sheet'):
            self.char_sheet.toggle()

    def _save_game(self):
        self._put_text("\n[System: Type a filename for your save and press Enter]\n")
        self.saving_mode = True
        self.player_input.focus = True
        pygame.key.start_text_input()

    def _manual_save(self, args: List[str]):
        self.game.save_session()
        self._put_text("\n[Sistema: Jogo salvo com sucesso!]\n")

    def _on_change(self, text):
        self.player_input.text.text = text

    def _submit(self, text):
        text = text.strip()
        if not text:
            return
        
        if getattr(self, 'saving_mode', False):
            if self.game.save_session(text):
                self._put_text(f"\n[System: Game saved as '{text}']\n")
            else:
                self._put_text(f"\n[System: Failed to save game!]\n")
            self.saving_mode = False
            self.player_input.text_str = ""
            return

        if text.startswith("/"):
            parts = text[1:].split()
            cmd = parts[0]
            args = parts[1:]
            if cmd in self.commands:
                self.commands[cmd](args)
                self.player_input.text.change_text("")
                return

        self.player_input.text.change_text("")
        user_msg = f"\n{self.game.player.name}:\n{text}\nDM:\n"
        self._put_text(user_msg)
        log_to_session(f"PLAYER ({self.game.player.name}): {text}")
        self._hide_input()
        
        self.active_typewriter = TypewriterManager("Mestre está pensando...", speed_ms=50)
        
        try:
            self.game.chat.send_message(text, callback=self._on_chat_response)
        except Exception as e:
            self._on_chat_response(f"[Erro na API: {str(e)}]")

    def _on_chat_response(self, response_text):
        self._ui_queue.put({"type": "chat_response", "text": response_text})

    def _extract_json_payloads(self, text: str) -> List[Dict[str, Any]]:
        blocks = []
        
        for m in re.finditer(r'```json\s*(.*?)\s*```', text, re.DOTALL):
            try:
                blocks.append((m.start(), m.end(), json.loads(m.group(1))))
            except Exception:
                pass

        stack = []
        start_idx = -1
        for i, char in enumerate(text):
            if any(b_start <= i < b_end for b_start, b_end, _ in blocks):
                continue
            if char == '{':
                if not stack:
                    start_idx = i
                stack.append('{')
            elif char == '}':
                if stack:
                    stack.pop()
                    if not stack and start_idx != -1:
                        try:
                            blocks.append((start_idx, i + 1, json.loads(text[start_idx:i+1])))
                        except Exception:
                            pass

        blocks.sort(key=lambda x: x[0])
        return [b[2] for b in blocks]

    def _update_player_state(self, data: dict):
        player = self.game.player
        if not player or not isinstance(data, dict): return

        if "stats" in data and isinstance(data["stats"], dict):
            s = data["stats"]
            if "hp" in s: player.heal(s["hp"])
            if "gold" in s: player.gold = max(0, player.gold + s["gold"])
            if "xp" in s: player.give_xp(s["xp"])
            if "mana" in s: player.mana = max(0, min(player.max_mana, player.mana + s["mana"]))

        inv = data.get("inventory") or data.get("itens") or data.get("items")
        if inv and isinstance(inv, dict):
            for item_id, qty in inv.items():
                try:
                    player.give_item(int(item_id), qty)
                except Exception: pass

        if "stats" in data and isinstance(data["stats"], dict) and "xp" in data["stats"]:
            self.elements.append(HorizontalBar(self.screen.get_width(), self.screen.get_height(), f"+{data['stats']['xp']} XP GAINED!"))

    def handle_events(self, events: List[pygame.event.Event], mouse_pos: tuple):
        super().handle_events(events, mouse_pos)
        
        if self.active_typewriter and not self.active_typewriter.is_complete:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        new_text = self.active_typewriter.reveal_all()
                        if new_text:
                            self.actual_text.text += new_text
                            typewriter_sound()

    def update(self):
        try:
            while True:
                msg = self._ui_queue.get_nowait()
                if msg.get("type") == "chat_response":
                    response_text = msg.get("text")
                    
                    if not response_text or not str(response_text).strip():
                        response_text = "[O Mestre permaneceu em silêncio...]"
                        self._show_input()

                    json_payloads = self._extract_json_payloads(response_text)
                    for data in json_payloads:
                        self._update_player_state(data)

                    response_text = re.sub(r'```json\s*', '', response_text)
                    response_text = re.sub(r'```', '', response_text)

                    log_to_session(f"DM: {response_text}")
                    self.active_typewriter = TypewriterManager(response_text, speed_ms=25)
        except queue.Empty:
            pass

        super().update()
        if self.active_typewriter and not self.active_typewriter.is_complete:
            keys = pygame.key.get_pressed()
            fast_forward_active = keys[pygame.K_SPACE]
            
            new_text = self.active_typewriter.update(fast_forward=fast_forward_active)
            if new_text:
                self.actual_text.text += new_text
                typewriter_sound()
        elif self.active_typewriter and self.active_typewriter.is_complete:
            self.active_typewriter = None
            self._show_input()

    def _put_text(self, new_text):
        self.actual_text.text += new_text
        typewriter_sound()

    def _get_player_attribute(self, args: List[str]):
        if not args:
            self._put_text("\nSystem:\nArgumentos inválidos!\n")
            return
        attr = args[0].lower()
        if not hasattr(self.game.player, attr):
            self._put_text(f"\nSystem:\nAtributo {attr} não encontrado!\n")
            return
        self._put_text(f"\nSystem:\n{attr}={str(getattr(self.game.player, attr))}\n")

    def _submit_combat(self):
        if self.eminent_combat:
            self.game.change_scene(CombatScene(
                game=self.game,
                screen=self.screen,
                combat=self.eminent_combat
            ))

    def _hide_input(self):
        self.submit_button.visible = self.submit_button.enabled = False
        self.player_input.visible = self.player_input.enabled = False

    def _show_input(self):
        if self.eminent_combat is None:
            self.submit_button.visible = self.submit_button.enabled = True
            self.player_input.visible = self.player_input.enabled = True

    def wait_combat_confirm(self, combat):
        self._hide_input()
        self.combat_button.visible = self.combat_button.enabled = True
        self.eminent_combat = combat

    def end_combat(self):
        self.combat_button.visible = self.combat_button.enabled = False
        if self.eminent_combat:
            result = getattr(self.eminent_combat, "result", None)
            
            victory = getattr(result, "victory", False)
            player_flee = getattr(result, "player_flee", False)
            enemies_flee = getattr(result, "enemies_flee", [])
            kills = getattr(result, "kills", 0)
            enemies = getattr(result, "enemies", [])
            
            xp_earned = getattr(result, "xp_earned", 0)
            loot_items = getattr(result, "loot_items", [])

            msg = (
                f"event:combat_ended\n"
                f"Victory:{victory}\n"
                f"Player Fled:{player_flee}\n"
                f"Enemies Flee:{len(enemies_flee)}\n"
                f"Player Kills:{kills}\n"
                f"Total Enemies:{len(enemies)}"
            )

            if xp_earned or loot_items:
                msg += f"\nYield Context (DM discretion): XP={xp_earned}, Items={loot_items}"

            self.game.chat.send_message(msg, callback=self._on_chat_response)
            self.eminent_combat = None

        self._show_input()