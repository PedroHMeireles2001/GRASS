import random
from enum import Enum


class CharacterAttrib(str,Enum):
    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    CONSTITUTION = "constitution"
    INTELLIGENCE = "intelligence"
    WISDOM = "wisdom"
    CHARISMA = "charisma"

from enum import Enum

class CharacterExpertise(str, Enum):
    ACROBATICS = "Acrobatics"
    ANIMAL_HANDLING = "Animal Handling"
    ARCANA = "Arcana"
    ATHLETICS = "Athletics"
    DECEPTION = "Deception"
    HISTORY = "History"
    INSIGHT = "Insight"
    INTIMIDATION = "Intimidation"
    INVESTIGATION = "Investigation"
    MEDICINE = "Medicine"
    NATURE = "Nature"
    PERCEPTION = "Perception"
    PERFORMANCE = "Performance"
    PERSUASION = "Persuasion"
    RELIGION = "Religion"
    SLEIGHT_OF_HAND = "Sleight of Hand"
    STEALTH = "Stealth"
    SURVIVAL = "Survival"

    @classmethod
    def list_all(cls):
        """Returns a list of all skill names."""
        return [skill.value for skill in cls]

    def get_associated_ability(self):
        """Returns the default ability score for the skill."""
        # Simple mapping for convenience
        mapping = {
            "Athletics": CharacterAttrib.STRENGTH,
            "Acrobatics": CharacterAttrib.DEXTERITY,
            "Sleight of Hand": CharacterAttrib.DEXTERITY,
            "Stealth": CharacterAttrib.DEXTERITY,
            "Arcana": CharacterAttrib.INTELLIGENCE,
            "History": CharacterAttrib.INTELLIGENCE,
            "Investigation": CharacterAttrib.INTELLIGENCE,
            "Nature": CharacterAttrib.INTELLIGENCE,
            "Religion": CharacterAttrib.INTELLIGENCE,
            "Animal Handling": CharacterAttrib.WISDOM,
            "Insight": CharacterAttrib.WISDOM,
            "Medicine": CharacterAttrib.WISDOM,
            "Perception": CharacterAttrib.WISDOM,
            "Survival": CharacterAttrib.WISDOM,
            "Deception": CharacterAttrib.CHARISMA,
            "Intimidation": CharacterAttrib.STRENGTH,
            "Performance": CharacterAttrib.CHARISMA,
            "Persuasion": CharacterAttrib.CHARISMA
        }
        return mapping.get(self.value, "None")


def roll_attribs(attribs=6):
    rolls = []
    for i in range(attribs):
        dices = [random.randint(1, 6) for _ in range(4)]
        dices = sorted(dices, reverse=True)
        dices = dices[0:3]
        rolls.append(sum(dices))
    return rolls

def random_attribs():
    roll = roll_attribs()
    return {
            CharacterAttrib.STRENGTH: roll[0],
            CharacterAttrib.DEXTERITY: roll[1],
            CharacterAttrib.CONSTITUTION: roll[2],
            CharacterAttrib.INTELLIGENCE: roll[3],
            CharacterAttrib.WISDOM: roll[4],
            CharacterAttrib.CHARISMA: roll[5],
    }

def fill_missing_attribs(initial_dict):
    attribs = initial_dict
    random_attribs_dict = random_attribs()
    for attrib in CharacterAttrib:
        if not attrib in initial_dict.keys():
            attribs[attrib] = random_attribs_dict[attrib]
    return attribs