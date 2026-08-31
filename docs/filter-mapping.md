# From research schema to filter — the mapping rules

`tools/compile_build.py <research.json>` applies these deterministically to
produce `data/builds/<id>.json` (highlight/hide lists), which
`tools/build_filter.py` turns into the importable code.

Three states per stat: **highlight** (glow), **hide** (dim), **neutral** (left
alone). Rules run in order; a later rule can override an earlier one. Anything
never touched stays neutral.

## A. Generic baseline (every build)

**Always highlight:** All Skills · All Attributes · Life · Life % · Life per
Level · All Resistances · Maximum All Resists · All Damage Reduction · Damage
Reduced · Faster Hit Recovery · Movement Speed · Cannot be Frozen · Phasing.

**Always hide (pure noise):** Jumping Power · Light Radius.

**Always hide unless the build opts in** (via `delivery` / `scaling_stats`):
whole Summon block + Summon Skills · whole Sentry block + Sentry Skills · all
ailment stats (Extra Damage to <state>, Increased <ailment> Frequency, Ailment
Damage) · Movement Speed Converted to Damage · Damage Return / Increased Damage
Return.

**Slot override:** Phasing is highlighted everywhere but is *most* wanted on
Boots (kept as-is; no per-slot logic needed for v1).

## B. Stage gate (`progression`)

| | leveling | maps | endgame |
|-|----------|------|---------|
| Increased Experience Gain | **highlight** | highlight | neutral |
| Magic Find / MF per Level | **hide** | neutral | **highlight** |
| Extra Gold / Merchant Prices | hide | neutral | neutral |
| Life/Mana After each Kill | **highlight** | highlight | neutral |
| Life/Mana per Second, Replenish | highlight | neutral | neutral |
| single-element Max Resists | neutral | highlight | **highlight** |
| Ignore All Resistance | neutral | highlight | **highlight** |
| flat/small rolls (Additive dmg, flat skill dmg) | keep | keep | de-prioritise (neutral) |

## C. Attribute

- highlight `primary_attribute` **and** its per-level twin
  (Int→42/43, Str→33/34, Dex→36/37, Energy→39/40, Armor→45/46, Vit→48/49).
- highlight Vitality always (life). highlight Energy for any `cast` build (mana).
- hide the *other* damage attributes: caster → hide Strength, Dexterity (+per
  level); attacker → hide Intelligence (+per level).
- Armor attribute: neutral unless `defense_model` = shield_block/hybrid.

## D. Skills

- highlight `<element> Skills` for `element` and `splash_element`.
- highlight Singular Skills, Sub Skills if in `scaling_stats`.
- highlight Explosion Skills iff `explosion` in `delivery`, else hide.
- hide every other `<element> Skills` (off-element).
- Summon/Sentry Skills: highlight iff `summon`/`sentry` in `delivery`
  (else already hidden by baseline).

## E. Skill damage

- highlight, for `element` (and `splash_element`): the flat + % skill damage.
- highlight Magic Skill Damage, Flat Elemental Skill Damage (generic, help every
  caster) — for any build whose `delivery` includes `cast`.
- hide off-element flat + % skill damage.

## F. Weapon / additive damage

- attacker: highlight Flat Physical Damage, Physical Damage %, Physical Damage
  per Level, Enhanced Damage (+per level), and Additive-`<element>` damage.
- caster: hide all physical weapon damage + Enhanced Damage; Additive-`<element>`
  damage → highlight only if `additive_element` in `scaling_stats`, else neutral;
  hide off-element additive.

## G. Attack mechanics

- attacker: highlight Attack Speed, Attack Rating (+% +per level).
- caster: hide Attack Speed, Attack Range, Attack Rating (+% +per level),
  Piercing, Slow Target, Ignore Target Defense, Deadly Blow, Crushing Blow,
  Open Wounds.
- Crit (Chance for Critical Strike, Critical Strike Damage): `crit_scaling` →
  `yes` highlight · `optional` neutral · `no` hide.

## H. Cast / cooldown

- `cast` in delivery: highlight Faster Cast Rate, Mana Cost Reduced.
- `cooldown_based`: highlight Skill Haste.
- pure attacker: hide Faster Cast Rate, Mana Cost Reduced; Skill Haste neutral.

## I. Penetration

- highlight `Ignore <element> Resistance` for `element` and Ignore All
  Resistance — strength by stage (see B; neutral at leveling).
- hide off-element Ignore Resistance.

## J. Delivery bonuses

- `explosion` in delivery: highlight Explosion Damage, Explosion AOE (else hide).
- `projectile` in delivery: highlight Projectile Speed (else neutral).

## K. Defence (from `defense_priority`, top ~6 → highlight)

Concept → stat id(s):

```
life_flat 52 · life_pct 53 · life_per_level 54 · vitality 48/49 ·
life_on_kill 59 · life_regen 55/58 ·
all_resist 173 · max_all_resist 174 ·
single_resist_<E> 175/177/179/181/183 · max_single_resist_<E> 176/178/180/182/184 ·
phys_dmg_reduction 159 · all_dmg_reduction 161 · damage_reduced 162 ·
faster_hit_recovery 170 · anti_freeze 287/288 ·
absorb_<E> 191/192/193/194/195 · block (only if uses_shield) ·
```

- Not-highlighted resistances stay **neutral** (never hide a resist).
- Leech (Life/Mana Stolen per Hit): highlight only for attackers, else hide.
- Enhanced Defense (+per level), Defense %, Defense per Level, Defense vs
  Missiles: hide unless `defense_model` ∈ {shield_block, hybrid} or Armor is
  the primary attribute.
- Damage Taken Recouped as Life/Mana: neutral.

## L. Everything else

Flask block, Mana (flat/%/level) for non-casters, per-level attribute twins not
covered, etc. → **neutral**.
