import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";

import { Slab } from "@/components/Slab";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useTheme } from "@/lib/useTheme";
import {
  type Catalog,
  type Explain,
  type Overrides,
  downloadArchetype,
  getArchetypeExplainCustom,
  getCatalog,
} from "@/api";

type Custom = {
  item_rarity_min?: number;
  grade_show_min?: number;
  grade_beam_min?: number;
  weapons?: number[];
  runeword_bases?: boolean;
  socket_counts?: number[];
  grade_escalation?: boolean;
  force_highlight: number[];
  force_hide: number[];
  force_neutral: number[];
};
const EMPTY: Custom = { force_highlight: [], force_hide: [], force_neutral: [] };

function isCustom(c: Custom): boolean {
  return (
    c.item_rarity_min !== undefined ||
    c.grade_show_min !== undefined ||
    c.grade_beam_min !== undefined ||
    c.weapons !== undefined ||
    c.runeword_bases === true ||
    c.grade_escalation === true ||
    c.force_highlight.length > 0 ||
    c.force_hide.length > 0 ||
    c.force_neutral.length > 0
  );
}

function toggle(list: number[], id: number): number[] {
  return list.includes(id) ? list.filter((x) => x !== id) : [...list, id];
}

export function App() {
  const { surface, toggle: toggleTheme } = useTheme();
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [explain, setExplain] = useState<Explain | null>(null);

  const [flavor, setFlavor] = useState("");
  const [play, setPlay] = useState("");
  const [attr, setAttr] = useState(""); // "" = shape default
  const [explosion, setExplosion] = useState(false);
  const [stage, setStage] = useState("");
  const [c, setC] = useState<Custom>(EMPTY);

  const resetBuild = () => {
    setAttr("");
    setExplosion(false);
    setC(EMPTY);
  };

  const [q, setQ] = useState("");
  const [filter, setFilter] = useState<"all" | "highlight" | "dim" | "neutral">("all");

  useEffect(() => {
    getCatalog()
      .then(setCatalog)
      .catch((e: unknown) => {
        setErr(String(e));
      });
  }, []);

  const opts = catalog?.archetype_options;
  const custom = isCustom(c);
  const ov: Overrides = useMemo(
    () => ({
      element: flavor,
      playstyle: play,
      stage,
      attribute: attr || null,
      explosion,
      item_rarity_min: c.item_rarity_min,
      grade_show_min: c.grade_show_min,
      grade_beam_min: c.grade_beam_min,
      weapons: c.weapons,
      runeword_bases: c.runeword_bases ?? false,
      socket_counts: c.socket_counts ?? null,
      grade_escalation: c.grade_escalation ?? false,
      force_highlight: c.force_highlight,
      force_hide: c.force_hide,
      force_neutral: c.force_neutral,
    }),
    [flavor, play, stage, attr, explosion, c],
  );
  const key =
    flavor && play && stage
      ? `generic_${flavor}_${play}_${stage}::${attr}:${explosion ? "x" : ""}:${custom ? JSON.stringify(c) : ""}`
      : "";
  const baseId = flavor && play && stage ? `generic_${flavor}_${play}_${stage}` : "";

  useEffect(() => {
    if (!flavor || !play || !stage) return;
    let live = true;
    const p = getArchetypeExplainCustom(ov);
    p.then((x) => {
      if (live) setExplain(x);
    }).catch((e: unknown) => {
      if (live) setErr(String(e));
    });
    return () => {
      live = false;
    };
    // `key` already encodes element/playstyle/stage + every tweak
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  const show =
    explain && (explain.id === baseId || explain.id === `${baseId}_custom`) ? explain : null;
  const neutral = show ? 167 - show.highlight.length - show.hide.length : 0;

  const download = () => {
    setBusy(true);
    downloadArchetype(ov, custom)
      .catch((e: unknown) => {
        setErr(String(e));
      })
      .finally(() => {
        setBusy(false);
      });
  };

  const cycleStat = (id: number, cur: string) => {
    setC((prev) => {
      const n = {
        ...prev,
        force_highlight: prev.force_highlight.filter((x) => x !== id),
        force_hide: prev.force_hide.filter((x) => x !== id),
        force_neutral: prev.force_neutral.filter((x) => x !== id),
      };
      // highlight -> dim -> neutral -> (back to compiled default)
      if (cur === "highlight") n.force_hide = [...n.force_hide, id];
      else if (cur === "dim") n.force_neutral = [...n.force_neutral, id];
      // cur === "neutral" -> clear all -> compiled default returns
      return n;
    });
  };

  return (
    <div className="mx-auto max-w-5xl px-6 pt-10 pb-16">
      <header className="flex items-center gap-4 border-b border-line pb-3">
        <span className="font-display text-base font-bold tracking-[0.22em] uppercase">
          hero&nbsp;siege
        </span>
        <span className="ef-label hidden sm:block">{"// loot filter"}</span>
        <span className="flex-1" />
        <span className="ef-mono text-[0.6875rem] text-ink-3">
          {catalog?.game_version ?? "…"}
          {catalog?.build?.sha ? (
            <span className="text-ink-4" title={catalog.build.built || undefined}>
              {" · "}
              {catalog.build.sha}
            </span>
          ) : null}
        </span>
        <ThemeToggle surface={surface} onToggle={toggleTheme} />
      </header>
      <div className="ef-rule--tri" style={{ height: 2 }} />

      <main className="mt-8 flex flex-col gap-8">
        <Slab
          kicker="// LOOT FILTER"
          headline={show ? (show.name.split(" — ")[0] ?? "Filter") : "Pick a build"}
          detail={
            show
              ? `${show.name}${custom ? " · customised" : ""}`
              : "flavor × playstyle × stage → tweak → download"
          }
          watermark="HERO SIEGE"
        />

        {err ? <p className="ef-mono text-sm text-crimson">API error — {err}</p> : null}

        <section>
          <div className="ef-sec-head mb-5">
            <span className="ef-idx">SEC.01</span>
            <h2>Build</h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <Field label="Flavor">
              <select
                className="ef-select"
                value={flavor}
                onChange={(e) => {
                  setFlavor(e.target.value);
                  resetBuild();
                }}
              >
                <option value="">—</option>
                {(opts?.elements ?? []).map((el) => (
                  <option key={el} value={el}>
                    {el}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Playstyle">
              <select
                className="ef-select"
                value={play}
                disabled={!flavor}
                onChange={(e) => {
                  setPlay(e.target.value);
                  resetBuild();
                }}
              >
                <option value="">—</option>
                {(opts?.playstyles ?? []).map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Stage">
              <select
                className="ef-select"
                value={stage}
                disabled={!play}
                onChange={(e) => {
                  setStage(e.target.value);
                }}
              >
                <option value="">—</option>
                {(opts?.stages ?? []).map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          {flavor && play ? (
            <div className="mt-4 flex flex-wrap items-end gap-x-8 gap-y-4">
              <div>
                <span className="ef-label">
                  Main attribute
                  {attr === "" && show ? (
                    <span className="text-ink-4"> · default {show.archetype.attribute}</span>
                  ) : null}
                </span>
                <div className="mt-2 flex flex-wrap gap-1">
                  <button
                    type="button"
                    className="ef-btn"
                    style={
                      attr === ""
                        ? { borderColor: "var(--ef-accent)", color: "var(--ef-accent-ink)" }
                        : undefined
                    }
                    onClick={() => {
                      setAttr("");
                    }}
                  >
                    auto
                  </button>
                  {(opts?.attributes ?? []).map((a) => {
                    const on = attr === a.id || (attr === "" && show?.archetype.attribute === a.id);
                    return (
                      <button
                        key={a.id}
                        type="button"
                        className="ef-btn"
                        style={
                          on
                            ? {
                                borderColor: "var(--ef-accent)",
                                color: attr === a.id ? "var(--ef-accent-ink)" : undefined,
                              }
                            : undefined
                        }
                        onClick={() => {
                          setAttr(a.id);
                        }}
                      >
                        {a.label}
                      </button>
                    );
                  })}
                </div>
              </div>
              <label className="flex cursor-pointer items-center gap-2 pb-1.5">
                <input
                  type="checkbox"
                  checked={explosion}
                  onChange={(e) => {
                    setExplosion(e.target.checked);
                  }}
                />
                <span className="ef-label">Scales explosion skills</span>
              </label>
            </div>
          ) : null}
        </section>

        {show ? (
          <>
            <section>
              <div className="ef-sec-head mb-5">
                <span className="ef-idx">SEC.02</span>
                <h2>Customise</h2>
                {custom ? (
                  <button
                    className="ef-btn ef-btn--ghost ml-3"
                    onClick={() => {
                      setC(EMPTY);
                    }}
                  >
                    reset
                  </button>
                ) : null}
              </div>

              <div className="flex flex-col gap-5">
                <GradeRow
                  label="Hide items below rarity"
                  grades={show.rarities}
                  value={show.rarity.item_min}
                  onPick={(gi) => {
                    setC((prev) => ({ ...prev, item_rarity_min: gi }));
                  }}
                />
                <GradeRow
                  label="Hide affix rolls below grade"
                  grades={show.grades}
                  value={show.rarity.grade_show_min}
                  onPick={(gi) => {
                    setC((prev) => ({
                      ...prev,
                      grade_show_min: gi,
                      grade_beam_min: Math.max(
                        gi,
                        prev.grade_beam_min ?? show.rarity.grade_beam_min,
                      ),
                    }));
                  }}
                />
                <GradeRow
                  label="Beam (chase glow) from grade"
                  grades={show.grades}
                  value={show.rarity.grade_beam_min}
                  minIdx={show.rarity.grade_show_min}
                  onPick={(gi) => {
                    setC((prev) => ({ ...prev, grade_beam_min: gi }));
                  }}
                />
                <p className="ef-mono text-[0.625rem] text-ink-4">
                  item rarity (Common…Satanic) and affix-roll grade (D…S) are separate · below the
                  rarity floor an item never drops · below the grade floor that roll is suppressed ·
                  between grade floor and beam, chase affixes show but don&apos;t glow
                </p>

                <label className="flex cursor-pointer items-center gap-2">
                  <input
                    type="checkbox"
                    checked={c.grade_escalation ?? false}
                    onChange={(e) => {
                      setC((prev) => ({ ...prev, grade_escalation: e.target.checked }));
                    }}
                  />
                  <span className="ef-label">
                    Grade escalation
                    <span className="text-ink-4">
                      {" "}
                      · show off-list stats (no glow) on A/S-grade rolls
                    </span>
                  </span>
                </label>

                <div>
                  <label className="flex cursor-pointer items-center gap-2">
                    <input
                      type="checkbox"
                      checked={c.runeword_bases ?? false}
                      onChange={(e) => {
                        setC((prev) => ({ ...prev, runeword_bases: e.target.checked }));
                      }}
                    />
                    <span className="ef-label">
                      Surface runeword bases
                      <span className="text-ink-4">
                        {" "}
                        · show Common gear + beam socketed bases on{" "}
                        {show.runeword.slots.join(" / ")}
                      </span>
                    </span>
                  </label>
                  {c.runeword_bases ? (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {[2, 3, 4, 5, 6].map((n) => {
                        const cur = c.socket_counts ?? [2, 3, 4, 5, 6];
                        const on = cur.includes(n);
                        return (
                          <button
                            key={n}
                            type="button"
                            className="ef-btn"
                            style={
                              on
                                ? { borderColor: "var(--ef-accent)", color: "var(--ef-accent-ink)" }
                                : { color: "var(--ef-ink-4)", opacity: 0.5 }
                            }
                            onClick={() => {
                              setC((prev) => {
                                const base = prev.socket_counts ?? [2, 3, 4, 5, 6];
                                const next = toggle(base, n).toSorted((a, b) => a - b);
                                return {
                                  ...prev,
                                  socket_counts: next.length > 0 ? next : undefined,
                                };
                              });
                            }}
                          >
                            {n} soc
                          </button>
                        );
                      })}
                      <span className="ef-mono ml-1 self-center text-[0.625rem] text-ink-4">
                        socket count = rune count of the recipe you want
                      </span>
                    </div>
                  ) : null}
                </div>

                <div>
                  <span className="ef-label">Weapon types on the filter</span>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {Object.entries(opts?.weapon_groups ?? {}).map(([name, bits]) => {
                      const cur =
                        c.weapons ??
                        (show.weapon_bits.length === 0
                          ? show.weapon_types.map((_, i) => i)
                          : show.weapon_bits);
                      const active =
                        cur.length === bits.length && bits.every((b) => cur.includes(b));
                      return (
                        <button
                          key={name}
                          className="ef-btn ef-btn--ghost"
                          style={
                            active
                              ? {
                                  borderColor: "var(--ef-accent)",
                                  color: "var(--ef-accent-ink)",
                                }
                              : undefined
                          }
                          onClick={() => {
                            setC((prev) => ({ ...prev, weapons: [...bits] }));
                          }}
                        >
                          {name}
                        </button>
                      );
                    })}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {show.weapon_types.map((w, wi) => {
                      const on =
                        c.weapons !== undefined
                          ? c.weapons.includes(wi)
                          : show.weapon_bits.length === 0 || show.weapon_bits.includes(wi);
                      return (
                        <button
                          key={w}
                          className="ef-btn"
                          style={
                            on
                              ? { borderColor: "var(--ef-accent)" }
                              : { color: "var(--ef-ink-4)", opacity: 0.5 }
                          }
                          onClick={() => {
                            setC((prev) => {
                              const base =
                                prev.weapons ??
                                (show.weapon_bits.length === 0
                                  ? show.weapon_types.map((_, i) => i)
                                  : [...show.weapon_bits]);
                              return { ...prev, weapons: toggle(base, wi) };
                            });
                          }}
                        >
                          {w}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>
            </section>

            <section>
              <div className="ef-sec-head mb-5">
                <span className="ef-idx">SEC.03</span>
                <h2>Filter</h2>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <span className="ef-tag">{show.highlight.length} highlight</span>
                <span className="ef-tag">{show.hide.length} dimmed</span>
                <span className="ef-tag">{neutral} neutral</span>
                <span className="ef-tag">items {show.rarity.item_from}+</span>
                <span className="ef-tag">
                  rolls {show.rarity.show_from}+ · beam {show.rarity.beam_from}+
                </span>
                {show.rarity.item_suppressed.length > 0 ? (
                  <span className="ef-tag" style={{ color: "var(--ef-ink-4)" }}>
                    {show.rarity.item_suppressed.join(" / ")} items off
                  </span>
                ) : null}
                {show.rarity.grade_suppressed.length > 0 ? (
                  <span className="ef-tag" style={{ color: "var(--ef-ink-4)" }}>
                    grade {show.rarity.grade_suppressed.join(" / ")} off
                  </span>
                ) : null}
                {show.weapons ? (
                  <span className="ef-tag">{show.weapons.length} weapon types</span>
                ) : null}
                {show.runeword.on ? (
                  <span className="ef-tag" style={{ borderColor: "var(--ef-accent)" }}>
                    runeword bases · {show.runeword.socket_counts.join("/")} soc
                  </span>
                ) : null}
                {show.grade_escalation ? (
                  <span className="ef-tag" style={{ borderColor: "var(--ef-accent)" }}>
                    grade escalation
                  </span>
                ) : null}
                <span className="flex-1" />
                <button className="ef-btn ef-btn--primary" disabled={busy} onClick={download}>
                  {busy ? <span className="ef-spinner" /> : null}
                  Download filter
                </button>
              </div>

              <p className="ef-mono mt-3 text-xs text-ink-3">{show.notes}</p>

              <div className="mt-6 flex flex-wrap items-center gap-3">
                <input
                  className="ef-input flex-1"
                  style={{ minWidth: "12rem" }}
                  placeholder="search 167 stats… (click a row to change its state)"
                  value={q}
                  onChange={(e) => {
                    setQ(e.target.value);
                  }}
                />
                {(["all", "highlight", "dim", "neutral"] as const).map((f) => (
                  <button
                    key={f}
                    className="ef-btn"
                    aria-pressed={filter === f}
                    style={
                      filter === f
                        ? {
                            borderColor: "var(--ef-accent)",
                            color: "var(--ef-accent-ink)",
                          }
                        : undefined
                    }
                    onClick={() => {
                      setFilter(f);
                    }}
                  >
                    {f}
                  </button>
                ))}
              </div>

              <ul className="mt-4 flex flex-col">
                {show.stats
                  .filter((s) => filter === "all" || s.state === filter)
                  .filter((s) => s.name.toLowerCase().includes(q.toLowerCase()))
                  .map((s) => {
                    const forced =
                      c.force_highlight.includes(s.id) ||
                      c.force_hide.includes(s.id) ||
                      c.force_neutral.includes(s.id);
                    return (
                      <li key={s.id} className="border-b border-line">
                        <button
                          type="button"
                          className="flex w-full items-baseline gap-2 py-1.5 text-left hover:bg-surface-2"
                          onClick={() => {
                            cycleStat(s.id, s.state);
                          }}
                          title="click: highlight → dim → neutral → default"
                        >
                          <span
                            className="ef-diamond mt-1.5 shrink-0"
                            data-active={s.state === "highlight" ? "" : undefined}
                            style={
                              s.state === "dim"
                                ? { opacity: 0.3 }
                                : s.state === "neutral"
                                  ? { opacity: 0.55 }
                                  : undefined
                            }
                          />
                          <span
                            className="text-sm"
                            style={{
                              color: s.state === "dim" ? "var(--ef-ink-4)" : "var(--ef-ink)",
                            }}
                          >
                            {s.name}
                            {forced ? " *" : ""}
                          </span>
                          <span className="ef-mono ml-2 text-[0.5625rem] text-ink-4">
                            {s.state === "highlight"
                              ? "◆ glow"
                              : s.state === "dim"
                                ? "· dim"
                                : "  —"}
                          </span>
                          <span className="flex-1" />
                          <span className="ef-mono text-[0.625rem] text-ink-4">{s.why}</span>
                        </button>
                      </li>
                    );
                  })}
              </ul>

              <details className="mt-6">
                <summary className="ef-label cursor-pointer">How to import</summary>
                <ol className="ef-mono mt-2 flex list-decimal flex-col gap-1 pl-5 text-xs text-ink-2">
                  <li>
                    Save it to <code>%localappdata%/Hero_Siege/hs2saves/</code> (Linux:{" "}
                    <code>~/.config/Hero_Siege/hs2saves/</code>).
                  </li>
                  <li>In-game loot filter window → pick it from the list.</li>
                </ol>
              </details>
            </section>
          </>
        ) : null}
      </main>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="ef-field">
      <span className="ef-label">{label}</span>
      {children}
    </label>
  );
}

function GradeRow({
  label,
  grades,
  value,
  minIdx = 0,
  onPick,
}: {
  label: string;
  grades: string[];
  value: number;
  minIdx?: number;
  onPick: (gi: number) => void;
}) {
  return (
    <div>
      <span className="ef-label">{label}</span>
      <div className="mt-2 flex flex-wrap gap-1">
        {grades.map((g, gi) => {
          const disabled = gi < minIdx;
          return (
            <button
              key={g}
              type="button"
              className="ef-btn"
              disabled={disabled}
              style={
                gi === value
                  ? { borderColor: "var(--ef-accent)", color: "var(--ef-accent-ink)" }
                  : disabled
                    ? { opacity: 0.3 }
                    : undefined
              }
              onClick={() => {
                onPick(gi);
              }}
            >
              {g}
            </button>
          );
        })}
      </div>
    </div>
  );
}
