"""Hero Siege loot-filter codec.

v2  (what we WRITE): one line of base64 -> UTF-8 JSON.
    { "version": 2,
      "wtc": <int>,                       # weapon-type bitfield (filter-wide), optional
      "<slot>": {                         # slot key t0..t18
          "soc": <int>,                   # socket-count bitfield, optional
          "<rarity>": { "hs": [id,...],   # dimmed / hidden stat lines
                        "hls": [id,...] } # highlighted stat lines
      } }
    Ints may be serialised with a trailing .0 by the game; we normalise.
    The game auto-converts v2 -> v3 on load, so writing v2 is safe and simplest.

v3  (what the game SAVES and reads): base64( u8 ver=3 | u32 zlib_len | zlib(body) ).
    body: ffff | u16 ver=3 | u32 wtc | u8 slot_count
          then per slot: u8 slotid | u16 sockets | 7x u8 tiermask
                         | u16 entry_count | entry[ u16 affix, u16 packed ] ...
    sockets      : low byte = socket counts to SHOW, high byte = counts to BEAM;
                   bit i (0..5) = (i+1) sockets. 0x003f = "1..6 shown, none
                   beamed" = no socket filtering (the neutral default). Confirmed
                   in-game 2026-09-01: helmet "show only 4-socket" -> 0x0008,
                   "show + beam 4-socket" -> 0x0808. Lets you surface runeword
                   bases (a white base needs sockets == the recipe's rune count).
    Two independent axes:
      tiermask[g]  (g = affix-grade column D,C,B,A,S) : a 5-bit ITEM-RARITY mask,
                   bit0 Common .. bit4 Satanic; 1 = that (grade, rarity) cell can
                   drop. bytes 5-6 spare (0x1f). Zero a whole column to kill that
                   grade; clear one bit in every column to kill that rarity.
      packed       : 5 x 2-bit AFFIX-GRADE states, LE (D bits 0-1 .. S bits 8-9);
                   0 = visible (red), 1 = off (hidden), 2 = beam (yellow glow).
                   An entry is written only when it differs from all-visible.
    An item drops iff at least one of its affix-tiers ends up visible or beamed.
    We both WRITE v3 (encode_v3) and READ it back (Filter.read_v3, for diffing).

Legacy note: the game still loads a v2 base64-JSON blob and upgrades it, but v2
cannot express the item-rarity axis, so we emit v3 directly now.
"""
from __future__ import annotations
import base64
import json
import struct
import zlib
from dataclasses import dataclass, field

SLOTS = {
    "t0": "Helmet", "t1": "Chest", "t2": "Boots", "t3": "Weapon", "t4": "Gloves",
    "t5": "Amulet", "t6": "Shield", "t7": "Ring", "t8": "Belt", "t10": "Charm",
    "t11": "Consumable", "t12": "Key", "t13": "Collectible", "t14": "Material",
    "t15": "Socketable", "t18": "Vial",
}
SLOT_ID = {k: int(k[1:]) for k in SLOTS}          # "t3" -> 3
# tr0..tr4 = the item's grade (D..S). Confirmed in-game 2026-08-31:
RARITIES = {"tr0": "D", "tr1": "C", "tr2": "B", "tr3": "A", "tr4": "S"}
RARITY_NAME = {"tr0": "Common", "tr1": "Superior", "tr2": "Rare",
               "tr3": "Mythic", "tr4": "Satanic"}
WEAPON_TYPES = [
    "Item", "Sword", "Dagger", "Mace", "Axe", "Claw", "Polearm", "Chainsaw",
    "Staff", "Cane", "Wand", "Book", "Spellblade", "Bow", "Gun", "Flask",
    "Throwing", "Novelty",
]


def _ints(xs):
    return [int(round(float(x))) for x in xs]


# ---- v3 writer -----------------------------------------------------------
# The filter the game actually reads. Two axes:
#   rarity_grid[slot] : 5 bytes, one per affix-grade column D..S; each a 5-bit
#                       item-rarity mask (bit0 Common .. bit4 Satanic). 1 = the
#                       (grade, rarity) cell is visible on the ground.
#   affixes[slot][id] : 5 ints, one per grade D..S; 0 visible / 1 hidden / 2 beam.
# An item drops only if >=1 of its affix-tiers ends up visible or beamed.

GRADE_STATE_VISIBLE = 0
GRADE_STATE_OFF = 1
GRADE_STATE_BEAM = 2

SOCKETS_ANY = 0x3F  # low byte 1..6 all shown, high byte 0 -> no socket filtering
# slots a runeword can be crafted in (a white base + sockets == rune count);
# gloves / amulet / ring / belt / charm never take a runeword.
RUNEWORD_SLOTS = ("t0", "t1", "t2", "t3", "t6")  # Helmet Chest Boots Weapon Shield


def socket_field(show: set[int] | None = None, beam: set[int] | None = None) -> int:
    """The per-slot u16: low byte = socket counts (1..6) to show, high byte =
    counts to beam. `show=None` -> 0x3f (all shown, no filtering)."""
    def mask(counts: set[int] | None, default: int) -> int:
        if counts is None:
            return default
        return sum(1 << (n - 1) for n in counts if 1 <= n <= 6) & 0x3F
    return mask(show, 0x3F) | (mask(beam, 0) << 8)


def rarity_grid(item_rarity_min: int = 0, grade_show_min: int = 0) -> list[int]:
    """The 5 affix-grade columns (D..S) of a slot's tiermask.

    Each column is a 5-bit item-rarity mask (bit0 Common .. bit4 Satanic):
      - rarities below `item_rarity_min` are cleared (item never drops), and
      - a whole grade column below `grade_show_min` is zeroed (rolls of that
        grade are suppressed regardless of item rarity).
    """
    rar = 0x1F & ~((1 << max(0, item_rarity_min)) - 1)
    return [0 if g < grade_show_min else rar for g in range(5)]


def encode_v3(
    slots: dict[str, dict],
    wtc: int = 0,
) -> str:
    """slots: {slot_key: {"rarity_grid": [5 ints], "affixes": {id: [5 ints]},
                          "socket_field": u16 | None}}"""
    body = bytearray(b"\xff\xff")
    body += struct.pack("<H", 3)
    body += struct.pack("<I", wtc)
    keys = [k for k in SLOTS if k in slots]
    body += struct.pack("<B", len(keys))
    for k in keys:
        s = slots[k]
        body += struct.pack("<B", SLOT_ID[k])
        sf = s.get("socket_field")
        body += struct.pack("<H", SOCKETS_ANY if sf is None else int(sf) & 0xFFFF)
        grid = s.get("rarity_grid") or [0x1F] * 5
        body += bytes(grid[:5]) + b"\x1f\x1f"
        ents = []
        for aid, states in sorted(s.get("affixes", {}).items()):
            if any(v != 0 for v in states):
                packed = sum((v & 3) << (2 * g) for g, v in enumerate(states[:5]))
                ents.append((aid, packed))
        body += struct.pack("<H", len(ents))
        for aid, packed in ents:
            body += struct.pack("<HH", aid, packed)
    blob = zlib.compress(bytes(body), 9)
    return base64.b64encode(bytes([3]) + struct.pack("<I", len(blob)) + blob).decode()


@dataclass
class Cell:
    hide: list[int] = field(default_factory=list)
    highlight: list[int] = field(default_factory=list)


@dataclass
class Filter:
    version: int = 2
    wtc: int | None = None
    cells: dict[str, dict[str, Cell]] = field(default_factory=dict)   # cells[slot][rarity]
    soc: dict[str, int] = field(default_factory=dict)
    _extra_slot: dict[str, dict] = field(default_factory=dict)
    _extra_root: dict = field(default_factory=dict)

    # ---- v2 (base64 JSON) --------------------------------------------------
    @classmethod
    def load_v2(cls, text: str) -> "Filter":
        raw = json.loads(base64.b64decode(text.strip()))
        f = cls(version=int(raw.get("version", 2)))
        for k, v in raw.items():
            if k == "version":
                continue
            if k == "wtc":
                f.wtc = int(v)
            elif k in SLOTS and isinstance(v, dict):
                for sk, sv in v.items():
                    if sk == "soc":
                        f.soc[k] = int(sv)
                    elif sk in RARITIES and isinstance(sv, dict):
                        f.cells.setdefault(k, {})[sk] = Cell(
                            hide=_ints(sv.get("hs", [])),
                            highlight=_ints(sv.get("hls", [])),
                        )
                    else:
                        f._extra_slot.setdefault(k, {})[sk] = sv
            else:
                f._extra_root[k] = v
        return f

    def to_json(self) -> dict:
        out: dict = {"version": 2, **self._extra_root}
        if self.wtc is not None:
            out["wtc"] = self.wtc
        for slot in SLOTS:
            block: dict = {}
            if slot in self.soc:
                block["soc"] = self.soc[slot]
            for rk, cell in self.cells.get(slot, {}).items():
                inner = {}
                if cell.hide:
                    inner["hs"] = sorted(set(cell.hide))
                if cell.highlight:
                    inner["hls"] = sorted(set(cell.highlight))
                if inner:
                    block[rk] = inner
            block.update(self._extra_slot.get(slot, {}))
            if block:
                out[slot] = block
        return out

    def dump_v2(self) -> str:
        j = json.dumps(self.to_json(), separators=(",", ":"))
        return base64.b64encode(j.encode()).decode()

    # ---- v3 (read only) --------------------------------------------------
    # container : base64( u8 ver=3 | u32 zlib_len | zlib(body) )
    # body      : ffff | u16 ver | u32 wtc | u8 slotcount
    #             then per slot: u8 slotid | u16 sockets | 7x u8 tiermask
    #                            | u16 entcount | entries[ u16 affix, u16 packed ]
    #   sockets : low byte = socket counts shown, high byte = counts beamed;
    #             bit i = (i+1) sockets. 0x003f = no socket filtering.
    #   tiermask[g] (g = affix-grade column D..S) : 5-bit item-rarity mask,
    #               bit0 Common .. bit4 Satanic; 1 = that (grade,rarity) cell drops.
    #               bytes 5-6 are spare (always 0x1f).
    #   packed : 5 x 2-bit affix-grade states, LE (D at bits 0-1 .. S at 8-9);
    #            0 = visible (red), 1 = off (hidden), 2 = beam (yellow).
    @staticmethod
    def read_v3(text: str) -> dict:
        d = base64.b64decode(text.strip())
        assert d[0] == 3, f"not v3 (version byte {d[0]})"
        body = zlib.decompress(d[5:])
        assert body[:2] == b"\xff\xff", "bad v3 magic"
        ver = struct.unpack_from("<H", body, 2)[0]
        wtc = struct.unpack_from("<I", body, 4)[0]
        nslots = body[8]
        off = 9
        slots: dict[int, dict] = {}
        for _ in range(nslots):
            slotid = body[off]
            off += 1
            pre = struct.unpack_from("<H", body, off)[0]
            off += 2
            sock_show = [n + 1 for n in range(6) if (pre & 0xFF) & (1 << n)]
            sock_beam = [n + 1 for n in range(6) if (pre >> 8) & (1 << n)]
            tiermask = body[off:off + 7]
            off += 7
            ecount = struct.unpack_from("<H", body, off)[0]
            off += 2
            entries = []
            for _ in range(ecount):
                affix, packed = struct.unpack_from("<HH", body, off)
                off += 4
                states = [(packed >> (2 * g)) & 3 for g in range(5)]
                entries.append((affix, packed, states))
            slots[slotid] = {"pre": pre,
                             "sockets_shown": sock_show,
                             "sockets_beamed": sock_beam,
                             "tiermask": tiermask.hex(),
                             "grid": [tiermask[g] for g in range(5)],
                             "entries": entries}
        return {"version": ver, "wtc": wtc, "slots": slots,
                "consumed": off, "total": len(body)}
