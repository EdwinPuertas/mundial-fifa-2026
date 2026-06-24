#!/usr/bin/env python3
"""
update_historial.py — Compara predicciones del modelo vs resultados reales.
Lee   wc2026_updates.json          → partidos jugados (date/goalsA/goalsB)
Lee   predicciones_v3_compact.json → predicciones pre-calculadas
Escribe predicciones_historial.json → historial con acierto por engine
"""

import json, os, math
from datetime import datetime

HISTORIAL_FILE = "predicciones_historial.json"
UPDATES_FILE   = "wc2026_updates.json"
COMPACT_FILE   = "predicciones_v3_compact.json"


def load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def poisson_prob(lam, k):
    """P(X=k) para distribución de Poisson con media lam"""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def predict_score_poisson(lam_a, lam_b, max_k=7):
    """Marcador más probable por argmax de probabilidad conjunta Poisson"""
    best_p, best_a, best_b = -1, 0, 0
    for a in range(max_k):
        for b in range(max_k):
            p = poisson_prob(lam_a, a) * poisson_prob(lam_b, b)
            if p > best_p:
                best_p, best_a, best_b = p, a, b
    return best_a, best_b


def outcome_label(p_victoria, p_empate, p_derrota):
    if p_victoria >= p_empate and p_victoria >= p_derrota:
        return "victoria_A"
    elif p_derrota >= p_empate:
        return "victoria_B"
    return "empate"


def real_outcome(golesA, golesB):
    if golesA > golesB:   return "victoria_A"
    elif golesB > golesA: return "victoria_B"
    return "empate"


def get_probs(engine_probs, swapped):
    if swapped:
        return {"p_victoria": engine_probs["p_derrota"],
                "p_empate":   engine_probs["p_empate"],
                "p_derrota":  engine_probs["p_victoria"]}
    return {k: engine_probs[k] for k in ("p_victoria", "p_empate", "p_derrota")}


def backfill_poisson(historial, preds):
    """Añade campos Poisson a entradas existentes que no los tienen"""
    updated = 0
    for e in historial.get("entries", []):
        if "lambda_A" in e:
            continue  # ya tiene los campos
        teamA, teamB = e["teamA"], e["teamB"]
        pred, swapped = None, False
        if teamA in preds and teamB in preds[teamA]:
            pred = preds[teamA][teamB]
        elif teamB in preds and teamA in preds[teamB]:
            pred = preds[teamB][teamA]; swapped = True
        if pred is None:
            continue
        lam_A = pred.get("lambda_B" if swapped else "lambda_A", 0.0)
        lam_B = pred.get("lambda_A" if swapped else "lambda_B", 0.0)
        pred_g_A, pred_g_B = predict_score_poisson(lam_A, lam_B)
        margen_pred = round(lam_A - lam_B, 3)
        margen_real = e.get("goles_A", 0) - e.get("goles_B", 0)
        acierto_goles = (pred_g_A == e.get("goles_A") and pred_g_B == e.get("goles_B"))
        if abs(margen_pred) < 0.20:
            acierto_margen = (margen_real == 0)
        elif margen_pred > 0:
            acierto_margen = (margen_real > 0)
        else:
            acierto_margen = (margen_real < 0)
        e.update({
            "lambda_A": round(lam_A, 3),
            "lambda_B": round(lam_B, 3),
            "pred_goles_A": pred_g_A,
            "pred_goles_B": pred_g_B,
            "acierto_goles": acierto_goles,
            "margen_pred": margen_pred,
            "margen_real": margen_real,
            "acierto_margen": acierto_margen,
        })
        updated += 1
    return updated


def main():
    historial = load_json(HISTORIAL_FILE, {
        "generated": datetime.now().strftime("%Y-%m-%d"),
        "accuracy":  {"engine_A": {"correct": 0, "total": 0},
                      "engine_B": {"correct": 0, "total": 0}},
        "entries":   [],
    })
    updates = load_json(UPDATES_FILE, {"matches": []})
    preds   = load_json(COMPACT_FILE, {})

    # Backfill Poisson fields for existing entries
    n_backfilled = backfill_poisson(historial, preds)
    if n_backfilled:
        print(f"[BACKFILL] {n_backfilled} entradas actualizadas con campos Poisson.")

    recorded = {(e["fecha"], e["teamA"], e["teamB"])
                for e in historial.get("entries", [])}

    new_entries = []
    for match in updates.get("matches", []):
        # Support both formats: date/goalsA/goalsB  and  fecha/golesA/golesB
        fecha  = match.get("date") or match.get("fecha", "")
        teamA  = match.get("teamA", "")
        teamB  = match.get("teamB", "")
        golesA = int(match.get("goalsA") if match.get("goalsA") is not None
                     else match.get("golesA", 0))
        golesB = int(match.get("goalsB") if match.get("goalsB") is not None
                     else match.get("golesB", 0))

        if not teamA or not teamB or not fecha:
            continue
        if (fecha, teamA, teamB) in recorded:
            continue

        pred, swapped = None, False
        if teamA in preds and teamB in preds[teamA]:
            pred = preds[teamA][teamB]
        elif teamB in preds and teamA in preds[teamB]:
            pred = preds[teamB][teamA]; swapped = True

        if pred is None:
            print(f"  [SKIP] Sin predicción para {teamA} vs {teamB}")
            continue

        pA = get_probs(pred["engine_A"], swapped)
        pB = get_probs(pred["engine_B"], swapped)
        pred_A = outcome_label(pA["p_victoria"], pA["p_empate"], pA["p_derrota"])
        pred_B = outcome_label(pB["p_victoria"], pB["p_empate"], pB["p_derrota"])
        real   = real_outcome(golesA, golesB)

        # Poisson fields
        lam_A = pred.get("lambda_A", 0.0)
        lam_B = pred.get("lambda_B", 0.0)
        if swapped:
            lam_A, lam_B = pred.get("lambda_B", 0.0), pred.get("lambda_A", 0.0)

        pred_g_A, pred_g_B = predict_score_poisson(lam_A, lam_B)
        margen_pred = round(lam_A - lam_B, 3)
        margen_real = golesA - golesB

        # Acierto exacto de marcador
        acierto_goles = (pred_g_A == golesA and pred_g_B == golesB)

        # Acierto de margen: misma dirección (victoria del mismo equipo o empate)
        if abs(margen_pred) < 0.20:
            acierto_margen = (margen_real == 0)
        elif margen_pred > 0:
            acierto_margen = (margen_real > 0)
        else:
            acierto_margen = (margen_real < 0)

        entry = {
            "fecha":   fecha, "teamA": teamA, "teamB": teamB,
            "engine_A": {"prediccion": pred_A,
                         "p_victoria": round(pA["p_victoria"], 4),
                         "p_empate":   round(pA["p_empate"],   4),
                         "p_derrota":  round(pA["p_derrota"],  4)},
            "engine_B": {"prediccion": pred_B,
                         "p_victoria": round(pB["p_victoria"], 4),
                         "p_empate":   round(pB["p_empate"],   4),
                         "p_derrota":  round(pB["p_derrota"],  4)},
            "resultado_real": real,
            "goles_A": golesA, "goles_B": golesB,
            "acierto_A": pred_A == real, "acierto_B": pred_B == real,
            "lambda_A": round(lam_A, 3),
            "lambda_B": round(lam_B, 3),
            "pred_goles_A": pred_g_A,
            "pred_goles_B": pred_g_B,
            "acierto_goles": acierto_goles,
            "margen_pred": margen_pred,
            "margen_real": margen_real,
            "acierto_margen": acierto_margen,
        }
        new_entries.append(entry)
        recorded.add((fecha, teamA, teamB))
        ok_A = "✓" if pred_A == real else "✗"
        ok_B = "✓" if pred_B == real else "✗"
        print(f"  [{ok_A}/{ok_B}] {teamA} {golesA}-{golesB} {teamB} "
              f"| real={real} | predA={pred_A} | predB={pred_B}")

    if new_entries or n_backfilled:
        if new_entries:
            historial["entries"].extend(new_entries)
        correct_A = sum(1 for e in historial["entries"] if e["acierto_A"])
        correct_B = sum(1 for e in historial["entries"] if e["acierto_B"])
        correct_goles  = sum(1 for e in historial["entries"] if e.get("acierto_goles"))
        correct_margen = sum(1 for e in historial["entries"] if e.get("acierto_margen"))
        total     = len(historial["entries"])
        historial["accuracy"] = {
            "engine_A": {"correct": correct_A, "total": total},
            "engine_B": {"correct": correct_B, "total": total},
            "goles_exacto": {"correct": correct_goles, "total": total},
            "margen": {"correct": correct_margen, "total": total},
        }
        historial["generated"] = datetime.now().strftime("%Y-%m-%d")
        with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
            json.dump(historial, f, ensure_ascii=False, indent=2)
        pct_A = round(100 * correct_A / total) if total else 0
        pct_B = round(100 * correct_B / total) if total else 0
        pct_g = round(100 * correct_goles / total) if total else 0
        pct_m = round(100 * correct_margen / total) if total else 0
        print(f"\n[HISTORIAL] {len(new_entries)} nuevas. Total={total}")
        print(f"  Engine A: {correct_A}/{total} ({pct_A}%)")
        print(f"  Engine B: {correct_B}/{total} ({pct_B}%)")
        print(f"  Marcador exacto (Poisson): {correct_goles}/{total} ({pct_g}%)")
        print(f"  Margen correcto (Poisson): {correct_margen}/{total} ({pct_m}%)")
    else:
        print("[HISTORIAL] Sin partidas nuevas.")


if __name__ == "__main__":
    main()
