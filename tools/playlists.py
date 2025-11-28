"""Herramientas de gestión de playlists."""

import json


def list_playlists() -> str:
    """
    Devuelve la lista de playlists disponibles junto con sus descripciones.
    Se utiliza como fuente de conocimiento base para la selección final de música.
    """
    try:
        with open('data/playlists.json', 'r', encoding='utf-8') as f:
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
        with open('data/playlists.json', 'r', encoding='utf-8') as f:
            playlists = json.load(f)
        
        playlists[name] = description
        
        with open('data/playlists.json', 'w', encoding='utf-8') as f:
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
        with open('data/playlists.json', 'r', encoding='utf-8') as f:
            playlists = json.load(f)
        
        if name in playlists:
            old_description = playlists[name]
            playlists[name] = new_description
            
            with open('data/playlists.json', 'w', encoding='utf-8') as f:
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
        with open('data/playlists.json', 'r', encoding='utf-8') as f:
            playlists = json.load(f)
        
        if name in playlists:
            deleted_description = playlists[name]
            del playlists[name]
            
            with open('data/playlists.json', 'w', encoding='utf-8') as f:
                json.dump(playlists, f, ensure_ascii=False, indent=2)
            
            return f"Playlist '{name}' eliminada exitosamente: {deleted_description}"
        else:
            return f"Playlist '{name}' no encontrada"
    except Exception as e:
        return f"Error eliminando playlist: {str(e)}"

