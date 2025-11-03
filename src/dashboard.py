"""App principal en Streamlit para explorar jugadores de League of Legends."""
from __future__ import annotations
import streamlit as st
import pandas as pd
from data_collection import (
    get_champion_data,
    get_puuid_by_riot_id,
    get_champion_mastery,
    get_match_ids,
    get_match_details
)


def analyze_player_matches(puuid: str, champion_names: dict, match_count: int = 10):
    """
    Analiza las últimas partidas de un jugador.
    
    Args:
        puuid (str): PUUID del jugador
        champion_names (dict): Diccionario de traducción de IDs a nombres
        match_count (int): Número de partidas a analizar
        
    Returns:
        tuple: (overall_stats, stats_by_role, stats_by_champion)
    """
    match_ids = get_match_ids(puuid, count=match_count)
    
    if not isinstance(match_ids, list) or len(match_ids) == 0:
        return None, None, None
    
    stats_by_role = {}
    stats_by_champion = {}
    overall_stats = {
        'total_games': 0,
        'wins': 0,
        'champions_played': [],
        'bans': [],
        'total_kills': 0,
        'total_deaths': 0,
        'total_assists': 0,
        'total_gold': 0,
        'total_game_duration': 0
    }
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, match_id in enumerate(match_ids):
        progress_bar.progress((idx + 1) / len(match_ids))
        status_text.text(f"Procesando partida {idx + 1}/{len(match_ids)}")
        
        match_data = get_match_details(match_id)
        
        if not isinstance(match_data, dict) or 'info' not in match_data:
            continue
        
        player_data = None
        for participant in match_data['info']['participants']:
            if participant['puuid'] == puuid:
                player_data = participant
                break
        
        if not player_data:
            continue
        
        # Datos básicos
        role = player_data.get('teamPosition', 'UNKNOWN')
        champion_id = player_data['championId']
        champion_name = champion_names.get(champion_id, f"ID:{champion_id}")
        won = player_data['win']
        
        # KDA
        kills = player_data.get('kills', 0)
        deaths = player_data.get('deaths', 0)
        assists = player_data.get('assists', 0)
        
        # Gold
        total_gold = player_data.get('goldEarned', 0)
        game_duration_minutes = match_data['info']['gameDuration'] / 60
        gold_per_min = total_gold / game_duration_minutes if game_duration_minutes > 0 else 0
        
        # Oro a los 15 min
        gold_at_15 = player_data.get('challenges', {}).get('goldPerMinute', 0) * 15
        if gold_at_15 == 0:
            gold_at_15 = gold_per_min * min(15, game_duration_minutes)
        
        # Ban del equipo
        team_id = player_data['teamId']
        player_ban = None
        for team in match_data['info']['teams']:
            if team['teamId'] == team_id:
                if 'bans' in team and len(team['bans']) > 0:
                    ban_champion_id = team['bans'][0].get('championId', -1)
                    if ban_champion_id != -1:
                        player_ban = champion_names.get(ban_champion_id, f"ID:{ban_champion_id}")
                break
        
        # Estadísticas por rol
        if role not in stats_by_role:
            stats_by_role[role] = {
                'games': 0,
                'wins': 0,
                'total_gold_15min': 0,
                'champions': [],
                'total_kills': 0,
                'total_deaths': 0,
                'total_assists': 0,
                'total_gold': 0,
                'total_duration': 0
            }
        
        stats_by_role[role]['games'] += 1
        stats_by_role[role]['wins'] += 1 if won else 0
        stats_by_role[role]['total_gold_15min'] += gold_at_15
        stats_by_role[role]['champions'].append(champion_name)
        stats_by_role[role]['total_kills'] += kills
        stats_by_role[role]['total_deaths'] += deaths
        stats_by_role[role]['total_assists'] += assists
        stats_by_role[role]['total_gold'] += total_gold
        stats_by_role[role]['total_duration'] += game_duration_minutes
        
        # Estadísticas por campeón
        if champion_name not in stats_by_champion:
            stats_by_champion[champion_name] = {
                'picks': 0,
                'wins': 0,
                'total_kills': 0,
                'total_deaths': 0,
                'total_assists': 0,
                'total_gold': 0,
                'total_duration': 0,
                'roles': []
            }
        
        stats_by_champion[champion_name]['picks'] += 1
        stats_by_champion[champion_name]['wins'] += 1 if won else 0
        stats_by_champion[champion_name]['total_kills'] += kills
        stats_by_champion[champion_name]['total_deaths'] += deaths
        stats_by_champion[champion_name]['total_assists'] += assists
        stats_by_champion[champion_name]['total_gold'] += total_gold
        stats_by_champion[champion_name]['total_duration'] += game_duration_minutes
        stats_by_champion[champion_name]['roles'].append(role)
        
        # Estadísticas generales
        overall_stats['total_games'] += 1
        overall_stats['wins'] += 1 if won else 0
        overall_stats['champions_played'].append(champion_name)
        overall_stats['total_kills'] += kills
        overall_stats['total_deaths'] += deaths
        overall_stats['total_assists'] += assists
        overall_stats['total_gold'] += total_gold
        overall_stats['total_game_duration'] += game_duration_minutes
        if player_ban:
            overall_stats['bans'].append(player_ban)
    
    progress_bar.empty()
    status_text.empty()
    
    return overall_stats, stats_by_role, stats_by_champion
    
    progress_bar.empty()
    status_text.empty()
    
    return overall_stats, stats_by_role


def main():
    st.set_page_config(page_title="LoL Player Analysis", page_icon="🎮", layout="wide")
    
    st.title("League of Legends - Análisis de Jugador")
    st.markdown("Analiza estadísticas de cualquier jugador usando su Riot ID")
    
    # Cargar datos de campeones
    if 'champion_names' not in st.session_state:
        with st.spinner("Cargando datos de campeones..."):
            st.session_state.champion_names = get_champion_data()
    
    champion_names = st.session_state.champion_names
    
    # Sidebar - Búsqueda de jugador
    st.sidebar.header("Buscar Jugador")
    
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        game_name = st.text_input("Nombre de invocador", value="El Jods")
    with col2:
        tag_line = st.text_input("Tag", value="LAN")
    
    match_count = st.sidebar.slider("Número de partidas a analizar", 5, 20, 10)
    
    if st.sidebar.button("Analizar Jugador", type="primary"):
        with st.spinner(f"Obteniendo información de {game_name}#{tag_line}..."):
            account_info = get_puuid_by_riot_id(game_name, tag_line)
            
            if 'puuid' not in account_info:
                st.error(f"No se pudo encontrar el jugador {game_name}#{tag_line}")
                st.json(account_info)
                return
            
            st.session_state.puuid = account_info['puuid']
            st.session_state.game_name = game_name
            st.session_state.tag_line = tag_line
    
    # Mostrar análisis si hay un PUUID
    if 'puuid' in st.session_state:
        puuid = st.session_state.puuid
        
        st.header(f" {st.session_state.game_name}#{st.session_state.tag_line}")
        
        # Tabs para diferentes análisis
        tab1, tab2 = st.tabs(["Maestría de Campeones", "Análisis de Partidas"])
        
        with tab1:
            with st.spinner("Obteniendo maestría de campeones..."):
                mastery_data = get_champion_mastery(puuid)
                
                if isinstance(mastery_data, list):
                    st.subheader("Top 10 Campeones por Maestría")
                    
                    mastery_df = pd.DataFrame([
                        {
                            'Campeón': champion_names.get(champ['championId'], f"ID:{champ['championId']}"),
                            'Nivel': champ['championLevel'],
                            'Puntos': champ['championPoints'],
                            'Cofres': 'Sí' if champ.get('chestGranted', False) else 'No'
                        }
                        for champ in mastery_data[:10]
                    ])
                    
                    st.dataframe(mastery_df, width='stretch', hide_index=True)
        
        with tab2:
            if st.button("Analizar Últimas Partidas"):
                overall_stats, stats_by_role, stats_by_champion = analyze_player_matches(puuid, champion_names, match_count)
                
                if overall_stats:
                    # Métricas generales
                    st.subheader("Resumen General")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        st.metric("Partidas", overall_stats['total_games'])
                    with col2:
                        win_rate = (overall_stats['wins'] / overall_stats['total_games']) * 100
                        st.metric("Win Rate", f"{win_rate:.1f}%")
                    with col3:
                        kda = (overall_stats['total_kills'] + overall_stats['total_assists']) / max(overall_stats['total_deaths'], 1)
                        st.metric("KDA", f"{kda:.2f}")
                    with col4:
                        avg_gold_per_min = overall_stats['total_gold'] / overall_stats['total_game_duration'] if overall_stats['total_game_duration'] > 0 else 0
                        st.metric("Gold/min", f"{avg_gold_per_min:,.0f}")
                    with col5:
                        avg_kda_str = f"{overall_stats['total_kills']/overall_stats['total_games']:.1f}/{overall_stats['total_deaths']/overall_stats['total_games']:.1f}/{overall_stats['total_assists']/overall_stats['total_games']:.1f}"
                        st.metric("K/D/A Promedio", avg_kda_str)
                    
                    # Estadísticas por campeón
                    st.subheader("Estadísticas por Campeón")
                    
                    champion_stats_list = []
                    for champ_name, stats in stats_by_champion.items():
                        champ_kda = (stats['total_kills'] + stats['total_assists']) / max(stats['total_deaths'], 1)
                        champ_gold_per_min = stats['total_gold'] / stats['total_duration'] if stats['total_duration'] > 0 else 0
                        champ_wr = (stats['wins'] / stats['picks']) * 100
                        
                        champion_stats_list.append({
                            'Campeón': champ_name,
                            'Picks': stats['picks'],
                            'Pick Rate %': f"{(stats['picks'] / overall_stats['total_games']) * 100:.1f}%",
                            'Win Rate %': f"{champ_wr:.1f}%",
                            'KDA': f"{champ_kda:.2f}",
                            'Gold/min': f"{champ_gold_per_min:,.0f}",
                            'K/D/A': f"{stats['total_kills']/stats['picks']:.1f}/{stats['total_deaths']/stats['picks']:.1f}/{stats['total_assists']/stats['picks']:.1f}"
                        })
                    
                    champion_df = pd.DataFrame(champion_stats_list).sort_values('Picks', ascending=False)
                    st.dataframe(champion_df, width='stretch', hide_index=True)
                    
                    # Baneos
                    if overall_stats['bans']:
                        st.subheader("Campeones Baneados")
                        ban_counts = pd.Series(overall_stats['bans']).value_counts()
                        ban_stats_list = []
                        for champ, count in ban_counts.items():
                            ban_rate = (count / overall_stats['total_games']) * 100
                            ban_stats_list.append({
                                'Campeón': champ,
                                'Baneos': count,
                                'Ban Rate %': f"{ban_rate:.1f}%"
                            })
                        ban_df = pd.DataFrame(ban_stats_list)
                        st.dataframe(ban_df, width='stretch', hide_index=True)
                    
                    # Estadísticas por rol
                    st.subheader("Estadísticas por Rol")
                    
                    for role, stats in stats_by_role.items():
                        with st.expander(f"{role} ({stats['games']} partidas)"):
                            # Métricas del rol
                            col1, col2, col3, col4 = st.columns(4)
                            
                            role_wr = (stats['wins'] / stats['games']) * 100
                            role_kda = (stats['total_kills'] + stats['total_assists']) / max(stats['total_deaths'], 1)
                            avg_gold = stats['total_gold_15min'] / stats['games']
                            role_gold_per_min = stats['total_gold'] / stats['total_duration'] if stats['total_duration'] > 0 else 0
                            
                            with col1:
                                st.metric("Win Rate", f"{role_wr:.1f}%")
                            with col2:
                                st.metric("KDA", f"{role_kda:.2f}")
                            with col3:
                                st.metric("Gold @ 15min", f"{avg_gold:,.0f}")
                            with col4:
                                st.metric("Gold/min", f"{role_gold_per_min:,.0f}")
                            
                            # Campeones jugados en este rol
                            champ_counter = {champ: stats['champions'].count(champ) for champ in set(stats['champions'])}
                            st.write("**Campeones:**", ", ".join([f"{k} ({v})" for k, v in sorted(champ_counter.items(), key=lambda x: x[1], reverse=True)]))
                else:
                    st.warning("No se pudieron obtener datos de partidas")


if __name__ == '__main__':
    main()
