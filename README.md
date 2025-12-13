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

- Levantar API:

```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000
```

- Abrí la UI de prueba:
  - `/docs`

### Flujo de uso (vía `/docs`)

1. `POST /auth/signup` (o `POST /auth/login`) → devuelve `access_token`.
2. En `/docs`, botón **Authorize** → pegás `Bearer <token>`.
3. `POST /chat` → chateás con el agente (queda asociado a tu usuario).
4. `GET /history` → ves tu historial.
5. `GET/POST/PUT/DELETE /playlists` → playlists persistentes por usuario.

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

