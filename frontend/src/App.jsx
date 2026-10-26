// The app shell: sidebar navigation, demo-mode banner, and the current page.
import { NavLink, Outlet } from "react-router-dom";
import Icon from "./components/Icon";
import { ErrorMessage } from "./components/ui";
import { useFetch } from "./lib/api";
import { HealthContext } from "./lib/health";
import { useTheme } from "./lib/theme";

const NAV = [
  { to: "/", label: "Dashboard", icon: "dashboard", end: true },
  { to: "/new-review", label: "New Review", icon: "plus" },
  { to: "/documents", label: "Documents", icon: "folder" },
  { to: "/rulebooks", label: "Rulebooks", icon: "book" },
];

const THEME_LABEL = { system: "System theme", light: "Light theme", dark: "Dark theme" };
const THEME_ICON = { system: "monitor", light: "sun", dark: "moon" };

export default function App() {
  const health = useFetch("/api/health");
  const { theme, cycle } = useTheme();
  const aiAvailable = health.data ? health.data.api_key_configured : true;

  return (
    <HealthContext.Provider value={{ aiAvailable, model: health.data?.model || "", provider: health.data?.provider || "" }}>
      <div className="min-h-screen md:flex">
        <aside className="border-b border-slate-200 bg-white md:fixed md:inset-y-0 md:flex md:w-60 md:flex-col md:border-b-0 md:border-r dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between px-5 py-4 md:block">
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white">
                <Icon name="check" />
              </span>
              <span className="text-lg font-semibold text-slate-900 dark:text-slate-50">DocReview</span>
            </div>
          </div>
          <nav className="flex gap-1 overflow-x-auto px-3 pb-3 md:flex-1 md:flex-col md:overflow-visible md:pb-0">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `flex items-center gap-3 whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300"
                      : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
                  }`
                }
              >
                <Icon name={item.icon} />
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="hidden border-t border-slate-200 p-3 md:block dark:border-slate-800">
            <button
              type="button"
              onClick={cycle}
              className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              title="Switch between system, light and dark"
            >
              <Icon name={THEME_ICON[theme]} />
              {THEME_LABEL[theme]}
            </button>
          </div>
        </aside>

        <div className="min-w-0 flex-1 md:pl-60">
          {health.error && (
            <div className="px-4 pt-4 md:px-8">
              <ErrorMessage error={health.error} title="The backend isn't responding" onRetry={health.reload} />
            </div>
          )}
          {!aiAvailable && (
            <div className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-900 md:px-8 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
              <strong>Demo mode:</strong> no AI key is set, so reviews use simple keyword matching instead of AI.
              Add <code className="rounded bg-amber-100 px-1 dark:bg-amber-900/60">ANTHROPIC_API_KEY</code> to the .env file and
              restart the backend for real reviews.
            </div>
          )}
          <main className="mx-auto max-w-6xl px-4 py-6 md:px-8 md:py-8">
            <Outlet />
          </main>
        </div>
      </div>
    </HealthContext.Provider>
  );
}
