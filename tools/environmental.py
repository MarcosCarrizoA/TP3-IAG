"""Herramientas de percepción ambiental (clima, ubicación, tiempo)."""

import requests
from datetime import datetime


def get_location_and_weather() -> str:
    """
    Obtiene la ubicación real del usuario (ciudad y país) y el clima actual usando las coordenadas exactas.
    Utiliza la API ipwho.is para ubicación y open-meteo.com para clima.
    """
    # Benchmark mode: deterministic per-case mocks (no external calls)
    try:
        from bench.mock_context import get_api_mocks  # type: ignore

        m = get_api_mocks()
        if m is not None:
            if not m.location and not m.weather and m.temperature_c is None:
                return "Ubicación: No disponible | Clima: No disponible"
            loc = m.location or "Ubicación desconocida"
            w = m.weather or "clima desconocido"
            if m.temperature_c is None:
                return f"Ubicación: {loc} | Clima: {w}"
            return f"Ubicación: {loc} | Clima: {w}, {m.temperature_c}°C"
    except Exception:
        pass

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
    # Benchmark mode: deterministic per-case mocks (no datetime dependency)
    try:
        from bench.mock_context import get_api_mocks  # type: ignore

        m = get_api_mocks()
        if m is not None:
            if not m.time and not m.season:
                return "Tiempo: No disponible"
            parts = []
            if m.time:
                parts.append(str(m.time))
            if m.season:
                parts.append(f"season={m.season}")
            return " | ".join(parts)
    except Exception:
        pass

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

