"""Herramientas de gestión de playlists."""

import json


def list_playlists() -> str:
    """
    Devuelve la lista de playlists disponibles junto con sus descripciones.
    Se utiliza como fuente de conocimiento base para la selección final de música.
    """
    try:
        # If running under the API, scope playlists per-user in DB.
        try:
            from api.user_context import get_current_user_id  # type: ignore
            user_id = get_current_user_id()
        except Exception:
            user_id = None

        if user_id is not None:
            from db.session import SessionLocal
            from db.repositories.playlists import list_playlists_for_user

            with SessionLocal() as db:
                playlists = list_playlists_for_user(db, user_id=user_id)

            result = "Playlists disponibles:\n"
            for p in playlists:
                result += f"- {p.name}: {p.description}\n"
            return result

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
        try:
            from api.user_context import get_current_user_id  # type: ignore
            user_id = get_current_user_id()
        except Exception:
            user_id = None

        if user_id is not None:
            from db.session import SessionLocal
            from db.repositories.playlists import create_playlist_for_user

            with SessionLocal() as db:
                p = create_playlist_for_user(db, user_id=user_id, name=name, description=description)
            return f"Playlist '{p.name}' agregada exitosamente: {p.description}"

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
        try:
            from api.user_context import get_current_user_id  # type: ignore
            user_id = get_current_user_id()
        except Exception:
            user_id = None

        if user_id is not None:
            from db.session import SessionLocal
            from db.repositories.playlists import list_playlists_for_user, update_playlist_for_user

            with SessionLocal() as db:
                playlists = list_playlists_for_user(db, user_id=user_id)
                found = next((p for p in playlists if p.name == name), None)
                if found is None:
                    return f"Playlist '{name}' no encontrada"
                old_description = found.description
                updated = update_playlist_for_user(db, user_id=user_id, playlist_id=found.id, description=new_description)
                if updated is None:
                    return f"Playlist '{name}' no encontrada"
            return f"Playlist '{name}' actualizada: {old_description} -> {new_description}"

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
        try:
            from api.user_context import get_current_user_id  # type: ignore
            user_id = get_current_user_id()
        except Exception:
            user_id = None

        if user_id is not None:
            from db.session import SessionLocal
            from db.repositories.playlists import list_playlists_for_user, delete_playlist_for_user

            with SessionLocal() as db:
                playlists = list_playlists_for_user(db, user_id=user_id)
                found = next((p for p in playlists if p.name == name), None)
                if found is None:
                    return f"Playlist '{name}' no encontrada"
                ok = delete_playlist_for_user(db, user_id=user_id, playlist_id=found.id)
                if not ok:
                    return f"Playlist '{name}' no encontrada"
            return f"Playlist '{name}' eliminada exitosamente"

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

