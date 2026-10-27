// Chart colours for light and dark mode (validated reference palette: blue series + fixed status colours).
import { useEffect, useState } from "react";

const LIGHT = {
  series: "#2a78d6", // single-series blue
  passed: "#0ca30c", // status: good
  failed: "#d03b3b", // status: critical
  grid: "#e2e8f0",
  axis: "#64748b",
  text: "#334155",
  surface: "#ffffff",
};

const DARK = {
  series: "#3987e5",
  passed: "#0ca30c",
  failed: "#d03b3b",
  grid: "#1e293b",
  axis: "#94a3b8",
  text: "#cbd5e1",
  surface: "#0f172a",
};

// Re-renders charts when the theme toggle adds or removes the "dark" class.
export function useChartColors() {
  const isDark = () => document.documentElement.classList.contains("dark");
  const [dark, setDark] = useState(isDark);
  useEffect(() => {
    const observer = new MutationObserver(() => setDark(isDark()));
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);
  return dark ? DARK : LIGHT;
}
