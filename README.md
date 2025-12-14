## Music Recommendation Agent (API + JWT + RAG)

Este repo contiene un agente de recomendación musical con herramientas y RAG (Chroma), expuesto como **API REST** con **FastAPI** y autenticación **JWT**, con persistencia por usuario (SQLite).

### Cómo correr local

- **Requisitos**: Python 3.10+ recomendado.
- Instalación:

```bash
pip install -r requirements.txt
```

- Variables de entorno:
  - Copiá `env.example` a `.env` y completá valores (o seteá variables en tu shell).
  - Mínimo requerido: `GOOGLE_API_KEY` y `JWT_SECRET`.

- Ejemplo `.env` (backend):

```env
GOOGLE_API_KEY=TU_KEY
JWT_SECRET=un_secreto_largo
DATABASE_URL=sqlite:///./app.db
CHROMA_MEMORY_DIR=./chroma_memory
CHROMA_KNOWLEDGE_DIR=./chroma_knowledge
CORS_ORIGINS=http://localhost:5173
GEMINI_MODEL=gemini-2.0-flash
GEMINI_TEMPERATURE=0.7
GEMINI_CONTEXT_MODEL=gemini-2.0-flash
GEMINI_CONTEXT_TEMPERATURE=0.7
EMBEDDINGS_PROVIDER=fastembed
FASTEMBED_MODEL=BAAI/bge-small-en-v1.5
# (opcional) si querés embeddings por Google en vez de local:
# EMBEDDINGS_PROVIDER=google
# GEMINI_EMBEDDINGS_MODEL=text-embedding-004
```

- Levantar API:

```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000
```

- Abrí la UI de prueba:
  - `/docs`

### UI de chat (React) para probar en local

Hay un frontend mínimo en `frontend/` (Vite + React).

- Crear `frontend/.env` (frontend):

```env
VITE_API_BASE_URL=http://localhost:8000
```

- Instalar y correr:

```bash
cd frontend
npm install
npm run dev
```

Luego abrís la URL que te muestre Vite (por defecto `http://localhost:5173`).

Tip: en el chat escribí `help` para ver comandos rápidos (`help`, `playlists`, `memory`).

### Flujo de uso (vía `/docs`)

1. `POST /auth/signup` (o `POST /auth/login`) → devuelve `access_token`.
2. En `/docs`, botón **Authorize** → pegás `Bearer <token>`.
3. `POST /chat` → chateás con el agente (queda asociado a tu usuario).
4. `GET/POST/PUT/DELETE /playlists` → playlists persistentes por usuario (también podés gestionarlas por chat).

### RAG / Chroma

- Conocimiento musical: Chroma persistido (global).
- Memoria de usuario: Chroma persistido y filtrado por `user_id` (cada usuario ve sus contextos).

### Deploy en Railway (recomendado)

1. Subí el repo a GitHub.
2. Railway → **New Project** → **Deploy from GitHub repo**.
3. En el servicio, agregá **Variables**:
   - `GOOGLE_API_KEY`
   - `JWT_SECRET`
   - `DATABASE_URL=sqlite:////app/data/app.db`
   - `CHROMA_MEMORY_DIR=/app/data/chroma_memory`
   - `CHROMA_KNOWLEDGE_DIR=/app/data/chroma_knowledge`
4. Agregá un **Volume** y montalo en:
   - `/app/data`
5. Configurá el **Start Command**:

```bash
uvicorn api.app:app --host 0.0.0.0 --port $PORT
```

6. Deploy → probá:
   - `GET /health`
   - `/docs`

