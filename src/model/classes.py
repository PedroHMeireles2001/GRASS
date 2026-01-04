from enum import Enum

from src.utils import get_mod


class CharacterClass(str, Enum):
    WARRIOR = "warrior"
    PALADIN = "paladin"
    ROGUE = "rogue"
    MAGE = "mage"
    CLERIC = "cleric"
    DRUID = "druid"
    BARD = "bard"
    MONK = "monk"
    BARBARIAN = "barbarian"

INITIAL_LIFE = {
    CharacterClass.WARRIOR: 100,
    CharacterClass.PALADIN: 100,
    CharacterClass.ROGUE: 80,
    CharacterClass.MAGE: 60,
    CharacterClass.CLERIC: 80,
    CharacterClass.DRUID: 80,
    CharacterClass.BARD: 80,
    CharacterClass.MONK: 80,
    CharacterClass.BARBARIAN: 120,
}

INITIAL_WEAPON = {

}

def get_initial_life(clazz,const) -> int:
    return INITIAL_LIFE[clazz] + (get_mod(const) * 10)