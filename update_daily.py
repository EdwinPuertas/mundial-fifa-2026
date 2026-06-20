#!/usr/bin/env python3
"""
Daily update: compare model predictions vs actual WC 2026 results.
Reads  wc2026_updates.json   → new match scores
Reads  predicciones_v3_compact.json → pre-computed predictions
Writes predicciones_historial.json  → running accuracy log
"""

import json
import os
from datetime import datetime

HISTORIAL_FILE = "predicciones_historial.json"
UPDATES_FILE   = "wc2026_updates.json"
COMPACT_FILE   = "predicciones_v3_compact.json"


def load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def outcome_label(p_victoria, p_empate, p_derrota):
    if p_victoria >= p_empate and p_victoria >= p_derrota:
        return "victoria_A"
    elif p_derrota >= p_empate:
        return "victoria_B"
    return "empate"


def real_outcome(golesA, golesB):
    if golesA > golesB:
        return "victoria_A"
    elif golesB > golesA:
        return "victoria_B"
    return "empate"


def get_probs(engine_probs, swapped):
    """Return probs dict oriented so team A is always the first team."""
    if swapped:
        return {
            "p_victoria": engine_probs["p_derrota"],
            "p_empate":   engine_probs["p_empate"],
            "p_derrota":  engine_probs["p_victoria"],
        }
    return {
        "p_victoria": engine_probs["p_victoria"],
        "p_empate":   engine_probs["p_empate"],
        "p_derrota":  engine_probs["p_derrota"],
    }


def main():
    historial = load_json(HISTORIAL_FILE, {
        "generated": datetime.now().strftime("%Y-%m-%d"),
        "accuracy": {
            "engine_A": {"correct": 0, "total": 0},
            "engine_B": {"correct": 0, "total": 0},
        },
        "entries": [],
    })

    updates = load_json(UPDATES_FILE, {"matches": []})
    preds   = load_json(COMPACT_FILE, {})

    recorded = {
        (e["fecha"], e["teamA"], e["teamB"])
        for e in historial.get("entries", [])
    }

    new_entries = []
    for match in updates.get("matches", []):
        fecha  = match.get("fecha", "")
        teamA  = match.get("teamA", "")
        teamB  = match.get("teamB", "")
        golesA = int(match.get("golesA", 0))
        golesB = int(match.get("golesB", 0))

        if (fecha, teamA, teamB) in recorded:
            continue

        # Look up prediction — try both orderings
        pred    = None
        swapped = False
        if teamA in preds and teamB in preds[teamA]:
            pred = preds[teamA][teamB]
        elif teamB in preds and teamA in preds[teamB]:
            pred = preds[teamB][teamA]
            swapped = True

        if pred is None:
            print(f"  [SKIP] Sin predicción para {teamA} vs {teamB}")
            continue

        pA = get_probs(pred["engine_A"], swapped)
        pB = get_probs(pred["engine_B"], swapped)

        pred_A = outcome_label(pA["p_victoria"], pA["p_empate"], pA["p_derrota"])
        pred_B = outcome_label(pB["p_victoria"], pB["p_empate"], pB["p_derrota"])
        real   = real_outcome(golesA, golesB)

        entry = {
            "fecha":   fecha,
            "teamA":   teamA,
            "teamB":   teamB,
            "engine_A": {
                "prediccion": pred_A,
                "p_victoria": round(pA["p_victoria"], 4),
                "p_empate":   round(pA["p_empate"],   4),
                "p_derrota":  round(pA["p_derrota"],  4),
            },
            "engine_B": {
                "prediccion": pred_B,
                "p_victoria": round(pB["p_victoria"], 4),
                "p_empate":   round(pB["p_empate"],   4),
                "p_derrota":  round(pB["p_derrota"],  4),
            },
            "resultado_real": real,
            "goles_A":   golesA,
            "goles_B":   golesB,
            "acierto_A": pred_A == real,
            "acierto_B": pred_B == real,
        }
        new_entries.append(entry)
        recorded.add((fecha, teamA, teamB))

        ok_A = "✓" if pred_A == real else "✗"
        ok_B = "✓" if pred_B == real else "✗"
        print(f"  [{ok_A}/{ok_B}] {teamA} {golesA}-{golesB} {teamB} "
              f"| real={real} | predA={pred_A} | predB={pred_B}")

    if new_entries:
        historial["entries"].extend(new_entries)
        correct_A = sum(1 for e in historial["entries"] if e["acierto_A"])
        correct_B = sum(1 for e in historial["entries"] if e["acierto_B"])
        total     = len(historial["entries"])
        historial["accuracy"] = {
            "engine_A": {"correct": correct_A, "total": total},
            "engine_B": {"correct": correct_B, "total": total},
        }
        historial["generated"] = datetime.now().strftime("%Y-%m-%d")

        with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
            json.dump(historial, f, ensure_ascii=False, indent=2)

        pct_A = round(100 * correct_A / total) if total else 0
        pct_B = round(100 * correct_B / total) if total else 0
        print(f"\n[HISTORIAL] {len(new_entries)} nuevas. Total={total}")
        print(f"  Engine A: {correct_A}/{total} ({pct_A}%)")
        print(f"  Engine B: {correct_B}/{total} ({pct_B}%)")
    else:
        print("[HISTORIAL] Sin partidas nuevas.")


if __name__ == "__main__":
    main()
