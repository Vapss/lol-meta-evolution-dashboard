"""Utilities para persistir partidas de League of Legends en SQLite.

El módulo crea una base de datos sencilla orientada a almacenar los
identificadores de partida consultados para cada jugador (PUUID). La lógica
principal se centra en agregar únicamente las partidas del año en curso (YTD)
que todavía no existen en la base, permitiendo así hacer consultas recurrentes
sin duplicados.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import sqlite3
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Sequence, Tuple


# Ruta por defecto para la base de datos dentro del repositorio
DEFAULT_DB_PATH = Path("data/processed/lol_matches.db")


@dataclass(frozen=True)
class MatchRecord:
    """Representa una partida asociada a un jugador.

    Attributes:
        match_id: Identificador único de la partida.
        game_year: Año en que se jugó la partida.
        raw_json: Representación cruda opcional de la partida.
    """

    match_id: str
    game_year: int
    raw_json: Optional[str] = None


def _initialize_database(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Crea (si no existe) e inicializa la base de datos de partidas."""

    db_path = Path(db_path)
    if not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS players (
            puuid TEXT PRIMARY KEY,
            game_name TEXT,
            tag_line TEXT,
            last_searched TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS matches (
            match_id TEXT NOT NULL,
            puuid TEXT NOT NULL,
            game_year INTEGER NOT NULL,
            raw_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (puuid) REFERENCES players(puuid),
            PRIMARY KEY (match_id, puuid)
        );

        CREATE INDEX IF NOT EXISTS idx_matches_puuid_year
            ON matches (puuid, game_year);

        CREATE TABLE IF NOT EXISTS match_timelines (
            match_id TEXT PRIMARY KEY,
            timeline_json TEXT NOT NULL,
            FOREIGN KEY (match_id) REFERENCES matches(match_id)
        );
        """
    )
    return conn


def _determine_year_from_match(match: dict) -> Optional[int]:
    """Extrae el año de la partida a partir de la estructura devuelta por Riot API."""

    if not isinstance(match, dict):
        return None

    timestamp_ms = None
    info = match.get("info")
    if isinstance(info, dict):
        timestamp_ms = info.get("gameStartTimestamp") or info.get("gameCreation")

    if timestamp_ms is None:
        timestamp_ms = match.get("gameStartTimestamp")

    if timestamp_ms is None:
        return None

    # Riot API devuelve timestamps en milisegundos.
    if timestamp_ms > 1e10:  # heurística robusta para distinguir milisegundos de segundos.
        timestamp_ms /= 1000

    return datetime.fromtimestamp(timestamp_ms, tz=timezone.utc).year


def _parse_match_records(
    matches: Iterable[dict | str],
    default_year: Optional[int],
    current_year: int,
) -> Sequence[MatchRecord]:
    """Convierte una secuencia de objetos en instancias `MatchRecord`."""

    records: List[MatchRecord] = []
    for match in matches:
        match_id: Optional[str] = None
        raw_json: Optional[str] = None
        match_year: Optional[int] = None

        if isinstance(match, dict):
            metadata = match.get("metadata")
            if isinstance(metadata, dict):
                match_id = metadata.get("matchId")
            if not match_id:
                match_id = match.get("matchId") or match.get("id")
            raw_json = json.dumps(match, ensure_ascii=False)
            match_year = _determine_year_from_match(match)
        elif isinstance(match, str):
            match_id = match

        if not match_id:
            continue

        if match_year is None:
            match_year = default_year if default_year is not None else current_year

        if match_year != current_year:
            continue

        records.append(MatchRecord(match_id=match_id, game_year=match_year, raw_json=raw_json))

    return records


class MatchRepository:
    """Encapsula las operaciones de persistencia sobre la base de datos local.

    La clase actúa como fachada para el backend y evita exponer la conexión
    interna, lo que facilita mantener el almacenamiento disponible sólo desde
    el propio proyecto (sin endpoints HTTP adicionales).
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def __enter__(self) -> "MatchRepository":
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        self.close()

    @classmethod
    def connect(cls, db_path: Path | str = DEFAULT_DB_PATH) -> "MatchRepository":
        """Crea un repositorio conectado a la ruta indicada."""

        connection = _initialize_database(db_path)
        return cls(connection)

    def close(self) -> None:
        """Cierra la conexión subyacente si sigue abierta."""

        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def _get_connection(self) -> sqlite3.Connection:
        """Devuelve la conexión activa o lanza un error si fue cerrada."""

        if self._connection is None:
            raise RuntimeError("La conexión a la base de datos ha sido cerrada.")
        return self._connection

    def register_player(
        self, puuid: str, game_name: str | None = None, tag_line: str | None = None
    ) -> None:
        """Registra o actualiza la información básica de un jugador."""

        conn = self._get_connection()
        timestamp = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO players (puuid, game_name, tag_line, last_searched)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(puuid) DO UPDATE SET
                game_name = COALESCE(excluded.game_name, players.game_name),
                tag_line = COALESCE(excluded.tag_line, players.tag_line),
                last_searched = excluded.last_searched;
            """,
            (puuid, game_name, tag_line, timestamp),
        )
        conn.commit()

    def store_matches(
        self,
        puuid: str,
        matches: Iterable[dict | str],
        *,
        default_year: Optional[int] = None,
    ) -> List[str]:
        """Guarda partidas nuevas para un jugador sólo si pertenecen al año actual."""

        conn = self._get_connection()
        current_year = datetime.now(timezone.utc).year
        records = _parse_match_records(matches, default_year, current_year)

        if not records:
            return []

        # Bulk check for existing matches to avoid N+1 queries.
        # Process in batches to respect SQLite variable limit (999 by default).
        match_ids = [record.match_id for record in records]
        existing_ids: set[str] = set()
        batch_size = 500  # Conservative batch size well under SQLite limit

        for i in range(0, len(match_ids), batch_size):
            batch = match_ids[i : i + batch_size]
            # Safe: placeholders is generated from len(batch), not user input
            placeholders = ",".join("?" * len(batch))
            cursor = conn.execute(
                f"SELECT match_id FROM matches WHERE match_id IN ({placeholders});",
                batch,
            )
            existing_ids.update(row[0] for row in cursor.fetchall())

        inserted: List[str] = []

        for record in records:
            if record.match_id in existing_ids:
                continue

            conn.execute(
                """
                INSERT INTO matches (match_id, puuid, game_year, raw_json)
                VALUES (?, ?, ?, ?);
                """,
                (record.match_id, puuid, record.game_year, record.raw_json),
            )
            inserted.append(record.match_id)

        if inserted:
            conn.commit()

        return inserted

    def get_stored_match_ids(self, puuid: str, *, year: Optional[int] = None) -> List[str]:
        """Obtiene los IDs de partidas almacenadas para un jugador."""

        conn = self._get_connection()
        if year is None:
            cursor = conn.execute(
                "SELECT match_id FROM matches WHERE puuid = ? ORDER BY match_id ASC;",
                (puuid,),
            )
        else:
            cursor = conn.execute(
                """
                SELECT match_id
                FROM matches
                WHERE puuid = ? AND game_year = ?
                ORDER BY match_id ASC;
                """,
                (puuid, year),
            )

        return [row[0] for row in cursor.fetchall()]

    def get_stored_matches(self, puuid: str, *, year: Optional[int] = None) -> List[MatchRecord]:
        """Obtiene las partidas almacenadas para un jugador."""

        conn = self._get_connection()
        if year is None:
            cursor = conn.execute(
                "SELECT match_id, game_year, raw_json FROM matches WHERE puuid = ? ORDER BY match_id DESC;",
                (puuid,),
            )
        else:
            cursor = conn.execute(
                """
                SELECT match_id, game_year, raw_json
                FROM matches
                WHERE puuid = ? AND game_year = ?
                ORDER BY match_id DESC;
                """,
                (puuid, year),
            )

        return [MatchRecord(match_id, game_year, raw_json) for match_id, game_year, raw_json in cursor.fetchall()]

    def get_player(self, puuid: str) -> Optional[Tuple[str, Optional[str], Optional[str]]]:
        """Recupera la información básica de un jugador almacenado."""

        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT puuid, game_name, tag_line FROM players WHERE puuid = ? LIMIT 1;",
            (puuid,),
        )
        row = cursor.fetchone()
        return row if row is not None else None

    def store_match_timeline(self, match_id: str, timeline_data: dict) -> None:
        """Guarda la línea de tiempo de una partida."""

        conn = self._get_connection()
        timeline_json = json.dumps(timeline_data, ensure_ascii=False)
        conn.execute(
            """
            INSERT INTO match_timelines (match_id, timeline_json)
            VALUES (?, ?)
            ON CONFLICT(match_id) DO NOTHING;
            """,
            (match_id, timeline_json),
        )
        conn.commit()

    def get_match_timeline(self, match_id: str) -> Optional[dict]:
        """Recupera la línea de tiempo de una partida."""

        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT timeline_json FROM match_timelines WHERE match_id = ? LIMIT 1;",
            (match_id,),
        )
        row = cursor.fetchone()
        return json.loads(row[0]) if row and row[0] else None


def connect_repository(db_path: Path | str = DEFAULT_DB_PATH) -> MatchRepository:
    """Función de conveniencia para abrir un repositorio listo para usarse."""

    return MatchRepository.connect(db_path)


def iter_stored_matches(
    repo: MatchRepository, puuid: str, *, year: Optional[int] = None
) -> Iterator[str]:
    """Genera los identificadores de partidas almacenadas para un jugador."""

    yield from repo.get_stored_match_ids(puuid, year=year)


__all__ = [
    "DEFAULT_DB_PATH",
    "MatchRecord",
    "MatchRepository",
    "connect_repository",
    "iter_stored_matches",
]

