"""research schema -> Profile (highlight/hide over the 167 stats).

Implements docs/filter-mapping.md. Pure function; deterministic.
"""
from __future__ import annotations

from .data import (ALL_IDS, ATTR, E_ABS, E_ADD, E_IGN, E_MAXRES, E_RES,
                   E_SD_FLAT, E_SD_PCT, E_SKILLS, NAME)
from .models import Profile, Research

# Stays visible (no glow) on every build — acceptable filler you would not
# reject an item for, but would not chase. Everything else the rules don't
# name gets hidden (section L). Mirrors the community filters' small neutral band.
KEEP_NEUTRAL = {
    54,   # Life per Level
    55, 58,   # Life Replenish / Life per Second
    59, 66,   # Life / Mana after each Kill
    386, 389,  # Flask instant mana / life replenish
    419,  # Sub Skills
    474,  # Increased Damage Return
}

# Hidden by section L but still worth surfacing on an A/S roll (a god-tier roll
# of one of these can make an item worth a look on any build).
ESCALATE_ANYWAY = {
    28, 29, 31,                     # enhanced damage / defense (+per level)
    52, 53, 54, 173, 174, 152,      # life, all resists, ignore-all-res
    175, 176, 177, 178, 179, 180, 181, 182, 183, 184,   # single + max resists
    68, 72, 73,                     # attack speed, crit chance / damage
    201, 51, 250,                   # all skills, all attributes, ailment damage
    132, 136, 140, 144, 148,        # additive elemental weapon damage
    159, 160, 161, 162, 170,        # damage reduction / faster hit recovery
    198, 200, 196,                  # skill haste, mana cost, faster cast
}

CASTER_KILL = [67, 68, 74, 75, 76, 77, 78, 94, 95, 97, 99]
SUMMON_BLOCK = [327, 328, 329, 330, 332, 333, 334, 331]
SENTRY_BLOCK = [336, 337, 338, 339, 335]
AILMENTS = [79, 80, 81, 82, 83, 84, 85, 86, 87,
            104, 105, 106, 107, 108, 109, 110, 250]
PHYS_WEAPON = [128, 129, 103, 28, 31]
OFF_DEFENSE = [29, 30, 155, 156, 169]

_DP = {
    "life_flat": [52], "life_pct": [53], "life_per_level": [54],
    "vitality": [48, 49], "life_on_kill": [59], "life_regen": [55, 58],
    "all_resist": [173], "max_all_resist": [174],
    "phys_dmg_reduction": [159], "all_dmg_reduction": [161],
    "damage_reduced": [162], "faster_hit_recovery": [170],
    "anti_freeze": [287, 288],
}


class _State:
    def __init__(self):
        self.state: dict[int, str] = {}
        self.why: dict[int, str] = {}

    def set(self, ids, st, reason):
        if st is None:
            return
        for i in ([ids] if isinstance(ids, int) else ids):
            if i in ALL_IDS:
                self.state[i] = st
                self.why[i] = reason


def compile_build(research: Research | dict) -> Profile:
    r = research if isinstance(research, Research) else Research.model_validate(research)
    c = _State()

    el = r.element.value
    splash = r.splash_element.value if r.splash_element else None
    els = [e for e in (el, splash) if e and e not in ("elemental", "converted")]
    delivery = {d.value for d in r.delivery}
    stage = r.stage
    scaling = set(r.scaling_stats)
    defprio = r.defense_priority
    pa = r.primary_attribute.value

    is_attacker = "attack" in delivery or "melee" in delivery
    is_summon = "summon" in delivery
    is_sentry = "sentry" in delivery
    is_minion = is_summon or is_sentry
    # a summon/sentry build isn't a "caster" for stat purposes even if you cast
    # the minion — the minion's own stat block carries the damage.
    is_caster = not is_minion and (
        "cast" in delivery or (el in E_SKILLS and not is_attacker)
    )
    # "spell-scaled" = damage comes from skill damage, not weapon phys: any caster,
    # or an attacker the player has explicitly told us scales Intelligence.
    spell_scaled = is_caster or (not is_minion and pa == "intelligence")

    # A. baseline
    c.set([201, 51, 52, 53, 54, 173, 174, 161, 162, 170, 25, 288, 26],
          "highlight", "generic-baseline")
    c.set([27, 281], "hide", "noise")
    if not is_summon:
        c.set(SUMMON_BLOCK, "hide", "not a summon build")
    if not is_sentry:
        c.set(SENTRY_BLOCK, "hide", "not a sentry build")
    if not ("dot" in delivery or {"ailment_damage", "ailment_frequency"} & scaling):
        c.set(AILMENTS, "hide", "not an ailment build")
    c.set(465, "highlight" if "movespeed_damage" in scaling else "hide", "move-speed conversion")
    c.set([171, 474], "hide", "reflect (opt-in)")

    # B. stage — collapse the bracket into three phases
    phase = {"leveling": "lvl", "normal": "lvl",
             "maps": "mid", "nightmare": "mid", "hell1": "mid",
             "endgame": "end", "hell3": "end", "hell5": "end"}[stage]
    if phase == "lvl":
        c.set(282, "highlight", "leveling: xp")
        c.set([284, 285, 286, 290], "hide", "leveling: not farming yet")
        c.set([59, 66, 58, 65, 55, 63], "highlight", "leveling: sustain")
    elif phase == "mid":
        c.set(282, "highlight", "maps: xp still good")
        c.set([284, 285], "highlight", "maps: mf matters")
        c.set([59, 66], "highlight", "maps: sustain")
        c.set(list(E_MAXRES.values()) + [174, 152], "highlight", "maps: cap resists / pen")
    else:
        c.set([284, 285], "highlight", "endgame: mf")
        c.set(282, "hide", "endgame: capped level")
        c.set(list(E_MAXRES.values()) + [174, 152], "highlight", "endgame: max resists / pen")
    early = phase == "lvl"

    # C. attribute — the picked damage attribute always wins; the other two are
    #    hidden unless a mechanic still needs them. This lets e.g. an Int-scaled
    #    lightning-melee Amazon keep Int highlighted even though it's an attacker.
    if pa in ATTR:
        c.set(list(ATTR[pa]), "highlight", f"primary attr {pa}")
    c.set(list(ATTR["vitality"]), "highlight", "life")
    if spell_scaled:
        c.set(list(ATTR["energy"]), "highlight", "spell scaling: mana")
        for a in ("strength", "dexterity"):
            if a != pa:
                c.set(list(ATTR[a]), "hide", "spell scaling: no str/dex")
    if is_attacker and pa != "intelligence":
        c.set(list(ATTR["intelligence"]), "hide", "attacker: no int")
    if r.defense_model not in ("shield_block", "hybrid") and pa != "armor":
        c.set(list(ATTR["armor"]), "hide", "armor attr unused")

    # D. skills — +element / +All raise the minion's skill level too, so keep
    for e in els:
        c.set(E_SKILLS[e], "highlight", f"+{e} skills")
    for e, sid in E_SKILLS.items():
        if e not in els and (e != "physical" or not is_attacker):
            c.set(sid, "hide", "off-element / unused skills")
    if "singular_skills" in scaling:
        c.set(202, "highlight", "singular")
    if "sub_skills" in scaling:
        c.set(419, "highlight", "sub skills")
    c.set(112, "highlight" if "explosion" in delivery else "hide", "explosion skills")

    # E. offense — minions have their own block; casters/attackers scale personally
    if is_summon:
        c.set(SUMMON_BLOCK, "highlight", "summoner: summon stat block")
    if is_sentry:
        c.set(SENTRY_BLOCK, "highlight", "sentry: sentry stat block")
    if not is_minion:
        for e in els:
            if e in E_SD_FLAT:
                c.set([E_SD_FLAT[e], E_SD_PCT[e]], "highlight", f"{e} skill damage")
        if spell_scaled:
            c.set([101, 153], "highlight", "generic magic/elemental skill damage")
        for e, sid in E_SD_FLAT.items():
            if e not in els:
                c.set([sid, E_SD_PCT[e]], "hide", "off-element skill damage")
    else:
        # personal skill damage does little for minion hits — off-element stays hidden
        for e, sid in E_SD_FLAT.items():
            if e not in els:
                c.set([sid, E_SD_PCT[e]], "hide", "minion: off-element noise")

    # F. weapon / additive
    if is_attacker and not is_caster:
        c.set(PHYS_WEAPON, "highlight", "attacker weapon damage")
        for e in els:
            if e in E_ADD:
                c.set(E_ADD[e], "highlight", f"additive {e}")
    else:
        c.set(PHYS_WEAPON, "hide", "no weapon attacks")
        for e in els:
            if e in E_ADD and "additive_element" in scaling and not is_minion:
                c.set(E_ADD[e], "highlight", f"additive {e} (build uses it)")
        for e, sid in E_ADD.items():
            if e not in els or is_minion:
                c.set(sid, "hide", "additive weapon damage — off/unused")

    # G. attack mechanics
    if is_attacker and not is_caster:
        c.set([68, 74, 75, 76], "highlight", "attacker mechanics")
    else:
        c.set(CASTER_KILL, "hide", "caster: no attack mechanics")
    if r.crit_scaling == "yes":
        c.set([72, 73], "highlight", "crit build")
    elif r.crit_scaling == "no":
        c.set([72, 73], "hide", "no crit scaling")

    # H. cast / cooldown
    if is_caster:
        c.set([196, 200], "highlight", "caster cast stats")
        c.set([198, 202], "highlight", "caster: skill haste / singular skills")
        c.set([60, 66], "highlight", "caster: mana pool / mana on kill")
    elif is_attacker:
        c.set([196, 200], "hide", "attacker: no cast")
    if r.cooldown_based:
        c.set(198, "highlight", "cooldown-based -> skill haste")

    # I. penetration
    for e in els:
        if e in E_IGN:
            c.set(E_IGN[e], "highlight" if not early else None, f"ignore {e} resist")
    for e, sid in E_IGN.items():
        if e not in els:
            c.set(sid, "hide", "off-element pen")

    # J. delivery bonuses
    c.set([111, 437], "highlight" if "explosion" in delivery else "hide", "explosion delivery")
    if "projectile" in delivery:
        c.set(70, "highlight", "projectile delivery")

    # K. defence
    for concept in defprio[:7]:
        if concept in _DP:
            c.set(_DP[concept], "highlight", "defense priority")
        elif concept.startswith("single_resist_") and concept.split("_")[-1] in E_RES:
            c.set(E_RES[concept.split("_")[-1]], "highlight", "defense priority")
        elif concept.startswith("max_single_resist_") and concept.split("_")[-1] in E_MAXRES:
            c.set(E_MAXRES[concept.split("_")[-1]], "highlight", "defense priority")
        elif concept.startswith("absorb_") and concept.split("_")[-1] in E_ABS:
            c.set(E_ABS[concept.split("_")[-1]], "highlight", "defense priority")
    c.set([57, 64], "highlight" if is_attacker else "hide", "leech")
    if r.defense_model not in ("shield_block", "hybrid") and pa != "armor":
        c.set(OFF_DEFENSE, "hide", "armor/defense unused")

    # L. tighten — community filters keep the neutral band tiny (~10 stats).
    #    Anything a rule didn't explicitly want is hidden, not left on the ground.
    #    These are "junk for this build": still hidden even on A/S rolls, so grade
    #    escalation only ever surfaces stats a rule deliberately hid (off-element
    #    skills, wrong attributes, caster attack mechanics …), never absorptions /
    #    merchant prices / defense-vs-missiles / etc.
    junk: list[int] = []
    for i in ALL_IDS:
        if i not in c.state and i not in KEEP_NEUTRAL:
            c.state[i] = "hide"
            c.why[i] = "not wanted for this build"
            if i not in ESCALATE_ANYWAY:
                junk.append(i)

    hi = sorted(i for i, s in c.state.items() if s == "highlight")
    hd = sorted(i for i, s in c.state.items() if s == "hide")
    junk_s = sorted(junk)

    # rarity policy. Default is the community-filter style (MisterSleepyCat):
    # NEVER hide an item by rarity or a roll by low grade -- item_rarity_min and
    # grade_show_min stay 0. Grade escalation is on by default (set below), so
    # off-list stats still surface on A/S rolls. Only grade_beam_min (where the
    # chase glow starts) ramps with the bracket. The user can re-impose the hard
    # floors from the UI (which turns grade escalation off).
    item_min, grade_show_min = 0, 0
    grade_beam_min = {
        "leveling": 0, "maps": 2, "endgame": 4,
        "normal": 0, "nightmare": 2, "hell1": 3, "hell3": 4, "hell5": 4,
    }[stage]

    # Runeword-base surfacing is a leveling / early-Hell tool (community advice:
    # once you only show items with the affixes you want, a socketed base
    # highlights from the affix anyway). On by default through Hell 1, off after.
    runeword_default = stage in ("leveling", "maps", "normal", "nightmare", "hell1")

    _G = ["D", "C", "B", "A", "S"]
    notes = (f"{r.class_} / {'+'.join(r.main_skills)} / {stage}. element={el}"
             + (f" splash={splash}" if splash else "")
             + f" delivery={sorted(delivery)}."
             + " No rarity/grade floor; most off-list stats surface on A/S rolls;"
             + f" chase glow from {_G[grade_beam_min]}+.")
    prof = Profile(id=r.id, name=r.name, notes=notes,
                   wtc=r.wtc, soc=None, highlight=hi, hide=hd,
                   hide_no_escalate=junk_s,
                   item_rarity_min=item_min, grade_show_min=grade_show_min,
                   grade_beam_min=grade_beam_min, grade_escalation=True,
                   runeword_bases=runeword_default)
    prof.__dict__["_why"] = {i: c.why[i] for i in hi + hd}
    return prof


def explain(profile: Profile) -> str:
    why = profile.__dict__.get("_why", {})
    out = [f"{profile.name}",
           f"{len(profile.highlight)} highlight / {len(profile.hide)} hide / "
           f"{167 - len(profile.highlight) - len(profile.hide)} neutral", ""]
    for label, ids in (("HIGHLIGHT", profile.highlight), ("HIDE", profile.hide)):
        out.append(label)
        out += [f"  {i:>3}  {NAME[i]:<34}  ({why.get(i, '')})" for i in ids]
        out.append("")
    return "\n".join(out)
