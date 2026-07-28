def build_daily_tips(fixtures, limit=5):
    tips = []

    if not isinstance(fixtures, list):
        return tips

    for match in fixtures:
        home = match.get("match_hometeam_name")
        away = match.get("match_awayteam_name")
        status = str(match.get("match_status", "")).lower()

        if not home or not away:
            continue

        if status and status not in ["not started", "scheduled", ""]:
            continue

        tip = {
            "match_id": match.get("match_id"),
            "match": f"{home} vs {away}",
            "league": match.get("league_name", "Football"),
            "kickoff": match.get("match_time", ""),
            "prediction": "Over 1.5 Goals",
            "confidence": 62
        }

        tips.append(tip)

    return tips[:limit]
