"""The catalog IS the repo. Dropdown data is derived from research/*.json;
research/_classes.json only supplies the archetype list + game version.

No database.
"""
from __future__ import annotations

import functools
import json
import os
import pathlib

from .models import Research

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
RESEARCH_DIR = pathlib.Path(
    os.environ.get("HSFILTER_RESEARCH_DIR", str(_ROOT / "research"))
).resolve()


def _safe_id(build_id: str) -> bool:
    return bool(build_id) and build_id.replace("_", "").isalnum() and not build_id.startswith("_")


@functools.lru_cache(maxsize=512)
def load_build(build_id: str) -> Research:
    if not _safe_id(build_id):
        raise KeyError(build_id)
    path = (RESEARCH_DIR / f"{build_id}.json").resolve()
    if path.parent != RESEARCH_DIR.resolve() or not path.is_file():
        raise KeyError(build_id)
    return Research.model_validate_json(path.read_text())


def known_build_ids() -> set[str]:
    return {p.stem for p in RESEARCH_DIR.glob("*.json") if _safe_id(p.stem)}


@functools.lru_cache(maxsize=1)
def _meta() -> dict:
    p = RESEARCH_DIR / "_classes.json"
    if not p.is_file():
        return {"game_version": "unknown", "archetypes": []}
    d = json.loads(p.read_text())
    return {"game_version": d.get("game_version", "unknown"),
            "archetypes": d.get("archetypes", [])}


def catalog() -> dict:
    """{ game_version, archetypes, classes:[{name,trees,builds:[{build,skill,tree,
    archetype,stages,element}]}], builds:[flat list of {build_id, class, skill, stage,...}] }"""
    by_class: dict[str, dict] = {}
    flat: list[dict] = []
    for bid in sorted(known_build_ids()):
        try:
            r = load_build(bid)
        except Exception:  # noqa: BLE001
            continue
        cls = by_class.setdefault(r.class_, {"name": r.class_, "trees": set(), "builds": {}})
        cls["trees"].add(r.tree)
        # build key = everything except the stage
        stem = bid.rsplit(f"_{r.stage}", 1)[0]
        b = cls["builds"].setdefault(stem, {
            "build": stem.split("_", 1)[1] if "_" in stem else stem,
            "skill": " + ".join(r.main_skills), "tree": r.tree,
            "element": r.element.value, "stages": [],
        })
        b["stages"].append(r.stage)
        flat.append({"build_id": bid, "class": r.class_, "skill": " + ".join(r.main_skills),
                     "tree": r.tree, "element": r.element.value, "stage": r.stage,
                     "name": r.name})
    m = _meta()
    return {
        "game_version": m["game_version"],
        "archetypes": m["archetypes"],
        "classes": [
            {"name": c["name"], "trees": sorted(c["trees"]),
             "builds": sorted(c["builds"].values(), key=lambda x: x["build"])}
            for c in sorted(by_class.values(), key=lambda x: x["name"])
        ],
        "builds": flat,
    }


def validate_all() -> dict[str, str]:
    errs: dict[str, str] = {}
    for bid in sorted(known_build_ids()):
        try:
            r = load_build(bid)
            if r.id != bid:
                errs[bid] = f"id {r.id!r} != filename {bid!r}"
        except Exception as e:  # noqa: BLE001
            errs[bid] = str(e)
    return errs


# back-compat alias
load_catalog = catalog


if __name__ == "__main__":
    errs = validate_all()
    for k, v in errs.items():
        print(f"FAIL {k}: {v}")
    if not errs:
        c = catalog()
        print(f"ok — {len(known_build_ids())} builds, {len(c['classes'])} classes")
    raise SystemExit(1 if errs else 0)
