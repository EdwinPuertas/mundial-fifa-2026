"""
update_daily.py — Actualización diaria de resultados del Mundial 2026
======================================================================
Fuente primaria : football-data.org API (requiere FOOTBALL_DATA_API_KEY en env)
Fuente de respaldo: resultados_hoy.json (actualización manual)

Flujo:
  1. Lee wc2026_updates.json (partidos ya registrados)
  2. Intenta obtener resultados nuevos vía API
  3. Si la API falla, carga resultados_hoy.json como fallback
  4. Escribe los partidos nuevos en wc2026_updates.json

Llamado por GitHub Actions (.github/workflows/daily_update.yml) a las 2am UTC.
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

# Mapeo: nombre del estadio (football-data.org) → clave de sede interna
STADIUM_VENUE_MAP = {
    "AT&T Stadium":                   "Arlington",
    "MetLife Stadium":                 "EastRutherford",
    "Levi's Stadium":                  "SantaClara",
    "Rose Bowl":                       "Pasadena",
    "SoFi Stadium":                    "Inglewood",
    "Lincoln Financial Field":         "Philadelphia",
    "Bank of America Stadium":         "Charlotte",
    "Arrowhead Stadium":               "KansasCity",
    "Empower Field at Mile High":      "Denver",
    "Soldier Field":                   "Chicago",
    "Hard Rock Stadium":               "Miami",
    "Gillette Stadium":                "Boston",
    "BMO Field":                       "Toronto",
    "BC Place":                        "Vancouver",
    "Stade Olympique de Montréal":     "Montreal",
    "Estadio Azteca":                  "MexicoCity",
    "Estadio BBVA":                    "Monterrey",
    "Estadio Akron":                   "Guadalajara",
}


def load_updates():
    path = OUT + "wc2026_updates.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
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


def fetch_from_api(api_key):
    url = "https://api.football-data.org/v4/competitions/WC/matches?status=FINISHED"
    req = urllib.request.Request(url, headers={"X-Auth-Token": api_key})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"[API] HTTP {e.code}: {e.reason}", file=sys.stderr)
    except Exception as e:
        print(f"[API] Error: {e}", file=sys.stderr)
    return None


def parse_api_response(data, seen_keys):
    new_matches = []
    if not data or "matches" not in data:
        return new_matches

    for m in data["matches"]:
        if m.get("status") != "FINISHED":
            continue

        score     = m.get("score", {})
        full_time = score.get("fullTime", {})
        home_g    = full_time.get("home")
        away_g    = full_time.get("away")
        if home_g is None or away_g is None:
            continue

        home_raw = m.get("homeTeam", {}).get("name", "")
        away_raw = m.get("awayTeam", {}).get("name", "")
        team_a   = TEAM_MAP.get(home_raw)
        team_b   = TEAM_MAP.get(away_raw)

        if not team_a or not team_b:
            print(f"[SKIP] Equipo desconocido: '{home_raw}' vs '{away_raw}'", file=sys.stderr)
            continue

        if match_key(team_a, team_b) in seen_keys:
            continue

        venue_raw = m.get("venue", "")
        venue     = STADIUM_VENUE_MAP.get(venue_raw, "neutral")
        date_str  = m.get("utcDate", "")[:10]

        entry = {
            "date":      date_str,
            "teamA":     team_a,
            "teamB":     team_b,
            "goalsA":    int(home_g),
            "goalsB":    int(away_g),
            "venue":     venue,
            "bk_probs":  None,
            "source":    "football-data.org",
        }
        new_matches.append(entry)
        print(f"  [API] {team_a} {int(home_g)}-{int(away_g)} {team_b}  [{venue}]")

    return new_matches


def load_manual_results(seen_keys):
    path = OUT + "resultados_hoy.json"
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    new_matches = []
    for m in data.get("matches", []):
        team_a = m.get("teamA", "")
        team_b = m.get("teamB", "")
        if not team_a or not team_b:
            continue
        if match_key(team_a, team_b) in seen_keys:
            continue

        entry = {
            "date":      m.get("date", datetime.now().strftime("%Y-%m-%d")),
            "teamA":     team_a,
            "teamB":     team_b,
            "goalsA":    int(m.get("goalsA", 0)),
            "goalsB":    int(m.get("goalsB", 0)),
            "venue":     m.get("venue", "neutral"),
            "bk_probs":  m.get("bk_probs"),
            "source":    "manual",
        }
        new_matches.append(entry)
        print(f"  [manual] {team_a} {entry['goalsA']}-{entry['goalsB']} {team_b}  [{entry['venue']}]")

    return new_matches


def main():
    updates    = load_updates()
    seen       = existing_keys(updates["matches"])
    new_matches = []

    api_key = os.environ.get("FOOTBALL_DATA_API_KEY", "").strip()
    if api_key:
        print("Consultando football-data.org API...")
        api_data = fetch_from_api(api_key)
        if api_data:
            new_matches = parse_api_response(api_data, seen)
        else:
            print("API no disponible — usando resultados_hoy.json como respaldo")
            new_matches = load_manual_results(seen)
    else:
        print("Sin API key — usando resultados_hoy.json como respaldo")
        new_matches = load_manual_results(seen)

    if new_matches:
        updates["matches"].extend(new_matches)
        print(f"\nAgregados {len(new_matches)} partido(s) nuevo(s).")
    else:
        print("Sin partidos nuevos.")

    save_updates(updates)
    return len(new_matches)


if __name__ == "__main__":
    count = main()
    sys.exit(0)
