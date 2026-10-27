// Small helpers for showing values consistently.

const NAME_KEY = "docreview.name";

// The server stores times in UTC without a time zone marker; add it so the browser shows local time.
// Plain dates ("2026-10-21") are left as they are.
function parse(value) {
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return new Date(`${value}T00:00:00`);
  const iso = String(value).replace(" ", "T");
  return new Date(/[zZ]|[+-]\d{2}:?\d{2}$/.test(iso) ? iso : `${iso}Z`);
}

export function formatDate(value) {
  if (!value) return "";
  return parse(value).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

export function formatDateTime(value) {
  if (!value) return "";
  return parse(value).toLocaleString(undefined, {
    day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

export function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// US dollars. Small amounts keep more decimals so a single review's cost (often under a cent) isn't shown as $0.00.
export function formatCost(dollars) {
  if (dollars == null) return "—";
  if (dollars === 0) return "$0";
  if (dollars < 0.01) return `$${dollars.toFixed(4)}`;
  if (dollars < 100) return `$${dollars.toFixed(2)}`;
  return `$${Math.round(dollars).toLocaleString()}`;
}

// 1234 -> "1.2K", 3456789 -> "3.5M"
export function formatTokens(tokens) {
  if (tokens == null) return "—";
  if (tokens < 1000) return String(tokens);
  if (tokens < 1_000_000) return `${(tokens / 1000).toFixed(1)}K`;
  return `${(tokens / 1_000_000).toFixed(1)}M`;
}

export function formatPoints(points) {
  return Number.isInteger(points) ? String(points) : points.toFixed(1);
}

export const WEIGHT_LABELS = { high: "High", medium: "Medium", low: "Low" };
export const WEIGHT_POINTS = { high: 3, medium: 2, low: 1 };

// Part A rules check the uploaded document; Part B rules check an optional Excel workbook.
export const PARTS = [
  { id: "document", label: "Part A: Document rules", short: "Document" },
  { id: "excel", label: "Part B: Excel rules", short: "Excel workbook" },
];

// The user's name is remembered in this browser so they don't retype it on every form.
export function savedName() {
  try {
    return localStorage.getItem(NAME_KEY) || "";
  } catch {
    return "";
  }
}

export function rememberName(name) {
  try {
    localStorage.setItem(NAME_KEY, name.trim());
  } catch {
    // Storage blocked: the name just won't be remembered.
  }
}

// "Data Migration Plan" -> "data_migration_plan" (matches the backend's key_from_name).
export function keyFromName(name) {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "") || "custom";
}

// "Data Migration Plan" -> "DMP", used for rule IDs like DMP-01.
export function idPrefix(name) {
  const initials = (name.match(/[A-Za-z]+/g) || []).map((w) => w[0]).join("").toUpperCase().slice(0, 4);
  return initials || "CUS";
}

// The next free rule ID, e.g. BRD-11 after BRD-10. Excel rules (Part B) are numbered separately: FRD-XL-03.
export function nextRuleId(rules, fallbackPrefix, part = "document") {
  const base = rules.length ? rules[0].id.split("-")[0] : fallbackPrefix;
  const prefix = part === "excel" ? `${base}-XL` : base;
  const numbers = rules
    .map((r) => r.id.slice(prefix.length + 1))
    .filter((rest, i) => rules[i].id.startsWith(prefix + "-") && /^\d+$/.test(rest))
    .map(Number);
  const next = (numbers.length ? Math.max(...numbers) : 0) + 1;
  return `${prefix}-${String(next).padStart(2, "0")}`;
}
