# Community filter study — MisterSleepyCat (Season 10)

Notes from decoding the loot filters attached to the build guides at
`mistersleepycat.info` (each guide has a "Loot filter" section with a
`/f/<id>` import page and a `/f/<id>/raw` download). Sampled 2026-09-01:
Prophet (poison caster), Marksman (arcane/explosion attacker), Pirate
(cold), Viking (phys melee), Bard (lightning caster), Paladin (lightning
hybrid). All Season 10.

## Format

- **All v2** (base64 → JSON), 39–47 KB each. No v3 in the wild here.
- One filter per build. Downloaded file name is `lootfilter_<slug>.txt`.

## The `trN` axis in v2 = affix GRADE (D..S), not item rarity

v2 has exactly one axis. `tr0..tr4` = the affix roll grade **D / C / B /
A / S** (confirmed by Mario's own capture named `colddoff` = "Cold [skills]
D-grade off" — "D" is a grade, no rarity starts with D). v2 **cannot**
express the item-rarity axis at all; that arrived with v3's per-slot
7-byte tiermask. So "he doesn't gate by item rarity" is a v2 limitation,
not a choice.

## What he does NOT use

- **No `wtc`** (weapon-type bitfield) on any filter.
- **No item-rarity gating** — impossible in v2 (see above).
- **No socket filtering** on most builds (Paladin is the exception).

## The core model: a tight per-slot highlight whitelist

- Each slot **hides ~145–165 of the 167 stats** and highlights a small,
  slot-tuned set. `hs` is essentially "everything except the keepers".
- A near-universal keep set appears on **every slot of every build**:
  **`26` Phasing, `52` Life, `201` All Skills**. Add the build's
  element skill (`227` Poison Skills for Prophet, `226` Lightning for
  Bard, …) and that is the whole gear-slot list for a lean build
  (Prophet gear = just those four).
- **The Charm slot (`t10`) always gets the fattest list** — it adds the
  primary attribute + per-level, All Attributes, Vitality, Magic Skill
  Damage, the flat elemental skill damage, Faster Cast Rate, Skill Haste,
  Mana / Mana-after-kill, All Resistances. Charms roll broadly, so the
  filter is more permissive there.
- **Slot-correct placement**, matching intuition:
  - `70` Projectile Speed — highlighted only on **Belt** (Marksman, Pirate).
  - `465` Movement Speed → Damage — only on **Boots**.
  - Flask stats (`385–396`) — only on **Vial** (`t18`).
  - Summon/Sentry stats (`327–339`) — only on **Socketable** (`t15`).

## The clever bit: GRADE escalation

On **Weapon, Charm, Socketable, and Vial** the highlight list is
*identical for D / C / B rolls*, then **widens at A-grade and widens
again at S-grade**. Paladin weapon (`t3`) is the clearest:

| grade | highlighted stats |
|---|---|
| D–C | 11 — core lightning + flask + skill-damage |
| B (Rare-tier roll) | +`Faster Cast Rate` |
| A | +~70 — "show me almost any decent affix" |
| S | +~100 — nearly the whole stat sheet |

Rationale: an S-grade roll is rare enough that it is worth seeing for
*any* useful stat; a D-grade roll is only worth seeing if it is a *core*
stat. **The bar for "interesting" scales down as the roll quality scales
up.** We brought a light version of this in as the `grade_escalation`
toggle (2026-09-01): off-list stats stay hidden on D/C/B, become visible
(not beamed) on A/S. Ours is per-slot and threshold-fixed; his is a full
per-grade highlight list.

## Sockets / runeword bases

- Most builds set **no `soc`**.
- **The Paladin filter sets `soc: 62` on exactly `t0/t1/t2/t3/t6`**
  (helmet, chest, boots, weapon, shield). `62 = 0x3E =` sockets 2–6.
  This independently confirms:
  - the **runeword-craftable slot set** we chose (helmet/chest/boots/
    weapon/shield — no gloves/amulet/ring/belt/charm), and
  - that **`0x3E` is the "any usable socket count" value** (drop the
    1-socket bit).
- `soc` in v2 is the **low byte** of the v3 per-slot socket u16 (the
  "show" mask; the "beam" high byte has no v2 spelling). So his approach
  **restricts those five slots to socketed items**, where our
  `runeword_bases` toggle instead **beams** them additively via the high
  byte. His is the "dedicated runeword filter" style; ours layers on top
  without disturbing the rest of the filter. Whether the v2 `soc`
  low-byte restrict is a hard gate (hides 0/1-socket items outright) or
  an additive OR-in is **still unverified in-game** — worth a capture.

## The neutral band

He deliberately leaves a handful of stats **neither highlighted nor
hidden** (visible, no glow). On Bard's gear slots the never-touched set
is: Life / Life% / Life-after-kill, Mana-after-kill, Faster Cast Rate,
Phasing, Sub Skills, Movement Speed, Flat Elemental Skill Damage, Ignore
All Resistance, Damage Reduced, Increased Damage Return, Flask instant
life/mana. Read as: "wouldn't reject an item for these, wouldn't chase
them either."

## Whitelist-only slots

For **Socketable (`t15`)** and **Vial (`t18`)** several filters set
`hs: []` (hide nothing) and only supply highlights — you always see every
gem / vial, with a glow on the good ones. Not fully consistent (Prophet
still hides on `t15`).

## Brought into our tool (2026-09-01) — now the DEFAULT

Mario's call: "do his way as default and grey out the options that
conflict."

1. **No rarity/grade floor by default.** `compile_build` now returns
   `item_rarity_min = 0`, `grade_show_min = 0` for every stage — an item
   is never hidden for being low rarity, a roll is never hidden for being
   low grade. Only `grade_beam_min` (where the chase glow starts) still
   ramps with the bracket (D / A / S for leveling / mid / endgame).
2. **`grade_escalation` on by default** (`Profile.grade_escalation=True`
   from the compiler). Off-list stats surface (visible, no beam) on A/S
   rolls. `Overrides.grade_escalation` is tri-state (`None` = keep
   default on).
3. **UI**: the "Hide items below rarity" and "Hide affix rolls below
   grade" rows are **greyed out while grade escalation is on**. Unchecking
   grade escalation re-enables them (and clears the auto-suppression) so a
   user can still build a hard-floor filter.
4. **Highlight-only slots** — Charm / Consumable / Socketable / Vial
   (`t10 t11 t15 t18`) never get hide entries, matching his `hs: []`
   treatment of gems/vials. Chase highlights still apply.
5. **Universal keepers** already covered: our section-A baseline
   highlights Phasing (26), Life (52), All Skills (201), Movement Speed
   (25) on every slot — verified, superset of his.

## Still just notes

- Our runeword-slot set and `0x3E` socket value are validated against his
  Paladin filter.
- He runs **zero grade suppression, zero wtc** — filters stay ~40 KB v2
  but never risk hiding a drop. Our v3 output is ~1 KB; different
  philosophy, both valid.
- Consider hosting downloadable filters behind stable short IDs like his
  `/f/<id>` + `/f/<id>/raw` (nice for guide embeds).
