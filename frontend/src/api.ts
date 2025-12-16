export type AuthResponse = { access_token: string; token_type: string };

const API_BASE =
  (import.meta as any).env?.VITE_API_BASE_URL?.toString() || "http://localhost:8000";

function authHeaders(token: string | null): HeadersInit {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function signup(username: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function login(username: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export type ChatUsage = {
  agent?: string;
  input_tokens?: number;
  output_tokens?: number;
  total_tokens?: number;
  model?: string;
};

export type ChatExpense = {
  total?: Omit<ChatUsage, "agent" | "model"> | null;
  breakdown: ChatUsage[];
};

export type ChatResponse = { reply: string; expense?: ChatExpense | null };

export async function chat(message: string, token: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export type PlaylistItem = { id: number; name: string; description: string };

export async function listPlaylists(token: string): Promise<PlaylistItem[]> {
  const res = await fetch(`${API_BASE}/playlists`, { headers: { ...authHeaders(token) } });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function addPlaylist(
  token: string,
  name: string,
  description: string,
): Promise<PlaylistItem> {
  const res = await fetch(`${API_BASE}/playlists`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({ name, description }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}


