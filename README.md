# hero-siege-filter

Reverse-engineered Hero Siege loot-filter format + a build-aware filter generator
and (WIP) editor. Season 10 / game build 2024.14.1.

## Filter format

Hero Siege stores filters at `~/.config/Hero_Siege/hs2saves/lootfilter_<name>.txt`
(also mirrored under `~/.config/HeroSiege/hs2saves/`).

- **v2** — one line of `base64( UTF-8 JSON )`. What older filters and hand-made
  imports use. We **write** v2; the game auto-upgrades it to v3 on load.
- **v3** — `base64( u8 ver=3 | u32 zlib_len | zlib(binary) )`. What the game
  **saves**. We only read it (to diff what the game wrote back). Layout in
  `tools/hsfilter.py`.

v2 JSON shape:

```jsonc
{ "version": 2,
  "wtc": 262015,                 // weapon-type bitfield (filter-wide), optional
  "t3": {                        // slot: t0..t18  (see hsfilter.SLOTS)
    "soc": 59,                   // socket-count bitfield, optional
    "tr4": { "hs": [68, 74],     // dimmed stat lines  (stat ids)
             "hls": [223, 137] } // highlighted stat lines
  } }
```

Slots `t0..t18`; rarities `tr0..tr4` = tiers **D C B A S**.

## Stat id map

`data/stats.json` — all **167** filterable stat ids -> name, recovered from
`GetLootFilterAffix` in the game binary and verified in-game (14 independent
anchors, all matched). The in-game stat list is 4 columns; within a column it is
sorted by id.

## The pipeline

```
 "I want <class> using <skill> at <stage>"
        │
 docs/gemini-research-spec.md   ──►  Gemini does the lookup, fills the schema
        │
 research/<id>.json             ──  one validated build (element, delivery,
        │                            ranked scaling_stats + defense_priority …)
        │                            research/_classes.json = archetype list only
        ▼
 hsfilter.compile_build()       ──  docs/filter-mapping.md + stat_taxonomy.json
        │                            + the generic baseline  →  Profile
        ▼
 hsfilter.profile_to_code()     ──  v2 base64 code (game upgrades it to v3)
        ▼
 build/<id>.txt                 ──  drop as lootfilter_<name>.txt, import in-game
```

The dropdown catalog is **derived from `research/*.json`** at runtime — adding a
build is just dropping in one reviewed file.

## Layout

```
src/hsfilter/        core library (importable): codec, compiler, generator,
                     models (pydantic), catalog, bundled data/
cli/hsf.py           list | check | explain <id> | build <id> [--install] | read <file>
app/backend/         FastAPI: GET /api/catalog, POST /api/filter, /api/health
app/frontend/        Endfield SPA (WIP)
research/            the catalog — one <id>.json per build + _classes.json
docs/                gemini-research-spec.md, hero-siege-scaling.md, filter-mapping.md
```

CLI:

```
uv run cli/hsf.py check                                  # validate every research file
uv run cli/hsf.py explain pirate_anchor_swing_leveling   # highlight/hide + reasoning
uv run cli/hsf.py build   pirate_anchor_swing_leveling --install
```

## Docs

- `docs/hero-siege-scaling.md` — how skills scale (element × delivery ×
  attribute), the caster/attacker/summoner priority orders, defence layers,
  progression-stage differences, slot notes. Shared model for the research step.
- `docs/gemini-research-spec.md` — the self-contained prompt for the research pass +
  the strict output schema.
- `docs/filter-mapping.md` — the deterministic rules `compile_build.py` runs,
  including the build-agnostic baseline (e.g. Phasing, All Skills, All Res).
- `data/stat_taxonomy.json` — every stat tagged with category / element /
  delivery / role.

## Reverse-engineering notes

- Game is YYC-compiled GameMaker — no GML bytecode. Logic lives in the native
  `Hero_Siege` ELF; `gml_Script_*` symbol strings survive, so `rizin` +
  `objdump` on the 224 MB `.text` is navigable.
- `helmetall.txt` (in-game "highlight all" on one slot) = the authoritative set
  of 167 filterable ids.
