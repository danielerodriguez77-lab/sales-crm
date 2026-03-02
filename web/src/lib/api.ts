const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export type ApiOptions = RequestInit & { token?: string };

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Error ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function apiForm<T>(path: string, body: URLSearchParams): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded"
    },
    body
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Error ${response.status}`);
  }
  return response.json() as Promise<T>;
}
