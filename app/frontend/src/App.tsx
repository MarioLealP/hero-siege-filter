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

const STAGE_LABEL: Record<string, string> = {
  leveling: "Leveling · 1–100",
  maps: "Maps · Inferno",
  endgame: "Endgame · Wormholes",
};

export function App() {
  const { surface, toggle } = useTheme();
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [explain, setExplain] = useState<Explain | null>(null);

  const [flavor, setFlavor] = useState("");
  const [play, setPlay] = useState("");
  const [stage, setStage] = useState("leveling");

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
                {(opts?.stages ?? ["leveling", "maps", "endgame"]).map((s) => (
                  <option key={s} value={s}>
                    {STAGE_LABEL[s] ?? s}
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

            <p className="ef-mono mt-4 text-xs text-ink-3">{show.notes}</p>

            <div className="mt-6 grid gap-8 lg:grid-cols-2">
              <StatList title="Highlight" accent="green" lines={show.highlight} />
              <StatList title="Dim" accent="ink-4" lines={show.hide} />
            </div>

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

function StatList({
  title,
  accent,
  lines,
}: {
  title: string;
  accent: string;
  lines: Explain["highlight"];
}) {
  return (
    <div>
      <div className="ef-sec-head mb-3">
        <span className="ef-idx" style={{ color: `var(--ef-${accent})` }}>
          {lines.length.toString().padStart(2, "0")}
        </span>
        <h2>{title}</h2>
      </div>
      <ul className="flex flex-col">
        {lines.map((l) => (
          <li
            key={l.id}
            className="flex items-baseline gap-2 border-b border-line py-1.5"
          >
            <span
              className="ef-diamond mt-1.5 shrink-0"
              data-active={accent === "green" ? "" : undefined}
            />
            <span className="text-sm text-ink">{l.name}</span>
            <span className="flex-1" />
            <span className="ef-mono text-[0.625rem] text-ink-4">{l.why}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
