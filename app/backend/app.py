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

from hsfilter import (ELEMENTS, PLAYSTYLE_LABEL, PLAYSTYLES, STAGES, FilterRequest,
                      archetype_research, compile_build, explain, profile_to_code)
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
        "stages": STAGES,
    }
    return c


def _archetype_profile(element: str, playstyle: str, stage: str):
    try:
        return compile_build(archetype_research(element, playstyle, stage))
    except ValueError as e:
        raise HTTPException(422, f"bad archetype: {e}")


@app.get("/api/archetype/{element}/{playstyle}/{stage}/explain")
def archetype_explain(element: str, playstyle: str, stage: str) -> dict:
    from hsfilter import NAME
    p = _archetype_profile(element, playstyle, stage)
    why = p.__dict__.get("_why", {})
    return {
        "id": p.id, "name": p.name, "notes": p.notes,
        "highlight": [{"id": i, "name": NAME[i], "why": why.get(i)} for i in p.highlight],
        "hide": [{"id": i, "name": NAME[i], "why": why.get(i)} for i in p.hide],
    }


@app.get("/api/archetype/{element}/{playstyle}/{stage}/filter", response_class=PlainTextResponse)
def archetype_filter(element: str, playstyle: str, stage: str):
    p = _archetype_profile(element, playstyle, stage)
    return PlainTextResponse(profile_to_code(p), headers={
        "Content-Disposition": f'attachment; filename="lootfilter_{p.id}.txt"',
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
    profile = compile_build(load_build(build_id))
    why = profile.__dict__.get("_why", {})
    from hsfilter import NAME
    return {
        "id": profile.id,
        "name": profile.name,
        "notes": profile.notes,
        "highlight": [{"id": i, "name": NAME[i], "why": why.get(i)} for i in profile.highlight],
        "hide": [{"id": i, "name": NAME[i], "why": why.get(i)} for i in profile.hide],
    }


if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="spa")
