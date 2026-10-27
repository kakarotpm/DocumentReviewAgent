// Talking to the backend. Every error becomes an ApiError with a message that's safe to show users.
import { useCallback, useEffect, useState } from "react";

export class ApiError extends Error {
  constructor(message, errors = [], status = 0) {
    super(message);
    this.errors = errors; // extra detail lines, e.g. each problem in an uploaded rulebook
    this.status = status;
  }
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(path, options);
  } catch {
    throw new ApiError("Can't reach the server. Check the backend is running, then try again.");
  }
  const isJson = (response.headers.get("content-type") || "").includes("application/json");
  const body = isJson ? await response.json() : await response.text();
  if (response.ok) return body;

  const detail = isJson ? body.detail : null;
  if (typeof detail === "string") throw new ApiError(detail, [], response.status);
  if (detail && detail.message) throw new ApiError(detail.message, detail.errors || [], response.status);
  if (Array.isArray(detail)) {
    const lines = detail.map((d) => `${d.loc.slice(1).join(" → ")}: ${d.msg}`);
    throw new ApiError("Some information is missing or invalid.", lines, response.status);
  }
  throw new ApiError(`Something went wrong on the server (error ${response.status}). Please try again.`, [], response.status);
}

function sendJson(method, path, data) {
  return request(path, { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
}

export const api = {
  get: (path) => request(path),
  post: (path, data) => sendJson("POST", path, data),
  put: (path, data) => sendJson("PUT", path, data),
  patch: (path, data) => sendJson("PATCH", path, data),
  upload: (path, formData) => request(path, { method: "POST", body: formData }),
};

// Load data for a page: { data, error, loading, reload }. Pass null to skip loading.
export function useFetch(path) {
  const [state, setState] = useState({ data: null, error: null, loading: Boolean(path) });

  const reload = useCallback(() => {
    if (!path) return;
    setState((s) => ({ ...s, loading: true, error: null }));
    api
      .get(path)
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => setState({ data: null, error, loading: false }));
  }, [path]);

  useEffect(reload, [reload]);
  return { ...state, reload };
}
