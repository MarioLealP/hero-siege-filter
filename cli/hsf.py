#!/usr/bin/env python3
"""hsf — Hero Siege loot-filter CLI.

    uv run cli/hsf.py list                       # catalog + which builds resolve
    uv run cli/hsf.py check                      # validate every research file
    uv run cli/hsf.py explain <build_id>         # show the highlight/hide reasoning
    uv run cli/hsf.py build <build_id> [--install]  # write build/<id>.txt (+ game dir)
    uv run cli/hsf.py read <path-to-lootfilter>  # decode a v2 or v3 filter file
"""
from __future__ import annotations

import pathlib
import sys

from hsfilter import compile_build, explain, profile_to_code
from hsfilter.catalog import known_build_ids, load_build, load_catalog, validate_all

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME_DIRS = [pathlib.Path.home() / ".config/Hero_Siege/hs2saves",
             pathlib.Path.home() / ".config/HeroSiege/hs2saves"]


def cmd_list():
    cat = load_catalog()
    have = known_build_ids()
    print(f"{cat.game_version}\n")
    for cls in cat.classes:
        print(f"{cls.name}  ({' / '.join(cls.trees)})")
        for b in cls.viable_builds:
            for st in b.stages:
                bid = f"{cls.name.lower().replace(' ', '_')}_{b.build}_{st}"
                mark = "ok " if bid in have else "-- "
                print(f"  [{mark}] {bid}")


def cmd_check():
    errs = validate_all()
    for k, v in errs.items():
        print(f"FAIL {k}: {v}")
    if not errs:
        print(f"ok — {len(known_build_ids())} build files valid")
    sys.exit(1 if errs else 0)


def cmd_explain(bid: str):
    print(explain(compile_build(load_build(bid))))


def cmd_build(bid: str, install: bool):
    prof = compile_build(load_build(bid))
    code = profile_to_code(prof)
    out = ROOT / "build" / f"{bid}.txt"
    out.parent.mkdir(exist_ok=True)
    out.write_text(code)
    print(f"{explain(prof).splitlines()[1]}\nwrote {out.relative_to(ROOT)}  ({len(code)} chars)")
    if install:
        for d in GAME_DIRS:
            if d.is_dir():
                (d / f"lootfilter_{bid}.txt").write_text(code)
                print(f"installed -> {d}/lootfilter_{bid}.txt")


def cmd_read(path: str):
    import json
    from hsfilter import Filter, NAME
    txt = pathlib.Path(path).read_text().strip()
    raw = __import__("base64").b64decode(txt)
    if raw[:1] == b"\x03":
        d = Filter.read_v3(txt)
        print(f"v3: {d['slots'] and len(d['slots'])} slots")
        for sid, s in d["slots"].items():
            hl = [e[0] for e in s["entries"] if e[2] == 2]
            hd = [e[0] for e in s["entries"] if e[2] == 1]
            print(f"  slot {sid}: {len(hl)} highlight, {len(hd)} hide")
    else:
        f = Filter.load_v2(txt)
        j = json.loads(raw)
        for slot, block in j.items():
            if slot in ("version", "wtc"):
                continue
            cell = next(iter(block.values())) if isinstance(block, dict) else {}
            hl = cell.get("hls", [])
            print(f"  {slot}: {len(cell.get('hs', []))} hs / {len(hl)} hls  "
                  f"e.g. {[NAME.get(int(i), i) for i in hl[:4]]}")


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    match a:
        case ["list"]:
            cmd_list()
        case ["check"]:
            cmd_check()
        case ["explain", bid]:
            cmd_explain(bid)
        case ["build", bid]:
            cmd_build(bid, install=False)
        case ["build", bid, "--install"]:
            cmd_build(bid, install=True)
        case ["read", path]:
            cmd_read(path)
        case _:
            sys.exit(__doc__)


if __name__ == "__main__":
    main()
