"""Profile -> importable Hero Siege v2 filter code (base64 JSON).

The game auto-upgrades v2 -> v3 on load, so v2 is what we emit.
"""
from __future__ import annotations

from .codec import SLOTS, Cell, Filter
from .data import ALL_IDS
from .models import Profile


_RANKS = ("tr0", "tr1", "tr2", "tr3", "tr4")  # grade 0..4 (Common..Satanic)

# Slot-aware chase — an affix beams only on its "home" slots; elsewhere it stays
# *visible* (item still drops, no beam), never hidden.
#
# HS turns out to be permissive: the loot filter exposes all 167 affixes on every
# slot, and affixes span item types (Enhanced Defense rolls on Rings *and*
# Amulets, different ranges). The game's affix-pool data is buried in a
# YYC-compiled item generator we couldn't crack. So we only slot-lock the handful
# of stats that are unambiguously slot-specific in every ARPG; everything else
# beams wherever it's a chase stat.
_BOOTS, _WEAPON, _CHARM = "t2", "t3", "t10"
SLOT_BEAM: dict[int, set[str]] = {
    25: {_BOOTS, _CHARM},   # Movement Speed
    26: {_BOOTS, _CHARM},   # Phasing
    465: {_BOOTS, _CHARM},  # Movement Speed Converted to Damage
    67: {_WEAPON},          # Attack Range
}


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
            elif grade >= p.rarity_min_highlight:
                beam = [i for i in hi
                        if i not in SLOT_BEAM or slot in SLOT_BEAM[i]]
                cell = Cell(hide=list(hd), highlight=beam)
            else:
                cell = Cell(hide=list(hd), highlight=[])
            f.cells.setdefault(slot, {})[rk] = cell
    return f


def profile_to_code(p: Profile) -> str:
    return profile_to_filter(p).dump_v2()
