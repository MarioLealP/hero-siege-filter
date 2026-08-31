"""Profile -> importable Hero Siege v2 filter code (base64 JSON).

The game auto-upgrades v2 -> v3 on load, so v2 is what we emit.
"""
from __future__ import annotations

from .codec import SLOTS, Cell, Filter
from .data import ALL_IDS
from .models import Profile


_RANKS = ("tr0", "tr1", "tr2", "tr3", "tr4")  # grade 0..4 (Common..Satanic)

# Slot-aware chase: an affix only gets the beam on its "home" slots; on other
# slots it stays *visible* (item still drops, no beam) — never hidden, so an
# off-slot roll is never missed. ARPG convention; tune per HS as we learn it.
_H, _C, _B, _W, _G, _A, _SH, _R, _BE, _CH = (
    "t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8", "t10")
SLOT_BEAM: dict[int, set[str]] = {
    25: {_B, _CH},                       # Movement Speed -> boots, charm
    26: {_B},                            # Phasing -> boots
    170: {_BE, _B, _SH, _H},             # Faster Hit Recovery
    67: {_W},                            # Attack Range -> weapon
    53: {_C, _SH, _BE},                  # Life % -> chest, shield, belt
    196: {_A, _R, _G, _W, _H},           # Faster Cast Rate
    198: {_A, _R, _BE, _CH},             # Skill Haste
    68: {_G, _W, _R, _A},                # Attack Speed
    72: {_G, _A, _R}, 73: {_G, _A, _R},  # Crit chance / damage
    284: {_H, _R, _A, _CH, _G, _B},      # Magic Find
    285: {_H, _R, _A, _CH, _G, _B},
    **{sid: {_A, _H, _W, _CH} for sid in (201, 202, 419, 222, 223, 224, 225, 226, 227)},  # +skills
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
