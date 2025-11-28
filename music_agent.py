import os
import json
import requests
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage

load_dotenv()

# =============================================================================
# CONFIGURACIÓN DE EMBEDDINGS Y VECTOR STORES
# =============================================================================

# Modelo de embeddings (multilingüe, incluye español)
EMBEDDING_MODEL = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)

# Instancias globales de vector stores (se inicializan al arrancar)
memory_vectorstore: Optional[Chroma] = None
knowledge_vectorstore: Optional[Chroma] = None

# =============================================================================
# INICIALIZACIÓN DE VECTOR STORES
# =============================================================================

def initialize_memory_vectorstore() -> Chroma:
    """
    Inicializa el vector store de memoria con ChromaDB.
    Si ya existe, lo carga. Si no, lo crea.
    """
    global memory_vectorstore
    
    if memory_vectorstore is not None:
        return memory_vectorstore
    
    persist_directory = "./chroma_memory"
    
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
    
    persist_directory = "./chroma_knowledge"
    
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
            with open('knowledge_base.json', 'r', encoding='utf-8') as f:
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
            print("⚠️ No se encontró knowledge_base.json")
        except Exception as e:
            print(f"⚠️ Error cargando conocimiento: {str(e)}")
    
    return knowledge_vectorstore

# =============================================================================
# HERRAMIENTAS DE PERCEPCIÓN AMBIENTAL
# =============================================================================

def get_location_and_weather() -> str:
    """
    Obtiene la ubicación real del usuario (ciudad y país) y el clima actual usando las coordenadas exactas.
    Utiliza la API ipwho.is para ubicación y open-meteo.com para clima.
    """
    try:
        response = requests.get("https://ipwho.is/", timeout=10)
        data = response.json()
        city = data.get('city', 'Unknown')
        country = data.get('country', 'Unknown')
        lat = data.get('latitude')
        lon = data.get('longitude')
        
        if lat and lon:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            weather_response = requests.get(url, timeout=10)
            weather_data = weather_response.json()
            
            if 'current_weather' in weather_data:
                weather = weather_data['current_weather']
                temp = weather.get('temperature', 0)
                code = weather.get('weathercode', 0)
                
                weather_descriptions = {
                    0: "despejado", 1: "mayormente despejado", 2: "parcialmente nublado",
                    3: "nublado", 45: "niebla", 48: "niebla helada", 51: "llovizna ligera",
                    53: "llovizna moderada", 55: "llovizna densa", 61: "lluvia ligera",
                    63: "lluvia moderada", 65: "lluvia intensa", 71: "nieve ligera",
                    73: "nieve moderada", 75: "nieve intensa", 77: "granizo",
                    80: "chubascos ligeros", 81: "chubascos moderados", 82: "chubascos intensos",
                    85: "chubascos de nieve ligeros", 86: "chubascos de nieve intensos",
                    95: "tormenta eléctrica", 96: "tormenta con granizo ligero", 99: "tormenta con granizo intenso"
                }
                
                weather_desc = weather_descriptions.get(code, "condiciones variables")
                return f"Ubicación: {city}, {country} | Clima: {weather_desc}, {temp}°C"
            else:
                return f"Ubicación: {city}, {country} | Clima: No disponible"
        else:
            return f"Ubicación: {city}, {country} | Error obteniendo coordenadas"
            
    except Exception as e:
        return f"Error obteniendo ubicación y clima: {str(e)}"

def get_time_context() -> str:
    """
    Obtiene el día de la semana, la hora actual y el momento del día (mañana/tarde/noche).
    Este contexto temporal se combina con el estado de ánimo para ajustar la selección musical.
    """
    now = datetime.now()
    day_of_week = now.strftime("%A")
    hour = now.hour
    time_period = ""
    
    if 5 <= hour < 12:
        time_period = "mañana"
    elif 12 <= hour < 18:
        time_period = "tarde"
    else:
        time_period = "noche"
    
    return f"{day_of_week}, {hour}:{now.minute:02d} ({time_period})"

# =============================================================================
# HERRAMIENTAS DE GESTIÓN MUSICAL
# =============================================================================

def list_playlists() -> str:
    """
    Devuelve la lista de playlists disponibles junto con sus descripciones.
    Se utiliza como fuente de conocimiento base para la selección final de música.
    """
    try:
        with open('playlists.json', 'r', encoding='utf-8') as f:
            playlists = json.load(f)
        
        result = "Playlists disponibles:\n"
        for name, description in playlists.items():
            result += f"- {name}: {description}\n"
        
        return result
    except Exception as e:
        return f"Error cargando playlists: {str(e)}"

def add_playlist(name: str, description: str) -> str:
    """
    Permite agregar nuevas playlists al catálogo interno del agente.
    El usuario puede "enseñarle" nuevas playlists, ampliando su repertorio de recomendaciones.
    """
    try:
        with open('playlists.json', 'r', encoding='utf-8') as f:
            playlists = json.load(f)
        
        playlists[name] = description
        
        with open('playlists.json', 'w', encoding='utf-8') as f:
            json.dump(playlists, f, ensure_ascii=False, indent=2)
        
        return f"Playlist '{name}' agregada exitosamente: {description}"
    except Exception as e:
        return f"Error agregando playlist: {str(e)}"

def edit_playlist(name: str, new_description: str) -> str:
    """
    Modifica la descripción o características de una playlist existente.
    Representa la capacidad del agente de refinar su conocimiento musical.
    """
    try:
        with open('playlists.json', 'r', encoding='utf-8') as f:
            playlists = json.load(f)
        
        if name in playlists:
            old_description = playlists[name]
            playlists[name] = new_description
            
            with open('playlists.json', 'w', encoding='utf-8') as f:
                json.dump(playlists, f, ensure_ascii=False, indent=2)
            
            return f"Playlist '{name}' actualizada: {old_description} -> {new_description}"
        else:
            return f"Playlist '{name}' no encontrada"
    except Exception as e:
        return f"Error editando playlist: {str(e)}"

def delete_playlist(name: str) -> str:
    """
    Elimina una playlist del catálogo interno del agente.
    Permite al usuario gestionar su colección musical removiendo playlists que ya no desea.
    """
    try:
        with open('playlists.json', 'r', encoding='utf-8') as f:
            playlists = json.load(f)
        
        if name in playlists:
            deleted_description = playlists[name]
            del playlists[name]
            
            with open('playlists.json', 'w', encoding='utf-8') as f:
                json.dump(playlists, f, ensure_ascii=False, indent=2)
            
            return f"Playlist '{name}' eliminada exitosamente: {deleted_description}"
        else:
            return f"Playlist '{name}' no encontrada"
    except Exception as e:
        return f"Error eliminando playlist: {str(e)}"

# =============================================================================
# HERRAMIENTAS DE MEMORIA
# =============================================================================

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
        
        # Si no hay query, usar búsqueda genérica para obtener últimos contextos
        if not query or query.strip() == "":
            query = "contexto previo"
        
        # Búsqueda semántica
        results = vectorstore.similarity_search_with_score(query, k=top_k)
        
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

# =============================================================================
# CONFIGURACIÓN DEL AGENTE
# =============================================================================

def get_context_insights(user_query: str = "") -> str:
    """
    Consulta al agente especializado en contexto para obtener insights profundos.
    """
    try:
        from context_analyzer_agent import analyze_context
        return analyze_context(user_query)
    except Exception as e:
        print(f"⚠️ Error obteniendo insights del agente especializado: {str(e)}")
        return "Insights de contexto no disponibles"

def create_music_agent():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY no encontrada en las variables de entorno")
    
    # Inicializar vector stores al crear el agente
    initialize_memory_vectorstore()
    initialize_knowledge_vectorstore()
    
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.7,
        google_api_key=api_key
    )
    
    tools = [
        get_location_and_weather,
        get_time_context,
        get_context_insights,
        list_playlists,
        add_playlist,
        edit_playlist,
        delete_playlist,
        save_context,
        get_similar_contexts,
        search_musical_knowledge
    ]
    
    checkpointer = InMemorySaver()
    
    with open('system_prompt.txt', 'r', encoding='utf-8') as f:
        system_prompt = f.read()
    
    # create_agent no acepta system_message directamente, se pasará en el invoke
    agent = create_agent(
        model=model,
        tools=tools,
        checkpointer=checkpointer
    )
    
    # Guardar system_prompt para usarlo en el invoke
    agent._system_prompt = system_prompt
    
    return agent

# =============================================================================
# FUNCIÓN PRINCIPAL Y EJEMPLOS
# =============================================================================

def main():
    try:
        print("🎵 Inicializando Agente de Recomendación Musical...")
        agent = create_music_agent()
        print("✅ Agente inicializado correctamente")
        
        config = {"configurable": {"thread_id": "music_session_1"}}
        
        while True:
            user_input = input("\n- ").strip()
            
            if user_input.lower() in ['salir', 'exit', 'quit']:
                print("¡Hasta luego! Que disfrutes tu música 🎵")
                break
            
            if not user_input:
                continue
            
            try:
                # Pasar el mensaje directamente al agente, él decidirá qué herramientas usar
                from langchain_core.messages import HumanMessage
                messages = [
                    SystemMessage(content=agent._system_prompt),
                    HumanMessage(content=user_input)
                ]
                
                response = agent.invoke(
                    {"messages": messages},
                    config
                )
                
                if "messages" in response and response["messages"]:
                    last_message = response["messages"][-1]
                    if hasattr(last_message, 'content'):
                        print(f"\n🎵 Recomendación: {last_message.content}")
                    else:
                        print(f"\n🎵 Recomendación: {last_message}")
                else:
                    print(f"\n🎵 Respuesta: {response}")
                
            except Exception as e:
                print(f"❌ Error procesando tu solicitud: {str(e)}")
                import traceback
                traceback.print_exc()

    except Exception as e:
        print(f"❌ Error inicializando el agente: {str(e)}")
        print("Asegúrate de tener configurada la variable GOOGLE_API_KEY en tu archivo .env")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()