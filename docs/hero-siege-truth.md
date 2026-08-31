# Hero Siege — verified truth base

Sources: the game's own data files (`translations*.csv` in the install — ground
truth for skills/elements), the official wiki (`herosiege.wiki.gg/wiki/Mechanics`,
`herosiege.fandom.com`), and Steam discussions. Season 10 "Ebontharn", 2026.
Everything here is either lifted from the game or cited.

## 1. Attribute formulas (official wiki + Steam)

| Attribute | Per point | Serves |
|-----------|-----------|--------|
| **Strength** | +1% Attack Damage, +1 additive Physical Damage | physical attackers |
| **Dexterity** | +8 Attack Rating, +0.125% Critical Damage | ranged / crit attackers |
| **Intelligence** | **+1% Magic (skill) Damage** | every caster |
| **Energy** | +4 Mana | casters (mana pool / skill cost) |
| **Armor** | armor / defense rating | tanks |
| **Vitality** | +max Life | everyone (early) |

Some classes add a per-point bonus on top (e.g. each Strength gives Viking +0.2
damage to his three Str-scaling actives). `+All Attributes` counts for the
damage attribute, so it is universally good.

**Consequence — the fork the filter runs on:**

- **Cast-rate caster** needs only: Intelligence, Faster Cast Rate, Skill Haste
  (if cooldown-gated), +Skill Damage (element + Magic + Elemental), Ignore
  Resistance. Weapon damage, attack speed, attack rating, crit do nothing.
- **Physical attacker** needs: Strength, Dexterity, Vitality, Crit Chance, Crit
  Damage, Ignore Target Defense, Additive Physical Damage, Attack Speed, Attack
  Rating. Cast rate / skill damage % do nothing.
- **Summoner / Sentry**: personal damage stats do nothing; only the Summon /
  Sentry stat blocks + `+Summon`/`+Sentry Skills` + Summon/Sentry Attack Speed.

## 2. Damage math (rough)

```
caster hit ≈ base(skill_lvl) × (1 + Int%/100 + MagicSkillDmg% + <el>SkillDmg%)
             × pen(Ignore<el>Resist) × crit? × ailmentBonus?
skill_lvl  = points + "+All Skills" + "+<el> Skills" [+ Singular/Sub if it hits this skill]
casts/sec  ≈ f(Faster Cast Rate [, Skill Haste if cooldown-gated])
```

Highlight priority for a caster, in order:
1. `+All Skills`, `+<element> Skills`
2. `<element> Skill Damage` flat + %, `Magic Skill Damage`, `Flat Elemental Skill Damage`
3. Intelligence (+per level), `+All Attributes`
4. Faster Cast Rate; **Skill Haste** only if the skill is cooldown-gated
5. `Ignore <element> Resistance`, `Ignore All Resistance` (endgame > leveling)
6. `Additive <element> Damage`, `Mana Cost Reduced`, delivery bonuses (Explosion
   Damage/AOE **only** if the skill is tagged explosion)

## 3. Progression stages (wiki + community, verified)

| | Leveling (1→100) | Maps (Inferno / early endgame) | Deep endgame (Wormholes, Torment III+) |
|-|-|-|-|
| stat points | ~60–100 Vitality early, rest into primary attribute | stop splitting — 100% primary attribute | 100% primary attribute |
| resistances | whatever leveling gear gives | **cap all four** — mandatory | cap + `Maximum` resists |
| filter emphasis | **XP Gain**, on-kill sustain, movement, cheap generic stats. Magic Find / gold = noise → dim | single-element resist capping, Magic Find starts to matter, % over flat | `100% Ignore Resistance/Defense` (mandatory), Damage Reduction layering, Magic Find, absorbs; flat/small rolls become noise |
| defence share | Vitality + baseline | ~1/3 of affixes | melee ~1/2 of affixes on survival; casters can be greedier (mobility is defence) |

## 4. Class → identity (from `data/game_truth.json` + the formulas)

`scale` = primary damage attribute. Classes with both a caster and an attacker
side are marked *hybrid — pick per build*.

| Class | Main elements | Archetype / scale | Notes |
|-------|---------------|-------------------|-------|
| Pirate | cold (Anchor Swing, Torrent, Parrot), fire (Cannonball, Buckshot, Bomb Barrage) | hybrid — cold **caster/Int** or fire **attacker/Str** | Anchor Swing = cold AoE swing around you (not explosion) |
| Necromancer | arcane (Bone*), poison (Poison*), summon (Raise*, Damned Legion) | **caster/Int** or **summoner** | Bone Spear tooltip scales Energy; Vengeful Spirit scales Int |
| Marksman | arcane / fire; turrets + Gunner Drone | **summon+sentry / Int** (Gunner Drone = "arcane damage") | drone/turret damage scales the summon/sentry blocks |
| Pyromancer | fire (all skills) | **caster/Int** | pure fire |
| Viking | physical (Whirlwind, Throw, Shockwave), arcane (Charge, Odin's Fury), cold (Ymir's Champion) | **attacker/Str**; Odin's Fury = arcane shout-caster for leveling | Str gives extra per-point damage to his actives |
| Amazon | poison (Caustic, Envenom, Noxious — Dex), lightning (Thunder Fury — Int, Spearnage, Storm Dash) | hybrid — poison **javelin/Dex** or lightning **caster/Int** | Noxious Strike scales Dex; Thunder Fury scales Int |
| Samurai | physical / explosive (Kunai, Blade Barrier, Omnislash) | **attacker/Str** | melee + thrown; crit-scaling |
| Paladin | lightning (Lightning Fury, Ball Lightning), holy (Holy Hammer/Bolt/Nova), aura | **hybrid** — Lightning Fury caster-ish; holy/melee = Str + armor-cap | see §5 caveat |
| Redneck | fire / physical (Chainsaw Slash, Chainsaw Massacre, Molotov, Tire Fire) | **attacker/Str** (chainsaw) | Chainsaw Slash strong endgame |
| Plague Doctor | poison (Miasma, Toxic Flask, Plague of Rats), summon (Jar of Leeches, Randy) | **caster/Int** (poison DoT) or summoner | safest S10 leveler |
| Prophet | many: frost (Maelstrom), physical (Wendigo/Leaping), summon (Ent, Raven, Carrion) | **hybrid** — form-shifter / summoner | |
| Jotunn | cold (all: Blizzard, Avalanche, Orb of Frost, Frost Sunder) | **caster/Int** | Frost Sunder strong endgame |
| Stormweaver | lightning (all: Storm Bolt, Charged Bolts, Lightning Surge, Static Shock) | **caster/Int** | pure lightning |
| White Mage | holy / shadow (Chain of Holy Light, Shadow Bolt, Dark Oath, Black Mass) | **caster/Int or Energy** (Burst of Light scales Energy) | |
| Shaman | fire/lightning/earth totems + Meteor Storm, Tornado | **sentry/Int** (totems) | totem = sentry block |
| Bard | physical / fire (Slaying Riffs, Moshpit, Pyro Technician) | **attacker/Str** | |
| Butcher | physical (Blender, Chain Rip, Furious Strike, Cleavers) | **attacker/Str** | |
| Demon Slayer | physical / demonic (bullet-hell, slices) | **attacker/Dex** (gun) | boss killer |
| Nomad | physical / sand (Blade Strike, Scimitar, Sand*) | **attacker/Str or Dex** | |
| Shield Lancer | physical (Lance*, Shield Slam/Wall, Battle Charge) | **attacker/Str + shield_block** | Shield Wall strong leveler |
| Exo | cosmic — solar (fire), lunar (cold/arcane), gravity | **caster/Int** | |
| Illusionist | arcane / sand (Gravitational Slam, Sand Guardian, Temporal Heroes) | **caster/Int** or summoner | |

## 5. Caveats / still-uncertain

- **Tree names** — the game groups subtalents by *skill*, not by the two named
  trees. Tree assignment per build needs a wiki/build-guide check and is not in
  the game data. Leave `tree` best-effort; it does not affect the filter.
- **Paladin scaling** — community sources split between Int (Lightning Fury) and
  Str + armor-cap (holy/melee). Verify per build.
- **S10 meta** is early-season (no public beta) — tier lists will shift. Loose
  consensus: strong levelers = Bone Shred, Gunner Drones, Shield Wall, Anchor
  Swing; strong endgame = Frost Sunder, Chainsaw Slash, Flicker, Anchor Swing;
  top classes = Paladin, Demonspawn, Pyromancer, Viking, Plague Doctor.
  (afleurdenet.com, tposegaming.com, grindnstrat.com, herosiegeguide.wiki S10 tier lists)
