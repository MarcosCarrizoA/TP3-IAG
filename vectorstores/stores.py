"""Inicialización y gestión de vector stores con ChromaDB."""

import os
import json
from typing import Optional
from langchain_chroma import Chroma
from langchain_core.documents import Document

from config.embeddings import EMBEDDING_MODEL

# Instancias globales de vector stores (se inicializan al arrancar)
memory_vectorstore: Optional[Chroma] = None
knowledge_vectorstore: Optional[Chroma] = None


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _memory_dir() -> str:
    return os.getenv("CHROMA_MEMORY_DIR", "./chroma_memory")


def _knowledge_dir() -> str:
    return os.getenv("CHROMA_KNOWLEDGE_DIR", "./chroma_knowledge")


def initialize_memory_vectorstore() -> Chroma:
    """
    Inicializa el vector store de memoria con ChromaDB.
    Si ya existe, lo carga. Si no, lo crea.
    """
    global memory_vectorstore
    
    if memory_vectorstore is not None:
        return memory_vectorstore
    
    persist_directory = _memory_dir()
    _ensure_dir(persist_directory)
    
    # Intentar cargar vector store existente
    if os.path.exists(persist_directory) and os.listdir(persist_directory):
        memory_vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=EMBEDDING_MODEL
        )
        print("✅ Vector store de memoria cargado")
    else:
        # Crear nuevo vector store vacío
        memory_vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=EMBEDDING_MODEL
        )
        print("✅ Vector store de memoria creado (vacío)")
    
    return memory_vectorstore


def initialize_knowledge_vectorstore() -> Chroma:
    """
    Inicializa el vector store de conocimiento musical con ChromaDB.
    Carga datos de knowledge_base.json.
    """
    global knowledge_vectorstore
    
    if knowledge_vectorstore is not None:
        return knowledge_vectorstore
    
    persist_directory = _knowledge_dir()
    _ensure_dir(persist_directory)
    
    # Intentar cargar vector store existente
    if os.path.exists(persist_directory) and os.listdir(persist_directory):
        knowledge_vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=EMBEDDING_MODEL
        )
        print("✅ Vector store de conocimiento cargado")
    else:
        # Crear nuevo vector store y cargar knowledge_base.json
        knowledge_vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=EMBEDDING_MODEL
        )
        
        try:
            with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
                knowledge_items = json.load(f)
            
            documents = []
            for item in knowledge_items:
                text = item.get('text', '')
                metadata = item.get('metadata', {})
                
                # Convertir listas en metadata a strings separados por comas (ChromaDB no acepta listas)
                metadata_clean = {}
                for key, value in metadata.items():
                    if isinstance(value, list):
                        metadata_clean[key] = ', '.join(str(v) for v in value)
                    else:
                        metadata_clean[key] = value
                metadata_clean['id'] = item.get('id', '')
                
                documents.append(Document(page_content=text, metadata=metadata_clean))
            
            if documents:
                knowledge_vectorstore.add_documents(documents)
                # Chroma persiste automáticamente, no necesita .persist()
                print(f"✅ Cargados {len(documents)} items de conocimiento al vector store")
        except FileNotFoundError:
            print("⚠️ No se encontró data/knowledge_base.json")
        except Exception as e:
            print(f"⚠️ Error cargando conocimiento: {str(e)}")
    
    return knowledge_vectorstore

