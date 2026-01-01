import random
from typing import List, Dict, TYPE_CHECKING

from src.model.attribs import CharacterAttrib
from src.model.classes import CharacterClass, get_initial_life
from src.constants import START_SKILLS
from src.model.entity import Entity
from src.model.skills import Skill, SKILL_FACTORY, SkillEnum

if TYPE_CHECKING:
    from src.model.race import CharacterRace, sum_atrib


class Player(Entity):
    def __init__(self, name: str, clazz: CharacterClass, race: "CharacterRace", attributes: Dict[CharacterAttrib, int],
                 skills: List[Skill]):
        super().__init__(None, name, get_initial_life(clazz, attributes[CharacterAttrib.CONSTITUTION]), 0,
                         attributes[CharacterAttrib.DEXTERITY], 10)
        self.name = name
        self.gold = 0
        self.xp = 0
        self.max_mana = 10
        self.mana = self.max_mana
        self.clazz = clazz
        self.race = race
        self.attributes = attributes
        self.skills = skills

    def give_xp(self, xp):
        self.xp += xp
        #TODO: level

    def rest(self):
        self.health = self.max_health
        self.mana = self.max_mana

    def get_damage(self) -> float:
        return 5

    def take_turn(self, combat):
        for effect in self.effects:
            effect.duration -= 1
            if effect.duration <= 0:
                self.effects.remove(effect)

        combat.player_turn = True

    def take_gold(self,gold_loss):
        self.gold = max(0,self.gold - gold_loss)


    def to_markdown(self) -> str:
        lines = []

        # Header
        lines.append(f"# 🧙 Player Character: {self.name}")
        lines.append("")

        # Character Info
        lines.append("## 🧾 Character Info")
        lines.append(f"- **Class:** {self.clazz.name.title()} (lvl 1)")
        lines.append(f"- **Race:** {self.race.name.title()}")

        lines.append("## 🧾 Character Status")
        lines.append(f"- **Life:** ({self.health}/{self.max_health})")
        lines.append(f"- **Armor:** {self.armor}")
        lines.append(f"- **Dodge:** {self.dodge}")
        lines.append(f"- **Gold:** {self.gold}")

        # Attributes
        lines.append("## 🧬 Attributes")

        if not self.attributes:
            lines.append("_No attributes defined._")
        else:
            for attr in CharacterAttrib:
                if attr in self.attributes:
                    value = self.attributes[attr]
                    lines.append(f"- **{attr.name.title()}:** {value}")

        lines.append("")

        # Skills
        lines.append("## ⚔️ Skills")

        for skill in self.skills:

            if skill:
                lines.append(f"### {skill.name}")
                lines.append(f"- **Required Level:** {skill.min_level}")
                lines.append(
                    f"- **Available to Classes:** "
                    f"{', '.join(c.name.title() for c in skill.classes)}"
                )
                lines.append(f"- **Description:** {skill.description}")

        return "\n".join(lines)
