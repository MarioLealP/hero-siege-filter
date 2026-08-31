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
  getArchetypeExplain,
  getArchetypeExplainCustom,
  getCatalog,
} from "@/api";

type Custom = {
  rarity_min_show?: number;
  rarity_min_highlight?: number;
  weapons?: number[];
  force_highlight: number[];
  force_hide: number[];
  force_neutral: number[];
};
const EMPTY: Custom = { force_highlight: [], force_hide: [], force_neutral: [] };

function isCustom(c: Custom): boolean {
  return (
    c.rarity_min_show !== undefined ||
    c.rarity_min_highlight !== undefined ||
    c.weapons !== undefined ||
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
  const [stage, setStage] = useState("nightmare");
  const [c, setC] = useState<Custom>(EMPTY);

  const [q, setQ] = useState("");
  const [filter, setFilter] = useState<"all" | "highlight" | "dim" | "neutral">("all");

  useEffect(() => {
    getCatalog().then(setCatalog).catch((e: unknown) => {
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
      rarity_min_show: c.rarity_min_show,
      rarity_min_highlight: c.rarity_min_highlight,
      weapons: c.weapons,
      force_highlight: c.force_highlight,
      force_hide: c.force_hide,
      force_neutral: c.force_neutral,
    }),
    [flavor, play, stage, c],
  );
  const key =
    flavor && play
      ? `generic_${flavor}_${play}_${stage}::${custom ? JSON.stringify(c) : ""}`
      : "";
  const baseId = flavor && play ? `generic_${flavor}_${play}_${stage}` : "";

  useEffect(() => {
    if (!flavor || !play) return;
    let live = true;
    const p = custom
      ? getArchetypeExplainCustom(ov)
      : getArchetypeExplain(flavor, play, stage);
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

  const show = explain && (explain.id === baseId || explain.id === `${baseId}_custom`) ? explain : null;
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

        {err ? (
          <p className="ef-mono text-sm text-crimson">API error — {err}</p>
        ) : null}

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
                  setC(EMPTY);
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
                  setC(EMPTY);
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
                  setC(EMPTY);
                }}
              >
                {(opts?.stages ?? []).map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
            </Field>
          </div>
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
                  label="Won't drop below"
                  grades={show.grades}
                  value={show.rarity.min_show}
                  onPick={(gi) => {
                    setC((prev) => ({
                      ...prev,
                      rarity_min_show: gi,
                      rarity_min_highlight: Math.max(
                        gi,
                        prev.rarity_min_highlight ?? show.rarity.min_highlight,
                      ),
                    }));
                  }}
                />
                <GradeRow
                  label="Beam (chase glow) from"
                  grades={show.grades}
                  value={show.rarity.min_highlight}
                  minIdx={show.rarity.min_show}
                  onPick={(gi) => {
                    setC((prev) => ({ ...prev, rarity_min_highlight: gi }));
                  }}
                />
                <p className="ef-mono text-[0.625rem] text-ink-4">
                  below the drop floor an item won&apos;t appear at all · between
                  the two, chase affixes are visible but not beamed
                </p>

                <div>
                  <span className="ef-label">Weapon types on the filter</span>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {Object.entries(opts?.weapon_groups ?? {}).map(
                      ([name, bits]) => {
                        const cur =
                          c.weapons ??
                          (show.weapon_bits.length === 0
                            ? show.weapon_types.map((_, i) => i)
                            : show.weapon_bits);
                        const active =
                          cur.length === bits.length &&
                          bits.every((b) => cur.includes(b));
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
                      },
                    )}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {show.weapon_types.map((w, wi) => {
                      const on =
                        c.weapons !== undefined
                          ? c.weapons.includes(wi)
                          : show.weapon_bits.length === 0 ||
                            show.weapon_bits.includes(wi);
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
                <span className="ef-tag">beam ≥ {show.rarity.beam_from}</span>
                {show.rarity.suppressed.length > 0 ? (
                  <span className="ef-tag" style={{ color: "var(--ef-ink-4)" }}>
                    {show.rarity.suppressed.join(" / ")} off
                  </span>
                ) : null}
                {show.weapons ? (
                  <span className="ef-tag">
                    {show.weapons.length} weapon types
                  </span>
                ) : null}
                <span className="flex-1" />
                <button
                  className="ef-btn ef-btn--primary"
                  disabled={busy}
                  onClick={download}
                >
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
                            color:
                              s.state === "dim"
                                ? "var(--ef-ink-4)"
                                : "var(--ef-ink)",
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
                        <span className="ef-mono text-[0.625rem] text-ink-4">
                          {s.why}
                        </span>
                        </button>
                      </li>
                    );
                  })}
              </ul>

              <details className="mt-6">
                <summary className="ef-label cursor-pointer">How to import</summary>
                <ol className="ef-mono mt-2 flex list-decimal flex-col gap-1 pl-5 text-xs text-ink-2">
                  <li>
                    Save it to <code>%localappdata%/Hero_Siege/hs2saves/</code>{" "}
                    (Linux: <code>~/.config/Hero_Siege/hs2saves/</code>).
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
