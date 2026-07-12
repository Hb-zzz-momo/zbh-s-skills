import fs from "node:fs";
import { mergeTheme } from "./theme.ts";

export function parsePresentationDesign(file: string) {
  const text = fs.readFileSync(file, "utf8");
  const fenced = text.match(/```presentation-theme\s*\r?\n([\s\S]*?)```/i) || text.match(/```json\s*\r?\n([\s\S]*?)```/i);
  if (!fenced) throw new Error(`PRESENTATION_DESIGN.md must contain a fenced presentation-theme JSON block: ${file}`);
  let data: any;
  try { data = JSON.parse(fenced[1]); } catch (error: any) { throw new Error(`Invalid presentation-theme JSON: ${error.message}`); }
  const required = ["colors", "fonts", "sizes", "slide", "layout_families", "forbidden_patterns", "motif"];
  for (const key of required) if (!(key in data)) throw new Error(`PRESENTATION_DESIGN missing ${key}`);
  for (const [name, value] of Object.entries(data.colors || {})) if (!/^[0-9A-F]{6}$/i.test(String(value))) throw new Error(`Invalid color token ${name}: ${value}`);
  return { theme: mergeTheme(data), contract: data };
}
