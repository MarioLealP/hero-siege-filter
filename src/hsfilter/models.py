"""Pydantic models — the research schema (see docs/gemini-research-spec.md) and
the API request/response shapes. Everything the app accepts is validated here."""
from __future__ import annotations
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Element(str, Enum):
    physical = "physical"
    fire = "fire"
    cold = "cold"
    lightning = "lightning"
    arcane = "arcane"
    poison = "poison"
    elemental = "elemental"
    converted = "converted"


class Delivery(str, Enum):
    attack = "attack"
    melee = "melee"
    cast = "cast"
    cooldown = "cooldown"
    projectile = "projectile"
    orbital = "orbital"
    explosion = "explosion"
    summon = "summon"
    sentry = "sentry"
    dot = "dot"
    aoe = "aoe"


class Attribute(str, Enum):
    strength = "strength"
    dexterity = "dexterity"
    intelligence = "intelligence"
    energy = "energy"
    armor = "armor"
    vitality = "vitality"


Stage = Literal[
    "leveling", "maps", "endgame",                       # legacy
    "normal", "nightmare", "hell1", "hell3", "hell5",     # difficulty brackets
]
CritScaling = Literal["yes", "no", "optional"]
DefenseModel = Literal["life", "shield_block", "dodge", "hybrid"]

# canonical vocab — scaling_stats / defense_priority tokens are checked loosely
# (element prefixes allowed) so a new element concept doesn't hard-fail the app.
_SCALING_BASE = {
    "all_skills", "singular_skills", "sub_skills", "explosion_skills",
    "summon_skills", "sentry_skills", "magic_skill_damage",
    "flat_elemental_skill_damage", "primary_attribute", "all_attributes",
    "faster_cast_rate", "skill_haste", "mana_cost_reduced", "attack_speed",
    "attack_rating", "weapon_flat_phys", "weapon_pct_phys", "crit_chance",
    "crit_damage", "ignore_all_resist", "explosion_damage", "explosion_aoe",
    "projectile_speed", "summon_block", "sentry_block", "ailment_damage",
    "ailment_frequency", "extra_damage_vs_ailment", "movespeed_damage",
    "additive_element",
}
_DEFENSE_BASE = {
    "life_flat", "life_pct", "life_per_level", "vitality", "life_on_kill",
    "life_regen", "all_resist", "max_all_resist", "phys_dmg_reduction",
    "all_dmg_reduction", "damage_reduced", "faster_hit_recovery", "anti_freeze",
    "block", "dodge",
}
_SUFFIXED = ("_skills", "_skill_damage_flat", "_skill_damage_pct", "_resist",
             "ignore_", "additive_", "single_resist_", "max_single_resist_",
             "absorb_")


class Research(BaseModel):
    model_config = {"extra": "forbid"}

    id: str = Field(pattern=r"^[a-z0-9_]+$")
    name: str
    class_: str = Field(alias="class")
    tree: str
    main_skills: list[str] = Field(min_length=1, max_length=3)
    element: Element
    splash_element: Element | None = None
    delivery: list[Delivery] = Field(min_length=1)
    primary_attribute: Attribute
    cooldown_based: bool
    aoe: bool
    crit_scaling: CritScaling
    defense_model: DefenseModel
    uses_shield: bool
    key_conversions: list[str] = []
    required_items: list[str] = []
    scaling_stats: list[str]
    defense_priority: list[str]
    stage: Stage
    stage_notes: dict[str, str] = {}
    sources: list[str] = []
    uncertain: list[str] = []
    wtc: int | None = None   # weapon-type bitfield, optional (archetypes set it late-game)

    @field_validator("scaling_stats", "defense_priority")
    @classmethod
    def _known_tokens(cls, v: list[str]) -> list[str]:
        known = _SCALING_BASE | _DEFENSE_BASE
        for tok in v:
            if tok in known or any(s in tok for s in _SUFFIXED):
                continue
            raise ValueError(f"unknown concept token: {tok!r}")
        return v


class Profile(BaseModel):
    """Compiled output: highlight/hide over the 167 stat ids + two rarity axes.

    Hero Siege's filter has two independent knobs:

    * item rarity (Common / Superior / Rare / Mythic / Satanic) -- what colour
      the item itself is;
    * affix grade (D / C / B / A / S) -- how well each individual stat rolled.

    `item_rarity_min` (0 Common .. 4 Satanic) hides items below that rarity.
    `grade_show_min`  (0 D .. 4 S) suppresses affix rolls below that grade.
    `grade_beam_min`  (0 D .. 4 S) beams (yellow glow) chase affixes at or above
                      that grade; between show and beam they are visible only.
    `hide` affixes are turned off at every grade; `highlight` affixes are the
    chase list that beams.

    `runeword_bases` layers a runeword-hunt pass on top: on the five slots a
    runeword can be crafted in (helmet / chest / boots / weapon / shield) it
    forces Common items visible again and beams anything with `socket_counts`
    sockets (default 2..6) so white runeword bases surface without disturbing
    the rest of the filter.
    """
    id: str
    name: str
    notes: str = ""
    wtc: int | None = None
    soc: int | None = None
    highlight: list[int]
    hide: list[int]
    item_rarity_min: int = 0
    grade_show_min: int = 0
    grade_beam_min: int = 0
    runeword_bases: bool = False
    socket_counts: list[int] = []


# ---- catalog + API shapes ------------------------------------------------

class CatalogBuild(BaseModel):
    build: str
    skill: str
    tree: str
    archetype: str
    stages: list[Stage]


class CatalogClass(BaseModel):
    name: str
    trees: list[str]
    viable_builds: list[CatalogBuild]


class Catalog(BaseModel):
    game_version: str
    retrieved: str
    classes: list[CatalogClass]
    archetypes: list[str]


class FilterRequest(BaseModel):
    """The only thing the UI POSTs. Every field is bounded / enum-checked."""
    model_config = {"extra": "forbid"}
    build_id: str = Field(pattern=r"^[a-z0-9_]+$", max_length=80)
