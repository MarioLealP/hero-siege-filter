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

v3  (what the game SAVES): base64( u8 version=3 | u32 decompressed_len | zlib(body) ).
    body: ffff | u32 ver | u16 flag | u16 slot_count
          then per slot: u16 rarity_mask | 7x u8 tier_state | u16 entry_count
                         | entry[ u16 id, u8 rarity, u8 state ] ...
          slots after the first are prefixed by a u8 slot id.
    state: 2 = highlight, 1 = hide/dim, 0 = neutral (observed).
    We only READ v3 (to diff what the game wrote back).
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
    #             then per slot: u8 slotid | u16 pre(0x3f) | 7x u8 tiermask
    #                            | u16 entcount | entries[ u16 affix, u8 rar, u8 state ]
    #   state: 2 = highlight (yellow), 1 = visible (red), 0 = hidden
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
            tiermask = body[off:off + 7]
            off += 7
            ecount = struct.unpack_from("<H", body, off)[0]
            off += 2
            entries = []
            for _ in range(ecount):
                affix, rar, st = struct.unpack_from("<HBB", body, off)
                off += 4
                entries.append((affix, rar, st))
            slots[slotid] = {"pre": pre, "tiermask": tiermask.hex(),
                             "entries": entries}
        return {"version": ver, "wtc": wtc, "slots": slots,
                "consumed": off, "total": len(body)}
