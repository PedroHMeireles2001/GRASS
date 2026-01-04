from enum import Enum

from src.model.attribs import CharacterAttrib


class CharacterRace(str, Enum):
    HUMAN = "Human"
    ELF = "Elf"
    DWARF = "Dwarf"

def sum_atrib(atual_atrib,race):
    for atrib in CharacterAttrib:
        bonus = SKILLS_BONUS.get(race,{}).get(atrib,0)
        atual_atrib[atrib] = atual_atrib.get(atrib,0) + bonus
    return atual_atrib

SKILLS_BONUS = {
    CharacterRace.HUMAN: {
        CharacterAttrib.STRENGTH: 1,
        CharacterAttrib.DEXTERITY: 1,
        CharacterAttrib.CONSTITUTION: 1,
        CharacterAttrib.INTELLIGENCE: 1,
        CharacterAttrib.WISDOM: 1,
        CharacterAttrib.CHARISMA: 1
    },
    CharacterRace.ELF: {
        CharacterAttrib.STRENGTH: -1,
        CharacterAttrib.DEXTERITY: 2,
        CharacterAttrib.CONSTITUTION: -1,
        CharacterAttrib.INTELLIGENCE: 1,
        CharacterAttrib.WISDOM: 1,
        CharacterAttrib.CHARISMA: 2
    },
    CharacterRace.DWARF: {
        CharacterAttrib.STRENGTH: 1,
        CharacterAttrib.CONSTITUTION: 2,
        CharacterAttrib.WISDOM: 1,
    }
}