from collections.abc import Callable
from typing import Tuple, List, Any, Optional, Dict

import pygame

from src.constants import DEBUG
from src.engine.ui.SimpleText import SimpleText
from src.engine.ui.UIElement import UIElement
from src.utils import get_default_font


class RadioButton:
    def __init__(self,position: Tuple[int, int],index: int,value: Any,text:str,color:Tuple[int,int,int] = (255,255,255),radius: int = 6,text_size:int = 12,text_gap:int = 12):
        self.position = position
        self.index = index
        self.value = value
        self.text = text
        self.color = color
        self.radius = radius
        self._text = SimpleText(
            text=text,
            size=text_size,
            position=(position[0]+text_gap,position[1]),
            text_color=color
        )
        self.rect = self._calculate_rect(text_size,text_gap)
        self.selected = False

    def render(self, surface: pygame.Surface):
        pygame.draw.circle(surface, self.color, self._get_sphere_center(), self.radius, width=2)
        self._text.render(surface)
        if self.selected:
            pygame.draw.circle(surface, self.color, self._get_sphere_center(), self.radius - 1, width=0)

    def _get_sphere_center(self) -> Tuple[int, int]:
        return self.position[0], self.position[1]

    def _calculate_rect(self,text_size:int,text_gap:int) -> pygame.Rect:
        font = get_default_font(text_size)

        w, h = font.size(self.text)

        total_width = (
                w +
                self.radius * 2 +
                text_gap  # espaço entre círculo e texto
        )

        return pygame.Rect(
            self.position[0],
            self.position[1],
            total_width,
            h
        )


class RadioButtonGroup(UIElement):
    def __init__(self,position: Tuple[int, int],options: List[Tuple[str,Any]],multiselect: int = 1,gap:int = 24,color: Tuple[int,int,int] = (255,255,255),radius: int = 6,text_size: int = 12,label_str: Optional[str] = None,label_size: int = 12,on_change: Optional[Callable[[Any,Any],None]] = None):
        super().__init__(None,position)
        self.multiselect = multiselect
        self.radio_buttons = []
        self.selected_value = [] if self._is_multiselect() else None
        self.label = SimpleText(
            text=label_str,
            size=label_size,
            text_color=color,
            position=(position[0], position[1]),
        ) if label_str else None
        self.radio_config = {
            "gap": gap,
            "color": color,
            "radius": radius,
            "text_size": text_size,
        }
        self.radio_buttons = self._initialize_radio_buttons(options)
        self.on_change = on_change
        self.rect = self._calculate_rect()


    def set_options(self,options: List[Tuple[str,Any]]) -> None:
        self.clear()
        self.radio_buttons = self._initialize_radio_buttons(options)

    def update(self, event: pygame.event.Event, mouse_position: Tuple[int, int]):
        if not self.enabled:
            return

        if event and event.type == pygame.MOUSEBUTTONDOWN:
            radio_button = self._get_clicked_radio_button(mouse_position)

            if not radio_button:
                return

            # 1. Resolver o valor 'previous' antes de alterar qualquer coisa
            # Se for lista, precisamos de uma cópia rasa (copy) para não alterar a referência
            if isinstance(self.selected_value, list):
                previous = self.selected_value.copy()
            else:
                previous = self.selected_value

            # Lógica para SINGLE SELECT
            if not self._is_multiselect():
                # Em Radio Buttons padrão, clicar no que já está selecionado não faz nada
                if radio_button.selected:
                    radio_button.selected = False
                    self.selected_value = None
                else:
                    self.clear()
                    radio_button.selected = True
                    self.selected_value = radio_button.value

            # Lógica para MULTI SELECT
            else:
                if self.selected_value is None:
                    self.selected_value = []

                # Se já está selecionado, vamos remover (desmarcar)
                if radio_button.selected:
                    radio_button.selected = False
                    if radio_button.value in self.selected_value:
                        self.selected_value.remove(radio_button.value)

                # Se não está selecionado, verificamos o limite ANTES de marcar
                else:
                    if len(self.selected_value) < self.multiselect:
                        radio_button.selected = True
                        self.selected_value.append(radio_button.value)
                    else:
                        return

            # Só chama o callback se houve mudança real
            if previous != self.selected_value:
                self._on_change(previous, radio_button)



    def _on_change(self,previous,radio_button):
        if self.on_change:
            try:
                self.on_change(previous, self.selected_value)
            except Exception as e:
                self.selected_value = previous
                if radio_button:
                    radio_button.selected = False

    def render(self,surface: pygame.Surface):
        if not self.visible:
            return
        if self.label:
            self.label.render(surface)
        for radio_button in self.radio_buttons:
            radio_button.render(surface)

    def clear(self):
        previous = self.selected_value
        self.selected_value = [] if self._is_multiselect() else None
        self._on_change(previous,None)
        for radio_button in self.radio_buttons:
            radio_button.selected = False

    def _get_clicked_radio_button(self,mouse_position: Tuple[int, int]) -> Optional[RadioButton]:
        for radio_button in self.radio_buttons:
            if radio_button.rect.collidepoint(mouse_position):
                return radio_button
        return None

    def _is_multiselect(self) -> bool:
        return self.multiselect > 1

    def _initialize_radio_buttons(self, options: List[Tuple[str,Any]]) -> List[RadioButton]:
        radio_buttons = []
        inital_gap = self.label.rect.size[1] + self.radio_config["gap"] if self.label else 0
        for i,option in enumerate(options):
            radio_buttons.append(RadioButton(
                index=i,
                position=(self.position[0], self.position[1] + i * self.radio_config["gap"] + inital_gap),
                text=option[0],
                text_size=self.radio_config["text_size"],
                value=option[1],
                color=self.radio_config["color"],
                radius=self.radio_config["radius"],
            ))

        return radio_buttons

    def set_text(self, text:str):
        if self.label:
            self.label.change_text(text)

    def _calculate_rect(self) -> pygame.Rect:
        x, y = self.position

        # Altura inicial = label (se existir)
        total_height = 0
        max_width = 0

        if self.label:
            label_rect = self.label.rect
            total_height += label_rect.height

        for radio in self.radio_buttons:
            max_width = max(max_width, radio.rect.width)
            total_height += self.radio_config["gap"] + radio.rect.height

        # Remove o último gap extra
        if self.radio_buttons:
            total_height -= self.radio_config["gap"]

        return pygame.Rect(
            x,
            y,
            max_width,
            total_height
        )



