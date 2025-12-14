"""Punto de entrada principal del sistema de recomendación musical."""

from langchain_core.messages import SystemMessage, HumanMessage

from agents import create_music_agent

# Expose the FastAPI app for deployment platforms that default to `uvicorn main:app` (e.g. Railway).
# This does not affect CLI usage (the interactive loop only runs under `__main__`).
from api.app import app  # noqa: F401


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

