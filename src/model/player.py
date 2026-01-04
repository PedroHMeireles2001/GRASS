import random
from typing import List, Dict, TYPE_CHECKING

from src.model.attribs import CharacterAttrib, CharacterExpertise
from src.model.classes import CharacterClass, get_initial_life
from src.model.entity import Entity
from src.model.skills import Skill

from src.model.race import CharacterRace, sum_atrib
from src.utils import get_mod

if TYPE_CHECKING:
    from src.model.Item import GenericItem


class Player(Entity):
    def __init__(self, name: str, clazz: CharacterClass, race: "CharacterRace", attributes: Dict[CharacterAttrib, int],
                 skills: List[Skill],expertises: List[CharacterExpertise]):
        self.name = name
        self.gold = 0
        self.xp = 0
        self.max_mana = 10
        self.proficiency = 2
        self.mana = self.max_mana
        self.clazz = clazz
        self.race = race
        self.skills = skills
        self.attributes = sum_atrib(attributes,self.race)
        self.expertises = expertises
        self.inventory:Dict["GenericItem",int] = {}
        super().__init__(None, name, get_initial_life(clazz, attributes[CharacterAttrib.CONSTITUTION]), 0,
                         10 + get_mod(attributes[CharacterAttrib.DEXTERITY]), 4)

    def give_xp(self, xp):
        self.xp += xp
        #TODO: level


    def give_item(self,item:"GenericItem",qnt:int):
        if item in self.inventory.keys():
            self.inventory[item] += qnt
        else:
            self.inventory[item] = qnt

    def remove_item(self,item:"GenericItem",qnt:int,remove_if_dont_enough=True):
        if item not in self.inventory.keys():
            return False

        if self.inventory[item] >= qnt:
            self.inventory[item] -= qnt
            if self.inventory[item] == 0:
                del self.inventory[item]
            return True
        else:
            if remove_if_dont_enough:
                del self.inventory[item]
            return False

    def sell_trash(self):
        for qnt,trash in [(i,trash) for (i,trash) in self.inventory if trash.useless]:
            del self.inventory[trash]
            self.gold += trash.value * qnt

    def rest(self):
        self.health = self.max_health
        self.mana = self.max_mana

    def get_attack_mod(self):
        return get_mod(self.attributes[CharacterAttrib.DEXTERITY])

    def get_damage(self) -> float:
        return self.base_damage + get_mod(self.attributes[CharacterAttrib.STRENGTH])

    def take_turn_impl(self, combat,skip):
        combat.player_turn = True
        if skip:
            combat.end_player_turn()

    def take_gold(self,gold_loss):
        self.gold = max(0,self.gold - gold_loss)


    def to_text(self, markdown=True) -> str:
        lines = []

        # Header
        lines.append(f"{"# 🧙" if markdown else ""} Player Character: {self.name}")
        lines.append("")

        # Character Info
        lines.append(f"{"## 🧾" if markdown else ""} Character Info")
        lines.append(f"- {"**Class:**" if markdown else "Class:"} {self.clazz.name.title()} (lvl 1)")
        lines.append(f"- {"**Race:**" if markdown else "Race:"}{self.race.name.title()}")

        lines.append(f"{"## 🧾" if markdown else ""} Character Status")
        lines.append(f"- {"**Life:**" if markdown else "Life:"} ({self.health}/{self.max_health})")
        lines.append(f"- {"**Armor:**" if markdown else "Armor:"} {self.armor}")
        lines.append(f"- {"**Dodge:**" if markdown else "Dodge:"} {self.dodge}")
        lines.append(f"- {"**Gold:**" if markdown else "GOld:"} {self.gold}")

        # Attributes
        lines.append(f"{"## 🧬" if markdown else ""} Attributes")

        if not self.attributes:
            lines.append("_No attributes defined._")
        else:
            for attr in CharacterAttrib:
                if attr in self.attributes:
                    value = self.attributes[attr]
                    lines.append(f"- {f"**{attr.name.title()}:**" if markdown else f"{attr.name.title()}:"} {value} ({get_mod(value)})")

        lines.append("")

        lines.append(f"{"## " if markdown else ""} Items")
        for item in self.inventory.keys():
            lines.append(f"- {item.name} x{self.inventory[item]}")
        # Skills
        lines.append(f"{"## ⚔️ " if markdown else ""} Skills")

        for skill in self.skills:

            if skill:
                lines.append(f"{"###" if markdown else ""} {skill.name}")
                lines.append(f"- {"** Description:**" if markdown else " Description:"} {skill.description}")

        return "\n".join(lines)
