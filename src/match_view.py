"""Este módulo contendrá la lógica y la interfaz de usuario para la vista de partidos."""

import streamlit as st
import pandas as pd
import json
from src import data_collection
from src import database

def show_match_view() -> None:
    """Muestra la vista de historial de partidos, permitiendo la actualización y visualización."""

    st.header("Historial de Partidas")

    if 'puuid' not in st.session_state:
        st.warning("Por favor, busca un jugador para ver su historial de partidas.")
        return

    puuid = st.session_state.puuid

    if st.button("Buscar nuevas partidas", type="primary"):
        with st.spinner("Buscando nuevas partidas..."):
            try:
                with database.connect_repository() as repo:
                    stored_match_ids = set(repo.get_stored_match_ids(puuid))
                    recent_match_ids = data_collection.get_match_ids(puuid, count=100)
                    if isinstance(recent_match_ids, list):
                        new_match_ids = [m_id for m_id in recent_match_ids if m_id not in stored_match_ids]
                        new_match_ids.reverse()
                        if new_match_ids:
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
                        else:
                            st.success("¡No se encontraron nuevas partidas! El historial está al día.")
            except Exception as e:
                st.error(f"Ocurrió un error al actualizar el historial: {e}")

    # Mostrar las partidas almacenadas
    try:
        with database.connect_repository() as repo:
            matches = repo.get_stored_matches(puuid)

            if not matches:
                st.info("No hay partidas almacenadas para este jugador. Haz clic en 'Buscar nuevas partidas' para empezar.")
                return

            for match_record in matches:
                if match_record.raw_json:
                    match_data = json.loads(match_record.raw_json)
                    player_data = next((p for p in match_data['info']['participants'] if p['puuid'] == puuid), None)

                    if player_data:
                        champion_names = st.session_state.get('champion_names', {})
                        champion_name = champion_names.get(player_data['championId'], f"ID:{player_data['championId']}")

                        kda = f"{player_data['kills']}/{player_data['deaths']}/{player_data['assists']}"
                        result = "Victoria" if player_data['win'] else "Derrota"

                        with st.expander(f"**{champion_name}** - {kda} - ({result})"):
                            tab1, tab2 = st.tabs(["Desglose por Jugador", "Estadísticas"])

                            with tab1:
                                teams = {}
                                for p in match_data['info']['participants']:
                                    team_id = p['teamId']
                                    if team_id not in teams:
                                        teams[team_id] = []
                                    teams[team_id].append(p)

                                for team_id, players in teams.items():
                                    team_result = "Victoria" if players[0]['win'] else "Derrota"
                                    st.subheader(f"Equipo ({team_result})")

                                    cols = st.columns(len(players))
                                    for i, player_details in enumerate(players):
                                        with cols[i]:
                                            champion_name = champion_names.get(player_details['championId'], f"ID:{player_details['championId']}")
                                            player_kda = f"{player_details['kills']}/{player_details['deaths']}/{player_details['assists']}"

                                            st.markdown(f"**{player_details['summonerName']}**")
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

                                if timeline_data:
                                    gold_data = {}
                                    damage_data = {}
                                    participant_map = {p['participantId']: p['summonerName'] for p in match_data['info']['participants']}

                                    for frame in timeline_data['info']['frames']:
                                        for p_id, p_frame in frame['participantFrames'].items():
                                            p_name = participant_map.get(int(p_id))
                                            if p_name:
                                                if p_name not in gold_data:
                                                    gold_data[p_name] = []
                                                    damage_data[p_name] = []

                                                gold_data[p_name].append(p_frame['totalGold'])
                                                damage_data[p_name].append(p_frame['damageStats']['totalDamageDoneToChampions'])

                                    st.subheader("Oro a lo largo del tiempo")
                                    gold_df = pd.DataFrame(gold_data)
                                    st.line_chart(gold_df)

                                    st.subheader("Daño a campeones a lo largo del tiempo")
                                    damage_df = pd.DataFrame(damage_data)
                                    st.line_chart(damage_df)

                                    st.subheader("Puntuación de Visión")
                                    vision_scores = {p['summonerName']: p['visionScore'] for p in match_data['info']['participants']}
                                    vision_df = pd.DataFrame(list(vision_scores.items()), columns=['Jugador', 'Puntuación de Visión']).sort_values('Puntuación de Visión', ascending=False)
                                    st.dataframe(vision_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Ocurrió un error al cargar el historial de partidas: {e}")
