from __future__ import annotations

from datetime import datetime, timezone

from src.database import MatchRepository, connect_repository


def _create_repository(tmp_path) -> MatchRepository:
    db_file = tmp_path / "lol_matches.db"
    return connect_repository(db_file)


def _build_match(match_id: str, *, year: int) -> dict:
    timestamp = datetime(year, 1, 15, tzinfo=timezone.utc).timestamp() * 1000
    return {
        "metadata": {"matchId": match_id},
        "info": {"gameStartTimestamp": timestamp},
    }


def test_store_matches_inserts_only_new_records(tmp_path):
    repo = _create_repository(tmp_path)
    repo.register_player("puuid-1", "Player", "LAS")

    current_year = datetime.now(timezone.utc).year
    previous_year = current_year - 1

    matches = [
        _build_match("match-current-1", year=current_year),
        _build_match("match-current-2", year=current_year),
        _build_match("match-previous", year=previous_year),
    ]

    inserted = repo.store_matches("puuid-1", matches)
    assert sorted(inserted) == ["match-current-1", "match-current-2"]

    # Un segundo guardado no debe duplicar partidas
    inserted_again = repo.store_matches("puuid-1", matches)
    assert inserted_again == []

    stored_ids = repo.get_stored_match_ids("puuid-1", year=current_year)
    assert sorted(stored_ids) == ["match-current-1", "match-current-2"]

    # Las partidas de años anteriores son ignoradas para YTD
    assert (
        "match-previous" not in repo.get_stored_match_ids("puuid-1", year=previous_year)
    )


def test_store_matches_accepts_strings_with_default_year(tmp_path):
    repo = _create_repository(tmp_path)
    repo.register_player("puuid-2", "Player", "LAS")

    current_year = datetime.now(timezone.utc).year

    inserted = repo.store_matches(
        "puuid-2",
        ["match-as-string"],
        default_year=current_year,
    )

    assert inserted == ["match-as-string"]
    assert repo.get_stored_match_ids("puuid-2", year=current_year) == [
        "match-as-string"
    ]
