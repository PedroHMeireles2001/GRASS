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

# Usage Examples:
# print(Expertise.SLEIGHT_OF_HAND.value) -> "Sleight of Hand"
# print(Expertise.STEALTH.get_associated_ability()) -> "Dexterity"