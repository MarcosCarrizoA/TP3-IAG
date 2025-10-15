import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

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

# =============================================================================
# HERRAMIENTAS DE MEMORIA
# =============================================================================

def save_context(context: str) -> str:
    """
    Guarda información del contexto actual (clima, hora, día, mood, playlist recomendada) en un archivo JSON.
    Permite construir una memoria episódica simple para personalizar futuras recomendaciones.
    """
    try:
        with open('context_memory.json', 'r', encoding='utf-8') as f:
            contexts = json.load(f)
        
        contexts.append({
            "timestamp": datetime.now().isoformat(),
            "context": context
        })
        
        if len(contexts) > 10:
            contexts = contexts[-10:]
        
        with open('context_memory.json', 'w', encoding='utf-8') as f:
            json.dump(contexts, f, ensure_ascii=False, indent=2)
        
        return f"Contexto guardado: {context[:50]}..."
    except Exception as e:
        return f"Error guardando contexto: {str(e)}"

def get_previous_context(max_contexts: int = 10) -> str:
    """
    Devuelve los últimos contextos almacenados de interacciones previas.
    Se utiliza para reconocer situaciones similares y evitar repeticiones excesivas en las recomendaciones.
    
    Args:
        max_contexts (int): Número máximo de contextos a devolver (máximo 10, por defecto 10)
    """
    try:
        with open('context_memory.json', 'r', encoding='utf-8') as f:
            contexts = json.load(f)
        
        if not contexts:
            return "No hay contextos previos almacenados"
        
        # Limitar el número de contextos a mostrar
        max_contexts = min(max_contexts, 10)
        
        result = "Contextos previos:\n"
        for i, ctx in enumerate(contexts[-max_contexts:], 1):
            timestamp = ctx.get('timestamp', 'Unknown')
            context = ctx.get('context', '')
            result += f"{i}. [{timestamp[:19]}] {context}\n"
        
        return result
    except Exception as e:
        return f"Error cargando contextos previos: {str(e)}"

# =============================================================================
# CONFIGURACIÓN DEL AGENTE
# =============================================================================

def create_music_agent():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY no encontrada en las variables de entorno")
    
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.7,
        google_api_key=api_key
    )
    
    tools = [
        get_location_and_weather,
        get_time_context,
        list_playlists,
        add_playlist,
        edit_playlist,
        save_context,
        get_previous_context
    ]
    
    checkpointer = InMemorySaver()
    
    with open('system_prompt.txt', 'r', encoding='utf-8') as f:
        system_prompt = f.read()
    
    agent = create_react_agent(
        model=model,
        tools=tools,
        checkpointer=checkpointer,
        prompt=system_prompt
    )
    
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
                print("\n🤔 Analizando tu contexto y buscando la playlist perfecta...")
                
                response = agent.invoke(
                    {"messages": [{"role": "user", "content": user_input}]},
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

    except Exception as e:
        print(f"❌ Error inicializando el agente: {str(e)}")
        print("Asegúrate de tener configurada la variable GOOGLE_API_KEY en tu archivo .env")

if __name__ == "__main__":
    main()