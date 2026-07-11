export const DEFAULT_THEME = {
  slide: { width: 13.333, height: 7.5, margin: 0.55 },
  colors: { ink: "172033", muted: "5E6B7A", paper: "F7F4ED", surface: "FFFFFF", accent: "E05A47", accent2: "1B7F79", line: "D7D9DD" },
  fonts: { head: "Microsoft YaHei", body: "Microsoft YaHei", mono: "Consolas" },
  sizes: { hero: 30, title: 24, body: 15, small: 10, metric: 28 },
  radius: 0.12,
  gap: 0.28
};

export function mergeTheme(overrides: any = {}) {
  return { ...DEFAULT_THEME, ...overrides, slide: { ...DEFAULT_THEME.slide, ...(overrides.slide || {}) }, colors: { ...DEFAULT_THEME.colors, ...(overrides.colors || {}) }, fonts: { ...DEFAULT_THEME.fonts, ...(overrides.fonts || {}) }, sizes: { ...DEFAULT_THEME.sizes, ...(overrides.sizes || {}) } };
}

