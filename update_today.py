"""
update_today.py — Partidos del día para el Mundial 2026
=========================================================
Fuente primaria : football-data.org API (requiere FOOTBALL_DATA_API_KEY en env)
Fallback        : fixtures.json + wc2026_updates.json

Flujo:
  1. Con API key: consulta los partidos de hoy (todos los estados)
     - Guarda en today.json
     - Los FINISHED los añade también a wc2026_updates.json (si no estaban)
  2. Sin API key: filtra fixtures.json por hoy,
     cruza con wc2026_updates.json para ver cuáles ya tienen resultado
"""
import json
import os
import sys
from datetime import datetime, timezone
import urllib.request
import urllib.error

OUT = os.path.dirname(os.path.abspath(__file__)) + "/"

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# Mapeo: nombres football-data.org → nombres internos en español
TEAM_MAP = {
    "France":                   "Francia",
    "Spain":                    "España",
    "Argentina":                "Argentina",
    "England":                  "Inglaterra",
    "Portugal":                 "Portugal",
    "Brazil":                   "Brasil",
    "Netherlands":              "Países Bajos",
    "Morocco":                  "Marruecos",
    "Belgium":                  "Bélgica",
    "Germany":                  "Alemania",
    "Croatia":                  "Croacia",
    "Colombia":                 "Colombia",
    "Senegal":                  "Senegal",
    "Mexico":                   "México",
    "United States":            "Estados Unidos",
    "USA":                      "Estados Unidos",
    "Uruguay":                  "Uruguay",
    "Japan":                    "Japón",
    "Switzerland":              "Suiza",
    "IR Iran":                  "Irán",
    "Iran":                     "Irán",
    "Turkey":                   "Turquía",
    "Ecuador":                  "Ecuador",
    "Austria":                  "Austria",
    "Korea Republic":           "Corea del Sur",
    "South Korea":              "Corea del Sur",
    "Australia":                "Australia",
    "Algeria":                  "Argelia",
    "Egypt":                    "Egipto",
    "Canada":                   "Canadá",
    "Norway":                   "Noruega",
    "Panama":                   "Panamá",
    "Côte d'Ivoire":            "Costa de Marfil",
    "Ivory Coast":              "Costa de Marfil",
    "Sweden":                   "Suecia",
    "Paraguay":                 "Paraguay",
    "Czech Republic":           "República Checa",
    "Czechia":                  "República Checa",
    "Scotland":                 "Escocia",
    "Tunisia":                  "Túnez",
    "DR Congo":                 "RD Congo",
    "Uzbekistan":               "Uzbekistán",
    "Qatar":                    "Qatar",
    "Iraq":                     "Irak",
    "South Africa":             "Sudáfrica",
    "Saudi Arabia":             "Arabia Saudita",
    "Jordan":                   "Jordania",
    "Bosnia and Herzegovina":   "Bosnia y Herz.",
    "Cape Verde":               "Cabo Verde",
    "Ghana":                    "Ghana",
    "Curaçao":                  "Curazao",
    "Haiti":                    "Haití",
    "New Zealand":              "Nueva Zelanda",
}


def load_fixtures():
    path = OUT + "fixtures.json"
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"schedule": []}


def load_updates():
    path = OUT + "wc2026_updates.json"
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"last_updated": None, "matches": []}


def save_updates(data):
    data["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(OUT + "wc2026_updates.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"wc2026_updates.json guardado ({len(data['matches'])} partidos en total)")


def match_key(team_a, team_b):
    return f"{team_a}:{team_b}"


def existing_keys(matches):
    keys = set()
    for m in matches:
        keys.add(match_key(m["teamA"], m["teamB"]))
        keys.add(match_key(m["teamB"], m["teamA"]))
    return keys


def fetch_today_from_api(api_key, date_str):
    url = f"https://api.football-data.org/v4/competitions/WC/matches?dateFrom={date_str}&dateTo={date_str}"
    req = urllib.request.Request(url, headers={"X-Auth-Token": api_key})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"[API] HTTP {e.code}: {e.reason}", file=sys.stderr)
    except Exception as e:
        print(f"[API] Error: {e}", file=sys.stderr)
    return None


def get_grupo_from_fixture(team_a, team_b, fixtures):
    """Look up the group for a match in fixtures."""
    for f in fixtures.get("schedule", []):
        if (f["teamA"] == team_a and f["teamB"] == team_b) or \
           (f["teamA"] == team_b and f["teamB"] == team_a):
            return f.get("grupo", ""), f.get("jornada", 0)
    return "", 0


def parse_api_today(data, fixtures):
    """Parse API response and return today_matches list + finished matches for updates."""
    today_matches = []
    finished_for_updates = []

    if not data or "matches" not in data:
        return today_matches, finished_for_updates

    for m in data["matches"]:
        status = m.get("status", "")
        if status not in ("SCHEDULED", "IN_PLAY", "PAUSED", "FINISHED", "TIMED"):
            continue

        home_raw = m.get("homeTeam", {}).get("name", "")
        away_raw = m.get("awayTeam", {}).get("name", "")
        team_a = TEAM_MAP.get(home_raw)
        team_b = TEAM_MAP.get(away_raw)

        if not team_a or not team_b:
            print(f"[SKIP] Equipo desconocido: '{home_raw}' vs '{away_raw}'", file=sys.stderr)
            continue

        # Extract group from API: "GROUP_A" → "A"
        group_raw = m.get("group", "") or ""
        grupo = group_raw.replace("GROUP_", "") if group_raw.startswith("GROUP_") else group_raw

        # If not in API response, look up from fixtures
        if not grupo:
            grupo, _ = get_grupo_from_fixture(team_a, team_b, fixtures)

        # Get jornada from fixtures
        _, jornada = get_grupo_from_fixture(team_a, team_b, fixtures)

        # UTC time
        hora_utc = m.get("utcDate", "")[11:16]

        score = m.get("score", {})
        full_time = score.get("fullTime", {})
        goals_a = full_time.get("home")
        goals_b = full_time.get("away")

        if status in ("IN_PLAY", "PAUSED"):
            in_play_score = score.get("halfTime", {})
            # Try to get current score
            current = score.get("fullTime", {})
            goals_a = current.get("home")
            goals_b = current.get("away")

        entry = {
            "teamA": team_a,
            "teamB": team_b,
            "grupo": grupo,
            "jornada": jornada,
            "hora_utc": hora_utc,
            "status": status if status in ("SCHEDULED", "IN_PLAY", "PAUSED", "FINISHED") else "SCHEDULED",
            "goalsA": int(goals_a) if goals_a is not None and status == "FINISHED" else (int(goals_a) if goals_a is not None else None),
            "goalsB": int(goals_b) if goals_b is not None and status == "FINISHED" else (int(goals_b) if goals_b is not None else None),
        }
        today_matches.append(entry)
        print(f"  [{status}] {team_a} vs {team_b} Grupo {grupo} J{jornada} {hora_utc}")

        # Collect finished matches for wc2026_updates
        if status == "FINISHED" and goals_a is not None and goals_b is not None:
            finished_for_updates.append({
                "teamA": team_a,
                "teamB": team_b,
                "goalsA": int(goals_a),
                "goalsB": int(goals_b),
                "date": m.get("utcDate", "")[:10],
            })

    return today_matches, finished_for_updates


def build_fallback_today(fixtures, updates):
    """Build today's matches from fixtures.json + wc2026_updates.json.
    Preserves hora_utc from existing today.json when fecha matches."""
    today_matches = []

    # Build a map from match pair → result from updates
    result_map = {}
    for mu in updates.get("matches", []):
        result_map[match_key(mu["teamA"], mu["teamB"])] = mu
        result_map[match_key(mu["teamB"], mu["teamA"])] = {
            "teamA": mu["teamB"],
            "teamB": mu["teamA"],
            "goalsA": mu["goalsB"],
            "goalsB": mu["goalsA"],
            "date": mu.get("date", ""),
        }

    # Load existing today.json to preserve hora_utc values
    hora_map = {}
    existing_path = OUT + "today.json"
    if os.path.exists(existing_path):
        try:
            with open(existing_path, encoding="utf-8") as f:
                existing = json.load(f)
            if existing.get("fecha") == TODAY:
                for m in existing.get("matches", []):
                    h = m.get("hora_utc", "")
                    if h:
                        hora_map[match_key(m["teamA"], m["teamB"])] = h
                        hora_map[match_key(m["teamB"], m["teamA"])] = h
        except Exception:
            pass

    for f in fixtures.get("schedule", []):
        if f.get("fecha") != TODAY:
            continue

        team_a = f["teamA"]
        team_b = f["teamB"]
        grupo = f.get("grupo", "")
        jornada = f.get("jornada", 0)
        hora_utc = hora_map.get(match_key(team_a, team_b), "")

        key = match_key(team_a, team_b)
        if key in result_map:
            r = result_map[key]
            entry = {
                "teamA": team_a,
                "teamB": team_b,
                "grupo": grupo,
                "jornada": jornada,
                "hora_utc": hora_utc,
                "status": "FINISHED",
                "goalsA": r["goalsA"],
                "goalsB": r["goalsB"],
            }
        else:
            entry = {
                "teamA": team_a,
                "teamB": team_b,
                "grupo": grupo,
                "jornada": jornada,
                "hora_utc": hora_utc,
                "status": "SCHEDULED",
                "goalsA": None,
                "goalsB": None,
            }

        today_matches.append(entry)
        print(f"  [fallback/{entry['status']}] {team_a} vs {team_b} Grupo {grupo} J{jornada} {hora_utc}")

    return today_matches


def save_today(matches):
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = {
        "fecha": TODAY,
        "updated": now_str,
        "matches": matches,
    }
    with open(OUT + "today.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"today.json guardado: {len(matches)} partidos para {TODAY}")


def main():
    fixtures = load_fixtures()
    updates = load_updates()

    api_key = os.environ.get("FOOTBALL_DATA_API_KEY", "").strip()

    if api_key:
        print(f"Consultando football-data.org API para {TODAY}...")
        api_data = fetch_today_from_api(api_key, TODAY)
        if api_data:
            today_matches, finished_for_updates = parse_api_today(api_data, fixtures)

            # Add finished matches to wc2026_updates if not already there
            if finished_for_updates:
                seen = existing_keys(updates["matches"])
                new_updates = []
                for fm in finished_for_updates:
                    key = match_key(fm["teamA"], fm["teamB"])
                    if key not in seen:
                        new_updates.append({
                            "date": fm["date"],
                            "teamA": fm["teamA"],
                            "teamB": fm["teamB"],
                            "goalsA": fm["goalsA"],
                            "goalsB": fm["goalsB"],
                            "venue": "neutral",
                            "bk_probs": None,
                            "source": "football-data.org",
                        })
                        seen.add(key)
                        seen.add(match_key(fm["teamB"], fm["teamA"]))
                        print(f"  [updates] {fm['teamA']} {fm['goalsA']}-{fm['goalsB']} {fm['teamB']}")
                if new_updates:
                    updates["matches"].extend(new_updates)
                    save_updates(updates)
                    print(f"Añadidos {len(new_updates)} partido(s) terminados a wc2026_updates.json")
                else:
                    print("Sin partidos terminados nuevos para wc2026_updates.json")
        else:
            print("API no disponible — usando fallback de fixtures.json")
            today_matches = build_fallback_today(fixtures, updates)
    else:
        print(f"Sin API key — usando fallback de fixtures.json para {TODAY}")
        today_matches = build_fallback_today(fixtures, updates)

    save_today(today_matches)
    return len(today_matches)


if __name__ == "__main__":
    count = main()
    print(f"Total: {count} partido(s) para hoy.")
    sys.exit(0)
