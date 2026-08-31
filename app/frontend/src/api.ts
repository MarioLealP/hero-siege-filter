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
  builds: { build_id: string; class: string; skill: string; stage: string; element: string; name: string }[];
  archetype_options: {
    elements: string[];
    playstyles: { id: string; label: string }[];
    stages: string[];
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
  rarity: { beam_from: string; drop_from: string; suppressed: string[] };
  weapons: string[] | null;
  highlight: StatLine[];
  hide: StatLine[];
  stats: StatRow[];
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

export const downloadArchetype = (el: string, play: string, stage: string) =>
  fetch(`/api/archetype/${el}/${play}/${stage}/filter`).then((r) =>
    saveBlob(r, `lootfilter_generic_${el}_${play}_${stage}.txt`),
  );
