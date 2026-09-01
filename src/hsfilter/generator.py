"""Profile -> importable Hero Siege v3 filter code.

v3 is what the game both saves and loads. It carries the two axes the filter UI
exposes: an item-rarity grid (7-byte tiermask per slot) and per-affix grade
states (visible / off / beam). v2 could only ever touch the second one, so we
emit v3 directly -- see hsfilter.codec for the byte layout.
"""
from __future__ import annotations

from .codec import (GRADE_STATE_BEAM, GRADE_STATE_OFF, GRADE_STATE_VISIBLE,
                    RUNEWORD_SLOTS, SLOTS, encode_v3, rarity_grid, socket_field)
from .data import ALL_IDS
from .models import Profile

# Slot-aware chase -- an affix beams only on its "home" slots; elsewhere it stays
# visible (item still drops, no beam), never hidden.
#
# HS is permissive: the loot filter exposes all 167 affixes on every slot, and
# affixes span item types. The game's affix-pool data lives in a YYC-compiled
# item generator we could not crack, so we only slot-lock the handful of stats
# that are unambiguously slot-specific in every ARPG.
_BOOTS, _WEAPON, _CHARM = "t2", "t3", "t10"
SLOT_BEAM: dict[int, set[str]] = {
    25: {_BOOTS, _CHARM},   # Movement Speed
    26: {_BOOTS, _CHARM},   # Phasing
    465: {_BOOTS, _CHARM},  # Movement Speed Converted to Damage
    67: {_WEAPON},          # Attack Range
}


def _chase_states(show_min: int, beam_min: int, beams_here: bool) -> list[int]:
    """5 grade states (D..S) for a chase affix on one slot.

    Below `show_min` the roll is turned off outright (the tiermask already zeroes
    those grade columns; this makes it explicit so it can't leak if the game
    treats an affix state as an override). At/above `beam_min` it beams on its
    home slots, otherwise it stays visible.
    """
    out = []
    for g in range(5):
        if g < show_min:
            out.append(GRADE_STATE_OFF)
        elif beams_here and g >= beam_min:
            out.append(GRADE_STATE_BEAM)
        else:
            out.append(GRADE_STATE_VISIBLE)
    return out


def _validate(p: Profile) -> tuple[list[int], list[int]]:
    hi = sorted(set(p.highlight))
    hd = sorted(set(p.hide))
    bad = (set(hi) | set(hd)) - ALL_IDS
    if bad:
        raise ValueError(f"unknown stat ids: {sorted(bad)}")
    if set(hi) & set(hd):
        raise ValueError(f"stat in both lists: {sorted(set(hi) & set(hd))}")
    return hi, hd


def profile_to_slots(p: Profile) -> dict[str, dict]:
    """Build the per-slot spec that codec.encode_v3 consumes."""
    hi, hd = _validate(p)
    show_min = max(0, min(4, p.grade_show_min))
    beam_min = max(show_min, min(4, p.grade_beam_min))
    grid = rarity_grid(p.item_rarity_min, show_min)
    off_all = [GRADE_STATE_OFF] * 5

    # runeword-hunt pass: on the craftable slots, force Common visible again and
    # beam bases with the wanted socket count. Purely additive — the show mask
    # stays "all" so nothing the main filter wants is hidden.
    rw_counts = {n for n in (p.socket_counts or [2, 3, 4, 5, 6]) if 2 <= n <= 6}
    rw_grid = [col | 0x01 for col in grid]
    rw_socket = socket_field(show=None, beam=rw_counts)

    slots: dict[str, dict] = {}
    for key in SLOTS:
        affixes: dict[int, list[int]] = {}
        for i in hd:
            affixes[i] = list(off_all)
        for i in hi:
            beams_here = i not in SLOT_BEAM or key in SLOT_BEAM[i]
            st = _chase_states(show_min, beam_min, beams_here)
            if any(v != GRADE_STATE_VISIBLE for v in st):
                affixes[i] = st
        rw_here = p.runeword_bases and key in RUNEWORD_SLOTS
        slots[key] = {
            "rarity_grid": list(rw_grid if rw_here else grid),
            "affixes": affixes,
            "socket_field": rw_socket if rw_here else None,
        }
    return slots


def profile_to_code(p: Profile) -> str:
    return encode_v3(profile_to_slots(p), wtc=int(p.wtc or 0))


# kept for callers/tests that still import it -- now returns the v3 slot spec
def profile_to_filter(p: Profile) -> dict[str, dict]:
    return profile_to_slots(p)
