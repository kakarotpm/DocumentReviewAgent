// Light / dark / system theme, remembered in this browser.
import { useEffect, useState } from "react";

const KEY = "docreview.theme";
const ORDER = ["system", "light", "dark"];

function readTheme() {
  try {
    return localStorage.getItem(KEY) || "system";
  } catch {
    return "system";
  }
}

function apply(theme) {
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  document.documentElement.classList.toggle("dark", theme === "dark" || (theme === "system" && prefersDark));
}

export function useTheme() {
  const [theme, setTheme] = useState(readTheme);

  useEffect(() => {
    apply(theme);
    try {
      localStorage.setItem(KEY, theme);
    } catch {
      // Storage blocked: the choice lasts until the page is closed.
    }
    if (theme !== "system") return;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => apply("system");
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, [theme]);

  const cycle = () => setTheme(ORDER[(ORDER.indexOf(theme) + 1) % ORDER.length]);
  return { theme, cycle };
}
