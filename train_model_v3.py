"""
MODELO v3 — Mundial FIFA 2026
==============================
Cambios vs v2:
  • Configuración de alineaciones: formación táctica + estilo por equipo (CONFIGURABLE)
  • Engine A: MLP profundo con Self-Attention (redes 2ª generación, sin TF/PyTorch)
  • Engine B: XGBoost agresivo (max_depth=7, low min_child_weight)
  • Output DUAL: ambos engines independientes en el JSON
  • Eliminadas variables de expertos: injury_factor (experto), is_host, xg_qual (=0)
  • Nuevas features: tácticas por formación, experiencia confederación WC,
    interacciones cruzadas ataque×defensa, style_score, set_piece threat
  • Predicciones más agresivas: calibración de temperatura T=0.55 (sharper)
  • Modelos de goles independientes por engine
"""

import os
import numpy as np
import pandas as pd
import json
import joblib
import warnings
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import (classification_report, confusion_matrix, roc_auc_score,
                              roc_curve, mean_absolute_error, f1_score, accuracy_score)
from sklearn.preprocessing import label_binarize
import xgboost as xgb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings('ignore')
np.random.seed(42)

OUT = "/home/user/mundial-fifa-2026/"

# ═══════════════════════════════════════════════════════════════════════════════
# 0. CONFIGURACIÓN DE ALINEACIONES — EDITABLE POR EL USUARIO
#    formation: "4-3-3" | "4-4-2" | "4-2-3-1" | "3-4-3" | "3-5-2" | "5-3-2"
#                "4-5-1" | "5-4-1" | "4-1-4-1"
#    style:     "attacking" | "balanced" | "defensive" | "counterattack"
# ═══════════════════════════════════════════════════════════════════════════════
LINEUP = {
    "Francia":         {"formation": "4-2-3-1", "style": "balanced"},
    "España":          {"formation": "4-2-3-1", "style": "attacking"},
    "Argentina":       {"formation": "4-3-3",   "style": "attacking"},
    "Inglaterra":      {"formation": "4-3-3",   "style": "balanced"},
    "Portugal":        {"formation": "4-2-3-1", "style": "attacking"},
    "Brasil":          {"formation": "4-3-3",   "style": "attacking"},
    "Países Bajos":    {"formation": "4-3-3",   "style": "attacking"},
    "Marruecos":       {"formation": "4-5-1",   "style": "defensive"},
    "Bélgica":         {"formation": "4-2-3-1", "style": "balanced"},
    "Alemania":        {"formation": "4-2-3-1", "style": "attacking"},
    "Croacia":         {"formation": "4-3-3",   "style": "balanced"},
    "Colombia":        {"formation": "4-2-3-1", "style": "attacking"},
    "Senegal":         {"formation": "4-3-3",   "style": "balanced"},
    "México":          {"formation": "4-3-3",   "style": "balanced"},
    "Estados Unidos":  {"formation": "4-3-3",   "style": "balanced"},
    "Uruguay":         {"formation": "4-4-2",   "style": "defensive"},
    "Japón":           {"formation": "4-2-3-1", "style": "balanced"},
    "Suiza":           {"formation": "3-4-3",   "style": "defensive"},
    "Irán":            {"formation": "4-5-1",   "style": "defensive"},
    "Turquía":         {"formation": "4-2-3-1", "style": "attacking"},
    "Ecuador":         {"formation": "3-4-3",   "style": "balanced"},
    "Austria":         {"formation": "4-2-3-1", "style": "balanced"},
    "Corea del Sur":   {"formation": "4-2-3-1", "style": "balanced"},
    "Australia":       {"formation": "4-4-2",   "style": "defensive"},
    "Argelia":         {"formation": "4-2-3-1", "style": "defensive"},
    "Egipto":          {"formation": "4-2-3-1", "style": "defensive"},
    "Canadá":          {"formation": "4-3-3",   "style": "attacking"},
    "Noruega":         {"formation": "4-2-3-1", "style": "attacking"},
    "Panamá":          {"formation": "4-5-1",   "style": "defensive"},
    "Costa de Marfil": {"formation": "4-4-2",   "style": "attacking"},
    "Suecia":          {"formation": "3-5-2",   "style": "balanced"},
    "Paraguay":        {"formation": "5-3-2",   "style": "defensive"},
    "República Checa": {"formation": "4-2-3-1", "style": "balanced"},
    "Escocia":         {"formation": "3-5-2",   "style": "defensive"},
    "Túnez":           {"formation": "4-2-3-1", "style": "defensive"},
    "RD Congo":        {"formation": "5-3-2",   "style": "defensive"},
    "Uzbekistán":      {"formation": "4-4-2",   "style": "defensive"},
    "Qatar":           {"formation": "5-3-2",   "style": "defensive"},
    "Irak":            {"formation": "4-4-2",   "style": "defensive"},
    "Sudáfrica":       {"formation": "4-3-3",   "style": "defensive"},
    "Arabia Saudita":  {"formation": "4-2-3-1", "style": "defensive"},
    "Jordania":        {"formation": "5-4-1",   "style": "defensive"},
    "Bosnia y Herz.":  {"formation": "4-3-3",   "style": "balanced"},
    "Cabo Verde":      {"formation": "4-5-1",   "style": "defensive"},
    "Ghana":           {"formation": "4-2-3-1", "style": "balanced"},
    "Curazao":         {"formation": "3-5-2",   "style": "defensive"},
    "Haití":           {"formation": "5-3-2",   "style": "defensive"},
    "Nueva Zelanda":   {"formation": "4-4-2",   "style": "balanced"},
}

FORMATION_FEATURES = {
    "4-3-3":   {"attack": 0.88, "defense": 0.62, "width": 0.92, "pressing": 0.85, "set_piece": 0.65},
    "4-4-2":   {"attack": 0.72, "defense": 0.76, "width": 0.78, "pressing": 0.70, "set_piece": 0.78},
    "4-2-3-1": {"attack": 0.78, "defense": 0.72, "width": 0.80, "pressing": 0.76, "set_piece": 0.75},
    "3-4-3":   {"attack": 0.85, "defense": 0.68, "width": 0.80, "pressing": 0.82, "set_piece": 0.68},
    "3-5-2":   {"attack": 0.75, "defense": 0.78, "width": 0.65, "pressing": 0.72, "set_piece": 0.82},
    "5-3-2":   {"attack": 0.58, "defense": 0.92, "width": 0.50, "pressing": 0.55, "set_piece": 0.78},
    "4-5-1":   {"attack": 0.55, "defense": 0.90, "width": 0.60, "pressing": 0.65, "set_piece": 0.75},
    "5-4-1":   {"attack": 0.48, "defense": 0.95, "width": 0.45, "pressing": 0.50, "set_piece": 0.72},
    "4-1-4-1": {"attack": 0.68, "defense": 0.82, "width": 0.72, "pressing": 0.78, "set_piece": 0.72},
}

STYLE_MOD = {
    "attacking":    {"am": 1.18, "dm": 0.88, "pm": 1.12},
    "defensive":    {"am": 0.82, "dm": 1.18, "pm": 0.82},
    "balanced":     {"am": 1.00, "dm": 1.00, "pm": 1.00},
    "counterattack":{"am": 0.90, "dm": 1.08, "pm": 0.78},
}
STYLE_SCORE = {"attacking": 1.18, "balanced": 1.00, "defensive": 0.82, "counterattack": 0.92}

CONF_MAP = {"UEFA": 0, "CONMEBOL": 1, "CONCACAF": 2, "CAF": 3, "AFC": 4, "OFC": 5}
CONF_WC_EXP = {"UEFA": 0.82, "CONMEBOL": 0.78, "CONCACAF": 0.45, "CAF": 0.42, "AFC": 0.40, "OFC": 0.25}

# ═══════════════════════════════════════════════════════════════════════════════
# VENUES — Estadios 2026 con datos ambientales
#   altitude  : metros sobre el nivel del mar
#   temp      : temperatura media en °C (junio-julio)
#   wind      : velocidad media del viento (km/h)
#   hydration : severidad de pause de hidratación obligatoria (0=ninguna, 1=máxima)
#               → penaliza equipos de alto pressing y estilo atacante
# ═══════════════════════════════════════════════════════════════════════════════
VENUES = {
    # ── USA ──────────────────────────────────────────────────────────────────
    "Arlington":     {"altitude":185,  "temp":36, "wind":15, "hydration":0.8},
    "EastRutherford":{"altitude":5,    "temp":28, "wind":18, "hydration":0.2},
    "SantaClara":    {"altitude":15,   "temp":19, "wind":14, "hydration":0.0},
    "Pasadena":      {"altitude":234,  "temp":29, "wind":8,  "hydration":0.3},
    "Inglewood":     {"altitude":30,   "temp":24, "wind":10, "hydration":0.1},
    "Philadelphia":  {"altitude":12,   "temp":30, "wind":14, "hydration":0.4},
    "Charlotte":     {"altitude":229,  "temp":31, "wind":10, "hydration":0.5},
    "KansasCity":    {"altitude":282,  "temp":32, "wind":18, "hydration":0.6},
    "Denver":        {"altitude":1609, "temp":26, "wind":14, "hydration":0.2},
    "Chicago":       {"altitude":179,  "temp":28, "wind":22, "hydration":0.2},
    "Miami":         {"altitude":3,    "temp":32, "wind":15, "hydration":0.9},
    "Boston":        {"altitude":8,    "temp":23, "wind":17, "hydration":0.1},
    # ── Canada ───────────────────────────────────────────────────────────────
    "Toronto":       {"altitude":76,   "temp":24, "wind":14, "hydration":0.1},
    "Vancouver":     {"altitude":4,    "temp":19, "wind":11, "hydration":0.0},
    "Montreal":      {"altitude":29,   "temp":25, "wind":14, "hydration":0.1},
    # ── México ───────────────────────────────────────────────────────────────
    "MexicoCity":    {"altitude":2240, "temp":18, "wind":9,  "hydration":0.0},
    "Monterrey":     {"altitude":538,  "temp":36, "wind":12, "hydration":0.9},
    "Guadalajara":   {"altitude":1566, "temp":22, "wind":10, "hydration":0.1},
    "Seattle":       {"altitude":5,   "temp":18, "wind":15, "hydration":0.1},
    "Atlanta":       {"altitude":318, "temp":30, "wind":11, "hydration":0.5},
    "Houston":       {"altitude":12,  "temp":35, "wind":14, "hydration":0.8},
    # ── Neutral (default para predicciones sin sede especificada) ─────────────
    "neutral":       {"altitude":300,  "temp":22, "wind":11, "hydration":0.0},
}

MATCH_SCHEDULE = {
    # Group A: México, Sudáfrica, Corea del Sur, República Checa
    "México_Sudáfrica": "MexicoCity",
    "Corea del Sur_República Checa": "EastRutherford",
    "México_Corea del Sur": "Guadalajara",
    "Sudáfrica_República Checa": "Monterrey",
    "República Checa_México": "MexicoCity",
    "Sudáfrica_Corea del Sur": "Monterrey",
    # Group B: Canadá, Suiza, Qatar, Bosnia y Herz.
    "Canadá_Bosnia y Herz.": "Toronto",
    "Qatar_Suiza": "MexicoCity",
    "Canadá_Qatar": "Vancouver",
    "Suiza_Bosnia y Herz.": "Boston",
    "Suiza_Canadá": "Vancouver",
    "Bosnia y Herz._Qatar": "Philadelphia",
    # Group C: Brasil, Marruecos, Haití, Escocia
    "Brasil_Marruecos": "EastRutherford",
    "Haití_Escocia": "Boston",
    "Escocia_Marruecos": "Boston",
    "Brasil_Haití": "Philadelphia",
    "Brasil_Escocia": "Miami",
    "Marruecos_Haití": "Atlanta",
    # Group D: Estados Unidos, Paraguay, Australia, Turquía
    "Estados Unidos_Paraguay": "Arlington",
    "Australia_Turquía": "Vancouver",
    "Turquía_Estados Unidos": "Inglewood",
    "Paraguay_Australia": "SantaClara",
    "Estados Unidos_Australia": "Seattle",
    "Turquía_Paraguay": "Denver",
    # Group E: Alemania, Costa de Marfil, Ecuador, Curazao
    "Alemania_Curazao": "EastRutherford",
    "Costa de Marfil_Ecuador": "Miami",
    "Alemania_Costa de Marfil": "Toronto",
    "Ecuador_Curazao": "KansasCity",
    "Alemania_Ecuador": "Charlotte",
    "Costa de Marfil_Curazao": "Charlotte",
    # Group F: Japón, Suecia, Túnez, Países Bajos
    "Suecia_Túnez": "EastRutherford",
    "Países Bajos_Japón": "Toronto",
    "Japón_Suecia": "Arlington",
    "Túnez_Países Bajos": "KansasCity",
    "Países Bajos_Suecia": "Houston",
    "Japón_Túnez": "Philadelphia",
    # Group G: Bélgica, Irán, Egipto, Nueva Zelanda
    "Bélgica_Egipto": "Charlotte",
    "Irán_Nueva Zelanda": "Guadalajara",
    "Bélgica_Irán": "Inglewood",
    "Nueva Zelanda_Egipto": "Vancouver",
    "Egipto_Irán": "Seattle",
    "Nueva Zelanda_Bélgica": "Vancouver",
    # Group H: España, Uruguay, Arabia Saudita, Cabo Verde
    "España_Cabo Verde": "Inglewood",
    "Uruguay_Arabia Saudita": "Charlotte",
    "España_Uruguay": "Arlington",
    "Arabia Saudita_Cabo Verde": "KansasCity",
    "España_Arabia Saudita": "Miami",
    "Uruguay_Cabo Verde": "Denver",
    # Group I: Francia, Senegal, Noruega, Irak
    "Francia_Senegal": "Chicago",
    "Noruega_Irak": "Pasadena",
    "Francia_Noruega": "Philadelphia",
    "Senegal_Irak": "Atlanta",
    "Francia_Irak": "Boston",
    "Senegal_Noruega": "EastRutherford",
    # Group J: Argentina, Argelia, Austria, Jordania
    "Argentina_Argelia": "Inglewood",
    "Austria_Jordania": "MexicoCity",
    "Argentina_Austria": "Pasadena",
    "Argelia_Jordania": "Guadalajara",
    "Argentina_Jordania": "Arlington",
    "Austria_Argelia": "Houston",
    # Group K: Portugal, Colombia, Uzbekistán, RD Congo
    "Portugal_RD Congo": "Houston",
    "Uzbekistán_Colombia": "MexicoCity",
    "Portugal_Uzbekistán": "Houston",
    "Colombia_RD Congo": "Guadalajara",
    "Colombia_Portugal": "Miami",
    "RD Congo_Uzbekistán": "Atlanta",
    # Group L: Inglaterra, Croacia, Ghana, Panamá
    "Inglaterra_Croacia": "Arlington",
    "Ghana_Panamá": "Toronto",
    "Inglaterra_Ghana": "Boston",
    "Panamá_Croacia": "Toronto",
    "Panamá_Inglaterra": "EastRutherford",
    "Croacia_Ghana": "Philadelphia",
}

def get_tact(name):
    lu = LINEUP.get(name, {"formation": "4-3-3", "style": "balanced"})
    ff = FORMATION_FEATURES.get(lu["formation"], FORMATION_FEATURES["4-3-3"])
    sm = STYLE_MOD.get(lu["style"], STYLE_MOD["balanced"])
    return {
        "form_attack":  ff["attack"]   * sm["am"],
        "form_defense": ff["defense"]  * sm["dm"],
        "width":        ff["width"],
        "pressing":     ff["pressing"] * sm["pm"],
        "set_piece":    ff["set_piece"],
        "style_score":  STYLE_SCORE.get(lu["style"], 1.0),
    }

def estimate_bk_prob(rankA, rankB, sqA, sqB, mvA, mvB):
    """Estima probabilidades pre-partido tipo casa de apuestas (para datos históricos sin cuotas reales)."""
    rank_adv = (rankB - rankA) / 25.0
    sq_adv   = (sqA - sqB) / 20.0
    mv_adv   = (np.log1p(mvA) - np.log1p(mvB)) / 2.0
    logit    = 0.35 * rank_adv + 0.25 * sq_adv + 0.40 * mv_adv
    p_base   = 1.0 / (1.0 + np.exp(-logit))
    draw_p   = max(0.15, min(0.30, 0.25 - 0.003 * abs(rankB - rankA)))
    bk_a     = p_base * (1 - draw_p)
    bk_b     = (1 - p_base) * (1 - draw_p)
    return [round(bk_a, 4), round(draw_p, 4), round(bk_b, 4)]

# ═══════════════════════════════════════════════════════════════════════════════
# 1. DATOS DE EQUIPOS (sin injury_factor, sin xg_qual, sin is_host)
# ═══════════════════════════════════════════════════════════════════════════════
TEAMS = {
    # [rank, conf, qual_gf, qual_ga, qual_w, qual_m, top_scorer, squad_rating, mv_M, avg_age, wc_pts, wc_gf, wc_ga, wc_pl]
    "Francia":         [1, "UEFA",    32, 8,  8, 10, 9,  88.2,1050,26.1, 3,3,1,1],
    "España":          [2, "UEFA",    30,10,  7, 10, 7,  87.5, 980,24.8, 1,0,0,1],
    "Argentina":       [3, "CONMEBOL",35,17, 12, 18, 8,  87.0, 760,28.2, 3,3,0,1],
    "Inglaterra":      [4, "UEFA",    30, 9,  8, 10, 7,  86.5,1100,26.5, 0,0,0,0],
    "Portugal":        [5, "UEFA",    28, 7,  9, 10, 7,  85.8, 920,27.8, 1,1,1,1],
    "Brasil":          [6, "CONMEBOL",29,22,  7, 18, 5,  86.0,1200,24.5, 1,1,1,1],
    "Países Bajos":    [7, "UEFA",    29,14,  7, 10, 8,  84.5, 870,25.8, 1,2,2,1],
    "Marruecos":       [8, "CAF",     15, 3,  5,  6, 4,  80.0, 320,25.2, 1,1,1,1],
    "Bélgica":         [9, "UEFA",    27,12,  7, 10, 6,  83.5, 680,28.5, 1,1,1,1],
    "Alemania":        [10,"UEFA",    33,11,  8, 10, 9,  84.0, 890,25.2, 3,7,1,1],
    "Croacia":         [11,"UEFA",    22,11,  6, 10, 5,  82.5, 420,29.5, 0,0,0,0],
    "Colombia":        [13,"CONMEBOL",26,22,  8, 18, 7,  82.0, 480,25.8, 0,0,0,0],
    "Senegal":         [14,"CAF",     12, 5,  4,  6, 4,  79.5, 280,26.0, 0,1,3,1],
    "México":          [15,"CONCACAF",26,16,  7, 14, 5,  80.5, 390,26.5, 3,2,0,1],
    "Estados Unidos":  [16,"CONCACAF",28,14,  8, 14, 8,  80.0, 520,25.2, 3,4,1,1],
    "Uruguay":         [17,"CONMEBOL",28,20,  8, 18, 6,  81.0, 430,27.8, 1,1,1,1],
    "Japón":           [18,"AFC",     48,10, 14, 18, 9,  81.5, 560,25.5, 1,2,2,1],
    "Suiza":           [19,"UEFA",    25, 8,  7, 10, 5,  80.5, 450,27.2, 1,1,1,1],
    "Irán":            [21,"AFC",     30,18, 11, 18, 7,  77.5, 180,26.5, 1,2,2,1],
    "Turquía":         [22,"UEFA",    24,14,  6, 10, 7,  79.5, 490,26.2, 0,0,2,1],
    "Ecuador":         [23,"CONMEBOL",26,17,  8, 18, 5,  79.0, 310,24.8, 0,0,1,1],
    "Austria":         [24,"UEFA",    25,14,  7, 10, 6,  79.5, 410,26.5, 3,3,1,1],
    "Corea del Sur":   [25,"AFC",     32,20, 10, 18, 6,  79.0, 380,26.0, 3,2,1,1],
    "Australia":       [27,"AFC",     26,24,  8, 18, 5,  77.5, 220,26.8, 3,2,0,1],
    "Argelia":         [28,"CAF",     12, 5,  4,  6, 4,  77.0, 160,26.5, 0,0,3,1],
    "Egipto":          [29,"CAF",     12, 4,  4,  6, 4,  76.5, 140,26.2, 1,1,1,1],
    "Canadá":          [30,"CONCACAF",25,12,  8, 14, 6,  78.0, 340,25.0, 1,1,1,1],
    "Noruega":         [31,"UEFA",    35,12,  8, 10,16,  79.5, 560,25.5, 3,4,1,1],
    "Panamá":          [33,"CONCACAF",18,18,  5, 14, 4,  73.5,  95,26.5, 0,0,0,0],
    "Costa de Marfil": [34,"CAF",     10, 6,  3,  6, 3,  74.5, 210,26.2, 3,1,0,1],
    "Suecia":          [38,"UEFA",    22,14,  5, 10, 8,  76.0, 360,26.8, 3,5,1,1],
    "Paraguay":        [40,"CONMEBOL",21,26,  5, 18, 4,  73.5, 150,26.5, 0,1,4,1],
    "República Checa": [41,"UEFA",    18,12,  4, 10, 5,  74.0, 220,27.0, 0,1,2,1],
    "Escocia":         [43,"UEFA",    20,16,  4, 10, 5,  72.5, 180,27.2, 3,1,0,1],
    "Túnez":           [44,"CAF",      9, 7,  3,  6, 3,  71.5, 120,26.8, 0,1,5,1],
    "RD Congo":        [46,"CAF",      8, 5,  3,  6, 3,  70.5,  95,26.0, 1,1,1,1],
    "Uzbekistán":      [50,"AFC",     18,12,  6, 12, 4,  70.0,  85,25.5, 0,0,0,0],
    "Qatar":           [55,"AFC",     20,35,  5, 18, 3,  68.5,  75,26.2, 1,1,1,1],
    "Irak":            [57,"AFC",     16,20,  5, 14, 4,  68.0,  65,26.5, 0,1,4,1],
    "Sudáfrica":       [60,"CAF",     10, 7,  3,  6, 2,  67.5,  80,26.8, 0,0,2,1],
    "Arabia Saudita":  [61,"AFC",     26,32,  7, 18, 5,  68.0, 110,26.5, 1,1,1,1],
    "Jordania":        [63,"AFC",     21,30,  6, 18, 4,  66.5,  55,26.2, 0,1,3,1],
    "Bosnia y Herz.":  [65,"UEFA",    14,18,  3, 10, 3,  69.0,  95,27.5, 1,1,1,1],
    "Cabo Verde":      [69,"CAF",      8, 7,  3,  6, 2,  66.0,  55,26.5, 1,0,0,1],
    "Ghana":           [74,"CAF",      8, 9,  2,  6, 2,  65.0,  70,26.0, 0,0,0,0],
    "Curazao":         [82,"CONCACAF", 6,10,  2,  8, 2,  61.5,  30,25.8, 0,1,7,1],
    "Haití":           [83,"CONCACAF", 5,12,  1,  8, 1,  60.5,  25,25.5, 0,0,1,1],
    "Nueva Zelanda":   [85,"OFC",     28,15,  7,  8, 9,  60.0,  40,26.5, 1,2,2,1],
}

PLAYERS = {
    "Francia":        [("Mbappé",9,93,180),("Griezmann",5,87,25),("Tchouaméni",2,86,90)],
    "España":         [("Yamal",7,88,180),("Pedri",4,88,120),("Morata",5,85,35)],
    "Argentina":      [("Messi",8,93,20),("J.Álvarez",6,88,90),("De Paul",3,85,35)],
    "Inglaterra":     [("Kane",7,90,80),("Bellingham",7,91,180),("Foden",5,88,130)],
    "Portugal":       [("Ronaldo",7,90,15),("B.Fernandes",5,87,60),("B.Silva",4,88,80)],
    "Brasil":         [("Vinicius",5,92,200),("Rodrygo",4,87,120),("Raphinha",4,86,80)],
    "Países Bajos":   [("Gakpo",8,86,80),("Depay",5,85,18),("F.de Jong",3,87,65)],
    "Marruecos":      [("En-Nesyri",4,83,30),("Ziyech",3,82,12),("Hakimi",2,87,60)],
    "Bélgica":        [("Lukaku",6,86,22),("De Bruyne",4,91,35),("Openda",5,84,50)],
    "Alemania":       [("Havertz",9,86,65),("Wirtz",7,90,150),("Musiala",5,89,120)],
    "Croacia":        [("Perišić",5,83,15),("Modrić",3,87,8),("Kramarić",5,83,18)],
    "Colombia":       [("L.Díaz",7,87,80),("James",4,83,15),("Falcao",2,82,3)],
    "Senegal":        [("Mané",4,83,25),("I.Sarr",4,82,30),("PM.Sarr",3,82,45)],
    "México":         [("S.Giménez",5,84,55),("Lozano",4,82,18),("E.Álvarez",2,81,35)],
    "Estados Unidos": [("Pulisic",8,84,50),("Balogun",6,83,35),("McKennie",3,80,28)],
    "Uruguay":        [("D.Núñez",6,87,80),("Valverde",4,88,120),("R.Araújo",1,84,55)],
    "Japón":          [("Ito",9,83,22),("Minamino",7,82,15),("Doan",6,82,20)],
    "Suiza":          [("Embolo",5,82,22),("Xhaka",3,83,15),("Shaqiri",3,79,8)],
    "Irán":           [("Taremi",7,82,12),("Azmoun",5,81,12),("Jahanbakhsh",4,79,8)],
    "Turquía":        [("Aktürkoğlu",7,84,35),("Çalhanoğlu",4,85,35),("A.Güler",6,86,55)],
    "Ecuador":        [("E.Valencia",5,81,8),("Caicedo",3,86,100),("Plata",4,80,20)],
    "Austria":        [("Sabitzer",6,83,22),("Arnautović",5,81,8),("Baumgartner",4,82,35)],
    "Corea del Sur":  [("Son",6,86,30),("Cho",5,81,8),("Lee",3,79,10)],
    "Australia":      [("Leckie",5,78,8),("Duke",4,77,5),("Mooy",3,79,6)],
    "Argelia":        [("Slimani",4,78,5),("Mahrez",4,83,15),("Benrahma",3,80,15)],
    "Egipto":         [("Salah",4,89,35),("M.Mohamed",3,79,15),("Trezeguet",3,78,8)],
    "Canadá":         [("A.Davies",6,86,70),("J.David",8,85,55),("Larin",5,78,10)],
    "Noruega":        [("Haaland",16,93,180),("Ødegaard",5,88,90),("Sørloth",5,82,35)],
    "Panamá":         [("Blackburn",4,73,3),("Godoy",2,74,3),("Escobar",2,72,2)],
    "Costa de Marfil":[("Haller",3,80,15),("Pépé",3,79,10),("Kessié",2,81,18)],
    "Suecia":         [("Gyökeres",8,84,65),("Isak",6,85,70),("Kulusevski",4,84,50)],
    "Paraguay":       [("Almirón",4,81,15),("Enciso",5,81,25),("Camacho",2,74,5)],
    "República Checa":[("Souček",5,81,20),("Schick",5,82,28),("Hložek",4,81,30)],
    "Escocia":        [("McTominay",5,81,25),("Robertson",2,83,25),("Adams",4,77,12)],
    "Túnez":          [("Msakni",3,75,5),("Khazri",3,76,3),("Bronn",1,74,4)],
    "RD Congo":       [("Bakambu",3,76,5),("Mbemba",1,76,6),("Bolasie",2,73,3)],
    "Uzbekistán":     [("Shomurodov",4,78,8),("Fayzullayev",3,76,5),("Shukurov",2,74,3)],
    "Qatar":          [("Afif",3,74,5),("Ali",3,75,4),("Al-Haydos",2,73,3)],
    "Irak":           [("Hussein",4,73,4),("Al-Hamadi",2,73,6),("Attwan",2,71,2)],
    "Sudáfrica":      [("Tau",2,76,4),("Mokoena",2,73,3),("Foster",3,75,8)],
    "Arabia Saudita": [("Al-Dawsari",5,79,6),("Al-Buraikan",5,77,5),("Al-Qasem",2,73,2)],
    "Jordania":       [("Faisal",4,71,2),("Al-Naimat",3,70,2),("Al-Taamari",3,73,3)],
    "Bosnia y Herz.": [("Džeko",3,80,5),("Pjanić",2,81,5),("Demirović",3,79,20)],
    "Cabo Verde":     [("G.Rodrigues",2,73,4),("R.Mendes",2,72,2),("Stopira",1,71,2)],
    "Ghana":          [("J.Ayew",2,75,8),("A.Ayew",2,76,4),("Kudus",3,82,45)],
    "Curazao":        [("Martina",1,68,1),("Bacuna",2,70,2),("Castro",2,68,1)],
    "Haití":          [("Nazon",2,68,3),("Pierrot",1,67,2),("Bazile",1,66,2)],
    "Nueva Zelanda":  [("Wood",9,79,12),("Lewis",3,73,3),("Cacace",2,74,3)],
}

# ═══════════════════════════════════════════════════════════════════════════════
# 2. FEATURES POR EQUIPO v3
# ═══════════════════════════════════════════════════════════════════════════════
def build_team_features_v3(name):
    d = TEAMS[name]
    rank, conf_name = d[0], d[1]
    qual_gf, qual_ga, qual_w, qual_m = d[2], d[3], d[4], d[5]
    top_sc, sq_rating, mv, avg_age  = d[6], d[7], d[8], d[9]
    wc_pts, wc_gf, wc_ga, wc_pl    = d[10], d[11], d[12], d[13]

    plrs = PLAYERS.get(name, [])
    star_goal_pow  = sum(p[1] for p in plrs)
    star_avg_rat   = np.mean([p[2] for p in plrs]) if plrs else sq_rating
    star_avg_val   = np.mean([p[3] for p in plrs]) if plrs else mv / 10
    att_combo      = (star_goal_pow * star_avg_rat) / 100

    qual_gf_pg = qual_gf / max(qual_m, 1)
    qual_ga_pg = qual_ga / max(qual_m, 1)
    qual_wr    = qual_w  / max(qual_m, 1)
    qual_gd    = qual_gf - qual_ga

    wc_gf_pg = wc_gf / max(wc_pl, 1) if wc_pl > 0 else qual_gf_pg
    wc_ga_pg = wc_ga / max(wc_pl, 1) if wc_pl > 0 else qual_ga_pg
    wc_form  = wc_pts / (wc_pl * 3) if wc_pl > 0 else qual_wr

    tact = get_tact(name)
    cwe  = CONF_WC_EXP[conf_name]

    return {
        "rank": rank, "conf": CONF_MAP[conf_name], "conf_wc_exp": cwe,
        "qual_gf_pg": qual_gf_pg, "qual_ga_pg": qual_ga_pg,
        "qual_wr": qual_wr, "qual_gd": qual_gd,
        "top_sc": top_sc, "squad_rating": sq_rating,
        "log_mv": np.log1p(mv), "avg_age": avg_age,
        "att_combo": att_combo, "star_avg_rat": star_avg_rat,
        "log_star_val": np.log1p(star_avg_val),
        "wc_form": wc_form, "wc_gf_pg": wc_gf_pg, "wc_ga_pg": wc_ga_pg,
        "is_top5": int(rank <= 5), "is_top10": int(rank <= 10),
        "form_attack": tact["form_attack"], "form_defense": tact["form_defense"],
        "width": tact["width"], "pressing": tact["pressing"],
        "set_piece": tact["set_piece"], "style_score": tact["style_score"],
    }

team_feats_v3 = {n: build_team_features_v3(n) for n in TEAMS}
print(f"Features/equipo: {len(next(iter(team_feats_v3.values())))}")

# ═══════════════════════════════════════════════════════════════════════════════
# 3. FUNCIÓN PARA CONSTRUIR VECTOR DE PARTIDO
# ═══════════════════════════════════════════════════════════════════════════════
def make_match_feat(fA, fB, altitude=300, temp=22, wind=11, hydration=0.0, bk_win_A=0.333, bk_draw=0.333, bk_win_B=0.333):
    ta = fA["form_attack"] * fB["form_defense"]   # ataque A vs defensa B
    tb = fB["form_attack"] * fA["form_defense"]   # ataque B vs defensa A
    # Environmental features
    alt_norm   = altitude / 2500.0
    temp_norm  = temp / 45.0
    wind_norm  = wind / 40.0
    alt_stress = max(0.0, (altitude - 1000) / 1500.0)
    heat_stress = max(0.0, (temp - 28) / 15.0)
    alt_pen_A  = fA["pressing"] * alt_stress
    alt_pen_B  = fB["pressing"] * alt_stress
    # Negative: pressing teams suffer in heat + hydration breaks
    heat_hydra_pen_A = -(fA["pressing"] * heat_stress + hydration * fA["pressing"] * 0.5)
    heat_hydra_pen_B = -(fB["pressing"] * heat_stress + hydration * fB["pressing"] * 0.5)
    return [
        fA["rank"], fB["rank"],
        fB["rank"] - fA["rank"],
        fB["rank"] / (fA["rank"] + 1),
        fA["conf"], fB["conf"],
        fA["conf_wc_exp"], fB["conf_wc_exp"], fA["conf_wc_exp"] - fB["conf_wc_exp"],
        fA["qual_gf_pg"], fA["qual_ga_pg"], fA["qual_wr"], fA["qual_gd"],
        fB["qual_gf_pg"], fB["qual_ga_pg"], fB["qual_wr"], fB["qual_gd"],
        fA["qual_gf_pg"] - fB["qual_gf_pg"],
        fA["qual_ga_pg"] - fB["qual_ga_pg"],
        fA["qual_wr"]    - fB["qual_wr"],
        fA["qual_gd"]    - fB["qual_gd"],
        fA["squad_rating"], fB["squad_rating"], fA["squad_rating"] - fB["squad_rating"],
        fA["log_mv"], fB["log_mv"], fA["log_mv"] - fB["log_mv"],
        fA["avg_age"], fB["avg_age"],
        fA["top_sc"], fB["top_sc"], fA["top_sc"] - fB["top_sc"],
        fA["att_combo"], fB["att_combo"], fA["att_combo"] - fB["att_combo"],
        fA["star_avg_rat"], fB["star_avg_rat"], fA["star_avg_rat"] - fB["star_avg_rat"],
        fA["log_star_val"], fB["log_star_val"],
        fA["wc_form"], fB["wc_form"], fA["wc_form"] - fB["wc_form"],
        fA["wc_gf_pg"], fB["wc_gf_pg"],
        fA["wc_ga_pg"], fB["wc_ga_pg"],
        fA["is_top5"], fB["is_top5"], fA["is_top10"], fB["is_top10"],
        # Tácticas v3
        fA["form_attack"], fB["form_attack"], fA["form_attack"] - fB["form_attack"],
        fA["form_defense"], fB["form_defense"], fA["form_defense"] - fB["form_defense"],
        fA["width"], fB["width"],
        fA["pressing"], fB["pressing"], fA["pressing"] - fB["pressing"],
        fA["set_piece"], fB["set_piece"], fA["set_piece"] - fB["set_piece"],
        fA["style_score"], fB["style_score"], fA["style_score"] - fB["style_score"],
        ta - tb,          # ventaja táctica neta
        ta, tb,           # interacciones cruzadas
        fA["style_score"] * fA["form_attack"],   # ofensiva real A
        fB["style_score"] * fB["form_attack"],   # ofensiva real B
        (fA["att_combo"] * fA["form_attack"]) - (fB["att_combo"] * fB["form_attack"]),  # poder ofensivo neto
        # Environmental features (8 nuevas)
        alt_norm, temp_norm, wind_norm, hydration,
        alt_pen_A, alt_pen_B,
        heat_hydra_pen_A, heat_hydra_pen_B,
        # Bookmaker odds — probabilidades de mercado pre-partido (3 nuevas)
        bk_win_A, bk_draw, bk_win_B,
    ]

N_FEAT = len(make_match_feat(next(iter(team_feats_v3.values())), next(iter(team_feats_v3.values()))))
print(f"Features/partido: {N_FEAT}")

FEAT_COLS = [
    "rank_A","rank_B","rank_diff","rank_ratio",
    "conf_A","conf_B",
    "cwe_A","cwe_B","diff_cwe",
    "gf_pg_A","ga_pg_A","wr_A","gd_A",
    "gf_pg_B","ga_pg_B","wr_B","gd_B",
    "diff_gf_pg","diff_ga_pg","diff_wr","diff_gd",
    "sq_rat_A","sq_rat_B","diff_sq_rat",
    "log_mv_A","log_mv_B","diff_log_mv",
    "age_A","age_B",
    "top_sc_A","top_sc_B","diff_top_sc",
    "att_A","att_B","diff_att",
    "star_rat_A","star_rat_B","diff_star_rat",
    "log_sv_A","log_sv_B",
    "wc_form_A","wc_form_B","diff_wc_form",
    "wc_gf_A","wc_gf_B",
    "wc_ga_A","wc_ga_B",
    "top5_A","top5_B","top10_A","top10_B",
    "fatk_A","fatk_B","diff_fatk",
    "fdef_A","fdef_B","diff_fdef",
    "width_A","width_B",
    "press_A","press_B","diff_press",
    "sp_A","sp_B","diff_sp",
    "style_A","style_B","diff_style",
    "tact_adv","cross_ta","cross_tb",
    "off_pow_A","off_pow_B","net_off_pow",
    # Environmental features
    "env_alt","env_temp","env_wind","env_hydration",
    "alt_pen_A","alt_pen_B",
    "heat_hydra_pen_A","heat_hydra_pen_B",
    # Bookmaker odds features
    "bk_win_A","bk_draw","bk_win_B",
]
assert len(FEAT_COLS) == N_FEAT, f"Mismatch: cols={len(FEAT_COLS)} feat={N_FEAT}"

# ═══════════════════════════════════════════════════════════════════════════════
# 4. DATASET HISTÓRICO — v3 (base v2 + columnas tácticas derivadas)
# ═══════════════════════════════════════════════════════════════════════════════
# Táctica aproximada por rango: se usa la formación más común históricamente
def hist_tact(rank, attacking_bias=0.0):
    if rank <= 5:
        return {"form_attack": min(0.96, 0.88+attacking_bias), "form_defense": 0.65,
                "width": 0.85, "pressing": 0.88, "set_piece": 0.70, "style_score": 1.10}
    elif rank <= 15:
        return {"form_attack": 0.80+attacking_bias, "form_defense": 0.70,
                "width": 0.80, "pressing": 0.80, "set_piece": 0.72, "style_score": 1.02}
    elif rank <= 30:
        return {"form_attack": 0.72+attacking_bias, "form_defense": 0.76,
                "width": 0.72, "pressing": 0.72, "set_piece": 0.75, "style_score": 0.98}
    else:
        return {"form_attack": 0.62+attacking_bias, "form_defense": 0.85,
                "width": 0.60, "pressing": 0.60, "set_piece": 0.78, "style_score": 0.85}

# raw: [rA,rB,confA,confB,gf_pgA,ga_pgA,gf_pgB,ga_pgB,sqA,sqB,tsA,tsB,mvA,mvB,ageA,ageB,acA,acB,wcfA,wcfB,gA,gB]
historical_raw = [
    # 2022 Qatar
    [3,12, 1,0,  1.94,0.94,1.50,1.20, 87.0,82.5,8,5,  760,420, 28.2,29.5,18.5,14.0,0.67,0.60, 0,0],
    [1,18, 0,2,  3.20,0.80,1.86,1.00, 88.2,81.5,9,9, 1050,560, 26.1,25.5,17.5,18.0,0.80,0.80, 0,1],
    [7,65, 0,4,  2.90,1.40,1.10,1.95, 84.5,70.0,8,4,  870, 65, 25.8,26.5,15.0, 8.0,0.70,0.33, 6,2],
    [10,45,0,4,  3.30,1.10,1.50,1.40, 84.0,72.0,9,5,  890, 85, 25.2,26.2,21.0,12.0,0.80,0.40, 1,2],
    [2,20, 0,3,  3.00,1.00,2.00,1.10, 87.5,79.0,7,4,  980,310, 24.8,24.8,19.0,12.0,0.70,0.80, 0,0],
    [4,50, 0,4,  3.00,0.90,1.60,1.20, 86.5,70.0,7,4, 1100, 85, 26.5,25.5,20.0,10.0,0.80,0.40, 6,2],
    [5,25, 0,1,  2.80,0.70,1.44,0.94, 85.8,79.0,7,5,  920,310, 27.8,24.8,18.0,12.0,0.90,0.44, 3,2],
    [6,22, 1,4,  1.61,1.22,1.67,1.00, 86.0,79.5,5,7, 1200,180, 24.5,26.5,14.0,16.0,0.39,0.44, 2,0],
    [8,35, 3,2,  2.50,0.50,1.67,1.00, 80.0,74.5,4,3,  320,210, 25.2,26.2,11.0, 8.0,0.83,0.50, 0,0],
    [9,30, 0,3,  2.70,1.20,2.00,0.83, 83.5,76.5,6,4,  680,140, 28.5,26.2,14.0,10.0,0.70,0.67, 1,0],
    [11,40,0,4,  2.20,1.10,1.78,1.33, 82.5,73.5,5,4,  420,150, 29.5,26.5,10.0, 9.0,0.60,0.44, 4,1],
    [13,55,1,4,  1.44,1.22,1.11,1.94, 82.0,68.5,7,3,  480, 75, 25.8,26.2,16.0, 8.0,0.44,0.28, 1,0],
    [14,60,3,3,  2.00,0.83,1.67,1.17, 79.5,67.5,4,2,  280, 80, 26.0,26.8,10.0, 6.0,0.67,0.50, 2,1],
    [15,70,2,3,  1.86,1.14,1.33,1.50, 80.5,66.0,5,2,  390, 55, 26.5,26.5,11.0, 5.0,0.50,0.36, 0,1],
    [16,28,2,1,  2.00,1.00,1.44,0.94, 80.0,79.0,8,5,  520,310, 25.2,24.8,18.0,12.0,0.57,0.44, 1,2],
    [17,33,1,2,  1.56,1.11,1.29,1.29, 81.0,73.5,6,4,  430, 95, 27.8,26.5,13.0, 9.0,0.44,0.36, 2,0],
    # 2018 Rusia
    [1, 4, 0,0,  2.80,0.80,2.70,0.90, 88.2,86.5,9,7, 1050,1100,26.1,26.5,25.0,20.0,0.80,0.80, 2,1],
    [2, 8, 0,3,  2.50,0.80,2.20,0.60, 87.5,80.0,7,4,  980,320, 24.8,25.2,18.0,10.0,0.70,0.80, 1,0],
    [3,12, 1,0,  2.20,1.00,1.80,1.10, 87.0,82.5,8,5,  760,420, 28.2,29.5,18.0,14.0,0.67,0.60, 0,0],
    [5,20, 0,2,  2.10,0.70,1.80,1.20, 85.8,80.5,7,5,  920,390, 27.8,26.5,16.0,11.0,0.90,0.50, 1,0],
    [6,25, 1,1,  1.70,1.30,1.70,1.00, 86.0,79.0,5,5, 1200,310, 24.5,24.8,12.0,12.0,0.39,0.44, 2,0],
    [7,30, 0,3,  2.40,1.20,1.60,1.00, 84.5,76.5,8,4,  870,140, 25.8,26.2,16.0, 9.0,0.70,0.60, 3,0],
    [9,15, 0,1,  2.60,1.10,1.60,1.20, 83.5,81.0,6,6,  680,430, 28.5,27.8,14.0,13.0,0.70,0.44, 2,0],
    [10,35,0,4,  3.10,1.20,1.50,1.40, 84.0,73.5,9,4,  890,150, 25.2,26.5,22.0, 9.0,0.80,0.28, 2,1],
    # Upsets históricos
    [8, 1, 3,0,  2.50,0.50,3.20,0.80, 80.0,88.2,4,9,  320,1050,25.2,26.1,10.0,25.0,0.83,0.92, 1,0],
    [35,5, 4,0,  1.80,1.40,2.20,0.80, 73.0,85.8,5,7,   85, 920,26.5,27.8, 9.0,16.0,0.40,0.90, 1,0],
    [22,3, 4,1,  1.67,1.00,1.94,0.94, 79.5,87.0,7,8,  180, 760,26.5,28.2,14.0,18.0,0.44,0.67, 2,1],
    [18,3, 2,1,  2.67,0.56,1.94,0.94, 81.5,87.0,9,8,  560, 760,25.5,28.2,20.0,18.0,0.78,0.67, 2,1],
    [25,6, 4,1,  1.78,1.11,1.61,1.22, 79.0,86.0,6,5,  380,1200,26.0,24.5,13.0,14.0,0.50,0.39, 0,1],
    # 2014 Brasil
    [1, 6, 1,0,  2.20,1.10,1.60,1.20, 88.2,85.8,9,7, 1050, 920,26.1,27.8,22.0,16.0,0.80,0.90, 3,1],
    [2,10, 0,0,  2.50,0.80,2.80,1.10, 87.5,84.0,7,9,  980, 890,24.8,25.2,17.0,20.0,0.70,0.80, 4,0],
    [3,15, 0,4,  2.00,1.00,1.60,1.50, 87.0,77.0,8,4,  760, 160,28.2,26.5,18.0, 9.0,0.67,0.40, 1,0],
    [4, 6, 0,0,  2.80,0.90,2.20,1.10, 86.5,85.8,7,7, 1100, 920,26.5,27.8,20.0,16.0,0.80,0.90, 2,1],
    [5,11, 0,0,  2.60,0.80,2.10,1.10, 85.8,82.5,7,5,  920, 420,27.8,29.5,16.0,10.0,0.90,0.60, 1,0],
    # Empates técnicos
    [5, 5, 0,0,  2.50,0.80,2.50,0.80, 85.8,85.8,7,7,  920, 920,27.8,27.8,16.0,16.0,0.90,0.90, 1,1],
    [10,10,0,0,  3.00,1.10,3.00,1.10, 84.0,84.0,9,9,  890, 890,25.2,25.2,22.0,22.0,0.80,0.80, 2,2],
    [20,20,0,3,  2.00,1.20,2.00,1.20, 80.5,80.5,5,5,  390, 390,26.5,26.5,10.0,10.0,0.57,0.57, 1,1],
    [8,10, 0,0,  2.80,0.80,2.80,0.80, 82.0,84.5,6,8,  480, 870,28.5,25.8,14.0,16.0,0.44,0.70, 1,1],
    [15,18,2,4,  1.86,1.14,2.67,0.56, 80.5,81.5,5,9,  390, 560,26.5,25.5,11.0,20.0,0.50,0.78, 0,0],
    [30,35,2,3,  1.79,0.86,1.67,1.17, 78.0,74.5,6,3,  340,  95,25.0,26.5,12.0, 7.0,0.57,0.50, 1,0],
    [40,45,3,4,  1.17,1.44,1.67,1.33, 73.5,72.0,4,5,  150,  85,26.5,26.2, 8.0,10.0,0.28,0.33, 0,1],
    [50,55,4,4,  1.50,1.00,1.11,1.94, 70.0,68.5,4,3,   85,  75,25.5,26.2, 8.0, 7.0,0.50,0.28, 2,2],
    # Partidos defensivos (sem. finales y finales mundiales - alta tensión)
    [1, 2, 0,0,  3.00,0.80,3.00,0.80, 88.0,87.5,9,7, 1000, 980,26.0,24.8,24.0,19.0,0.90,0.80, 1,0],
    [3, 4, 1,0,  2.10,0.90,2.70,0.90, 87.0,86.5,8,7,  760,1100,28.2,26.5,18.0,20.0,0.67,0.80, 0,1],
    [1, 3, 0,1,  3.10,0.80,2.00,0.95, 88.2,87.0,9,8, 1050, 760,26.1,28.2,26.0,18.0,0.80,0.67, 2,0],
    [2, 6, 0,1,  3.00,0.90,1.61,1.22, 87.5,86.0,7,5,  980,1200,24.8,24.5,19.0,14.0,0.70,0.39, 1,0],
    [5, 7, 0,0,  2.70,0.80,2.80,1.20, 85.8,84.5,7,8,  920, 870,27.8,25.8,16.0,16.0,0.90,0.70, 1,2],
    [6,10, 1,0,  1.80,1.10,2.90,1.10, 86.0,84.0,5,9, 1200, 890,24.5,25.2,13.0,22.0,0.40,0.80, 0,1],
    # Cross-confederation: UEFA vs AFC
    [1, 18, 0,4,  3.20,0.80,2.67,0.56, 88.2,81.5, 9,9, 1050,560,26.1,25.5,25.0,20.0,0.80,0.78, 2,1],
    [2, 25, 0,4,  3.00,0.90,1.78,1.11, 87.5,79.0, 7,6,  980,380,24.8,26.0,19.0,13.0,0.70,0.50, 3,0],
    [10,18, 0,4,  3.30,1.10,2.67,0.56, 84.0,81.5, 9,9,  890,560,25.2,25.5,22.0,20.0,0.80,0.78, 2,0],
    [7, 25, 0,4,  2.90,1.40,1.78,1.11, 84.5,79.0, 8,6,  870,380,25.8,26.0,15.0,13.0,0.70,0.50, 1,0],
    # Cross-confederation: UEFA vs CAF
    [1,  8, 0,3,  3.20,0.80,2.50,0.50, 88.2,80.0, 9,4, 1050,320,26.1,25.2,25.0,11.0,0.80,0.83, 2,0],
    [2, 14, 0,3,  3.00,0.90,2.00,0.83, 87.5,79.5, 7,4,  980,280,24.8,26.0,19.0,10.0,0.70,0.67, 2,0],
    [5, 14, 0,3,  2.80,0.70,2.00,0.83, 85.8,79.5, 7,4,  920,280,27.8,26.0,16.0,10.0,0.90,0.67, 1,0],
    [8, 10, 3,0,  2.50,0.50,3.30,1.10, 80.0,84.0, 4,9,  320,890,25.2,25.2,11.0,22.0,0.83,0.80, 0,1],  # Morocco beats Germany
    # Cross-confederation: UEFA vs CONCACAF
    [1, 15, 0,2,  3.20,0.80,1.86,1.14, 88.2,80.5, 9,5, 1050,390,26.1,26.5,25.0,11.0,0.80,0.50, 2,0],
    [10,16, 0,2,  3.10,1.20,2.00,1.00, 84.0,80.0, 9,8,  890,520,25.2,25.2,22.0,18.0,0.80,0.57, 1,0],
    [5, 30, 0,2,  2.80,0.70,1.79,0.86, 85.8,78.0, 7,6,  920,340,27.8,25.0,16.0,12.0,0.90,0.57, 2,0],
    # Cross-confederation: CONMEBOL vs AFC
    [3, 18, 1,4,  1.94,0.94,2.67,0.56, 87.0,81.5, 8,9,  760,560,28.2,25.5,18.5,20.0,0.67,0.78, 0,1],  # Japan beats Argentina (upset)
    [6, 25, 1,4,  1.61,1.22,1.78,1.11, 86.0,79.0, 5,6, 1200,380,24.5,26.0,14.0,13.0,0.39,0.50, 1,0],
    [13,18, 1,4,  1.44,1.22,2.67,0.56, 82.0,81.5, 7,9,  480,560,25.8,25.5,16.0,20.0,0.44,0.78, 0,1],  # Japan upsets Colombia
    # CONMEBOL vs CAF
    [3,  8, 1,3,  1.94,0.94,2.50,0.50, 87.0,80.0, 8,4,  760,320,28.2,25.2,18.5,11.0,0.67,0.83, 1,0],
    [6, 14, 1,3,  1.61,1.22,2.00,0.83, 86.0,79.5, 5,4, 1200,280,24.5,26.0,14.0,10.0,0.39,0.67, 2,1],
    # Matches favoring lower teams clearly
    [1, 85, 0,5,  3.00,0.80,3.50,1.88, 88.2,60.0, 9,9, 1050, 40,26.1,26.5,25.0, 8.0,0.80,0.88, 4,0],
    [2, 83, 0,2,  2.80,0.90,0.63,1.50, 87.5,60.5, 7,1,  980, 25,24.8,25.5,19.0, 2.0,0.70,0.13, 3,0],
    [4, 82, 0,2,  2.70,0.90,0.75,1.25, 86.5,61.5, 7,2, 1100, 30,26.5,25.8,20.0, 3.0,0.80,0.25, 5,0],
    [6, 61, 1,4,  1.61,1.22,1.44,1.78, 86.0,68.0, 5,5, 1200,110,24.5,26.5,14.0, 7.0,0.39,0.39, 2,0],  # Brasil beats Arabia
    [10,61, 0,4,  3.30,1.10,1.44,1.78, 84.0,68.0, 9,5,  890,110,25.2,26.5,22.0, 7.0,0.80,0.39, 2,0],  # Germany beats Arabia
    [7, 63, 0,4,  2.90,1.40,1.17,1.67, 84.5,66.5, 8,4,  870, 55,25.8,26.2,15.0, 6.0,0.70,0.33, 3,0],  # Netherlands beats Jordan
    # Partidos reales — Mundial FIFA 2026 (Jornada 1, 14-15 junio 2026)
    [10,82, 0,2, 3.30,1.10, 0.75,1.25, 84.0,61.5, 9,2,  890, 30, 25.2,25.8, 21.0, 3.0, 0.80,0.25, 7,1],  # Alemania 7-1 Curazao
    [38,44, 0,3, 2.20,1.40, 1.50,1.17, 76.0,71.5, 8,3,  360,120, 26.8,26.8, 15.0, 5.0, 0.50,0.50, 5,1],  # Suecia 5-1 Túnez
    [34,23, 3,1, 1.67,1.00, 1.44,0.94, 74.5,79.0, 3,5,  210,310, 26.2,24.8,  6.0,10.0, 0.50,0.44, 1,0],  # Costa de Marfil 1-0 Ecuador (upset)
    [ 9,29, 0,3, 2.70,1.20, 2.00,0.67, 83.5,76.5, 6,4,  680,140, 28.5,26.2, 13.0, 8.0, 0.70,0.67, 1,1],  # Bélgica 1-1 Egipto
    [ 2,69, 0,3, 3.00,1.00, 1.33,1.17, 87.5,66.0, 7,2,  980, 55, 24.8,26.5, 14.0, 4.0, 0.70,0.50, 0,0],  # España 0-0 Cabo Verde (upset draw)
    # Jornada 1 continuación — 11-17 junio 2026
    [15,60, 2,3, 1.86,1.14, 1.67,1.17, 80.5,67.5, 5,2,  390, 80, 26.5,26.8, 11.0, 6.0, 0.50,0.50, 2,0],  # México 2-0 Sudáfrica
    [25,41, 4,0, 1.78,1.11, 1.80,1.20, 79.0,74.0, 6,5,  380,220, 26.0,27.0, 13.0, 9.0, 0.56,0.40, 2,1],  # Corea del Sur 2-1 República Checa (sorpresa)
    [30,65, 2,0, 1.79,0.86, 1.40,1.80, 78.0,69.0, 6,3,  340, 95, 25.0,27.5, 13.0, 8.0, 0.57,0.30, 1,1],  # Canadá 1-1 Bosnia y Herz.
    [55,19, 4,0, 1.11,1.94, 2.50,0.80, 68.5,80.5, 3,5,   75,450, 26.2,27.2,  7.0, 9.0, 0.28,0.70, 1,1],  # Qatar 1-1 Suiza (sorpresa)
    [ 6, 8, 1,3, 1.61,1.22, 2.50,0.50, 86.0,80.0, 5,4, 1200,320, 24.5,25.2, 14.0,11.0, 0.39,0.83, 1,1],  # Brasil 1-1 Marruecos (sorpresa)
    [43,83, 0,2, 2.00,1.60, 0.63,1.50, 72.5,60.5, 5,1,  180, 25, 27.2,25.5,  9.0, 2.0, 0.40,0.13, 1,0],  # Escocia 1-0 Haití
    [16,40, 2,1, 2.00,1.00, 1.17,1.44, 80.0,73.5, 8,4,  520,150, 25.2,26.5, 18.0, 8.0, 0.57,0.28, 4,1],  # Estados Unidos 4-1 Paraguay
    [27,22, 4,0, 1.44,1.33, 2.40,1.40, 77.5,79.5, 5,7,  220,490, 26.8,26.2,  9.0,14.0, 0.44,0.60, 2,0],  # Australia 2-0 Turquía (sorpresa)
    [ 7,18, 0,4, 2.90,1.40, 2.67,0.56, 84.5,81.5, 8,9,  870,560, 25.8,25.5, 15.0,18.0, 0.70,0.78, 2,2],  # Países Bajos 2-2 Japón
    [21,85, 4,5, 1.67,1.00, 3.50,1.88, 77.5,60.0, 7,9,  180, 40, 26.5,26.5, 12.0, 6.0, 0.61,0.88, 2,2],  # Irán 2-2 Nueva Zelanda (sorpresa)
    [17,61, 1,4, 1.56,1.11, 1.44,1.78, 81.0,68.0, 6,5,  430,110, 27.8,26.5, 13.0, 7.0, 0.44,0.39, 1,1],  # Uruguay 1-1 Arabia Saudita
    [ 1,14, 0,3, 3.20,0.80, 2.00,0.83, 88.2,79.5, 9,4, 1050,280, 26.1,26.0, 25.0,10.0, 0.80,0.67, 3,1],  # Francia 3-1 Senegal
    [31,57, 0,4, 3.50,1.20, 1.14,1.43, 79.5,68.0,16,4,  560, 65, 25.5,26.5, 21.0, 7.0, 0.80,0.36, 4,1],  # Noruega 4-1 Irak
    [ 3,28, 1,3, 1.94,0.94, 2.00,0.83, 87.0,77.0, 8,4,  760,160, 28.2,26.5, 18.5,10.0, 0.67,0.67, 3,0],  # Argentina 3-0 Argelia
    [24,63, 0,4, 2.50,1.40, 1.17,1.67, 79.5,66.5, 6,4,  410, 55, 26.5,26.2, 11.0, 6.0, 0.70,0.33, 3,1],  # Austria 3-1 Jordania
    [ 5,46, 0,3, 2.80,0.70, 1.33,0.83, 85.8,70.5, 7,3,  920, 95, 27.8,26.0, 18.0, 8.0, 0.90,0.50, 1,1],  # Portugal 1-1 RD Congo (sorpresa)
]

# Datos ambientales por partido (paralelo a historical_raw)
historical_env = [
    # Qatar 2022 — 16 partidos (estadios AC, temperatura controlada)
    *[{"altitude":10,  "temp":22, "wind":8,  "hydration":0.0}] * 16,
    # Rusia 2018 — 8 partidos (temperatura fresca, viento variable)
    *[{"altitude":140, "temp":18, "wind":14, "hydration":0.0}] * 8,
    # Upsets históricos — 5 partidos
    *[{"altitude":300, "temp":24, "wind":12, "hydration":0.1}] * 5,
    # Brasil 2014 — 5 partidos (calor intenso, algo de altitud)
    *[{"altitude":600, "temp":29, "wind":9,  "hydration":0.6}] * 5,
    # Empates técnicos — 8 partidos
    *[{"altitude":300, "temp":22, "wind":10, "hydration":0.0}] * 8,
    # Finales / partidos defensivos — 6 partidos
    *[{"altitude":200, "temp":20, "wind":8,  "hydration":0.0}] * 6,
    # Cross UEFA vs AFC — 4 partidos
    *[{"altitude":300, "temp":22, "wind":10, "hydration":0.0}] * 4,
    # Cross UEFA vs CAF — 4 partidos
    *[{"altitude":300, "temp":25, "wind":12, "hydration":0.1}] * 4,
    # Cross UEFA vs CONCACAF — 3 partidos
    *[{"altitude":300, "temp":22, "wind":10, "hydration":0.0}] * 3,
    # Cross CONMEBOL vs AFC — 3 partidos
    *[{"altitude":300, "temp":23, "wind":10, "hydration":0.0}] * 3,
    # CONMEBOL vs CAF — 2 partidos
    *[{"altitude":400, "temp":26, "wind":10, "hydration":0.2}] * 2,
    # Equipos débiles favorecidos — 6 partidos
    *[{"altitude":300, "temp":24, "wind":10, "hydration":0.0}] * 6,
    # 2026 Jornada 1 (14-15 jun) — 5 partidos con sede real
    {"altitude":5,   "temp":27, "wind":18, "hydration":0.2},  # Alemania 7-1 Curazao → MetLife
    {"altitude":5,   "temp":28, "wind":18, "hydration":0.2},  # Suecia 5-1 Túnez → MetLife
    {"altitude":3,   "temp":31, "wind":15, "hydration":0.8},  # Costa de Marfil 1-0 Ecuador → Miami
    {"altitude":229, "temp":30, "wind":10, "hydration":0.5},  # Bélgica 1-1 Egipto → Charlotte
    {"altitude":30,  "temp":24, "wind":10, "hydration":0.1},  # España 0-0 Cabo Verde → SoFi
    # 2026 Jornada 1 continuación (11-17 jun) — 16 partidos con sede real
    {"altitude":282, "temp":32, "wind":18, "hydration":0.6},  # México 2-0 Sudáfrica → Kansas City
    {"altitude":5,   "temp":27, "wind":18, "hydration":0.2},  # Corea del Sur 2-1 Rep. Checa → MetLife
    {"altitude":76,  "temp":24, "wind":14, "hydration":0.1},  # Canadá 1-1 Bosnia → Toronto
    {"altitude":2240,"temp":18, "wind":9,  "hydration":0.0},  # Qatar 1-1 Suiza → México DF
    {"altitude":3,   "temp":32, "wind":15, "hydration":0.9},  # Brasil 1-1 Marruecos → Miami
    {"altitude":8,   "temp":24, "wind":17, "hydration":0.1},  # Escocia 1-0 Haití → Boston
    {"altitude":185, "temp":35, "wind":15, "hydration":0.7},  # USA 4-1 Paraguay → Arlington
    {"altitude":538, "temp":35, "wind":12, "hydration":0.8},  # Australia 2-0 Turquía → Monterrey
    {"altitude":76,  "temp":24, "wind":14, "hydration":0.1},  # Países Bajos 2-2 Japón → Toronto
    {"altitude":1566,"temp":22, "wind":10, "hydration":0.1},  # Irán 2-2 Nueva Zelanda → Guadalajara
    {"altitude":229, "temp":30, "wind":10, "hydration":0.5},  # Uruguay 1-1 Arabia Saudita → Charlotte
    {"altitude":179, "temp":28, "wind":22, "hydration":0.2},  # Francia 3-1 Senegal → Chicago
    {"altitude":234, "temp":28, "wind":8,  "hydration":0.3},  # Noruega 4-1 Irak → Pasadena
    {"altitude":30,  "temp":24, "wind":10, "hydration":0.1},  # Argentina 3-0 Argelia → SoFi
    {"altitude":2240,"temp":18, "wind":9,  "hydration":0.0},  # Austria 3-1 Jordania → Azteca
    {"altitude":5,   "temp":28, "wind":16, "hydration":0.2},  # Portugal 1-1 RD Congo → MetLife
]
assert len(historical_env) == len(historical_raw), f"Env list mismatch: {len(historical_env)} vs {len(historical_raw)}"

# Probabilidades pre-partido de casas de apuestas por partido
# Fuentes: Squawka AI, CleverScores, FoxSports, CBS Sports, 1960Tips
# None = estimado por fórmula a partir de ranking/calidad de plantilla
historical_bk = [
    *[None] * 70,  # Partidos históricos (2014, 2018, 2022) — estimación por fórmula
    # ── 2026 Jornada 1 (14-15 jun) — cuotas reales de mercado ─────────────────
    [0.87, 0.09, 0.04],  # Alemania 7-1 Curazao     (bk: Ale 85%)
    [0.73, 0.18, 0.09],  # Suecia 5-1 Túnez          (bk: Sue 70%)
    [0.38, 0.30, 0.32],  # Costa de Marfil 1-0 Ecu   (bk: igualado — sorpresa)
    [0.65, 0.22, 0.13],  # Bélgica 1-1 Egipto        (bk: Bél 62%)
    [0.90, 0.07, 0.03],  # España 0-0 Cabo Verde      (bk: Esp 90% — sorpresa extrema)
    # ── 2026 Jornada 1 continuación (11-17 jun) — cuotas reales ───────────────
    [0.62, 0.23, 0.15],  # México 2-0 Sudáfrica
    [0.45, 0.28, 0.27],  # Corea del Sur 2-1 Rep.Checa
    [0.48, 0.28, 0.24],  # Canadá 1-1 Bosnia
    [0.11, 0.24, 0.65],  # Qatar 1-1 Suiza            (bk: Sui 65% — sorpresa Qatar)
    [0.64, 0.22, 0.14],  # Brasil 1-1 Marruecos       (bk: Bra 62% — sorpresa)
    [0.75, 0.17, 0.08],  # Escocia 1-0 Haití
    [0.58, 0.24, 0.18],  # USA 4-1 Paraguay
    [0.28, 0.27, 0.45],  # Australia 2-0 Turquía      (bk: Tur 45% — sorpresa Aus)
    [0.68, 0.20, 0.12],  # Países Bajos 2-2 Japón     (bk: NED 65% — sorpresa)
    [0.52, 0.25, 0.23],  # Irán 2-2 Nueva Zelanda
    [0.60, 0.24, 0.16],  # Uruguay 1-1 Arabia Saudita
    [0.79, 0.15, 0.06],  # Francia 3-1 Senegal
    [0.83, 0.12, 0.05],  # Noruega 4-1 Irak
    [0.89, 0.07, 0.04],  # Argentina 3-0 Argelia
    [0.78, 0.15, 0.07],  # Austria 3-1 Jordania
    [0.87, 0.09, 0.04],  # Portugal 1-1 RD Congo      (bk: Por 87% — sorpresa)
]
assert len(historical_bk) == len(historical_raw), f"BK list mismatch: {len(historical_bk)} vs {len(historical_raw)}"

# Construir el dataset combinando raw data con features tácticas históricas aproximadas
rows = []
for i, r in enumerate(historical_raw):
    rA,rB,cA,cB,gfA,gaA,gfB,gaB,sqA,sqB,tsA,tsB,mvA,mvB,ageA,ageB,acA,acB,wcfA,wcfB,gA,gB = r
    env    = historical_env[i]
    bk_raw = historical_bk[i]
    if bk_raw is None:
        bk_fwd = estimate_bk_prob(rA, rB, sqA, sqB, mvA, mvB)
    else:
        bk_fwd = bk_raw
    bk_inv = [bk_fwd[2], bk_fwd[1], bk_fwd[0]]

    def make_fake_team_feat(rnk, cf, gf_pg, ga_pg, sq, ts, mv, age, ac, wcf, is_A=True, ab=0.0):
        wc_wr = wcf
        wc_gf_pg_ = gf_pg
        wc_ga_pg_ = ga_pg
        tact = hist_tact(rnk, ab)
        return {
            "rank": rnk, "conf": cf, "conf_wc_exp": list(CONF_WC_EXP.values())[min(cf, 5)],
            "qual_gf_pg": gf_pg, "qual_ga_pg": ga_pg, "qual_wr": wc_wr, "qual_gd": (gf_pg - ga_pg) * 10,
            "top_sc": ts, "squad_rating": sq, "log_mv": np.log1p(mv), "avg_age": age,
            "att_combo": ac, "star_avg_rat": sq - 2, "log_star_val": np.log1p(mv * 0.1),
            "wc_form": wcf, "wc_gf_pg": wc_gf_pg_, "wc_ga_pg": wc_ga_pg_,
            "is_top5": int(rnk <= 5), "is_top10": int(rnk <= 10),
            "form_attack": tact["form_attack"], "form_defense": tact["form_defense"],
            "width": tact["width"], "pressing": tact["pressing"],
            "set_piece": tact["set_piece"], "style_score": tact["style_score"],
        }

    fA_ = make_fake_team_feat(rA, cA, gfA, gaA, sqA, tsA, mvA, ageA, acA, wcfA, is_A=True)
    fB_ = make_fake_team_feat(rB, cB, gfB, gaB, sqB, tsB, mvB, ageB, acB, wcfB, is_A=False)

    feat_fwd = make_match_feat(fA_, fB_, **env, bk_win_A=bk_fwd[0], bk_draw=bk_fwd[1], bk_win_B=bk_fwd[2])
    feat_inv = make_match_feat(fB_, fA_, **env, bk_win_A=bk_inv[0], bk_draw=bk_inv[1], bk_win_B=bk_inv[2])

    res_fwd = 2 if gA > gB else (1 if gA == gB else 0)
    res_inv = 2 if gB > gA else (1 if gB == gA else 0)

    rows.append(feat_fwd + [float(gA), float(gB), res_fwd])
    rows.append(feat_inv + [float(gB), float(gA), res_inv])

# ──────────────────────────────────────────────────────────────────────────────
# DYNAMIC UPDATES — carga resultados nuevos del Mundial 2026
# Usa team_feats_v3 reales en lugar de aproximaciones históricas
# ──────────────────────────────────────────────────────────────────────────────
_updates_path = OUT + "wc2026_updates.json"
if os.path.exists(_updates_path):
    with open(_updates_path, "r", encoding="utf-8") as _f:
        _wc_upd = json.load(_f)
    _dyn_added = 0
    for _m in _wc_upd.get("matches", []):
        _tA, _tB = _m.get("teamA"), _m.get("teamB")
        if _tA not in team_feats_v3 or _tB not in team_feats_v3:
            print(f"  [UPDATE SKIP] {_tA} o {_tB} no está en team_feats_v3")
            continue
        _gA, _gB = int(_m["goalsA"]), int(_m["goalsB"])
        _venue   = _m.get("venue", "neutral")
        _env     = VENUES.get(_venue, VENUES["neutral"])
        _bk      = _m.get("bk_probs") or estimate_bk_prob(
                       TEAMS[_tA][0], TEAMS[_tB][0],
                       TEAMS[_tA][7], TEAMS[_tB][7],
                       TEAMS[_tA][8], TEAMS[_tB][8])
        _bk_inv  = [_bk[2], _bk[1], _bk[0]]
        _fA      = team_feats_v3[_tA]
        _fB      = team_feats_v3[_tB]
        _feat_fwd = make_match_feat(_fA, _fB, **_env,
                                    bk_win_A=_bk[0],     bk_draw=_bk[1],     bk_win_B=_bk[2])
        _feat_inv = make_match_feat(_fB, _fA, **_env,
                                    bk_win_A=_bk_inv[0], bk_draw=_bk_inv[1], bk_win_B=_bk_inv[2])
        _res_fwd  = 2 if _gA > _gB else (1 if _gA == _gB else 0)
        _res_inv  = 2 if _gB > _gA else (1 if _gB == _gA else 0)
        rows.append(_feat_fwd + [float(_gA), float(_gB), _res_fwd])
        rows.append(_feat_inv + [float(_gB), float(_gA), _res_inv])
        _dyn_added += 1
    if _dyn_added > 0:
        print(f"  [UPDATE] +{_dyn_added} partidos dinámicos de wc2026_updates.json")

df = pd.DataFrame(rows, columns=FEAT_COLS + ["gA", "gB", "resultado"])
print(f"\nDataset v3: {len(df)} partidos | Features: {len(FEAT_COLS)}")
print(f"Distribución: {dict(zip(['Derrota','Empate','Victoria'], df['resultado'].value_counts().sort_index().tolist()))}")

X = df[FEAT_COLS].values
y_clf = df["resultado"].values
y_gA  = df["gA"].values.astype(float)
y_gB  = df["gB"].values.astype(float)

# ═══════════════════════════════════════════════════════════════════════════════
# 5. SELF-ATTENTION PREPROCESSOR (Red 2ª generación — sin TF/PyTorch)
#    Implementa multi-head feature attention sobre grupos semánticos de features
# ═══════════════════════════════════════════════════════════════════════════════
class MultiHeadFeatureAttention(BaseEstimator, TransformerMixin):
    """
    Mecanismo de self-attention sobre grupos de features.
    Aprende pesos de atención usando GBT feature importances.
    Output: X_original + X_attended (skip connection)
    """
    def __init__(self, n_heads=4, temperature=0.5):
        self.n_heads = n_heads
        self.temperature = temperature
        self.attention_weights_ = None

    def _softmax(self, x):
        e = np.exp((x - x.max()) / self.temperature)
        return e / e.sum()

    def fit(self, X, y=None):
        n_feat = X.shape[1]
        # Dividir features en n_heads grupos
        self.group_size = n_feat // self.n_heads
        self.n_feat = n_feat
        # Inicializar pesos de atención uniformes (se refinan con GBT importances si se proveen)
        self.attention_weights_ = [
            np.ones(self.group_size) / self.group_size
            for _ in range(self.n_heads)
        ]
        return self

    def set_attention_from_importances(self, importances):
        """Actualiza pesos de atención usando feature importances."""
        n = self.group_size
        for h in range(self.n_heads):
            start = h * n
            end   = start + n
            if end > len(importances):
                end = len(importances)
            group_imp = importances[start:end]
            if group_imp.sum() > 0:
                self.attention_weights_[h] = self._softmax(group_imp * 10)  # amplificar diferencias

    def transform(self, X):
        n = self.group_size
        heads_out = []
        for h in range(self.n_heads):
            start = h * n
            end   = min(start + n, X.shape[1])
            group = X[:, start:end]
            w = self.attention_weights_[h][:end - start]
            w = w / w.sum()
            attended = group * w  # weighted feature scaling
            heads_out.append(attended)
        # Concatenar salidas de todos los heads
        X_attended = np.concatenate(heads_out, axis=1)
        # Skip connection: X original + X_attended
        padding = X.shape[1] - X_attended.shape[1]
        if padding > 0:
            X_attended = np.concatenate([X_attended, np.zeros((X.shape[0], padding))], axis=1)
        return np.concatenate([X, X_attended], axis=1)

    def get_feature_names_out(self, input_features=None):
        n_orig = self.n_feat
        return list(range(n_orig * 2))

# ═══════════════════════════════════════════════════════════════════════════════
# 6. ENTRENAMIENTO — Split
# ═══════════════════════════════════════════════════════════════════════════════
X_tr, X_te, yc_tr, yc_te, gA_tr, gA_te, gB_tr, gB_te = train_test_split(
    X, y_clf, y_gA, y_gB, test_size=0.22, random_state=42, stratify=y_clf
)

# ───────────────────────────────────────────────────────────────────────────────
# ENGINE A — Deep MLP con Self-Attention (2ª generación)
# ───────────────────────────────────────────────────────────────────────────────
print("\n[ENGINE A] Entrenando Deep MLP + Self-Attention...")

# Paso 1: Preentrenar GBT rápido para obtener feature importances
from sklearn.ensemble import GradientBoostingClassifier
scaler_pre = StandardScaler()
X_tr_pre   = scaler_pre.fit_transform(X_tr)
X_te_pre   = scaler_pre.transform(X_te)

gbt_pre = GradientBoostingClassifier(n_estimators=80, max_depth=3, random_state=42)
gbt_pre.fit(X_tr_pre, yc_tr)

# Paso 2: Self-Attention con pesos calibrados por importances
attention = MultiHeadFeatureAttention(n_heads=4, temperature=0.45)
attention.fit(X_tr_pre)
attention.set_attention_from_importances(gbt_pre.feature_importances_)

X_tr_att = attention.transform(X_tr_pre)
X_te_att  = attention.transform(X_te_pre)

# Paso 3: Scaler sobre output atención
scaler_A = StandardScaler()
X_tr_A   = scaler_A.fit_transform(X_tr_att)
X_te_A   = scaler_A.transform(X_te_att)

# MLP profundo agresivo
mlp_A = MLPClassifier(
    hidden_layer_sizes=(512, 256, 128, 64, 32),
    activation='relu', solver='adam',
    alpha=0.001, learning_rate='adaptive', learning_rate_init=0.0008,
    max_iter=3000, random_state=42,
    early_stopping=True, validation_fraction=0.15, n_iter_no_change=50,
    batch_size=16,
)
mlp_A.fit(X_tr_A, yc_tr)

pred_A   = mlp_A.predict(X_te_A)
prob_A   = mlp_A.predict_proba(X_te_A)
acc_A    = accuracy_score(yc_te, pred_A)
f1_A     = f1_score(yc_te, pred_A, average='weighted')
auc_A    = roc_auc_score(yc_te, prob_A, multi_class='ovr', average='weighted')
print(f"  Engine A: Acc={acc_A:.3f} | F1={f1_A:.3f} | AUC={auc_A:.3f}")

# ───────────────────────────────────────────────────────────────────────────────
# ENGINE B — XGBoost Agresivo
# ───────────────────────────────────────────────────────────────────────────────
print("\n[ENGINE B] Entrenando XGBoost agresivo...")

scaler_B = StandardScaler()
X_tr_B   = scaler_B.fit_transform(X_tr)
X_te_B   = scaler_B.transform(X_te)

xgb_B = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.07,
    subsample=0.80,
    colsample_bytree=0.80,
    min_child_weight=3,
    gamma=0.20,
    reg_alpha=0.3,
    reg_lambda=2.5,
    objective='multi:softprob',
    num_class=3,
    use_label_encoder=False,
    eval_metric='mlogloss',
    random_state=42,
    n_jobs=-1,
)
xgb_B.fit(X_tr_B, yc_tr,
          eval_set=[(X_te_B, yc_te)],
          verbose=False)

pred_B = xgb_B.predict(X_te_B)
prob_B = xgb_B.predict_proba(X_te_B)
acc_B  = accuracy_score(yc_te, pred_B)
f1_B   = f1_score(yc_te, pred_B, average='weighted')
auc_B  = roc_auc_score(yc_te, prob_B, multi_class='ovr', average='weighted')
print(f"  Engine B: Acc={acc_B:.3f} | F1={f1_B:.3f} | AUC={auc_B:.3f}")

# ───────────────────────────────────────────────────────────────────────────────
# CALIBRACIÓN DE TEMPERATURA — predicciones más agresivas (T < 1)
# ───────────────────────────────────────────────────────────────────────────────
TEMP = 0.55  # valores < 1 agudizan las predicciones (menos empates, más decisión)

def apply_temperature(probs, T=TEMP):
    log_p = np.log(np.clip(probs, 1e-9, 1.0)) / T
    log_p -= log_p.max(axis=1, keepdims=True)
    e = np.exp(log_p)
    return e / e.sum(axis=1, keepdims=True)

prob_A_cal = apply_temperature(prob_A, TEMP)
prob_B_cal = apply_temperature(prob_B, TEMP)

pred_A_cal = prob_A_cal.argmax(axis=1)
pred_B_cal = prob_B_cal.argmax(axis=1)

acc_A_cal  = accuracy_score(yc_te, pred_A_cal)
acc_B_cal  = accuracy_score(yc_te, pred_B_cal)
f1_A_cal   = f1_score(yc_te, pred_A_cal, average='weighted')
f1_B_cal   = f1_score(yc_te, pred_B_cal, average='weighted')

print(f"\n[CALIBRADO T={TEMP}]")
print(f"  Engine A calibrado: Acc={acc_A_cal:.3f} | F1={f1_A_cal:.3f}")
print(f"  Engine B calibrado: Acc={acc_B_cal:.3f} | F1={f1_B_cal:.3f}")

# ───────────────────────────────────────────────────────────────────────────────
# REGRESORES DE GOLES (XGBoost para ambos engines)
# ───────────────────────────────────────────────────────────────────────────────
reg_A_goals = xgb.XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.08,
                                subsample=0.8, random_state=42, n_jobs=-1)
reg_A_goals.fit(X_tr_B, gA_tr)
reg_B_goals = xgb.XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.08,
                                subsample=0.8, random_state=42, n_jobs=-1)
reg_B_goals.fit(X_tr_B, gB_tr)

gA_pred = reg_A_goals.predict(X_te_B).clip(0, 6)
gB_pred = reg_B_goals.predict(X_te_B).clip(0, 6)
mae_A   = mean_absolute_error(gA_te, gA_pred)
mae_B   = mean_absolute_error(gB_te, gB_pred)
print(f"\n  Regresor goles: MAE_A={mae_A:.3f} | MAE_B={mae_B:.3f}")

# Reports
print(f"\n{'='*60}")
print("CLASSIFICATION REPORT — ENGINE A (calibrado):")
print(classification_report(yc_te, pred_A_cal, target_names=["Derrota","Empate","Victoria"]))
print("CLASSIFICATION REPORT — ENGINE B (calibrado):")
print(classification_report(yc_te, pred_B_cal, target_names=["Derrota","Empate","Victoria"]))

# Feature importance XGBoost
fi_xgb = pd.DataFrame({
    "feature": FEAT_COLS,
    "importance": xgb_B.feature_importances_
}).sort_values("importance", ascending=False)
print("\nTop 15 features (XGBoost Engine B):")
print(fi_xgb.head(15).to_string(index=False))

# ═══════════════════════════════════════════════════════════════════════════════
# 7. GUARDAR MODELOS
# ═══════════════════════════════════════════════════════════════════════════════
joblib.dump({"attention": attention, "scaler_pre": scaler_pre, "scaler_A": scaler_A, "mlp": mlp_A}, OUT + "engine_A_v3.pkl")
joblib.dump({"scaler": scaler_B, "xgb": xgb_B, "reg_A": reg_A_goals, "reg_B": reg_B_goals}, OUT + "engine_B_v3.pkl")
print("\nModelos v3 guardados.")

# ═══════════════════════════════════════════════════════════════════════════════
# 8. GENERAR PREDICCIONES DUALES — 48×47 partidos
# ═══════════════════════════════════════════════════════════════════════════════
print("\nGenerando predicciones duales...")

def predict_match(nameA, nameB, venue="neutral", bk_probs=None):
    fA = team_feats_v3[nameA]
    fB = team_feats_v3[nameB]
    env = VENUES.get(venue, VENUES["neutral"])
    if bk_probs is None:
        tA = TEAMS[nameA]; tB = TEAMS[nameB]
        bk = estimate_bk_prob(tA[0], tB[0], tA[7], tB[7], tA[8], tB[8])
    else:
        bk = bk_probs
    x  = np.array(make_match_feat(fA, fB, **env,
                                   bk_win_A=bk[0], bk_draw=bk[1], bk_win_B=bk[2])).reshape(1, -1)

    # Engine A
    xA_pre  = scaler_pre.transform(x)
    xA_att  = attention.transform(xA_pre)
    xA_fin  = scaler_A.transform(xA_att)
    p_A_raw = mlp_A.predict_proba(xA_fin)
    p_A     = apply_temperature(p_A_raw, TEMP)[0]

    # Engine B
    xB_fin  = scaler_B.transform(x)
    p_B_raw = xgb_B.predict_proba(xB_fin)
    p_B     = apply_temperature(p_B_raw, TEMP)[0]

    # Goles
    lA = float(np.clip(reg_A_goals.predict(xB_fin)[0], 0.2, 5.5))
    lB = float(np.clip(reg_B_goals.predict(xB_fin)[0], 0.2, 5.5))

    return {
        "engine_A": {
            "p_derrota":  round(float(p_A[0]), 4),
            "p_empate":   round(float(p_A[1]), 4),
            "p_victoria": round(float(p_A[2]), 4),
        },
        "engine_B": {
            "p_derrota":  round(float(p_B[0]), 4),
            "p_empate":   round(float(p_B[1]), 4),
            "p_victoria": round(float(p_B[2]), 4),
        },
        "lambda_A": round(lA, 3),
        "lambda_B": round(lB, 3),
        "lineup_A": LINEUP.get(nameA, {"formation": "4-3-3", "style": "balanced"}),
        "lineup_B": LINEUP.get(nameB, {"formation": "4-3-3", "style": "balanced"}),
        "bk_estimate": [round(float(bk[0]),3), round(float(bk[1]),3), round(float(bk[2]),3)],
    }

preds_v3 = {}
teams_list = sorted(TEAMS.keys())
for tA in teams_list:
    preds_v3[tA] = {}
    for tB in teams_list:
        if tA == tB:
            continue
        preds_v3[tA][tB] = predict_match(tA, tB)

with open(OUT + "predicciones_v3.json", "w", encoding="utf-8") as f:
    json.dump(preds_v3, f, ensure_ascii=False, indent=2)

fi_xgb.to_csv(OUT + "feature_importance_v3.csv", index=False)
print(f"predicciones_v3.json generado: {len(preds_v3)} equipos")

# Guardar también config de alineaciones
lineup_config = {"LINEUP": LINEUP, "FORMATION_FEATURES": FORMATION_FEATURES, "STYLE_SCORE": STYLE_SCORE, "VENUES": VENUES, "MATCH_SCHEDULE": MATCH_SCHEDULE}
with open(OUT + "lineup_config.json", "w", encoding="utf-8") as f:
    json.dump(lineup_config, f, ensure_ascii=False, indent=2)

# ═══════════════════════════════════════════════════════════════════════════════
# 9. VISUALIZACIONES
# ═══════════════════════════════════════════════════════════════════════════════
label_names = ["Derrota","Empate","Victoria"]
colors_3    = ['#f85149','#d29922','#56d364']

fig, axes = plt.subplots(2, 3, figsize=(20, 12))
fig.patch.set_facecolor('#0d1117')
fig.suptitle("MODELO v3 — Engine A (MLP+Atención) vs Engine B (XGBoost Agresivo)\nMundial FIFA 2026 · Calibración T=0.55",
             fontsize=14, color='white', y=0.98)

# 1. Confusion matrix Engine A
ax = axes[0, 0]
cm_A = confusion_matrix(yc_te, pred_A_cal)
sns.heatmap(cm_A, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=label_names, yticklabels=label_names,
            linewidths=0.5, cbar_kws={"shrink": 0.8})
ax.set_facecolor('#161b22')
ax.set_title(f"Confusión Engine A (MLP+Atención)\nAcc={acc_A_cal:.3f} F1={f1_A_cal:.3f}", color='white', fontsize=11)
ax.tick_params(colors='white')
ax.set_xlabel("Predicho", color='lightgray')
ax.set_ylabel("Real", color='lightgray')

# 2. Confusion matrix Engine B
ax = axes[0, 1]
cm_B = confusion_matrix(yc_te, pred_B_cal)
sns.heatmap(cm_B, annot=True, fmt='d', cmap='Oranges', ax=ax,
            xticklabels=label_names, yticklabels=label_names,
            linewidths=0.5, cbar_kws={"shrink": 0.8})
ax.set_facecolor('#161b22')
ax.set_title(f"Confusión Engine B (XGBoost Agresivo)\nAcc={acc_B_cal:.3f} F1={f1_B_cal:.3f}", color='white', fontsize=11)
ax.tick_params(colors='white')
ax.set_xlabel("Predicho", color='lightgray')
ax.set_ylabel("Real", color='lightgray')

# 3. Feature importance top 15 (Engine B XGBoost)
ax = axes[0, 2]
top15 = fi_xgb.head(15)
cmap_fi = plt.cm.RdYlGn(np.linspace(0.2, 0.9, 15))[::-1]
ax.barh(top15["feature"][::-1], top15["importance"][::-1], color=cmap_fi, edgecolor='white', lw=0.3)
ax.set_facecolor('#161b22')
ax.set_title("Feature Importance Top-15 (XGBoost Engine B)", color='white', fontsize=11)
ax.set_xlabel("Importance", color='lightgray')
ax.tick_params(colors='white')
ax.spines[:].set_color('#30363d')

# 4. Comparativa Acc/F1/AUC entre engines
ax = axes[1, 0]
metrics = ['Accuracy', 'F1-weighted', 'AUC-ROC']
vals_A  = [acc_A_cal, f1_A_cal, auc_A]
vals_B  = [acc_B_cal, f1_B_cal, auc_B]
x_pos   = np.arange(3)
w       = 0.35
b1 = ax.bar(x_pos - w/2, vals_A, w, label='Engine A (MLP+Atención)', color='#58a6ff', edgecolor='white', lw=0.3)
b2 = ax.bar(x_pos + w/2, vals_B, w, label='Engine B (XGBoost)',      color='#f0883e', edgecolor='white', lw=0.3)
ax.set_xticks(x_pos); ax.set_xticklabels(metrics)
ax.set_ylim(0, 1.1)
ax.set_facecolor('#161b22')
ax.set_title("Comparativa: Engine A vs Engine B", color='white', fontsize=11)
ax.tick_params(colors='white')
ax.spines[:].set_color('#30363d')
ax.legend(facecolor='#161b22', edgecolor='#30363d', labelcolor='white', fontsize=9)
for bar in list(b1) + list(b2):
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + 0.02, f"{h:.2f}", ha='center', color='white', fontsize=8)

# 5. Distribución probabilidades calibradas (Engine B — más agresivo)
ax = axes[1, 1]
for i, (name, color) in enumerate(zip(label_names, colors_3)):
    ax.hist(prob_B_cal[:, i], bins=15, alpha=0.75, color=color, label=name, edgecolor='white', lw=0.3)
ax.set_facecolor('#161b22')
ax.set_title(f"Distribución Probs Engine B (T={TEMP} → más agresivo)", color='white', fontsize=11)
ax.set_xlabel("Probabilidad", color='lightgray')
ax.tick_params(colors='white')
ax.spines[:].set_color('#30363d')
ax.legend(facecolor='#161b22', edgecolor='#30363d', labelcolor='white')

# 6. Goles: real vs predicho
ax = axes[1, 2]
ax.scatter(gA_te, gA_pred, alpha=0.7, color='#58a6ff', s=50, edgecolors='white', lw=0.3,
           label=f'λ_A MAE={mae_A:.2f}')
ax.scatter(gB_te, gB_pred, alpha=0.7, color='#f0883e', s=50, edgecolors='white', lw=0.3,
           label=f'λ_B MAE={mae_B:.2f}', marker='^')
mx = max(gA_te.max(), gB_te.max()) + 0.5
ax.plot([0, mx], [0, mx], 'w--', lw=1, alpha=0.5)
ax.set_facecolor('#161b22')
ax.set_title("Goles: Real vs Predicho (XGBoost)", color='white', fontsize=11)
ax.set_xlabel("Goles reales", color='lightgray')
ax.set_ylabel("Goles predichos", color='lightgray')
ax.tick_params(colors='white')
ax.spines[:].set_color('#30363d')
ax.legend(facecolor='#161b22', edgecolor='#30363d', labelcolor='white', fontsize=9)

fig.text(0.5, 0.01,
         f"Engine A: Acc={acc_A_cal:.3f} F1={f1_A_cal:.3f} AUC={auc_A:.3f}  |  "
         f"Engine B: Acc={acc_B_cal:.3f} F1={f1_B_cal:.3f} AUC={auc_B:.3f}  |  "
         f"Features={N_FEAT} | Dataset={len(df)} partidos | T={TEMP}",
         ha='center', color='lightgray', fontsize=9)

plt.tight_layout(rect=[0, 0.04, 1, 0.96])
plt.savefig(OUT + "metricas_v3.png", dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close()
print("metricas_v3.png guardada.")

# ═══════════════════════════════════════════════════════════════════════════════
# 10. RESUMEN FINAL
# ═══════════════════════════════════════════════════════════════════════════════
print(f"""
╔══════════════════════════════════════════════════════════════╗
║         MODELO v3 — MUNDIAL FIFA 2026                        ║
╠══════════════════════════════════════════════════════════════╣
║  Features v3:   {N_FEAT:<5} (tácticas + sin injury + sin is_host)  ║
║  Dataset:       {len(df):<5} partidos históricos                   ║
║  Temperatura:   {TEMP} (predicciones más agresivas/decisivas) ║
║                                                              ║
║  ENGINE A — Deep MLP + Self-Attention (2ª generación):      ║
║    Capas: 512→256→128→64→32 | Heads: 4 | T: {TEMP}         ║
║    Acc: {acc_A_cal:.3f} | F1: {f1_A_cal:.3f} | AUC: {auc_A:.3f}            ║
║                                                              ║
║  ENGINE B — XGBoost Agresivo:                               ║
║    depth=7 | estimators=400 | lr=0.06                       ║
║    Acc: {acc_B_cal:.3f} | F1: {f1_B_cal:.3f} | AUC: {auc_B:.3f}            ║
║                                                              ║
║  MAE Goles: A={mae_A:.3f} | B={mae_B:.3f}                       ║
╚══════════════════════════════════════════════════════════════╝
""")

# Muestra ejemplos de predicciones duales para partidos clave
print("EJEMPLOS DE PREDICCIONES DUALES:")
showcases = [
    ("Francia", "Argentina"),
    ("España", "Brasil"),
    ("Alemania", "Portugal"),
    ("Marruecos", "Uruguay"),
    ("Japón", "Colombia"),
]
for tA, tB in showcases:
    if tA in team_feats_v3 and tB in team_feats_v3:
        p = predict_match(tA, tB)
        pA = p["engine_A"]; pB = p["engine_B"]
        print(f"\n  {tA} [{p['lineup_A']['formation']} {p['lineup_A']['style']}]"
              f" vs {tB} [{p['lineup_B']['formation']} {p['lineup_B']['style']}]")
        print(f"    Engine A (MLP+Atención): D={pA['p_derrota']:.2f} E={pA['p_empate']:.2f} V={pA['p_victoria']:.2f}")
        print(f"    Engine B (XGBoost):      D={pB['p_derrota']:.2f} E={pB['p_empate']:.2f} V={pB['p_victoria']:.2f}")
        print(f"    Goles esperados: {tA}={p['lambda_A']:.1f} | {tB}={p['lambda_B']:.1f}")
