# Gemini brief — Hero Siege meta-build facts (NARROW SCOPE)

You research **only the facts that are not in skill tooltips**. Mechanics
(element, what the skill does) are already known from the game files — do **not**
research or restate them.

Game: **Hero Siege, Season 10 "Ebontharn"**, 2026.

## Your inputs

`data/skills.json` in this repo — 720 skills, each `{slug, name, desc_en,
elements, delivery_hint}` straight from the game. This is authoritative for skill
names and elements. Use these exact names.

## Your job, per class

For each class you are given:

1. **The two real skill trees** (NOT "Incarnation" — that is the shared tree
   every class unlocks at level 100; ignore it). Name both trees.
2. **The 1–3 currently-viable builds** per S10 tier lists / build guides. For
   each build:
   - `main_skills` — from `data/skills.json` names.
   - `tree` — which of the two.
   - `primary_attribute` — `strength|dexterity|intelligence|energy|armor|vitality`
     — the stat the build **dumps points into for damage** (not a requirement).
   - `defense_model` — `life` | `armor_cap` | `shield_block` | `dodge` | `hybrid`.
   - `crit_scaling` — `yes` (build stacks Crit Chance + Crit Damage) / `no` /
     `optional`.
   - `cooldown_based` — bool: does the skill's DPS depend on its cooldown
     (→ Skill Haste matters), or is it freely spammable.
   - `uses_shield` — bool.
   - `key_conversions` — exact phrasing of any "X% of A added/converted to B"
     the build leans on, else `[]`.
   - `tier` — `S` / `A` / `B` this season.
   - `stages` — which of `leveling` / `maps` / `endgame` this build is used at.
   - `stage_notes` — one sentence each for leveling / maps / endgame.
   - `required_items` — runewords/uniques that gate it, else `[]`.
3. `sources` — a URL for **every** non-obvious claim. If you cannot find a
   source for a field, put your best guess in the value and add a line to
   `uncertain` naming that field. Never leave `sources` empty.

## Sources

`herosiege.fandom.com/wiki/<Class>`, `graxyguides.com/herosiege/builds/season-10-builds/<class>/`,
`herosiegebuilds.com/builds`, `herosiegewiki.com/builds`, recent YouTube S10 guides,
official patch notes. `hero-siege-helper.vercel.app/data/skills` for skill metadata.

## Output

One file per class: `research/_meta/<class>.json`

```json
{
  "class": "Pirate",
  "trees": ["Gunner", "Plunderer"],
  "retrieved": "2026-08-31",
  "builds": [
    {
      "build": "anchor_swing",
      "main_skills": ["Anchor Swing"],
      "tree": "Plunderer",
      "primary_attribute": "intelligence",
      "defense_model": "life",
      "crit_scaling": "no",
      "cooldown_based": true,
      "uses_shield": false,
      "key_conversions": [],
      "tier": "A",
      "stages": ["leveling", "maps"],
      "stage_notes": {
        "leveling": "...",
        "maps": "...",
        "endgame": "swap to Cannonball once a real DPS weapon drops"
      },
      "required_items": ["Glacier Talons"],
      "sources": ["https://..."],
      "uncertain": []
    }
  ]
}
```

Valid JSON only. No prose outside `stage_notes` / `uncertain`. Do the popular
classes first (Pirate, Necromancer, Marksman, Amazon, Samurai, Pyromancer,
Viking, Paladin). Do **not** create or edit any file under `research/` except
`research/_meta/<class>.json`.
