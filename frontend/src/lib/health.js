// Whether the backend has an AI key, and which AI (provider and model) it uses. Loaded once by the app shell and shared with every page.
import { createContext, useContext } from "react";

export const HealthContext = createContext({ aiAvailable: true, model: "", provider: "" });

export function useHealth() {
  return useContext(HealthContext);
}
