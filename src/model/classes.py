from enum import Enum

from src.utils import get_mod


class CharacterClassEnum(str, Enum):
    WARRIOR = "warrior"
    PALADIN = "paladin"
    ROGUE = "rogue"
    MAGE = "mage"
    CLERIC = "cleric"
    #DRUID = "druid"
    BARD = "bard"
    #MONK = "monk"
    BARBARIAN = "barbarian"

class CharacterClass:
    def __init__(self,name,initial_life,initial_mana):
        self.name = name
        self.initial_life = initial_life
        self.initial_mana = initial_mana

    def get_initial_life(self, const) -> int:
        return self.initial_life + (get_mod(const) * 10)

    def get_initial_mana(self,inteligence):
        return self.initial_mana + (get_mod(inteligence) * 10)

CLASS_FACTORY = {
    CharacterClassEnum.WARRIOR : CharacterClass("Warrior",100,100),
    CharacterClassEnum.BARBARIAN: CharacterClass("Barbarian",120,80),
    CharacterClassEnum.PALADIN: CharacterClass("Paladin",80,120),
    CharacterClassEnum.CLERIC: CharacterClass("Cleric",80,120),
    CharacterClassEnum.MAGE: CharacterClass("Mage",60,140),
    CharacterClassEnum.BARD: CharacterClass("Bard",80,120),
    CharacterClassEnum.ROGUE: CharacterClass("Rogue",80,120)
}

