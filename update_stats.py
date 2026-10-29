
import json
from datetime import datetime, timezone
from pathlib import Path

from fc_clubs_api import FC27API

CLUB_ID = 756201
PLATFORM = "common-gen5"
OUTPUT = Path("stats.json")


def first_record(data):
    if isinstance(data, list):
        return data[0] if data else None
    return data if isinstance(data, dict) else None


def to_number(record, key):
    value = record.get(key)
    if value is None:
        return None

    try:
        number = float(value)
        return int(number) if number.is_integer() else number
    except (ValueError, TypeError):
        return None


def main():
    api = FC27API(output="raw")

    # Estatisticas gerais
    overall_data = api.get_club_overall_stats(CLUB_ID)
    overall = first_record(overall_data)

    if not overall:
        raise RuntimeError("A EA nao retornou estatisticas gerais.")

    if str(overall.get("clubId")) != str(CLUB_ID):
        raise RuntimeError("O ID do clube nao corresponde.")

    # Jogadores
    members_data = api.get_member_stats(CLUB_ID)
    members = (
        members_data.get("members")
        if isinstance(members_data, dict)
        else None
    )

    if not isinstance(members, list):
        raise RuntimeError("Lista de jogadores indisponivel.")

    # Ultimas partidas amistosas retornadas pela EA.
    friendlies_data = api.get_club_matches(
        CLUB_ID,
        match_type="friendlyMatch",
        count=10
    )

    if not isinstance(friendlies_data, list):
        raise RuntimeError("Formato inesperado no historico de amistosos.")

    stats = {
        "clubId": str(CLUB_ID),
        "platform": PLATFORM,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "overall": {
            key: to_number(overall, key)
            for key in (
                "gamesPlayed",
                "wins",
                "ties",
                "losses",
                "goals",
                "goalsAgainst",
            )
        },
        "members": [],
        "friendlyMatches": friendlies_data,
    }

    for player in members:
        if not isinstance(player, dict):
            continue

        stats["members"].append({
            "name": player.get("name"),
            "gamesPlayed": to_number(player, "gamesPlayed"),
            "goals": to_number(player, "goals"),
            "assists": to_number(player, "assists"),
            "ratingAve": to_number(player, "ratingAve"),
        })

    stats["members"].sort(
        key=lambda player: player["goals"] or 0,
        reverse=True
    )

    # Grava apenas depois de todas as consultas serem concluidas.
    temp = OUTPUT.with_suffix(".tmp")
    temp.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8"
    )
    temp.replace(OUTPUT)

    print(f"Clube: {CLUB_ID}")
    print(f"Jogadores: {len(stats['members'])}")
    print(f"Amistosos retornados: {len(friendlies_data)}")
    print("Arquivo stats.json atualizado.")


if __name__ == "__main__":
    main()
