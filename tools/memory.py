"""Herramientas de memoria y conocimiento musical."""

from datetime import datetime
from langchain_core.documents import Document

from vectorstores import initialize_memory_vectorstore, initialize_knowledge_vectorstore


def save_context(context: str) -> str:
    """
    Guarda información del contexto actual (clima, hora, día, mood, playlist recomendada) 
    en el vector store con embeddings para búsqueda semántica.
    """
    try:
        timestamp = datetime.now().isoformat()
        
        # Guardar en vector store con embeddings
        try:
            vectorstore = initialize_memory_vectorstore()
            
            # Extraer metadata del contexto
            metadata = {
                'timestamp': timestamp,
                'id': f"context_{timestamp}"
            }

            # If running under the API, associate saved context to the authenticated user.
            try:
                from api.user_context import get_current_user_id  # type: ignore
                user_id = get_current_user_id()
                if user_id is not None:
                    metadata["user_id"] = int(user_id)
            except Exception:
                pass
            
            if 'Playlist:' in context:
                metadata['playlist_recommended'] = context.split('Playlist:')[-1].strip()
            if 'Mood:' in context:
                metadata['mood'] = context.split('Mood:')[-1].split(',')[0].strip()
            if 'Clima:' in context:
                metadata['weather'] = context.split('Clima:')[-1].split(',')[0].strip()
            if 'Hora:' in context:
                metadata['time_period'] = context.split('Hora:')[-1].split(',')[0].strip()
            
            doc = Document(page_content=context, metadata=metadata)
            vectorstore.add_documents([doc])
            # Chroma persiste automáticamente, no necesita .persist()
        except Exception as e:
            return f"Error guardando en vector store: {str(e)}"
        
        return f"Contexto guardado: {context[:50]}..."
    except Exception as e:
        return f"Error guardando contexto: {str(e)}"


def search_musical_knowledge(query: str, top_k: int = 3) -> str:
    """
    Busca en la base de conocimiento musical usando RAG (búsqueda semántica).
    Retorna información relevante sobre música, géneros, actividades y condiciones ambientales.
    
    Args:
        query (str): Consulta sobre música, actividad, mood, etc.
        top_k (int): Número máximo de resultados a retornar (por defecto 3)
    """
    try:
        vectorstore = initialize_knowledge_vectorstore()
        
        if vectorstore is None:
            return "Base de conocimiento no disponible"
        
        results = vectorstore.similarity_search_with_score(query, k=top_k)
        
        if not results:
            return "No se encontró información relevante en la base de conocimiento"
        
        result = "Conocimiento musical relevante:\n"
        for i, (doc, score) in enumerate(results, 1):
            knowledge_text = doc.page_content
            metadata = doc.metadata
            result += f"{i}. {knowledge_text}\n"
            if metadata.get('genero'):
                result += f"   Género: {metadata.get('genero')}\n"
            if metadata.get('actividad'):
                # actividad ahora es un string, no una lista
                result += f"   Actividad: {metadata.get('actividad')}\n"
            result += "\n"
        
        return result
    except Exception as e:
        return f"Error buscando en base de conocimiento: {str(e)}"


def get_similar_contexts(query: str, top_k: int = 5) -> str:
    """
    Busca contextos similares usando búsqueda semántica con embeddings.
    Si query está vacío, devuelve los últimos contextos del vector store.
    
    Args:
        query (str): Consulta para buscar contextos similares (puede ser mood, actividad, etc.)
        top_k (int): Número máximo de contextos a retornar (por defecto 5)
    """
    try:
        vectorstore = initialize_memory_vectorstore()

        # If running under the API, restrict results to the authenticated user.
        try:
            from api.user_context import get_current_user_id  # type: ignore
            user_id = get_current_user_id()
        except Exception:
            user_id = None
        
        # Si no hay query, usar búsqueda genérica para obtener últimos contextos
        if not query or query.strip() == "":
            query = "contexto previo"
        
        # Búsqueda semántica
        kwargs = {}
        if user_id is not None:
            kwargs["filter"] = {"user_id": int(user_id)}
        results = vectorstore.similarity_search_with_score(query, k=top_k, **kwargs)
        
        if not results:
            return "No hay contextos previos almacenados"
        
        # Formatear resultados
        if query == "contexto previo":
            result = "Contextos previos:\n"
            for i, (doc, score) in enumerate(results, 1):
                timestamp = doc.metadata.get('timestamp', 'Unknown')
                context = doc.page_content
                result += f"{i}. [{timestamp[:19]}] {context}\n"
        else:
            result = f"Contextos similares a '{query}':\n"
            for i, (doc, score) in enumerate(results, 1):
                timestamp = doc.metadata.get('timestamp', 'Unknown')
                context = doc.page_content
                result += f"{i}. [{timestamp[:19]}] {context} (similitud: {score:.3f})\n"
        
        return result
    except Exception as e:
        return f"Error cargando contextos previos: {str(e)}"


def get_context_insights(user_query: str = "") -> str:
    """
    Consulta al agente especializado en contexto para obtener insights profundos.
    """
    try:
        from agents.context_analyzer_agent import analyze_context
        return analyze_context(user_query)
    except Exception as e:
        print(f"⚠️ Error obteniendo insights del agente especializado: {str(e)}")
        return "Insights de contexto no disponibles"

