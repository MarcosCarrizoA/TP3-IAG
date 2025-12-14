"""Configuración de embeddings para vector stores."""

import os

from dotenv import load_dotenv

# Ensure .env is loaded even when this module is imported before api/app.py startup.
load_dotenv()


def _embedding_provider() -> str:
    # Default to local embeddings to avoid external quota/rate-limits during RAG indexing.
    return os.getenv("EMBEDDINGS_PROVIDER", "fastembed").strip().lower()


provider = _embedding_provider()

if provider == "google":
    # Google embeddings (requires API key). Useful if you explicitly want managed embeddings.
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is required for embeddings when EMBEDDINGS_PROVIDER=google")

    EMBEDDING_MODEL = GoogleGenerativeAIEmbeddings(
        model=os.getenv("GEMINI_EMBEDDINGS_MODEL", "text-embedding-004"),
        google_api_key=api_key,
    )
else:
    # Local embeddings (no torch). Much faster/cheaper to build vectorstores on Railway.
    from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

    EMBEDDING_MODEL = FastEmbedEmbeddings(
        model_name=os.getenv("FASTEMBED_MODEL", "BAAI/bge-small-en-v1.5")
)

