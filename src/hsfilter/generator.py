"""Profile -> importable Hero Siege v2 filter code (base64 JSON).

The game auto-upgrades v2 -> v3 on load, so v2 is what we emit.
"""
from __future__ import annotations

from .codec import SLOTS, Cell, Filter
from .data import ALL_IDS
from .models import Profile


_RANKS = ("tr0", "tr1", "tr2", "tr3", "tr4")  # grade 0..4 (Common..Satanic)


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
        for grade, rk in enumerate(_RANKS):
            if grade < p.rarity_min_show:
                # whole grade suppressed — every affix hidden, item won't drop
                cell = Cell(hide=sorted(ALL_IDS), highlight=[])
            else:
                cell_hi = list(hi) if grade >= p.rarity_min_highlight else []
                cell = Cell(hide=list(hd), highlight=cell_hi)
            f.cells.setdefault(slot, {})[rk] = cell
    return f


def profile_to_code(p: Profile) -> str:
    return profile_to_filter(p).dump_v2()
