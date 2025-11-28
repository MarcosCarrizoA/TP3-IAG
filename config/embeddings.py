"""Configuración de embeddings para vector stores."""

from langchain_huggingface import HuggingFaceEmbeddings

# Modelo de embeddings (multilingüe, incluye español)
EMBEDDING_MODEL = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)

