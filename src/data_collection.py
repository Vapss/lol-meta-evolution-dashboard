"""Módulo para recolectar datos desde Riot API.

Contiene funciones para llamar endpoints de Riot API, Data Dragon y obtener información de jugadores.
"""
from __future__ import annotations
import os
import requests
from typing import Any, Dict, List
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("RIOT_API_KEY")
REGION = os.getenv("RIOT_REGION", "americas")
PLATFORM = os.getenv("RIOT_PLATFORM", "la1")


def get_latest_version() -> str:
    """
    Obtiene la versión más reciente de Data Dragon.
    
    Returns:
        str: Versión más reciente (ej: "13.24.1")
    """
    versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"
    versions = requests.get(versions_url, timeout=10).json()
    return versions[0]


def get_champion_data() -> Dict[int, str]:
    """
    Obtiene la información de campeones desde Data Dragon.
    
    Returns:
        Dict[int, str]: Diccionario con {championId: nombre}
        
    Notes:
        Usa la versión más reciente de Data Dragon y datos en español (es_MX).
    """
    latest_version = get_latest_version()
    
    champions_url = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/es_MX/champion.json"
    response = requests.get(champions_url, timeout=10)
    champions_data = response.json()
    
    champion_dict = {}
    for champ_key, champ_info in champions_data['data'].items():
        champion_id = int(champ_info['key'])
        champion_dict[champion_id] = champ_info['name']
    
    return champion_dict


def get_champion_icon_url(champion_id: int, champion_name: str | None = None) -> str:
    """
    Obtiene la URL del icono de un campeón desde Data Dragon.
    
    Args:
        champion_id (int): ID del campeón
        champion_name (str | None): Nombre del campeón (para optimización)
        
    Returns:
        str: URL del icono del campeón
        
    Notes:
        Formato: https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{champion}.png
        Usa el nombre interno del campeón (ej: "MonkeyKing" para Wukong).
    """
    try:
        latest_version = get_latest_version()
        
        # Si no se proporciona el nombre, obtener datos de campeones
        if not champion_name:
            champions_url = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/es_MX/champion.json"
            response = requests.get(champions_url, timeout=10)
            champions_data = response.json()
            
            # Buscar el campeón por ID
            for champ_key, champ_info in champions_data['data'].items():
                if int(champ_info['key']) == champion_id:
                    champion_name = champ_key
                    break
        
        if champion_name:
            return f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/img/champion/{champion_name}.png"
        else:
            # Fallback a un icono genérico
            return f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/img/profileicon/29.png"
    except Exception:
        # En caso de error, devolver icono por defecto
        return "https://ddragon.leagueoflegends.com/cdn/13.24.1/img/profileicon/29.png"


def get_puuid_by_riot_id(game_name: str, tag_line: str) -> Dict[str, Any]:
    """
    Obtiene el PUUID de un jugador usando su Riot ID.
    
    Args:
        game_name (str): Nombre del jugador (sin el #)
        tag_line (str): Tag del jugador (después del #)
        
    Returns:
        Dict[str, Any]: Información de la cuenta o diccionario con error
        
    Notes:
        Usa Account-V1 API con routing regional (americas/europe/asia).
    """
    url = f"https://{REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    headers = {"X-Riot-Token": API_KEY}
    response = requests.get(url, headers=headers, timeout=10)
    return response.json() if response.status_code == 200 else {"error": response.status_code, "message": response.text}


def get_champion_mastery(puuid: str) -> Dict[str, Any] | List[Dict[str, Any]]:
    """
    Obtiene la maestría de campeones de un jugador.
    
    Args:
        puuid (str): PUUID del jugador
        
    Returns:
        List[Dict[str, Any]]: Lista de campeones con estadísticas de maestría
        
    Notes:
        Usa Champion-Mastery-V4 API con plataforma específica (la1/na1/euw1).
    """
    url = f"https://{PLATFORM}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}"
    headers = {"X-Riot-Token": API_KEY}
    response = requests.get(url, headers=headers, timeout=10)
    return response.json() if response.status_code == 200 else {"error": response.status_code, "message": response.text}


def get_match_ids(puuid: str, count: int = 20) -> List[str] | str:
    """
    Obtiene lista de IDs de partidas recientes de un jugador.
    
    Args:
        puuid (str): PUUID del jugador
        count (int): Número de partidas a obtener
        
    Returns:
        List[str]: Lista de IDs de partidas o string con error
        
    Notes:
        Usa Match-V5 API con routing regional (americas/europe/asia).
    """
    url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
    headers = {"X-Riot-Token": API_KEY}
    params = {"count": count}
    response = requests.get(url, headers=headers, params=params, timeout=10)
    return response.json() if response.status_code == 200 else response.text


def get_match_details(match_id: str) -> Dict[str, Any] | str:
    """
    Obtiene detalles completos de una partida.
    
    Args:
        match_id (str): ID de la partida
        
    Returns:
        Dict[str, Any]: Datos completos de la partida o string con error
        
    Notes:
        Usa Match-V5 API con routing regional (americas/europe/asia).
    """
    url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    headers = {"X-Riot-Token": API_KEY}
    response = requests.get(url, headers=headers, timeout=10)
    return response.json() if response.status_code == 200 else response.text


def get_match_timeline(match_id: str) -> Dict[str, Any] | str:
    """
    Obtiene la línea de tiempo de una partida.

    Args:
        match_id (str): ID de la partida

    Returns:
        Dict[str, Any]: Datos de la línea de tiempo o string con error

    Notes:
        Usa Match-V5 API con routing regional (americas/europe/asia).
    """
    url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
    headers = {"X-Riot-Token": API_KEY}
    response = requests.get(url, headers=headers, timeout=10)
    return response.json() if response.status_code == 200 else response.text
