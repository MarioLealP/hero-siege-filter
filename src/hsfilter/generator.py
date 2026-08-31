"""Profile -> importable Hero Siege v2 filter code (base64 JSON).

The game auto-upgrades v2 -> v3 on load, so v2 is what we emit.
"""
from __future__ import annotations

from .codec import RARITIES, SLOTS, Cell, Filter
from .data import ALL_IDS
from .models import Profile


def profile_to_filter(p: Profile) -> Filter:
    hi = sorted(set(p.highlight))
    hd = sorted(set(p.hide))
    bad = (set(hi) | set(hd)) - ALL_IDS
    if bad:
        raise ValueError(f"unknown stat ids: {sorted(bad)}")
    if set(hi) & set(hd):
        raise ValueError(f"stat in both lists: {sorted(set(hi) & set(hd))}")

    f = Filter(version=2)
    if p.wtc is not None:
        f.wtc = int(p.wtc)
    for slot in SLOTS:
        if p.soc is not None:
            f.soc[slot] = int(p.soc)
        for rk in RARITIES:
            f.cells.setdefault(slot, {})[rk] = Cell(hide=list(hd), highlight=list(hi))
    return f


def profile_to_code(p: Profile) -> str:
    return profile_to_filter(p).dump_v2()
