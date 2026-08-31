# Gemini research spec — Hero Siege build catalog

**You are building a catalog of Hero Siege build profiles.** Each profile is one
JSON file that a deterministic tool turns into a loot filter. Follow this spec
exactly — the tool rejects anything off-schema.

Game: **Hero Siege, Season 10 "Ebontharn"**, build 2024.x. If a mechanic changed
recently, use the most recent patch and record it in `uncertain`.

---

## 1. Deliverable & organisation

Produce files under `research/`, **one file per (class, build, stage)**:

```
research/
  <class>_<build>_<stage>.json      e.g. pirate_anchor_swing_leveling.json
                                         necromancer_bone_spear_endgame.json
                                         amazon_generic_phys_attacker_maps.json
```

- `<class>` — lowercase, the class name, no spaces (`plague_doctor`).
- `<build>` — the skill's name (`anchor_swing`) **or** a generic archetype when
  the build isn't one signature skill (`generic_cold_caster`,
  `generic_phys_attacker`, `generic_summoner`, `generic_sentry`,
  `generic_bow_attacker`). Use generics sparingly — prefer a real skill.
- `<stage>` — one of `leveling`, `maps`, `endgame`.

**Workflow:**

1. First pull the current **class list** from
   `herosiege.fandom.com` / `hero-siege-helper.vercel.app/data/skills`. List every
   class and its two trees. Save that as `research/_classes.json` (see §5).
2. For each class, identify its **1–3 currently viable builds** (S10 tier lists /
   build sites). For each, produce the three stage files (leveling / maps /
   endgame) unless a stage genuinely doesn't apply (note why in `uncertain`).
3. Also produce the **generic archetype** files once each (class-independent):
   `research/generic_<archetype>_<stage>.json` — these are the fallback when a
   user picks "archetype" instead of a named skill.

Do the common / popular classes first (Pirate, Necromancer, Marksman, Amazon,
Samurai, Pyromancer, Viking). Don't block the whole catalog on one obscure class.

---

## 2. Sources, in priority order

1. In-game skill tooltips (screenshots) if provided — ground truth.
2. `herosiege.fandom.com/wiki/<Class>` and each skill's wiki page.
3. `graxyguides.com/herosiege/builds/season-10-builds/<class>/<build>`,
   `herosiegebuilds.com/builds`, `herosiegewiki.com/builds`,
   `tposegaming.com/hero-siege-filter-guide`.
4. `hero-siege-helper.vercel.app/data/skills` and `/data/affixes`.
5. Recent YouTube S10 build guides, official patch notes.

Cite every URL you used in `sources`. Where sources disagree, pick
majority/most-recent and add a line to `uncertain`.

---

## 3. The schema (return exactly this shape)

```json
{
  "id": "pirate_anchor_swing_leveling",
  "name": "Pirate — Anchor Swing (Plunderer) — Leveling",
  "class": "Pirate",
  "tree": "Plunderer",
  "main_skills": ["Anchor Swing"],
  "element": "cold",
  "splash_element": null,
  "delivery": ["cast", "cooldown", "aoe", "explosion"],
  "primary_attribute": "intelligence",
  "cooldown_based": true,
  "aoe": true,
  "crit_scaling": "no",
  "defense_model": "life",
  "uses_shield": false,
  "key_conversions": [],
  "required_items": ["Skysong (budget)", "Glacier Talons (progression)"],
  "scaling_stats": [
    "all_skills", "cold_skills", "cold_skill_damage_pct",
    "cold_skill_damage_flat", "magic_skill_damage",
    "flat_elemental_skill_damage", "primary_attribute", "all_attributes",
    "faster_cast_rate", "skill_haste", "mana_cost_reduced",
    "explosion_damage", "explosion_aoe", "explosion_skills",
    "ignore_cold_resist", "ignore_all_resist", "additive_element"
  ],
  "defense_priority": [
    "life_flat", "life_pct", "all_resist", "anti_freeze",
    "faster_hit_recovery", "life_on_kill", "all_dmg_reduction"
  ],
  "stage": "leveling",
  "stage_notes": {
    "leveling": "XP gain + on-kill sustain + movement; ignore magic find / gold.",
    "maps": "cap single resists, pick up magic find, keep cast/haste.",
    "endgame": "respec toward Cannonball once a real DPS weapon drops."
  },
  "sources": ["https://..."],
  "uncertain": ["Whether Anchor Swing is genuinely explosion-tagged."]
}
```

### Field rules

| field | allowed values / rule |
|-------|-----------------------|
| `id` | `<class>_<build>_<stage>`, lowercase, `_` separated, matches filename |
| `class` | exact class name, Title Case |
| `tree` | which of the class's two trees, or `"both"` |
| `main_skills` | 1–3 skill names as shown in game |
| `element` | `physical` `fire` `cold` `lightning` `arcane` `poison` `elemental` `converted` |
| `splash_element` | a second real element the build also deals, else `null` |
| `delivery` | subset of: `attack` `melee` `cast` `cooldown` `projectile` `orbital` `explosion` `summon` `sentry` `dot` `aoe` |
| `primary_attribute` | `strength` `dexterity` `intelligence` `energy` `armor` `vitality` |
| `cooldown_based` | bool — does DPS depend on the skill's cooldown (→ Skill Haste matters) |
| `aoe` | bool — is this the clear skill |
| `crit_scaling` | `yes` (build stacks crit) / `no` / `optional` (works but not core) |
| `defense_model` | `life` `shield_block` `dodge` `hybrid` |
| `uses_shield` | bool |
| `key_conversions` | list of exact stat-conversion phrases the build relies on, e.g. `"X% of Intelligence added as Magic Skill Damage"`; else `[]` |
| `required_items` | runewords/uniques that gate the build (context only); else `[]` |
| `scaling_stats` | **ordered, best first** — only concept names from §4 |
| `defense_priority` | **ordered, best first** — only concept names from §4 |
| `stage` | `leveling` / `maps` / `endgame` — must match filename |
| `stage_notes` | one short sentence per stage |
| `sources` | list of URLs actually used |
| `uncertain` | list of short sentences — anything you're guessing or sources disagreed on. **Empty list is fine if you're confident; never leave it out.** |

---

## 4. Canonical concept vocabulary

`scaling_stats` and `defense_priority` may **only** contain these tokens.
Substitute the build's element for `element` (e.g. `cold_skills`,
`cold_skill_damage_pct`, `ignore_cold_resist`, `single_resist_cold`).

**Offense (`scaling_stats`):**
```
all_skills  element_skills  singular_skills  sub_skills  explosion_skills
summon_skills  sentry_skills
element_skill_damage_flat  element_skill_damage_pct  magic_skill_damage
flat_elemental_skill_damage
primary_attribute  all_attributes
faster_cast_rate  skill_haste  mana_cost_reduced
attack_speed  attack_rating  weapon_flat_phys  weapon_pct_phys
additive_element  crit_chance  crit_damage
ignore_element_resist  ignore_all_resist
explosion_damage  explosion_aoe  projectile_speed
summon_block  sentry_block
ailment_damage  ailment_frequency  extra_damage_vs_ailment
movespeed_damage
```

**Defense (`defense_priority`):**
```
life_flat  life_pct  life_per_level  vitality  life_on_kill  life_regen
all_resist  max_all_resist  single_resist_<element>  max_single_resist_<element>
phys_dmg_reduction  all_dmg_reduction  damage_reduced  faster_hit_recovery
anti_freeze  block  absorb_<element>  dodge
```

If the build genuinely wants something with no token, **do not invent one** —
describe it in `uncertain` and pick the closest token.

---

## 5. `research/_classes.json`

The dropdown catalog is built **automatically from the `research/*.json` files**,
so you do **not** maintain a class list here. This file is just metadata:

```json
{
  "game_version": "2024.x / Season 10 (Ebontharn)",
  "retrieved": "YYYY-MM-DD",
  "archetypes": [
    "cold_caster", "fire_caster", "lightning_caster", "arcane_caster",
    "poison_caster", "phys_attacker", "bow_attacker", "gun_attacker",
    "summoner", "sentry", "hybrid"
  ]
}
```

Optionally keep a `docs/knowledge-base/classes/<class>.md` per class with the raw
notes you gathered (trees, skills, viable builds, sources) — useful context, not
consumed by the pipeline.

---

## 6. Quality checklist (per file)

- [ ] filename == `id` == `<class>_<build>_<stage>`
- [ ] `element` and `delivery` reflect the **skill tooltip**, not vibes
- [ ] `scaling_stats` ordered, best first, only §4 tokens, element substituted
- [ ] `defense_priority` ordered, only §4 tokens
- [ ] `primary_attribute` is what the build **dumps points into**, not a requirement
- [ ] `cooldown_based` true ⇒ `skill_haste` appears in `scaling_stats`
- [ ] `crit_scaling: yes` ⇒ `crit_chance` + `crit_damage` in `scaling_stats`
- [ ] summoner/sentry build ⇒ `summon`/`sentry` in `delivery` **and**
      `summon_block`/`sentry_block` high in `scaling_stats`; personal damage
      stats absent
- [ ] every claim traceable to a URL in `sources`
- [ ] `uncertain` present (may be `[]`)
- [ ] valid JSON, no comments, no trailing commas

---

## 7. Don't

- Don't write prose anywhere except `*_notes` and `uncertain`.
- Don't invent stat names or concept tokens.
- Don't guess an element/delivery you couldn't verify — say so in `uncertain`.
- Don't include item-name recommendations outside `required_items`.
- Don't produce partial files — every field filled.
