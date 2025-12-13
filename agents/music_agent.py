"""Agente principal de recomendación musical."""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import SystemMessage

from tools import (
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
)
from vectorstores import initialize_memory_vectorstore, initialize_knowledge_vectorstore

load_dotenv()


def create_music_agent():
    """
    Crea el agente principal de recomendación musical.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY no encontrada en las variables de entorno")
    
    # Inicializar vector stores al crear el agente
    initialize_memory_vectorstore()
    initialize_knowledge_vectorstore()
    
    # Allow overriding model/temperature from env for easier local testing and quota workarounds.
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))

    model = ChatGoogleGenerativeAI(
        model=gemini_model,
        temperature=temperature,
        google_api_key=api_key,
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
    
    with open('prompts/system_prompt.txt', 'r', encoding='utf-8') as f:
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

