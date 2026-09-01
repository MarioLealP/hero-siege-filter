export interface CatalogBuild {
  build: string;
  skill: string;
  tree: string;
  element: string;
  stages: string[];
}
export interface CatalogClass {
  name: string;
  trees: string[];
  builds: CatalogBuild[];
}
export interface Catalog {
  game_version: string;
  archetypes: string[];
  classes: CatalogClass[];
  builds: {
    build_id: string;
    class: string;
    skill: string;
    stage: string;
    element: string;
    name: string;
  }[];
  archetype_options: {
    elements: string[];
    playstyles: { id: string; label: string }[];
    attributes: { id: string; label: string }[];
    stages: { id: string; label: string }[];
    weapon_groups: Record<string, number[]>;
  };
}

export interface StatLine {
  id: number;
  name: string;
  why: string | null;
}
export type StatState = "highlight" | "dim" | "neutral";
export interface StatRow extends StatLine {
  col: number;
  state: StatState;
}
export interface Explain {
  id: string;
  name: string;
  notes: string;
  grades: string[];
  rarities: string[];
  archetype: { attribute: string | null; explosion: boolean };
  runeword: { on: boolean; socket_counts: number[]; slots: string[] };
  weapon_types: string[];
  rarity: {
    item_min: number;
    item_from: string;
    item_suppressed: string[];
    grade_show_min: number;
    grade_beam_min: number;
    show_from: string;
    beam_from: string;
    grade_suppressed: string[];
  };
  weapon_bits: number[];
  weapons: string[] | null;
  highlight: StatLine[];
  hide: StatLine[];
  stats: StatRow[];
}

export interface Overrides {
  element: string;
  playstyle: string;
  stage: string;
  attribute?: string | null;
  explosion?: boolean;
  item_rarity_min?: number;
  grade_show_min?: number;
  grade_beam_min?: number;
  weapons?: number[];
  runeword_bases?: boolean;
  socket_counts?: number[] | null;
  force_highlight?: number[];
  force_hide?: number[];
  force_neutral?: number[];
}

async function j<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, init);
  if (!r.ok) throw new Error(`${r.status} ${(await r.text()).slice(0, 200)}`);
  return r.json() as Promise<T>;
}

export const getCatalog = () => j<Catalog>("/api/catalog");
export const getExplain = (buildId: string) => j<Explain>(`/api/filter/${buildId}/explain`);
export const getArchetypeExplain = (el: string, play: string, stage: string) =>
  j<Explain>(`/api/archetype/${el}/${play}/${stage}/explain`);

export const getArchetypeExplainCustom = (ov: Overrides) =>
  j<Explain>("/api/archetype/explain", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(ov),
  });

async function saveBlob(r: Response, filename: string): Promise<void> {
  if (!r.ok) throw new Error(`${r.status} ${(await r.text()).slice(0, 200)}`);
  const url = URL.createObjectURL(await r.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.append(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export async function downloadFilter(buildId: string): Promise<void> {
  const r = await fetch("/api/filter", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ build_id: buildId }),
  });
  await saveBlob(r, `lootfilter_${buildId}.txt`);
}

export const downloadArchetype = (ov: Overrides, custom: boolean) => {
  const a = ov.attribute ? `_${ov.attribute.slice(0, 3)}` : "";
  const x = ov.explosion ? "_expl" : "";
  const rw = ov.runeword_bases ? "_rw" : "";
  const name = `lootfilter_generic_${ov.element}_${ov.playstyle}${a}${x}${rw}_${ov.stage}${
    custom ? "_custom" : ""
  }.txt`;
  const req = fetch("/api/archetype/filter", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(ov),
  });
  return req.then((r) => saveBlob(r, name));
};
