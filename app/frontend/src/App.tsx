import type { ReactNode } from "react";
import { useEffect, useState } from "react";

import { Slab } from "@/components/Slab";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useTheme } from "@/lib/useTheme";
import {
  type Catalog,
  type Explain,
  downloadArchetype,
  getArchetypeExplain,
  getCatalog,
} from "@/api";

export function App() {
  const { surface, toggle } = useTheme();
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [explain, setExplain] = useState<Explain | null>(null);

  const [flavor, setFlavor] = useState("");
  const [play, setPlay] = useState("");
  const [stage, setStage] = useState("nightmare");

  const [q, setQ] = useState("");
  const [filter, setFilter] = useState<"all" | "highlight" | "dim" | "neutral">("all");

  useEffect(() => {
    getCatalog().then(setCatalog).catch((e: unknown) => {
      setErr(String(e));
    });
  }, []);

  const opts = catalog?.archetype_options;
  const key = flavor && play ? `generic_${flavor}_${play}_${stage}` : "";

  useEffect(() => {
    if (!key) return;
    let live = true;
    getArchetypeExplain(flavor, play, stage)
      .then((x) => {
        if (live) setExplain(x);
      })
      .catch((e: unknown) => {
        if (live) setErr(String(e));
      });
    return () => {
      live = false;
    };
  }, [key, flavor, play, stage]);

  const show = explain && explain.id === key ? explain : null;
  const neutral = show ? 167 - show.highlight.length - show.hide.length : 0;

  const download = () => {
    setBusy(true);
    downloadArchetype(flavor, play, stage)
      .catch((e: unknown) => {
        setErr(String(e));
      })
      .finally(() => {
        setBusy(false);
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
        <ThemeToggle surface={surface} onToggle={toggle} />
      </header>
      <div className="ef-rule--tri" style={{ height: 2 }} />

      <main className="mt-8 flex flex-col gap-8">
        <Slab
          kicker="// LOOT FILTER"
          headline={show ? (show.name.split(" — ")[0] ?? "Filter") : "Pick a build"}
          detail={show ? show.name : "flavor × playstyle × stage → download"}
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
          <section>
            <div className="ef-sec-head mb-5">
              <span className="ef-idx">SEC.02</span>
              <h2>Filter</h2>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <span className="ef-tag">{show.highlight.length} highlight</span>
              <span className="ef-tag">{show.hide.length} dimmed</span>
              <span className="ef-tag">{neutral} neutral</span>
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

            <div className="mt-4 flex flex-wrap gap-2">
              <span className="ef-tag">
                beam ≥ {show.rarity.beam_from}
              </span>
              {show.rarity.suppressed.length > 0 ? (
                <span className="ef-tag" style={{ color: "var(--ef-ink-4)" }}>
                  {show.rarity.suppressed.join(" / ")} suppressed
                </span>
              ) : (
                <span className="ef-tag">all grades drop</span>
              )}
              {show.weapons ? (
                <span className="ef-tag">weapons: {show.weapons.join(", ")}</span>
              ) : null}
            </div>

            <p className="ef-mono mt-3 text-xs text-ink-3">{show.notes}</p>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <input
                className="ef-input flex-1"
                style={{ minWidth: "12rem" }}
                placeholder="search 167 stats…"
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
                  data-on={filter === f ? "" : undefined}
                  style={filter === f ? { borderColor: "var(--ef-accent)", color: "var(--ef-accent-ink)" } : undefined}
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
                .map((s) => (
                  <li
                    key={s.id}
                    className="flex items-baseline gap-2 border-b border-line py-1.5"
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
                      style={{ color: s.state === "dim" ? "var(--ef-ink-4)" : "var(--ef-ink)" }}
                    >
                      {s.name}
                    </span>
                    <span className="ef-mono ml-2 text-[0.5625rem] text-ink-4">
                      {s.state === "highlight" ? "◆ glow" : s.state === "dim" ? "· dim" : "  —"}
                    </span>
                    <span className="flex-1" />
                    <span className="ef-mono text-[0.625rem] text-ink-4">{s.why}</span>
                  </li>
                ))}
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

