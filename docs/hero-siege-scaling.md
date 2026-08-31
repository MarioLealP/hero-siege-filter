# Hero Siege — how builds and skills scale

Shared mental model for the research → filter pipeline. Season 10 (Ebontharn),
game build 2024.14.1.

## 1. Characters and skill trees

- Each class has **two skill trees**. A build commits to one tree (occasionally
  splashes the other). Example: Pirate = *Gunner* (attack / proc) vs *Plunderer*
  (cold AoE cast).
- Trees have a handful of **active skills** plus **passives** and a **subskill**
  layer. A build is defined by its **main damage skill** (sometimes two).
- Skills have, from the tooltip / wiki:
  - a **damage element**: physical / fire / cold / lightning / arcane / poison
    (some skills are "elemental" = the lowest of your resists, or convert).
  - a **delivery mechanism** (see §3).
  - a **base scaling attribute** (see §2).
  - **cooldown-based** (fixed recharge) or **spammable** (mana/resource-gated).
  - **single-target** vs **AoE / clear**.

## 2. Attributes

Six: **Strength, Dexterity, Intelligence, Energy, Armor, Vitality**. Each point
does a fixed thing; builds dump into their damage attribute after meeting
requirements.

| Attribute | Primary effect | Who scales on it |
|-----------|----------------|------------------|
| Strength | melee / physical attack damage, some HP | physical attackers |
| Dexterity | ranged / crit / attack rating | gun / bow / dagger attackers |
| Intelligence | **1 Int ≈ 1% Magic (skill) Damage** | every caster |
| Energy | max mana, mana regen | casters (as a secondary req) |
| Armor | armor / defense rating | tanky bruisers |
| Vitality | max life | everyone (secondary) |

Most builds: **all damage-attribute after requirements**, with just enough
Energy for mana comfort and a few points of Vitality while levelling.

`+All Attributes` counts for the damage attribute too, so it is universally good.

## 3. Delivery mechanisms — this decides which stats matter

| Delivery | Speed stat that matters | Notes |
|----------|------------------------|-------|
| **Attack** (weapon swings/shots) | Attack Speed, Attack Rating, weapon damage, crit | scales with the physical/element *additive weapon* damage and Enhanced Damage |
| **Cast** (spells) | **Faster Cast Rate**, Mana Cost Reduced | scales with *skill damage* stats, not weapon damage |
| **Cooldown** (fixed recharge, e.g. Anchor Swing) | **Skill Haste** (a.k.a. cooldown reduction) | more casts per second = more DPS; FCR still helps the cast animation |
| **Projectile** | Projectile Speed (QoL), sometimes Piercing | |
| **Orbital** | — | |
| **Explosion** (bombs / on-hit blasts) | — | scales **Explosion Damage**, **Explosion AOE**, **+Explosion Skills** |
| **Summon** (minions) | Summon Attack Speed | scales the whole **Summon** stat block + **+Summon Skills**, NOT your own damage stats |
| **Sentry** (turrets) | Sentry Attack Speed | scales the **Sentry** block + **+Sentry Skills**, plus Sentry Duration/Amount |

A single skill can carry several tags (e.g. Anchor Swing = cold + cast + cooldown
+ AoE, possibly + explosion).

## 4. The damage formula, roughly

For a **caster** skill of element `E`:

```
hit ≈ base(skill_level) × (1 + Int%/100 + MagicSkillDamage% + E_SkillDamage% + additive_E%)
      × crit_multiplier × penetration × ailment_bonus
skill_level = allocated + "+All Skills" + "+E Skills" + "+Singular/Sub" (if it hits this skill)
casts/sec  ≈ f(Faster Cast Rate, Skill Haste if cooldown)
```

So the **highlight priority for any caster** is, in order:

1. `+All Skills`, `+<element> Skills` (multiplies base — biggest single lever)
2. `<element> Skill Damage` flat **and** %, `Magic Skill Damage %`,
   `Flat Elemental Skill Damage`
3. the scaling **attribute** (usually Intelligence) + `+All Attributes`
4. **Faster Cast Rate**, plus **Skill Haste** if the skill is cooldown-based
5. `Ignore <element> Resistance` / `Ignore All Resistance` (flat more-damage vs
   resistant enemies — big in endgame, minor while levelling)
6. `Additive <element> Damage`, `Mana Cost Reduced` (sustain), delivery bonuses
   (Explosion Damage/AOE) **if** the skill has that tag

For an **attacker** swap: attribute = Str/Dex, and 1–4 become Attack Speed +
Attack Rating + weapon (Flat/% Physical or Additive-element) damage + crit +
`+Physical Skills` (for physical attack skills).

For a **summoner/sentry**: your personal damage stats do **nothing**. Only the
Summon/Sentry blocks + `+Summon/Sentry Skills` + Summon/Sentry Attack Speed.

## 5. Defence — every build needs a layer

- **Life**: `Life` flat, `Life %`, `Life per Level`, `Vitality`. `Life %` is
  multiplicative so it scales best late.
- **Resistances**: cap all resists. `All Resistances` + `Maximum All Resists`
  are the workhorses; single-element resist/max-resist matter for capping a
  specific hole or for hard-hitting element bosses.
- **Damage reduction**: `Physical Damage Reduction`, `All Damage Reduction`,
  `Damage Reduced` — flat mitigation, always useful.
- **Sustain**: `Life/Mana After each Kill` and `Life/Mana per Second` carry the
  levelling grind; leech (`... Stolen per Hit`) only works for attackers.
- **Anti-freeze** (`Cannot be Frozen`, `Half Freeze Duration`) is close to
  mandatory in cold-heavy zones.

## 6. Progression stages

| Stage | What changes |
|-------|--------------|
| **Levelling** (1 → ~100) | want **XP Gain**, cheap generic stats, on-kill sustain, movement. Magic Find / gold are *noise* — dim them. Single-resist rolls less useful than All-Res. |
| **Maps / early endgame** | Magic Find and single-resist capping start to matter; damage % stats over flat; start caring about `Ignore Resistance`. |
| **Deep endgame (T15+ / wormholes)** | Magic Find, `Maximum` resists, `Ignore All Resistance`, `All Damage Reduction`, absorbs, conversions. Flat/small rolls become noise. |

## 7. Conversions & specials (build-defining when present)

- "X% of Intelligence added as Magic/Lightning Skill Damage" — makes Int a
  double-dipping stat.
- "X% of your <Resistance> converted to <Element> Skill Damage" — turns a
  defensive stat offensive; only relevant to that element's casters.
- "Movement Speed Converted to Damage" — only for builds that stack move speed.
- Runewords / uniques often gate a build (e.g. Anchor Swing wants *Glacier
  Talons*); those are item-name filters, out of scope for the stat filter.

## 8. Slot notes (for the generic baseline)

- **Boots** are the movement slot — Movement Speed and **Phasing** belong here
  and are good on essentially every build.
- **Charm** commonly rolls `+Skills` and unique effects — treat generously.
- **Amulet / Ring** are flexible high-value affix slots.
- **Shield** only matters for builds that use one (many casters dual-wield or
  two-hand instead) — its block/defense stats are build-dependent.
- **Weapon** carries the damage stats; for casters the *skill* damage lines, for
  attackers the *weapon* damage lines.
