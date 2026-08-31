"""Generic archetype builds — flavor (element) x playstyle x stage, with no
specific skill. Synthesises a Research the compiler can consume, so all
element x playstyle x stage combinations work without an authored file.

Use for off-meta / "weird shenanigan" builds where you know the shape but not a
canonical skill.
"""
from __future__ import annotations

from typing import Any

from .models import Research

ELEMENTS = ["physical", "fire", "cold", "lightning", "arcane", "poison"]
PLAYSTYLES = ["melee", "ranged", "caster", "summon", "sentry"]
# damage attributes the user can pick (Amazon lightning-melee scales Int, etc.)
ATTRIBUTES = ["strength", "dexterity", "intelligence"]
ATTRIBUTE_LABEL = {"strength": "Strength", "dexterity": "Dexterity",
                   "intelligence": "Intelligence"}
# difficulty brackets, mirroring the game's own loot-filter presets
STAGES = ["normal", "nightmare", "hell1", "hell3", "hell5"]
STAGE_LABEL = {
    "normal": "Normal · lv 1–70 · grab everything",
    "nightmare": "Nightmare · lv 70–100 · chase Rare+",
    "hell1": "Hell 1–3 · just hit 100 · beam Mythic+",
    "hell3": "Hell 3–5 · Incarnation · beam Satanic",
    "hell5": "Hell 5+ · speedfarm · Satanic only, weapons filtered",
}

PLAYSTYLE_LABEL = {
    "melee": "Melee", "ranged": "Ranged / attack", "caster": "Caster",
    "summon": "Summoner", "sentry": "Sentry / totem",
}

# weapon-type bit positions (0=Item .. 17=Novelty), confirmed from the game
_WEP = {"item": 0, "sword": 1, "dagger": 2, "mace": 3, "axe": 4, "claw": 5,
        "polearm": 6, "chainsaw": 7, "staff": 8, "cane": 9, "wand": 10,
        "book": 11, "spellblade": 12, "bow": 13, "gun": 14, "flask": 15,
        "throwing": 16, "novelty": 17}
_WEAPON_SET = {
    "melee": ["item", "sword", "dagger", "mace", "axe", "claw", "polearm",
              "chainsaw", "spellblade"],
    "ranged": ["item", "bow", "gun", "flask", "throwing"],
    "caster": ["item", "staff", "cane", "wand", "book", "spellblade"],
    "summon": ["item", "staff", "cane", "wand", "book"],
    "sentry": ["item", "staff", "cane", "wand", "book"],
}

# named quick-select groups for the UI (bit positions)
WEAPON_GROUPS: dict[str, list[int]] = {
    "all": list(range(18)),
    "none": [],
    "melee": sorted(_WEP[w] for w in _WEAPON_SET["melee"]),
    "ranged": sorted(_WEP[w] for w in _WEAPON_SET["ranged"]),
    "caster": sorted(_WEP[w] for w in _WEAPON_SET["caster"]),
}


def _wtc(playstyle: str) -> int:
    return sum(1 << _WEP[w] for w in _WEAPON_SET[playstyle])


_SHAPE: dict[str, dict[str, Any]] = {
    "melee": dict(delivery=["attack", "melee"], attr_phys="strength",
                  crit="optional", defense="hybrid", cd=False),
    "ranged": dict(delivery=["attack", "projectile"], attr_phys="dexterity",
                   crit="yes", defense="hybrid", cd=False),
    "caster": dict(delivery=["cast", "aoe"], attr_phys="intelligence",
                   crit="no", defense="life", cd=False),
    "summon": dict(delivery=["summon"], attr_phys="intelligence",
                   crit="no", defense="life", cd=False),
    "sentry": dict(delivery=["sentry"], attr_phys="intelligence",
                   crit="no", defense="life", cd=False),
}


def recommended_attribute(element: str, playstyle: str) -> str:
    """The default damage attribute for a shape, before the user overrides it."""
    s = _SHAPE[playstyle]
    if element == "physical" or playstyle in ("melee", "ranged"):
        return s["attr_phys"]
    return "intelligence"


def archetype_research(element: str, playstyle: str, stage: str,
                       attribute: str | None = None,
                       explosion: bool = False) -> Research:
    if element not in ELEMENTS:
        raise ValueError(element)
    if playstyle not in PLAYSTYLES:
        raise ValueError(playstyle)
    if stage not in STAGES:
        raise ValueError(stage)
    if attribute is not None and attribute not in ATTRIBUTES:
        raise ValueError(f"attribute {attribute!r}")
    s = _SHAPE[playstyle]

    # attribute: the user's pick wins; otherwise fall back to the shape default
    # (physical / weapon playstyles -> str/dex, spell playstyles -> int).
    attr = attribute or recommended_attribute(element, playstyle)

    caster_like = playstyle in ("caster", "summon", "sentry")
    scaling = ["all_skills", f"{element}_skills"]
    if caster_like:
        scaling += [f"{element}_skill_damage_pct", f"{element}_skill_damage_flat",
                    "magic_skill_damage", "flat_elemental_skill_damage",
                    "faster_cast_rate", "mana_cost_reduced"]
    else:
        scaling += ["attack_speed", "attack_rating",
                    "weapon_flat_phys", "weapon_pct_phys", "additive_element"]
        if s["crit"] in ("yes", "optional"):
            scaling += ["crit_chance", "crit_damage"]
    if playstyle == "summon":
        scaling = ["summon_skills", "summon_block", "all_skills", "sub_skills",
                   "primary_attribute", "all_attributes"]
    if playstyle == "sentry":
        scaling = ["sentry_skills", "sentry_block", "all_skills", "sub_skills",
                   "primary_attribute", "all_attributes"]
    scaling += ["primary_attribute", "all_attributes",
                f"ignore_{element}_resist", "ignore_all_resist"]

    delivery = list(s["delivery"])
    if explosion:
        delivery.append("explosion")
        scaling += ["explosion_skills", "explosion_damage", "explosion_aoe"]

    attr_suffix = "" if attribute is None else f" ({ATTRIBUTE_LABEL[attr][:3]})"
    return Research.model_validate({
        "wtc": _wtc(playstyle) if stage == "hell5" else None,
        "id": f"generic_{element}_{playstyle}_{stage}",
        "name": (f"{element.capitalize()} {PLAYSTYLE_LABEL[playstyle]}{attr_suffix}"
                 f"{' + explosion' if explosion else ''} — {stage.capitalize()}"),
        "class": "Generic",
        "tree": "—",
        "main_skills": [f"{element} {playstyle}"],
        "element": element,
        "splash_element": None,
        "delivery": delivery,
        "primary_attribute": attr,
        "cooldown_based": s["cd"],
        "aoe": True,
        "crit_scaling": s["crit"] if not caster_like else "no",
        "defense_model": s["defense"],
        "uses_shield": playstyle == "melee",
        "key_conversions": [],
        "required_items": [],
        "scaling_stats": list(dict.fromkeys(scaling)),
        "defense_priority": [
            "life_flat", "life_pct", "all_resist",
            *(["faster_hit_recovery"] if caster_like else ["phys_dmg_reduction", "all_dmg_reduction"]),
            "life_on_kill", "anti_freeze",
        ],
        "stage": stage,
        "stage_notes": {
            "leveling": "Generic archetype — verify against your actual skill once you know it.",
            "maps": "Cap resists, start capping single-element weaknesses.",
            "endgame": "Push Ignore Resistance / Defense to 100% for your flavour.",
        },
        "sources": ["synthesised archetype — not a researched build"],
        "uncertain": ["No specific skill; delivery/attribute are archetype defaults."],
    })
