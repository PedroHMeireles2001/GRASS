import random
from typing import List, TYPE_CHECKING, Optional

from src.constants import START_SKILLS
from src.engine.scene.ChatScene import ChatScene
from src.engine.scene.Scene import Scene
from src.engine.scene.SceneElement import SceneElement
from src.engine.ui.Button import Button
from src.engine.ui.ImageTransformStrategy import ColorInverter
from src.engine.ui.RadioButton import RadioButtonGroup
from src.engine.ui.SimpleText import SimpleText
from src.engine.ui.TextInput import TextInput
from src.model.attribs import CharacterAttrib, CharacterExpertise
from src.model.classes import CharacterClass
from src.model.player import Player
from src.model.race import CharacterRace
from src.model.skills import SkillEnum, SKILL_FACTORY
from src.utils import get_center_x, get_default_font, grid_position

if TYPE_CHECKING:
    from src.engine.Game import Game

class CharacterCreator(Scene):
    def __init__(self,background,screen, game:"Game"):
        self.selected_race = None
        self.selected_class = None
        self.rolled_atribs = self._roll_attribs()
        self.selected_attribs = {}
        self.avaliable_skills:List[SkillEnum] = []
        self.skill_len = START_SKILLS if len(self.avaliable_skills) >= START_SKILLS else len(self.avaliable_skills)
        self.skills_radio_button: RadioButtonGroup = RadioButtonGroup(label_str=f"Select {str(self.skill_len)} skill(s)",multiselect=self.skill_len,position=(240,90),options=[],on_change=self._set_selected_skills)
        self.selected_skills = []
        self.selected_expertises = []
        self.error: Optional[SimpleText] = None
        self.selected_name = self._gerar_nome(random.randint(6,8),bool(random.randint(0,1)))
        self.re_rolls = 3

        self.attrib_radio_button = self._build_scene_attribs(screen)
        self.reroll_button = Button(
            image=None,
            position=(24,24),
            background_color=(255,255,255),
            text=SimpleText(text="Reroll (3)",text_color=(0,0,0),position=(0,0),size=24),
            hover_transform_strategy=ColorInverter(),
            click_function=self._reroll
        )
        super().__init__(background, screen, game)

    def _reroll(self):
        if self.re_rolls <= 0:
            return
        self.re_rolls -= 1
        self.rolled_atribs = self._roll_attribs()
        self.reroll_button.text.change_text(f"Reroll ({self.re_rolls})")
        self.reroll_button.update_image()
        for i,radio_button_group in enumerate(self.attrib_radio_button):
            value = self.rolled_atribs[i]
            radio_button_group.set_text(str(value))
            radio_button_group.on_change = lambda p,x, val=value: self._set_selected_attribs(p,x, val)


    def _play(self):
        if not self._validate():
            return
        player = Player(self.selected_name,self.selected_class,self.selected_race,self.selected_attribs,self.selected_skills,self.selected_expertises)
        self.game.player = player
        self.game.change_scene(ChatScene(self.screen,self.game,self.game.scenario))


    def _validate(self) -> bool:
        if not self.selected_race:
            self._update_error("Select a race")
            return False
        if not self.selected_class:
            self._update_error("Select a class")
            return False
        if not self.selected_skills:
            self._update_error(f"You must select at least {self.skill_len} skill(s)")
            return False
        if len(self.selected_skills) < self.skill_len:
            self._update_error(f"You must select at least {self.skill_len} skill(s)")
            return False
        if len(self.selected_attribs) != len(CharacterAttrib):
            self._update_error("You must select all attributes")
            return False
        if not self.selected_name:
            self._update_error("You must select a name")
            return False
        if self.selected_name.replace(" ","") == "":
            self._update_error("You must select a name")
            return False
        if len(self.selected_expertises) != 4:
            self._update_error("You must select at least 4 expertises")
            return False

        return True

    def _update_error(self,error_txt:str):
        if self.error is None:
            SIZE = 24
            fw, fh = get_default_font(SIZE).size("error_txt")
            self.error = SimpleText(
                text=error_txt,
                position=(get_center_x(self.screen,fw),self.screen.get_height() - fh - 90),
                size=SIZE,
                text_color=(255,0,0)
            )
            self.elements.append(self.error)
        else:
            self.error.change_text(error_txt)

    def _set_selected_skills(self,previous,skills: List[SkillEnum]) -> None:
        self.selected_skills = skills

    def _set_selected_race(self,previous,race:CharacterRace):
        self.selected_race = race

    def _set_selected_class(self,previous,clazz:CharacterClass):
        self.selected_class = clazz
        self.avaliable_skills = [skill for skill in SkillEnum if self.selected_class in SKILL_FACTORY[skill].classes and SKILL_FACTORY[skill].min_level == 1]
        self.skill_len = START_SKILLS if len(self.avaliable_skills) >= START_SKILLS else len(self.avaliable_skills)
        self.skills_radio_button.set_options([(skill.name,skill) for skill in [SKILL_FACTORY[skillenum] for skillenum in self.avaliable_skills]])
        self.skills_radio_button.multiselect = self.skill_len
        self.skills_radio_button.set_text(f"Select {str(self.skill_len)} skill(s)")

    def _set_selected_name(self,name):
        self.selected_name = name


    def _set_selected_attribs(self,previous:CharacterAttrib,attrib:CharacterAttrib, value:int):
        if attrib in self.selected_attribs.keys():
            raise AttributeError

        if attrib is not None:
            self.selected_attribs[attrib] = value
        else:
            if previous is not None and previous in self.selected_attribs.keys():
                del self.selected_attribs[previous]

    def build_scene(self, game: "Game") -> List[SceneElement]:

        return [
            SimpleText("Character Creator", 48, (get_center_x(self.screen, get_default_font(48).size("Character Creator")[0]), 0)),
            RadioButtonGroup(label_str="Select Race",position=(12,90),on_change=self._set_selected_race,options=[(race.value,race) for race in CharacterRace]),
            RadioButtonGroup(label_str="Select Class",position=(12,self.screen.get_height()//2),on_change=self._set_selected_class,options=[(clazz.value,clazz) for clazz in CharacterClass]),
            RadioButtonGroup(
                label_str="Select 4 Expertises",
                position=(220,(self.screen.get_height()//2)),
                options=[(expertise.value, expertise) for expertise in CharacterExpertise],
                multiselect=4,
                on_change=self._change_expertise
            ),
            Button(
                image=None,
                text=SimpleText(text="Create!",size=24,position=(0,0),text_color=(0,0,0)),
                hover_transform_strategy=ColorInverter(),
                background_color=(255,255,255),
                click_function=self._play,
                position=(get_center_x(self.screen, get_default_font(24).size("Create!")[0]), self.screen.get_height() - get_default_font(24).size("Create!")[1] - 10),
            ),
            TextInput(
                initial_text=self.selected_name,
                label_str="Name:",
                position=(get_center_x(self.screen,10),50),
                width=220,
                on_change=self._set_selected_name,
                label_top=False
            )
        ] + [self.skills_radio_button,self.reroll_button] + self.attrib_radio_button


    def _change_expertise(self,previous,actual):
        self.selected_expertises = actual

    def _build_scene_attribs(self,screen):
        item_width = 200
        item_height = 300
        h_spacing = 4
        v_spacing = 8

        start_x = (
                self.skills_radio_button.position[0]
                + self.skills_radio_button.rect.width
                + 250
        )
        start_y = self.skills_radio_button.position[1]

        available_width = screen.get_width() - start_x
        columns = max(1, available_width // (item_width + h_spacing))

        return [
            RadioButtonGroup(
                label_str=str(value),
                position=grid_position(
                    index=index,
                    start_x=start_x,
                    start_y=start_y,
                    item_width=item_width,
                    item_height=item_height,
                    columns=columns,
                    h_spacing=h_spacing,
                    v_spacing=v_spacing
                ),
                options=[(attrib.value, attrib) for attrib in CharacterAttrib],
                on_change=lambda p,x, val=value: self._set_selected_attribs(p,x, val)
            )
            for index, value in enumerate(self.rolled_atribs)
        ]

    def _roll_attribs(self):
        rolls = []
        for i in range(6):
            dices = [random.randint(1, 6) for _ in range(4)]
            dices = sorted(dices, reverse=True)
            dices = dices[0:3]
            rolls.append(sum(dices))
        return rolls




    def _gerar_nome(self,tamanho: int = 6, iniciar_com_consoante: bool = True) -> str:
        vogais = "aeiou"
        consoantes = "bcdfghjklmnpqrstvwxyz"

        nome = []
        usar_consoante = iniciar_com_consoante

        for _ in range(tamanho):
            if usar_consoante:
                nome.append(random.choice(consoantes))
            else:
                nome.append(random.choice(vogais))
            usar_consoante = not usar_consoante

        return "".join(nome).capitalize()
