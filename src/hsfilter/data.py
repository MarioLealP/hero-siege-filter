"""Bundled data: the 167-stat id->name map and the functional taxonomy."""
from __future__ import annotations
import json
import pathlib

_D = pathlib.Path(__file__).parent / "data"

STATS: dict[str, dict] = json.loads((_D / "stats.json").read_text())
TAXONOMY: dict = json.loads((_D / "stat_taxonomy.json").read_text())
RUNEWORDS: dict = json.loads((_D / "runewords.json").read_text())

NAME: dict[int, str] = {int(k): v["name"] for k, v in STATS.items() if k.isdigit()}
ALL_IDS: set[int] = set(NAME)
assert len(ALL_IDS) == 167, f"expected 167 stats, got {len(ALL_IDS)}"

# element -> stat id
E_SKILLS = {"cold": 223, "fire": 225, "lightning": 226, "arcane": 224,
            "poison": 227, "physical": 222}
E_SD_FLAT = {"cold": 137, "fire": 133, "lightning": 145, "arcane": 141, "poison": 149}
E_SD_PCT = {"cold": 138, "fire": 134, "lightning": 146, "arcane": 142, "poison": 150}
E_IGN = {"cold": 139, "fire": 135, "lightning": 147, "arcane": 143, "poison": 151}
E_ADD = {"cold": 136, "fire": 132, "lightning": 144, "arcane": 140, "poison": 148}
E_RES = {"fire": 175, "cold": 177, "lightning": 179, "arcane": 181, "poison": 183}
E_MAXRES = {"fire": 176, "cold": 178, "lightning": 180, "arcane": 182, "poison": 184}
E_ABS = {"fire": 191, "cold": 192, "poison": 193, "lightning": 194, "arcane": 195}
ATTR = {"strength": (33, 34), "dexterity": (36, 37), "energy": (39, 40),
        "intelligence": (42, 43), "armor": (45, 46), "vitality": (48, 49)}
