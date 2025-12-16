import { useEffect, useMemo, useState } from "react";
import {
  chat,
  listPlaylists,
  login,
  signup,
  type ChatExpense,
  type PlaylistItem,
} from "./api";

type Msg = { role: "user" | "assistant"; content: string };
type Typing = { role: "typing"; content: "" };

const TOKEN_KEY = "music_agent_token";
const USERNAME_KEY = "music_agent_username";

export default function App() {
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [username, setUsername] = useState(localStorage.getItem(USERNAME_KEY) || "");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState<string | null>(localStorage.getItem(TOKEN_KEY));

  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [playlists, setPlaylists] = useState<PlaylistItem[]>([]);
  const [lastExpense, setLastExpense] = useState<ChatExpense | null>(null);

  const isAuthed = useMemo(() => Boolean(token), [token]);
  const roleLabel = (role: "user" | "assistant" | "typing") =>
    role === "user" ? username || "Usuario" : "MusicBot";

  const agentLabel = (agent?: string) => {
    const a = (agent || "").trim();
    if (!a) return "Agente";
    if (a === "main_agent") return "Agente Principal (MusicBot)";
    if (a === "context_agent") return "Subagente de contexto";
    return a;
  };

  useEffect(() => {
    if (!token) return;
    (async () => {
      try {
        const p = await listPlaylists(token);
        setPlaylists(p);
        setMessages([]);
      } catch (e: any) {
        setError(e?.message || String(e));
      }
    })();
  }, [token]);

  async function onAuthSubmit() {
    setError(null);
    setBusy(true);
    try {
      const res = mode === "login" ? await login(username, password) : await signup(username, password);
      localStorage.setItem(TOKEN_KEY, res.access_token);
      localStorage.setItem(USERNAME_KEY, username);
      setToken(res.access_token);
      setPassword("");
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setBusy(false);
    }
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setMessages([]);
    setPlaylists([]);
    setLastExpense(null);
  }

  async function send() {
    if (!token) return;
    const text = input.trim();
    if (!text) return;

    setError(null);
    setBusy(true);
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    try {
      const res = await chat(text, token);
      setMessages((m) => [...m, { role: "assistant", content: res.reply }]);
      setLastExpense(res.expense || null);
      setPlaylists(await listPlaylists(token));
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setBusy(false);
    }
  }

  if (!isAuthed) {
    return (
      <div className="page">
        <div className="card">
          <h1>Music Agent</h1>
          <p className="muted">Login / Signup para guardar tu memoria (para el modelo) y playlists.</p>

          <div className="row">
            <button className={mode === "login" ? "primary" : ""} onClick={() => setMode("login")}>
              Login
            </button>
            <button className={mode === "signup" ? "primary" : ""} onClick={() => setMode("signup")}>
              Signup
            </button>
          </div>

          <label>
            Usuario
            <input value={username} onChange={(e) => setUsername(e.target.value)} />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => (e.key === "Enter" ? onAuthSubmit() : null)}
            />
          </label>

          <button className="primary" disabled={busy} onClick={onAuthSubmit}>
            {busy ? "..." : mode === "login" ? "Entrar" : "Crear cuenta"}
          </button>

          {error ? <pre className="error">{error}</pre> : null}
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="topbar">
        <div>
          <strong>Music Agent</strong> <span className="muted">({username})</span>
        </div>
        <button onClick={logout}>Logout</button>
      </div>

      <div className="grid">
        <div className="card chat">
          <h2>Chat</h2>
          <p className="muted small">Tip: si necesitás ayuda escribí <code>help</code> para ver comandos.</p>
          <div className="messages">
            {messages.map((m, idx) => (
              <div key={idx} className={`msg ${m.role}`}>
                <div className="role">{roleLabel(m.role)}</div>
                <div className="content">{m.content}</div>
              </div>
            ))}

            {busy ? (
              <div className="msg typing">
                <div className="role">{roleLabel("typing")}</div>
                <div className="content">
                  <span className="typingDots" aria-label="Cargando">
                    <span className="dot" />
                    <span className="dot" />
                    <span className="dot" />
                  </span>
                </div>
              </div>
            ) : null}
          </div>

          <div className="composer">
            <input
              placeholder="Escribí tu mensaje…"
              value={input}
              disabled={busy}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => (e.key === "Enter" ? send() : null)}
            />
            <button className="primary" disabled={busy} onClick={send}>
              Enviar
            </button>
          </div>

          {error ? <pre className="error">{error}</pre> : null}
        </div>

        <div className="card side">
          <h2>Playlists</h2>
          <p className="muted small">Estas playlists se editan solo por chat (pedile al agente que las agregue/edite/borrre).</p>
          <div className="list">
            {playlists.length === 0 ? <div className="muted">Sin playlists todavía.</div> : null}
            {playlists.map((p) => (
              <div key={p.id} className="item">
                <div className="itemTitle">{p.name}</div>
                <div className="muted small">{p.description}</div>
              </div>
            ))}
          </div>

          <h2>Gasto de la última consulta</h2>
          <div className="list">
            {!lastExpense ? (
              <div className="muted">Todavía no hay datos de gasto.</div>
            ) : (
              <>
                {lastExpense.total ? (
                  <div className="item">
                    <div className="itemTitle">Total</div>
                    <div className="muted small">
                      input {lastExpense.total.input_tokens ?? "-"} · output {lastExpense.total.output_tokens ?? "-"} · total{" "}
                      {lastExpense.total.total_tokens ?? "-"}
                    </div>
                  </div>
                ) : null}

                {lastExpense.breakdown?.length ? (
                  lastExpense.breakdown.map((b, i) => (
                    <div key={i} className="item">
                      <div className="itemTitle">{agentLabel(b.agent)}</div>
                      <div className="muted small">
                        input {b.input_tokens ?? "-"} · output {b.output_tokens ?? "-"} · total {b.total_tokens ?? "-"}
                        {b.model ? ` · ${b.model}` : ""}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="muted">Sin breakdown disponible.</div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}


