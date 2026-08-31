"""hsfilter-api — stateless, read-only.

Endpoints:
  GET  /api/health
  GET  /api/catalog          dropdown data + list of build ids that resolve
  POST /api/filter           { "build_id": "<id>" } -> the .txt as a download

No database, no writes, no auth code (Authentik forward-auth sits in front).
Every input is an enum / bounded string validated by Pydantic and then checked
against the on-disk catalog.
"""
from __future__ import annotations

import pathlib

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from hsfilter import (ELEMENTS, PLAYSTYLE_LABEL, PLAYSTYLES, STAGE_LABEL, STAGES, WEAPON_GROUPS,
                      FilterRequest, archetype_research, compile_build, explain,
                      profile_to_code)
from hsfilter.catalog import catalog as build_catalog
from hsfilter.catalog import known_build_ids, load_build, validate_all

app = FastAPI(title="Hero Siege loot filter", version="0.1.0", docs_url="/api/docs")

STATIC_DIR = pathlib.Path(__file__).parent / "static"


@app.get("/api/health")
def health() -> dict:
    errs = validate_all()
    return {"ok": not errs, "builds": len(known_build_ids()), "errors": errs}


@app.get("/api/catalog")
def catalog() -> dict:
    c = build_catalog()
    c["archetype_options"] = {
        "elements": ELEMENTS,
        "playstyles": [{"id": p, "label": PLAYSTYLE_LABEL[p]} for p in PLAYSTYLES],
        "stages": [{"id": s, "label": STAGE_LABEL[s]} for s in STAGES],
        "weapon_groups": WEAPON_GROUPS,
    }
    return c


_RARITY = ["Common", "Superior", "Rare", "Mythic", "Satanic"]   # item rarity
_GRADE = ["D", "C", "B", "A", "S"]                              # affix roll grade


class Overrides(BaseModel):
    """Optional per-request tweaks applied on top of the compiled archetype."""
    model_config = {"extra": "forbid"}
    element: str
    playstyle: str
    stage: str
    item_rarity_min: int | None = Field(None, ge=0, le=4)   # hide items below this rarity
    grade_show_min: int | None = Field(None, ge=0, le=4)    # suppress affix rolls below this grade
    grade_beam_min: int | None = Field(None, ge=0, le=4)    # beam chase affixes at/above this grade
    weapons: list[int] | None = None          # weapon-type bit positions, or [] / null
    force_highlight: list[int] = []
    force_hide: list[int] = []
    force_neutral: list[int] = []


def _archetype_profile(element: str, playstyle: str, stage: str,
                       ov: Overrides | None = None):
    from hsfilter import ALL_IDS
    try:
        p = compile_build(archetype_research(element, playstyle, stage))
    except ValueError as e:
        raise HTTPException(422, f"bad archetype: {e}")
    if ov is None:
        return p
    if ov.item_rarity_min is not None:
        p.item_rarity_min = ov.item_rarity_min
    if ov.grade_show_min is not None:
        p.grade_show_min = ov.grade_show_min
    if ov.grade_beam_min is not None:
        p.grade_beam_min = max(ov.grade_beam_min, p.grade_show_min)
    else:
        p.grade_beam_min = max(p.grade_beam_min, p.grade_show_min)
    if ov.weapons is not None:
        bad = [b for b in ov.weapons if not 0 <= b <= 17]
        if bad:
            raise HTTPException(422, f"bad weapon bits: {bad}")
        p.wtc = sum(1 << b for b in ov.weapons) or None
    hi, hd = set(p.highlight), set(p.hide)
    for i in ov.force_neutral:
        hi.discard(i)
        hd.discard(i)
    for i in ov.force_highlight:
        if i in ALL_IDS:
            hi.add(i)
            hd.discard(i)
    for i in ov.force_hide:
        if i in ALL_IDS:
            hd.add(i)
            hi.discard(i)
    p.highlight, p.hide = sorted(hi), sorted(hd)
    return p


def _explain_payload(p) -> dict:
    from hsfilter import NAME, STATS
    why = p.__dict__.get("_why", {})
    hi, hd = set(p.highlight), set(p.hide)
    state = {i: ("highlight" if i in hi else "dim" if i in hd else "neutral") for i in NAME}
    wtc = p.wtc or 0
    from hsfilter import WEAPON_TYPES
    return {
        "id": p.id, "name": p.name, "notes": p.notes,
        "grades": _GRADE,
        "rarities": _RARITY,
        "weapon_types": WEAPON_TYPES,
        "rarity": {
            "item_min": p.item_rarity_min,
            "item_from": _RARITY[p.item_rarity_min],
            "item_suppressed": _RARITY[: p.item_rarity_min],
            "grade_show_min": p.grade_show_min,
            "grade_beam_min": p.grade_beam_min,
            "show_from": _GRADE[p.grade_show_min],
            "beam_from": _GRADE[p.grade_beam_min],
            "grade_suppressed": _GRADE[: p.grade_show_min],
        },
        "weapon_bits": [i for i in range(18) if wtc >> i & 1],
        "weapons": [WEAPON_TYPES[i] for i in range(18) if wtc >> i & 1] or None,
        "highlight": [{"id": i, "name": NAME[i], "why": why.get(i)} for i in p.highlight],
        "hide": [{"id": i, "name": NAME[i], "why": why.get(i)} for i in p.hide],
        "stats": [
            {"id": i, "name": NAME[i], "col": STATS[str(i)]["col"],
             "state": state[i], "why": why.get(i)}
            for i in sorted(NAME, key=lambda x: (STATS[str(x)]["col"], NAME[x]))
        ],
    }


@app.get("/api/archetype/{element}/{playstyle}/{stage}/explain")
def archetype_explain(element: str, playstyle: str, stage: str) -> dict:
    return _explain_payload(_archetype_profile(element, playstyle, stage))


@app.get("/api/archetype/{element}/{playstyle}/{stage}/filter", response_class=PlainTextResponse)
def archetype_filter(element: str, playstyle: str, stage: str):
    p = _archetype_profile(element, playstyle, stage)
    return PlainTextResponse(profile_to_code(p), headers={
        "Content-Disposition": f'attachment; filename="lootfilter_{p.id}.txt"',
    })


@app.post("/api/archetype/explain")
def archetype_explain_custom(ov: Overrides) -> dict:
    return _explain_payload(_archetype_profile(ov.element, ov.playstyle, ov.stage, ov))


@app.post("/api/archetype/filter", response_class=PlainTextResponse)
def archetype_filter_custom(ov: Overrides):
    p = _archetype_profile(ov.element, ov.playstyle, ov.stage, ov)
    return PlainTextResponse(profile_to_code(p), headers={
        "Content-Disposition": f'attachment; filename="lootfilter_{p.id}_custom.txt"',
    })


@app.post("/api/filter", response_class=PlainTextResponse)
def make_filter(req: FilterRequest):
    if req.build_id not in known_build_ids():
        raise HTTPException(404, f"unknown build: {req.build_id}")
    try:
        research = load_build(req.build_id)
        profile = compile_build(research)
        code = profile_to_code(profile)
    except KeyError:
        raise HTTPException(404, f"unknown build: {req.build_id}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"compile failed: {e}")
    return PlainTextResponse(
        code,
        headers={
            "Content-Disposition": f'attachment; filename="lootfilter_{req.build_id}.txt"',
            "X-Filter-Summary": explain(profile).splitlines()[1],
        },
    )


@app.get("/api/filter/{build_id}/explain")
def explain_filter(build_id: str) -> dict:
    if build_id not in known_build_ids():
        raise HTTPException(404, f"unknown build: {build_id}")
    return _explain_payload(compile_build(load_build(build_id)))


if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="spa")
