# 🎵 Agente de Recomendación Musical Inteligente

Un agente conversacional basado en IA que recomienda playlists musicales personalizadas considerando el estado de ánimo del usuario, contexto ambiental (clima, ubicación, hora del día) y memoria de interacciones previas.

## 📋 Descripción

Este proyecto implementa un agente inteligente construido con **LangGraph** y **Google Gemini** que actúa como un asistente musical personalizado. El agente analiza múltiples factores contextuales para proporcionar recomendaciones musicales adaptadas a cada situación específica del usuario.

### Características Principales

- 🎯 **Recomendaciones Contextuales**: Considera clima, ubicación, hora del día y día de la semana
- 🧠 **Memoria Episódica**: Aprende de interacciones previas para personalizar recomendaciones futuras
- 🌍 **Percepción Ambiental**: Obtiene automáticamente ubicación y clima actual del usuario
- 📚 **Gestión de Playlists**: Permite agregar, editar y eliminar playlists del catálogo
- 💬 **Interfaz Conversacional**: Interacción natural en español mediante chat
- 🔄 **Evita Repeticiones**: Utiliza memoria histórica para variar recomendaciones cuando corresponde

## 🚀 Instalación

### Requisitos Previos

- Python 3.8 o superior
- Cuenta de Google Cloud con API Key para Gemini
- Conexión a internet (para APIs de ubicación y clima)

### Pasos de Instalación

1. **Clonar el repositorio** (o descargar los archivos)

```bash
git clone <url-del-repositorio>
cd TP3-IAG
```

2. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno**

Crear un archivo `.env` en la raíz del proyecto con tu API Key de Google:

```env
GOOGLE_API_KEY=tu_api_key_aqui
```

Para obtener una API Key:
- Visita [Google AI Studio](https://makersuite.google.com/app/apikey)
- Crea una nueva API Key
- Cópiala al archivo `.env`

## 📖 Uso

### Ejecutar el Agente

```bash
python music_agent.py
```

### Interactuar con el Agente

Una vez iniciado, el agente te saludará y podrás comenzar a hacer preguntas. Ejemplos:

```
- Estoy muy feliz y quiero música para una previa con amigos. Qué playlist me recomendás?
- Necesito concentrarme para estudiar programación. Quiero música tranquila, preferentemente sin mucha letra.
- Está lluvioso y estoy medio bajón. Quiero algo tranquilo para relajarme.
- Quiero música bien arriba para entrenar fuerte. Tengo mucha energía.
```

### Comandos Especiales

- `salir`, `exit` o `quit`: Termina la sesión

### Gestión de Playlists

El agente también puede gestionar playlists:

```
- Mostrame todas las playlists que conocés
- Agregá una playlist nueva llamada "rock_argento" para rock nacional tranquilo
- Editá la playlist "Focus Flow" para que sea más electrónica
- Borrá la playlist "Calm Evenings"
```

## 📁 Estructura del Proyecto

```
TP3-IAG/
│
├── music_agent.py          # Código principal del agente
├── system_prompt.txt       # Prompt del sistema que define el comportamiento
├── playlists.json          # Catálogo de playlists disponibles
├── context_memory.json     # Memoria de contextos previos (se genera automáticamente)
├── requirements.txt        # Dependencias del proyecto
├── README.md              # Este archivo
└── INFORME_EVALUACION.md  # Informe detallado de evaluación del agente
```

### Archivos Importantes

- **`music_agent.py`**: Implementación del agente con todas las herramientas y lógica principal
- **`playlists.json`**: Base de datos de playlists disponibles. Formato JSON con nombre y descripción
- **`context_memory.json`**: Historial de interacciones previas. Se actualiza automáticamente
- **`system_prompt.txt`**: Instrucciones del sistema que guían el comportamiento del agente

## 🛠️ Tecnologías Utilizadas

- **LangGraph**: Framework para construir agentes con flujos de trabajo complejos
- **LangChain**: Biblioteca para aplicaciones con LLMs
- **Google Gemini 2.0 Flash**: Modelo de lenguaje para el razonamiento del agente
- **Python**: Lenguaje de programación principal
- **APIs Externas**:
  - `ipwho.is`: Para obtener ubicación basada en IP
  - `open-meteo.com`: Para obtener datos meteorológicos

**Nota**: Este agente requiere conexión a internet para funcionar correctamente, ya que utiliza APIs externas para obtener ubicación y clima.