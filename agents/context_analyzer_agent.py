"""
Agente especializado en análisis profundo de contexto ambiental.
Genera insights sobre cómo clima, hora y ubicación influyen en la selección musical.
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

load_dotenv()

def create_context_analyzer_agent():
    """
    Crea el agente especializado en análisis de contexto ambiental.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY no encontrada en las variables de entorno")
    
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.7,
        google_api_key=api_key
    )
    
    # El agente especializado solo necesita las herramientas de contexto ambiental
    from tools.environmental import get_location_and_weather, get_time_context
    
    tools = [
        get_location_and_weather,
        get_time_context
    ]
    
    # Leer el prompt del sistema especializado
    with open('prompts/system_prompt_context_analyzer.txt', 'r', encoding='utf-8') as f:
        system_prompt = f.read()
    
    # create_agent no acepta system_message directamente, se pasará en el invoke
    agent = create_agent(
        model=model,
        tools=tools
    )
    
    # Guardar system_prompt para usarlo en el invoke
    agent._system_prompt = system_prompt
    
    return agent

def analyze_context(user_query: str = "") -> str:
    """
    Analiza el contexto ambiental y genera insights.
    
    Args:
        user_query: Query opcional del usuario (puede incluir mood, actividad, etc.)
    
    Returns:
        Insights sobre el contexto ambiental y su relación con la música
    """
    print(f"🎶 Analizando contexto ambiental con agente especializado: {user_query}")
    agent = create_context_analyzer_agent()
    
    # Construir el prompt para el agente especializado
    prompt = f"""
Analiza el contexto ambiental actual y genera insights profundos sobre cómo influye en la selección musical.

{f'Contexto adicional del usuario: {user_query}' if user_query else ''}

Genera insights específicos sobre cómo el clima, hora del día y ubicación se relacionan con el estado de ánimo esperado y el tipo de música apropiada.
"""

    config = {"configurable": {"thread_id": "context_analysis"}}

    # Incluir system message en los mensajes
    from langchain_core.messages import HumanMessage
    messages = [
        SystemMessage(content=agent._system_prompt),
        HumanMessage(content=prompt)
    ]

    response = agent.invoke(
        {"messages": messages},
        config
    )
    
    if "messages" in response and response["messages"]:
        last_message = response["messages"][-1]
        if hasattr(last_message, 'content'):
            return last_message.content
        else:
            return str(last_message)
    
    return "No se pudieron generar insights del contexto"

