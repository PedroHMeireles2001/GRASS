import os
from enum import Enum

import pygame

from src.model.entity import Entity
from src.utils import get_assets_path


class EnemyEnum(str,Enum):
    SKELETON = "skeleton"

ENEMY_FACTORY = {
    EnemyEnum.SKELETON: Entity(
        name="Skeleton",
        health=10,
        armor=0,
        dodge=10,
        base_damage=10,
        image=pygame.image.load(os.path.join(get_assets_path(), "entities", "skeleton.png"))
    )
}