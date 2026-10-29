
import json
import os
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


def main():
    # Solicita somente dados públicos do clube.
    api = FC27API(output="raw")

    overall_data = api.get_club_overall_stats(CLUB_ID)
    members_data = api.get_member_stats(CLUB_ID)

    overall = first_record(overall_data)

    if not overall:
        raise RuntimeError("A API não retornou estatísticas gerais.")

    if not isinstance(members_data, dict):
        raise RuntimeError("Formato inesperado nas estatísticas dos jogadores.")

    members = members_data.get("members")

    if not isinstance(members, list):
        raise RuntimeError("A lista de jogadores não foi encontrada.")

    # Não publica um arquivo aparentemente válido com
    # estatísticas incompletas ou sem identificação do clube.
    returned_id = overall.get("clubId")
    if returned_id is not None and str(returned_id) != str(CLUB_ID):
        raise RuntimeError("O ID do clube retornado não corresponde.")

    def number(record, key):
        value = record.get(key)
        if value is None:
            return None
        try:
            return float(value) if "." in str(value) else int(value)
        except (ValueError, TypeError):
            return None

    stats = {
        "clubId": str(CLUB_ID),
        "platform": PLATFORM,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "overall": {
            key: number(overall, key)
            for key in (
                "gamesPlayed", "wins", "ties", "losses",
                "goals", "goalsAgainst"
            )
        },
        "members": []
    }

    for player in members:
        if not isinstance(player, dict):
            continue

        stats["members"].append({
            "name": player.get("name"),
            "gamesPlayed": number(player, "gamesPlayed"),
            "goals": number(player, "goals"),
            "assists": number(player, "assists"),
            "ratingAve": number(player, "ratingAve")
        })

    stats["members"].sort(
        key=lambda p: p["goals"] or 0,
        reverse=True
    )

    # Escreve somente após a consulta e validação terminarem.
    temp = OUTPUT.with_suffix(".tmp")
    temp.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    temp.replace(OUTPUT)

    print(
        f"Dados atualizados: {len(stats['members'])} jogadores. "
        f"Clube {CLUB_ID}."
    )


if __name__ == "__main__":
    main()
