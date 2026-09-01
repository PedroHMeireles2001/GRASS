import random
from typing import List, Dict, TYPE_CHECKING

from src.model.attribs import CharacterAttrib, CharacterExpertise
from src.model.classes import CharacterClass
from src.model.entity import Entity
from src.model.skills import Skill

from src.model.race import CharacterRace, sum_atrib
from src.utils import get_mod

if TYPE_CHECKING:
    from src.model.Item import GenericItem


class Player(Entity):
    def __init__(self, name: str, clazz: CharacterClass, race: "CharacterRace",attributes: Dict[CharacterAttrib, int],
                 skills: List[Skill],expertises: List[CharacterExpertise]):
        self.race = race
        self.attributes = sum_atrib(attributes, self.race)
        self.name = name
        self.gold = 0
        self.xp = 0
        self.max_mana = clazz.get_initial_mana(attributes[CharacterAttrib.INTELLIGENCE])
        self.proficiency = 2
        self.mana = self.max_mana
        self.clazz = clazz
        self.skills = skills
        self.expertises = expertises
        self.inventory:Dict[int,int] = {}

        super().__init__(image_str=None,
                         attributes=self.attributes,
                         name=name,
                         base_damage=1,
                         type=None,
                         armor=0,
                         dodge=10+get_mod(attributes[CharacterAttrib.DEXTERITY]),
                         health=clazz.get_initial_life(self.attributes[CharacterAttrib.CONSTITUTION]),
                         )

    def give_xp(self, xp):
        self.xp += xp
        #TODO: level


    def give_item(self,item_id:int,qnt:int):
        if item_id in self.inventory.keys():
            self.inventory[item_id] += qnt
        else:
            self.inventory[item_id] = qnt

    def has_item(self,item_id,qnt):
        if not item_id in self.inventory.keys():
            return False
        else:
            return self.inventory[item_id] >= qnt

    def remove_item(self,item_id:int,qnt:int,remove_if_dont_enough=True):
        if item_id not in self.inventory.keys():
            return False

        if self.inventory[item_id] >= qnt:
            self.inventory[item_id] -= qnt
            if self.inventory[item_id] == 0:
                del self.inventory[item_id]
            return True
        else:
            if remove_if_dont_enough:
                del self.inventory[item_id]
            return False

    def sell_trash(self):
        for qnt,trash in [(i,trash) for (i,trash) in self.inventory if trash.useless]:
            del self.inventory[trash]
            self.gold += trash.value * qnt

    def rest(self):
        self.health = self.max_health
        self.mana = self.max_mana





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
        for idx,item in enumerate(self.inventory.keys()):
            lines.append(f"{idx}) {item.name} x{self.inventory[item]}")
        # Skills
        lines.append(f"{"## ⚔️ " if markdown else ""} Skills")

        for idx,skill in enumerate(self.skills):
            if skill:
                lines.append(f"{"###" if markdown else ""} {idx}) {skill.name}")
                lines.append(f"- {"** Description:**" if markdown else " Description:"} {skill.description}")

        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """
        Converts the player object into a JSON-serializable dictionary,
        storing Enum string identifiers for skills, race, class, and attributes.
        """
        # Serialize skills as string enum identifiers (e.g., ["accurate_shot", "reckless_attack"])
        skills_serialized = []
        for s in self.skills:
            if hasattr(s, "enum"):
                enum_val = s.enum.value if hasattr(s.enum, "value") else str(s.enum)
                skills_serialized.append(enum_val)
            elif isinstance(s, str):
                skills_serialized.append(s)
            elif isinstance(s, dict) and "enum" in s:
                skills_serialized.append(s["enum"])

        # Serialize race
        race_val = self.race.value if hasattr(self.race, "value") else str(self.race)

        # Serialize clazz as dict or string
        if hasattr(self.clazz, "name"):
            clazz_val = {"name": self.clazz.name}
        elif isinstance(self.clazz, str):
            clazz_val = {"name": self.clazz}
        else:
            clazz_val = {"name": str(self.clazz)}

        # Serialize expertises
        expertises_serialized = [
            e.value if hasattr(e, "value") else str(e)
            for e in self.expertises
        ]

        # Serialize attributes dictionary with string keys
        attributes_serialized = {}
        for k, v in self.attributes.items():
            key_str = k.value if hasattr(k, "value") else str(k)
            if "." in key_str:
                key_str = key_str.split(".")[-1].lower()
            attributes_serialized[key_str] = v

        # Serialize inventory (item_id -> quantity)
        inventory_serialized = {str(k): v for k, v in self.inventory.items()}

        return {
            "name": self.name,
            "race": race_val,
            "clazz": clazz_val,
            "attributes": attributes_serialized,
            "skills": skills_serialized,
            "expertises": expertises_serialized,
            "inventory": inventory_serialized,
            "health": self.health,
            "max_health": self.max_health,
            "mana": self.mana,
            "max_mana": self.max_mana,
            "gold": self.gold,
            "xp": self.xp,
            "armor": self.armor,
            "dodge": self.dodge,
            "proficiency": self.proficiency
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        """
        Reconstructs a Player instance from a dictionary representation.
        Handles both string Enum identifiers and legacy dictionary objects.
        """
        from src.model.classes import CLASS_FACTORY, CharacterClassEnum
        from src.model.race import CharacterRace
        from src.model.skills import SKILL_FACTORY, SkillEnum
        from src.model.attribs import CharacterAttrib, CharacterExpertise

        name = data.get("name", "Hero")

        # Reconstruct race
        race_raw = data.get("race", "Human")
        if isinstance(race_raw, dict):
            race_raw = race_raw.get("name", "Human")
        try:
            race = CharacterRace(race_raw)
        except ValueError:
            matched = False
            for r in CharacterRace:
                if r.value.lower() == str(race_raw).lower():
                    race = r
                    matched = True
                    break
            if not matched:
                race = CharacterRace.HUMAN

        # Reconstruct clazz
        clazz_raw = data.get("clazz", "warrior")
        if isinstance(clazz_raw, dict):
            clazz_name = clazz_raw.get("name", "warrior").lower()
        else:
            clazz_name = str(clazz_raw).lower()
        
        try:
            clazz_enum = CharacterClassEnum(clazz_name)
            clazz = CLASS_FACTORY[clazz_enum]
        except (ValueError, KeyError):
            clazz = CLASS_FACTORY[CharacterClassEnum.WARRIOR]

        # Reconstruct attributes
        attribs = {}
        raw_attribs = data.get("attributes", {})
        for k, v in raw_attribs.items():
            key_str = k.value if hasattr(k, "value") else str(k)
            if "." in key_str:
                key_str = key_str.split(".")[-1].lower()
            try:
                attribs[CharacterAttrib(key_str)] = int(v)
            except ValueError:
                pass

        # Reconstruct skills
        skills = []
        raw_skills = data.get("skills", [])
        for s in raw_skills:
            skill_key = None
            if isinstance(s, str):
                skill_key = s
            elif isinstance(s, dict):
                skill_key = s.get("enum")
            elif hasattr(s, "enum"):
                skill_key = s.enum.value if hasattr(s.enum, "value") else str(s.enum)

            if skill_key:
                try:
                    s_enum = SkillEnum(skill_key)
                    if s_enum in SKILL_FACTORY:
                        skills.append(SKILL_FACTORY[s_enum])
                except (ValueError, KeyError):
                    print(f"[Warning] Could not deserialize skill '{skill_key}'")

        # Reconstruct expertises
        expertises = []
        raw_expertises = data.get("expertises", [])
        for e in raw_expertises:
            exp_val = e.value if hasattr(e, "value") else str(e)
            try:
                expertises.append(CharacterExpertise(exp_val))
            except ValueError:
                pass

        # Instantiate Player
        player = cls(
            name=name,
            clazz=clazz,
            race=race,
            attributes=attribs.copy(),
            skills=skills,
            expertises=expertises
        )
        if attribs:
            player.attributes = attribs.copy()



        # Restore stats & inventory
        if "health" in data:
            player.health = data["health"]
        if "max_health" in data:
            player.max_health = data["max_health"]
        if "mana" in data:
            player.mana = data["mana"]
        if "max_mana" in data:
            player.max_mana = data["max_mana"]
        if "gold" in data:
            player.gold = data["gold"]
        if "xp" in data:
            player.xp = data["xp"]
        if "armor" in data:
            player.armor = data["armor"]
        if "dodge" in data:
            player.dodge = data["dodge"]
        if "proficiency" in data:
            player.proficiency = data["proficiency"]

        raw_inventory = data.get("inventory", {})
        player.inventory = {int(k): int(v) for k, v in raw_inventory.items()}

        return player

