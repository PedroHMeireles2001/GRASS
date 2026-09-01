from typing import List, Optional, Dict, Any, TYPE_CHECKING
import pygame

from src.engine.ui.DiceRollAnimation import DiceRollAnimation
from src.constants import IMAGE_SIZE
from src.engine.scene.Scene import Scene
from src.engine.scene.SceneElement import SceneElement
from src.engine.ui.Bar import Bar
from src.engine.ui.Button import Button
from src.engine.ui.EntityImg import EntityImg
from src.engine.ui.ImageTransformStrategy import ColorInverter
from src.engine.ui.RadioButton import RadioButtonGroup
from src.engine.ui.SimpleText import SimpleText
from src.engine.ui.TextInput import TextInput
from src.model.Item import Usable
from src.model.combat import Combat
from src.model.entity import Entity
from src.model.skills import Skill
from src.utils import get_center_x, get_default_font, grid_position, print_debug

if TYPE_CHECKING:
    from src.engine.Game import Game

class CombatScene(Scene):
    def __init__(self, screen, game, combat: Combat):
        self.game = game
        self.combat = combat
        self.use_skill: bool = False
        self.use_item = False
        self.selected_skill: Optional[Skill] = None
        self.selected_item: Optional[Usable] = None
        self.target: Entity = combat.enemies[0]

        # Dice animation state variables
        self.dice_animation = None
        self.roll_animation_active = False

        # Physical dice roll modal components
        self.physical_roll_active = False
        self.pending_physical_action: Optional[Dict[str, Any]] = None
        self.physical_d20_input = TextInput(
            position=(0, 0),
            width=120,
            height=35,
            initial_text="",
            text_size=18,
            label_str="Result d20 (1-20):",
            label_top=True
        )
        self.physical_roll_error = SimpleText("", 16, (0, 0), (255, 60, 60))
        self.physical_roll_submit_button = Button(
            image=None,
            position=(0, 0),
            background_color=(100, 255, 100),
            text=SimpleText("Submit Roll", 18, (0, 0), (0, 0, 0)),
            hover_transform_strategy=ColorInverter(),
            click_function=self._submit_physical_attack_roll
        )

        self.rg_skill_select = RadioButtonGroup(
            position=(50, screen.get_height() - screen.get_height() // 4),
            label_str="Skills",
            options=[(skill.name, skill) for skill in self.game.player.skills],
            on_change=self._set_selected_skill
        )
        self.rg_item_select = RadioButtonGroup(
            position=(50, screen.get_height() - screen.get_height() // 4),
            label_str="Usable Items",
            options=[(item.name, item) for item in self.game.player.inventory if isinstance(item, Usable)],
            on_change=self._set_selected_item
        )
        self.life_bar = Bar(
            position=(get_center_x(screen, 100), 100),
            width=100,
            max_progress=self.game.player.max_health,
            initial_progress=self.game.player.health
        )
        self.log_text = SimpleText("", 24, position=(0, 0))
        self.flee_button = Button(
            image=None,
            position=self._button_grid_position(3, screen),
            background_color=(255, 255, 255),
            text=SimpleText("Flee!", 24, position=(0, 0), text_color=(0, 0, 0)),
            hover_transform_strategy=ColorInverter(),
            click_function=lambda: self.combat.flee_player()
        )
        self.flee_button.visible = combat.fleeable
        self.flee_button.enabled = combat.fleeable

        self.action_buttons = [
            Button(
                image=None,
                position=self._button_grid_position(0, screen),
                background_color=(255, 255, 255),
                text=SimpleText("Attack", 24, position=(0, 0), text_color=(0, 0, 0)),
                hover_transform_strategy=ColorInverter(),
                click_function=self._player_attack
            ),
            Button(
                image=None,
                position=self._button_grid_position(1, screen),
                background_color=(255, 255, 255),
                text=SimpleText("Use Skill", 24, position=(0, 0), text_color=(0, 0, 0)),
                hover_transform_strategy=ColorInverter(),
                click_function=self._use_skill_button
            ),
            Button(
                image=None,
                position=self._button_grid_position(2, screen),
                background_color=(255, 255, 255),
                text=SimpleText("Use Item", 24, position=(0, 0), text_color=(0, 0, 0)),
                hover_transform_strategy=ColorInverter(),
                click_function=self._use_item_button
            ),
            self.flee_button
        ]

        self.rg_skill_select.visible = False
        self.rg_skill_select.enabled = False
        self.rg_item_select.visible = False
        self.rg_item_select.enabled = False

        self.enemies_imgs = [EntityImg(
            entity=entity,
            position=grid_position(i, 50, 200, IMAGE_SIZE[0], IMAGE_SIZE[1], 5),
            on_click=self._set_target
        ) for i, entity in enumerate(combat.enemies)]

        super().__init__(None, screen, game)

    def update(self):
        if self.roll_animation_active and self.dice_animation:
            self.dice_animation.update(None, None)
            if not self.dice_animation.is_rolling:
                self._end_dice_animation()

        super().update()
        self.combat.update()
        self._update_action_buttons()
        self._update_log_text()
        self._update_life_bar()
        self._update_target()
        self.typewriter.update()

    def draw(self, screen):
        super().draw(screen)
        self.typewriter.draw(screen, (50, 480))
        if self.roll_animation_active and self.dice_animation:
            self.dice_animation.draw(screen)

    def render(self, screen: pygame.Surface):
        super().render(screen)
        if getattr(self, "physical_roll_active", False):
            self._render_physical_roll_modal(screen)

    def _render_physical_roll_modal(self, screen: pygame.Surface):
        sw, sh = screen.get_width(), screen.get_height()
        modal_w, modal_h = 440, 240
        modal_x = (sw - modal_w) // 2
        modal_y = (sh - modal_h) // 2

        dim = pygame.Surface((sw, sh), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 190))
        screen.blit(dim, (0, 0))

        panel = pygame.Surface((modal_w, modal_h))
        panel.fill((20, 24, 35))
        screen.blit(panel, (modal_x, modal_y))
        pygame.draw.rect(screen, (255, 215, 0), (modal_x, modal_y, modal_w, modal_h), 2)

        title_str = "Physical Skill Roll" if (self.pending_physical_action and self.pending_physical_action.get("type") == "skill") else "Physical Attack Roll"
        title = get_default_font(22).render(title_str, True, (255, 215, 0))
        screen.blit(title, (modal_x + 30, modal_y + 20))

        if self.pending_physical_action and self.pending_physical_action.get("type") == "skill":
            skill_name = self.pending_physical_action["skill"].name
            prompt_str = f"Roll a d20 physically for skill {skill_name}:"
        else:
            prompt_str = f"Roll a d20 physically to attack {self.target.name}:"

        prompt = get_default_font(14).render(prompt_str, True, (220, 220, 220))
        screen.blit(prompt, (modal_x + 30, modal_y + 55))

        inp_x = modal_x + (modal_w - 120) // 2
        inp_y = modal_y + 105
        self.physical_d20_input.position = (inp_x, inp_y)
        self.physical_d20_input.base_y = inp_y
        self.physical_d20_input.rect.x = inp_x
        self.physical_d20_input.rect.y = inp_y
        self.physical_d20_input.render(screen)

        btn_x = modal_x + (modal_w - 140) // 2
        btn_y = modal_y + 160
        self.physical_roll_submit_button.position = (btn_x, btn_y)
        self.physical_roll_submit_button.rect.topleft = (btn_x, btn_y)
        self.physical_roll_submit_button.render(screen)

        if self.physical_roll_error.text:
            err_surf = get_default_font(14).render(self.physical_roll_error.text, True, (255, 80, 80))
            err_x = modal_x + (modal_w - err_surf.get_width()) // 2
            screen.blit(err_surf, (err_x, modal_y + 205))

    def handle_events(self, events: List[pygame.event.Event], mouse_pos: tuple = (0, 0)):
        if getattr(self, "physical_roll_active", False):
            for event in events:
                self.physical_d20_input.update(event, mouse_pos)
                self.physical_roll_submit_button.update(event, mouse_pos)
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._submit_physical_attack_roll()
            return

        super().handle_events(events, mouse_pos)

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_END:
                for enemy in self.combat.enemies:
                    enemy.apply_damage(None, 9999)

    def build_scene(self, game: "Game") -> List[SceneElement]:
        return [
            SimpleText("Combat!", 48, (get_center_x(self.screen, get_default_font(48).size("Combat!")[0]), 0)),
            self.life_bar,
            self.rg_skill_select,
            self.rg_item_select,
            self.log_text,
        ] + self.action_buttons + self.enemies_imgs

    def _update_life_bar(self):
        self.life_bar.change_label(f"Life: {str(self.game.player.health)}/{str(self.game.player.max_health)}", True)
        self.life_bar.progress = self.game.player.health

    def _set_target(self, target):
        self.target = target

    def _update_log_text(self):
        if len(self.combat.log) == 0:
            return
        previous_log = self.log_text.text
        log = self.combat.log[-1]
        if log != previous_log:
            self._change_log_text(log)

    def _change_log_text(self, log):
        self.log_text.position = (get_center_x(self.screen, get_default_font(24).size(log)[0]), self.screen.get_height() - 100)
        self.log_text.change_text(log)

    def _start_dice_animation(self):
        if self.dice_animation and self.dice_animation in self.elements:
            self.elements.remove(self.dice_animation)
        self.dice_animation = DiceRollAnimation(position=(10, 10), duration_ms=800)
        self.elements.append(self.dice_animation)
        self.roll_animation_active = True

    def _end_dice_animation(self):
        if self.dice_animation and self.dice_animation in self.elements:
            self.elements.remove(self.dice_animation)
            self.dice_animation = None
        self.roll_animation_active = False

    def _update_action_buttons(self):
        for button in self.action_buttons:
            button.visible = self.combat.is_player_turn
            button.enabled = self.combat.is_player_turn
    # fallback to previous button grid position if the new one causes issues with rendering off-screen
    # def _button_grid_position(self, index, screen):
    #     return grid_position(index, 24, screen.get_height() - 50, 300, 50, 4, 20, 8)

    def _button_grid_position(self, index, screen):
        # Anchor start_y higher (screen.get_height() - 140) so 2nd row items render on-screen
        return grid_position(index, 24, screen.get_height() - 140, 300, 50, 4, 20, 8)

    def _set_selected_skill(self, _, skill: Skill):
        self.selected_skill = skill

    def _set_selected_item(self, _, item: Usable):
        self.selected_item = item

    def _player_attack(self):
        if getattr(self.game, "physical_dice_enabled", False):
            self.pending_physical_action = {"type": "attack"}
            self.physical_roll_active = True
            self.physical_d20_input.focus = True
            self.physical_d20_input.text_str = ""
            self.physical_d20_input.cursor = 0
            self.physical_d20_input.anchor = 0
            self.physical_roll_error.change_text("")
            pygame.key.start_text_input()
            return

        self._start_dice_animation()
        passed, result, damage = self.game.player.attack(self.target)
        self._resolve_attack_result(passed, result, damage)

    def _submit_physical_attack_roll(self):
        txt = self.physical_d20_input.text_str.strip()
        if not txt.isdigit():
            self.physical_roll_error.change_text("Please enter a valid number (1-20)!")
            return
        val = int(txt)
        if val < 1 or val > 20:
            self.physical_roll_error.change_text("Roll must be between 1 and 20!")
            return

        self.physical_roll_active = False
        self.physical_roll_error.change_text("")
        pygame.key.stop_text_input()

        action = getattr(self, "pending_physical_action", None) or {"type": "attack"}
        self.pending_physical_action = None

        self._start_dice_animation()

        if action.get("type") == "skill":
            skill = action.get("skill")
            if skill:
                skill.execute(self.combat.game.player, self.target, self.combat, raw_d20=val)
                self.combat.game.player.mana -= skill.cost
                if skill.skip_turn:
                    self.combat.end_player_turn()
        else:
            passed, result, damage = self.game.player.attack(self.target, raw_d20=val)
            self._resolve_attack_result(passed, result, damage)

    def _resolve_attack_result(self, passed, result, damage):
        self.combat.print_text(f"You rolled {result} {'(success!)' if passed else '(miss!)'}")
        if passed and damage > 0:
            self.combat.delayed_action(
                text=f"You deal {damage} damage to {self.target.name}",
                action=lambda: self.target.apply_damage(self.target, damage, self.game.player.get_damage_type(), self.combat),
            )
        self.combat.end_player_turn()

    def _use_skill_button(self):
        if self.use_item:
            self.use_item = False
            self.selected_item = None
            self.rg_item_select.visible = False
            self.rg_item_select.enabled = False

        self.use_skill = not self.use_skill

        if self.selected_skill is not None:
            if not self.combat.game.player.mana >= self.selected_skill.cost:
                self._change_log_text("Not enough mana")
                return

            if getattr(self.game, "physical_dice_enabled", False):
                self.pending_physical_action = {"type": "skill", "skill": self.selected_skill}
                self.physical_roll_active = True
                self.physical_d20_input.focus = True
                self.physical_d20_input.text_str = ""
                self.physical_d20_input.cursor = 0
                self.physical_d20_input.anchor = 0
                self.physical_roll_error.change_text("")
                pygame.key.start_text_input()

                self.rg_skill_select.visible = False
                self.rg_skill_select.enabled = False
                self.use_skill = False
                self.selected_skill = None
                return

            self.selected_skill.execute(self.combat.game.player, self.target, self.combat)
            self.combat.game.player.mana -= self.selected_skill.cost
            if self.selected_skill.skip_turn:
                self.combat.end_player_turn()

            self.rg_skill_select.visible = False
            self.rg_skill_select.enabled = False
            self.use_skill = False
            self.selected_skill = None

        self.rg_skill_select.visible = self.use_skill
        self.rg_skill_select.enabled = self.use_skill

    def _use_item_button(self):
        if self.use_skill:
            self.use_skill = False
            self.selected_skill = None
            self.rg_skill_select.visible = False
            self.rg_skill_select.enabled = False

        self.use_item = not self.use_item

        if self.selected_item is not None:
            self.selected_item.on_use(self.combat.game.player, self.selected_item.get_targets(self.combat.game.player, self.target, self.combat.enemies))
            if self.selected_item.skip_turn:
                self.combat.end_player_turn()

        self.rg_item_select.visible = self.use_item
        self.rg_item_select.enabled = self.use_item

        self.selected_item = None

    def _update_target(self):
        if self.target is not None and self.target.dead and len(self.combat.get_alives_enemies()) > 0:
            self.target = self.combat.get_alives_enemies()[0]
        for eimg in self.enemies_imgs:
            eimg.targeted = self.target == eimg.entity
            eimg.enabled = not eimg.entity.dead