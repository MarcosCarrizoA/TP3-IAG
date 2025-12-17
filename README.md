## Music Recommendation Agent (MusicBot)

Este proyecto implementa **MusicBot**, un agente conversacional que recomienda playlists según el **mood** y el **contexto** (hora, clima, situación/actividad). El objetivo es dar recomendaciones breves y justificadas, y aprender de interacciones previas (memoria) para personalizar.

### Tecnologías

- **Backend**: Python + **FastAPI**
- **LLM**: **Gemini** (via `langchain-google-genai`)
- **Agentes/Herramientas**: LangChain + LangGraph (tools + subagente de contexto)
- **Embeddings / Vectorstore**: Chroma + (por defecto) **FastEmbed** (opción Google embeddings)
- **Persistencia**: SQLite (usuarios y playlists) + Chroma persistido (memoria/knowledge)
- **Frontend**: Vite + React (UI mínima para probar)

### Variables de entorno (backend)

- **Requeridas**:
  - `GOOGLE_API_KEY`: clave de Gemini
  - `JWT_SECRET`: secret para auth (aunque uses solo la UI local, el backend lo requiere)

- **Recomendadas / comunes**:
  - `DATABASE_URL=sqlite:///./app.db`
  - `CHROMA_MEMORY_DIR=./chroma_memory`
  - `CHROMA_KNOWLEDGE_DIR=./chroma_knowledge`
  - `CORS_ORIGINS=http://localhost:5173`
  - `GEMINI_MODEL=gemini-2.0-flash`
  - `GEMINI_TEMPERATURE=0.7`
  - `GEMINI_CONTEXT_MODEL=gemini-2.0-flash`
  - `GEMINI_CONTEXT_TEMPERATURE=0.7`

- **Embeddings**:
  - `EMBEDDINGS_PROVIDER=fastembed`
  - `FASTEMBED_MODEL=BAAI/bge-small-en-v1.5`
  - (opcional, embeddings por Google)
    - `EMBEDDINGS_PROVIDER=google`
    - `GEMINI_EMBEDDINGS_MODEL=text-embedding-004`

Podés copiar `env.example` a `.env` y completar valores.

### Cómo levantar el backend (local)

- **Requisitos**: Python 3.10+ recomendado.

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Levantar el server:

```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000
```

### Cómo levantar el frontend (local)

El frontend vive en `frontend/` (Vite + React).

Crear `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Instalar y correr:

```bash
cd frontend
npm install
npm run dev
```

Luego abrís la URL que te muestre Vite (por defecto `http://localhost:5173`).

