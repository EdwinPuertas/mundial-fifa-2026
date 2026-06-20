"""
update_fixtures.py — Actualización del calendario de partidos del Mundial 2026
===============================================================================
Fuente: football-data.org API (requiere FOOTBALL_DATA_API_KEY en env)

Flujo:
  1. Consulta https://api.football-data.org/v4/competitions/WC/matches (todos los partidos)
  2. Filtra solo stage == "GROUP_STAGE"
  3. Escribe fixtures.json ordenado por fecha

Llamado por GitHub Actions (.github/workflows/daily_update.yml).
"""
import json
import os
import sys
from datetime import datetime, timezone
import urllib.request
import urllib.error

OUT = os.path.dirname(os.path.abspath(__file__)) + "/"

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


def fetch_all_matches(api_key):
    url = "https://api.football-data.org/v4/competitions/WC/matches"
    req = urllib.request.Request(url, headers={"X-Auth-Token": api_key})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"[API] HTTP {e.code}: {e.reason}", file=sys.stderr)
    except Exception as e:
        print(f"[API] Error: {e}", file=sys.stderr)
    return None


def parse_group_stage(data):
    schedule = []
    if not data or "matches" not in data:
        return schedule

    for m in data["matches"]:
        if m.get("stage") != "GROUP_STAGE":
            continue

        home_raw = m.get("homeTeam", {}).get("name", "")
        away_raw = m.get("awayTeam", {}).get("name", "")
        team_a = TEAM_MAP.get(home_raw)
        team_b = TEAM_MAP.get(away_raw)

        if not team_a or not team_b:
            print(f"[SKIP] Equipo desconocido: '{home_raw}' vs '{away_raw}'", file=sys.stderr)
            continue

        group_raw = m.get("group", "")
        grupo = group_raw.replace("GROUP_", "") if group_raw else "?"

        fecha = m.get("utcDate", "")[:10]
        jornada = m.get("matchday", 1)

        entry = {
            "fecha": fecha,
            "grupo": grupo,
            "jornada": jornada,
            "teamA": team_a,
            "teamB": team_b,
        }
        schedule.append(entry)

    # Ordenar por fecha
    schedule.sort(key=lambda x: x["fecha"])
    return schedule


def main():
    api_key = os.environ.get("FOOTBALL_DATA_API_KEY", "").strip()
    if not api_key:
        print("Sin FOOTBALL_DATA_API_KEY — fixtures.json no se modifica.")
        return

    print("Consultando football-data.org API (todos los partidos)...")
    data = fetch_all_matches(api_key)
    if not data:
        print("No se pudo obtener datos de la API — fixtures.json no se modifica.")
        return

    schedule = parse_group_stage(data)
    print(f"  {len(schedule)} partidos de fase de grupos encontrados.")

    fixtures = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schedule": schedule,
    }

    path = OUT + "fixtures.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(fixtures, f, ensure_ascii=False, indent=2)
    print(f"fixtures.json guardado ({len(schedule)} partidos).")


if __name__ == "__main__":
    main()
    sys.exit(0)
