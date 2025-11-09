"""Este módulo contendrá la lógica y la interfaz de usuario para la vista de partidos."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

import data_collection
import database

def show_match_view() -> None:
    """Muestra la vista de historial de partidos, permitiendo la actualización y visualización."""

    st.header("Historial de Partidas")

    if 'puuid' not in st.session_state:
        st.warning("Por favor, busca un jugador para ver su historial de partidas.")
        return

    puuid = st.session_state.puuid

    game_name = st.session_state.get("game_name")
    tag_line = st.session_state.get("tag_line")

    if st.button("Buscar nuevas partidas", type="primary"):
        with st.spinner("Buscando nuevas partidas..."):
            try:
                with database.connect_repository() as repo:
                    # Asegurar que el jugador exista en la tabla `players` antes de insertar partidas.
                    repo.register_player(puuid, game_name=game_name, tag_line=tag_line)

                    stored_match_ids = set(repo.get_stored_match_ids(puuid))
                    recent_match_ids = data_collection.get_match_ids(puuid, count=100)
                    if isinstance(recent_match_ids, list):
                        new_match_ids = [m_id for m_id in recent_match_ids if m_id not in stored_match_ids]
                        new_match_ids.reverse()
                        if new_match_ids:
                            _extracted_from_show_match_view_28(new_match_ids, repo, puuid)
                        else:
                            st.success("¡No se encontraron nuevas partidas! El historial está al día.")
            except Exception as e:
                st.error(f"Ocurrió un error al actualizar el historial: {e}")

    # Mostrar las partidas almacenadas con paginación
    try:
        # Inicializar estado de paginación
        if 'match_page' not in st.session_state:
            st.session_state.match_page = 0
        
        matches_per_page = 10
        
        with database.connect_repository() as repo:
            total_matches = repo.get_match_count(puuid)
            
            if total_matches == 0:
                st.info("No hay partidas almacenadas para este jugador. Haz clic en 'Buscar nuevas partidas' para empezar.")
                return
            
            # Calcular paginación
            total_pages = (total_matches + matches_per_page - 1) // matches_per_page
            current_page = st.session_state.match_page
            offset = current_page * matches_per_page
            
            # Mostrar información de paginación
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if current_page > 0:
                    if st.button("< Anterior"):
                        st.session_state.match_page -= 1
                        st.rerun()
            
            with col2:
                st.markdown(f"<div style='text-align: center'>Página {current_page + 1} de {total_pages} ({total_matches} partidas totales)</div>", unsafe_allow_html=True)
            
            with col3:
                if current_page < total_pages - 1:
                    if st.button("Siguiente >"):
                        st.session_state.match_page += 1
                        st.rerun()
            
            st.divider()
            
            # Obtener solo las partidas de la página actual
            matches = repo.get_stored_matches(puuid, limit=matches_per_page, offset=offset)

            for match_record in matches:
                if match_record.raw_json:
                    match_data = json.loads(match_record.raw_json)
                    if player_data := next(
                        (
                            p
                            for p in match_data['info']['participants']
                            if p['puuid'] == puuid
                        ),
                        None,
                    ):
                        champion_names = st.session_state.get('champion_names', {})
                        champion_name = champion_names.get(int(player_data['championId']), f"ID:{player_data['championId']}")
                        
                        # Obtener nombre del jugador (prioridad: riotIdGameName > summonerName > game_name del session_state)
                        player_name = player_data.get('riotIdGameName') or player_data.get('summonerName') or game_name or 'Jugador'
                        kda = f"{player_data['kills']}/{player_data['deaths']}/{player_data['assists']}"
                        result = "Victoria" if player_data['win'] else "Derrota"
                        
                        # Calcular KDA ratio
                        deaths = player_data['deaths'] if player_data['deaths'] > 0 else 1
                        kda_ratio = round((player_data['kills'] + player_data['assists']) / deaths, 2)

                        with st.expander(f"**{player_name}** jugó **{champion_name}** - KDA: {kda} ({kda_ratio}:1) - {result}"):
                            tab1, tab2 = st.tabs(["Desglose por Jugador", "Estadísticas"])

                            with tab1:
                                teams = {}
                                for p in match_data['info']['participants']:
                                    team_id = p['teamId']
                                    if team_id not in teams:
                                        teams[team_id] = []
                                    teams[team_id].append(p)

                                for players in teams.values():
                                    team_result = "Victoria" if players[0]['win'] else "Derrota"
                                    st.subheader(f"Equipo ({team_result})")

                                    cols = st.columns(len(players))
                                    for i, player_details in enumerate(players):
                                        with cols[i]:
                                            champion_name = champion_names.get(int(player_details['championId']), f"ID:{player_details['championId']}")
                                            player_kda = f"{player_details['kills']}/{player_details['deaths']}/{player_details['assists']}"
                                            
                                            # Obtener nombre del jugador (prioridad: riotIdGameName > summonerName)
                                            display_name = player_details.get('riotIdGameName') or player_details.get('summonerName', 'Jugador')

                                            st.markdown(f"**{display_name}**")
                                            st.markdown(f"*{champion_name}*")
                                            st.text(f"KDA: {player_kda}")
                                            st.text(f"Daño: {player_details['totalDamageDealtToChampions']:,}")
                                            st.text(f"Oro: {player_details['goldEarned']:,}")
                                            st.text(f"Visión: {player_details['visionScore']}")

                            with tab2:
                                timeline_data = repo.get_match_timeline(match_record.match_id)
                                if not timeline_data:
                                    with st.spinner("Descargando datos de la línea de tiempo..."):
                                        timeline_data = data_collection.get_match_timeline(match_record.match_id)
                                        if isinstance(timeline_data, dict):
                                            repo.store_match_timeline(match_record.match_id, timeline_data)
                                        else:
                                            st.error("No se pudieron obtener los datos de la línea de tiempo.")
                                            timeline_data = None

                                if timeline_data and isinstance(timeline_data, dict) and 'info' in timeline_data:
                                    gold_data = {}
                                    damage_data = {}
                                    
                                    # Crear mapa de participantId a nombre de jugador (usando riotIdGameName si está disponible)
                                    participant_map = {}
                                    for p in match_data['info']['participants']:
                                        participant_id = p.get('participantId')
                                        if participant_id:
                                            player_name = p.get('riotIdGameName') or p.get('summonerName', f'Jugador {participant_id}')
                                            participant_map[participant_id] = player_name

                                    frames = timeline_data.get('info', {}).get('frames', [])
                                    
                                    if not frames:
                                        st.warning("No hay datos de timeline disponibles para esta partida.")
                                    else:
                                        for frame in frames:
                                            participant_frames = frame.get('participantFrames', {})
                                            for p_id, p_frame in participant_frames.items():
                                                p_id_int = int(p_id)
                                                if p_name := participant_map.get(p_id_int):
                                                    if p_name not in gold_data:
                                                        gold_data[p_name] = []
                                                        damage_data[p_name] = []

                                                    gold_data[p_name].append(p_frame.get('totalGold', 0))
                                                    damage_stats = p_frame.get('damageStats', {})
                                                    damage_data[p_name].append(damage_stats.get('totalDamageDoneToChampions', 0))

                                        if gold_data:
                                            st.subheader("Oro a lo largo del tiempo")
                                            gold_df = pd.DataFrame(gold_data)
                                            st.line_chart(gold_df)

                                            st.subheader("Daño a campeones a lo largo del tiempo")
                                            damage_df = pd.DataFrame(damage_data)
                                            st.line_chart(damage_df)
                                        else:
                                            st.warning("No se pudieron procesar los datos de timeline.")

                                    st.subheader("Puntuación de Visión")
                                    vision_scores = {}
                                    for p in match_data['info']['participants']:
                                        player_name = p.get('riotIdGameName') or p.get('summonerName', 'Jugador')
                                        vision_scores[player_name] = p.get('visionScore', 0)
                                    
                                    vision_df = pd.DataFrame(
                                        list(vision_scores.items()), 
                                        columns=['Jugador', 'Puntuación de Visión']
                                    ).sort_values('Puntuación de Visión', ascending=False)
                                    st.dataframe(vision_df, width='stretch', hide_index=True)

    except Exception as e:
        st.error(f"Ocurrió un error al cargar el historial de partidas: {e}")


# TODO Rename this here and in `show_match_view`
def _extracted_from_show_match_view_28(new_match_ids, repo, puuid):
    new_matches_data = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    for i, match_id in enumerate(new_match_ids):
        status_text.text(f"Descargando partida {i + 1}/{len(new_match_ids)}...")
        details = data_collection.get_match_details(match_id)
        if isinstance(details, dict):
            new_matches_data.append(details)
        progress_bar.progress((i + 1) / len(new_match_ids))
    progress_bar.empty()
    status_text.empty()
    if new_matches_data:
        repo.store_matches(puuid, new_matches_data)
        st.success(f"¡Se han añadido {len(new_matches_data)} nuevas partidas al historial!")
