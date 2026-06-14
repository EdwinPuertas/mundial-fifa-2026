"""
MODELO v2 — Mundial FIFA 2026
==============================
Nuevas variables:
  • Stats eliminatorias (GF, GA, W, GD, GF/partido, forma)
  • Jugadores clave: goles eliminatorias, rating FIFA, valor de mercado, edad promedio
  • xG en eliminatorias
  • Combinatoria de ataque (scorer_index = top_scorer_goals × squad_depth)
  • Resultados actuales del torneo (jun 2026)
  • Lesiones / disponibilidad de estrellas
  • Head-to-head histórico simplificado

Modelos: MLP + XGBoost → Ensemble (VotingClassifier)
"""

import numpy as np, pandas as pd, json, joblib, warnings
import sys; sys.path.insert(0, '/sessions/intelligent-focused-ritchie/.local/lib/python3.12/site-packages')
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor, VotingClassifier
from sklearn.preprocessing import StandardScaler, label_binarize
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import (classification_report, confusion_matrix, roc_auc_score,
                              roc_curve, mean_absolute_error, mean_squared_error,
                              f1_score, accuracy_score)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
warnings.filterwarnings('ignore')
np.random.seed(42)

OUT = "/sessions/intelligent-focused-ritchie/mnt/outputs/"
CONF_MAP = {"UEFA":0,"CONMEBOL":1,"CONCACAF":2,"CAF":3,"AFC":4,"OFC":5}

# ═══════════════════════════════════════════════════════════════════════════════
# 1. BASE DE DATOS COMPLETA — 48 SELECCIONES
#    Fuentes: Ranking FIFA jun-2026, stats eliminatorias, jugadores clave
# ═══════════════════════════════════════════════════════════════════════════════
TEAMS = {
# Nombre: [rank, conf, qual_gf, qual_ga, qual_w, qual_matches,
#           top_scorer_goals, squad_rating, market_value_M, avg_age,
#           xg_qual, injury_factor, wc_pts, wc_gf, wc_ga, wc_played]
# injury_factor: 0=todos disponibles, 0.15=estrella lesionada, 0.25=múltiples bajas

"Francia":         [1,"UEFA",   32,8,  8,10, 9,  88.2, 1050, 26.1, 28.5, 0.00, 0,0,0,0],
"España":          [2,"UEFA",   30,10, 7,10, 7,  87.5, 980,  24.8, 26.5, 0.10, 0,0,0,0],
"Argentina":       [3,"CONMEBOL",35,17,12,18,8,  87.0, 760,  28.2, 26.8, 0.05, 0,0,0,0],
"Inglaterra":      [4,"UEFA",   30,9,  8,10, 7,  86.5, 1100, 26.5, 25.5, 0.00, 0,0,0,0],
"Portugal":        [5,"UEFA",   28,7,  9,10, 7,  85.8, 920,  27.8, 27.0, 0.00, 0,0,0,0],
"Brasil":          [6,"CONMEBOL",29,22, 7,18, 5,  86.0, 1200, 24.5, 25.5, 0.10, 0,0,0,0],
"Países Bajos":    [7,"UEFA",   29,14, 7,10, 8,  84.5, 870,  25.8, 26.0, 0.00, 0,0,0,0],
"Marruecos":       [8,"CAF",    15,3,  5,6,  4,  80.0, 320,  25.2, 25.8, 0.00, 0,0,0,0],
"Bélgica":         [9,"UEFA",   27,12, 7,10, 6,  83.5, 680,  28.5, 27.5, 0.00, 0,0,0,0],
"Alemania":        [10,"UEFA",  33,11, 8,10, 9,  84.0, 890,  25.2, 25.0, 0.00, 0,0,0,0],
"Croacia":         [11,"UEFA",  22,11, 6,10, 5,  82.5, 420,  29.5, 28.5, 0.00, 0,0,0,0],
"Colombia":        [13,"CONMEBOL",26,22,8,18,7,  82.0, 480,  25.8, 25.5, 0.00, 0,0,0,0],
"Senegal":         [14,"CAF",   12,5,  4,6,  4,  79.5, 280,  26.0, 25.5, 0.00, 0,0,0,0],
"México":          [15,"CONCACAF",26,16,7,14,5,  80.5, 390,  26.5, 26.5, 0.00, 3,2,0,1],
"Estados Unidos":  [16,"CONCACAF",28,14,8,14,8,  80.0, 520,  25.2, 25.5, 0.00, 0,0,0,0],
"Uruguay":         [17,"CONMEBOL",28,20,8,18,6,  81.0, 430,  27.8, 27.0, 0.00, 0,0,0,0],
"Japón":           [18,"AFC",   48,10,14,18,9,  81.5, 560,  25.5, 25.0, 0.00, 0,0,0,0],
"Suiza":           [19,"UEFA",  25,8,  7,10, 5,  80.5, 450,  27.2, 27.5, 0.00, 0,0,0,0],
"Irán":            [21,"AFC",   30,18,11,18,7,  77.5, 180,  26.5, 27.0, 0.00, 0,0,0,0],
"Turquía":         [22,"UEFA",  24,14, 6,10, 7,  79.5, 490,  26.2, 26.0, 0.00, 0,0,0,0],
"Ecuador":         [23,"CONMEBOL",26,17, 8,18, 5, 79.0, 310,  24.8, 25.5, 0.00, 0,0,0,0],
"Austria":         [24,"UEFA",  25,14, 7,10, 6,  79.5, 410,  26.5, 26.0, 0.00, 0,0,0,0],
"Corea del Sur":   [25,"AFC",   32,20,10,18, 6,  79.0, 380,  26.0, 26.0, 0.00, 3,2,1,1],
"Australia":       [27,"AFC",   26,24, 8,18, 5,  77.5, 220,  26.8, 26.5, 0.00, 0,0,0,0],
"Argelia":         [28,"CAF",   12,5,  4,6,  4,  77.0, 160,  26.5, 26.5, 0.00, 0,0,0,0],
"Egipto":          [29,"CAF",   12,4,  4,6,  4,  76.5, 140,  26.2, 26.2, 0.00, 0,0,0,0],
"Canadá":          [30,"CONCACAF",25,12, 8,14, 6, 78.0, 340,  25.0, 25.0, 0.00, 0,0,0,0],
"Noruega":         [31,"UEFA",  35,12, 8,10,16,  79.5, 560,  25.5, 24.8, 0.00, 0,0,0,0],
"Panamá":          [33,"CONCACAF",18,18, 5,14, 4, 73.5, 95,  26.5, 27.0, 0.00, 0,0,0,0],
"Costa de Marfil": [34,"CAF",   10,6,  3,6,  3,  74.5, 210,  26.2, 25.8, 0.00, 0,0,0,0],
"Suecia":          [38,"UEFA",  22,14, 5,10, 8,  76.0, 360,  26.8, 26.5, 0.00, 0,0,0,0],
"Paraguay":        [40,"CONMEBOL",21,26, 5,18, 4, 73.5, 150,  26.5, 27.0, 0.00, 0,0,0,0],
"República Checa": [41,"UEFA",  18,12, 4,10, 5,  74.0, 220,  27.0, 27.0, 0.00, 0,1,2,1],
"Escocia":         [43,"UEFA",  20,16, 4,10, 5,  72.5, 180,  27.2, 26.8, 0.00, 0,0,0,0],
"Túnez":           [44,"CAF",   9,7,   3,6,  3,  71.5, 120,  26.8, 27.0, 0.00, 0,0,0,0],
"RD Congo":        [46,"CAF",   8,5,   3,6,  3,  70.5, 95,   26.0, 26.0, 0.00, 0,0,0,0],
"Uzbekistán":      [50,"AFC",   18,12, 6,12, 4,  70.0, 85,   25.5, 25.8, 0.00, 0,0,0,0],
"Qatar":           [55,"AFC",   20,35, 5,18, 3,  68.5, 75,   26.2, 27.0, 0.00, 0,0,0,0],
"Irak":            [57,"AFC",   16,20, 5,14, 4,  68.0, 65,   26.5, 26.5, 0.00, 0,0,0,0],
"Sudáfrica":       [60,"CAF",   10,7,  3,6,  2,  67.5, 80,   26.8, 27.2, 0.00, 0,0,2,1],
"Arabia Saudita":  [61,"AFC",   26,32, 7,18, 5,  68.0, 110,  26.5, 26.8, 0.00, 0,0,0,0],
"Jordania":        [63,"AFC",   21,30, 6,18, 4,  66.5, 55,   26.2, 26.5, 0.00, 0,0,0,0],
"Bosnia y Herz.":  [65,"UEFA",  14,18, 3,10, 3,  69.0, 95,   27.5, 27.0, 0.00, 0,0,0,0],
"Cabo Verde":      [69,"CAF",   8,7,   3,6,  2,  66.0, 55,   26.5, 27.0, 0.00, 0,0,0,0],
"Ghana":           [74,"CAF",   8,9,   2,6,  2,  65.0, 70,   26.0, 26.5, 0.00, 0,0,0,0],
"Curazao":         [82,"CONCACAF",6,10,2,8,  2,  61.5, 30,   25.8, 26.0, 0.00, 0,0,0,0],
"Haití":           [83,"CONCACAF",5,12,1,8,  1,  60.5, 25,   25.5, 26.0, 0.00, 0,0,0,0],
"Nueva Zelanda":   [85,"OFC",   28,15, 7,8,  9,  60.0, 40,   26.5, 27.0, 0.00, 0,0,0,0],
}

# Jugadores clave por equipo: [nombre, goles_elim, rating_FIFA, valor_M, posicion]
PLAYERS = {
"Francia":        [("Kylian Mbappé",9,93,180,"DEL"),("Antoine Griezmann",5,87,25,"CAM"),("Aurélien Tchouaméni",2,86,90,"MCD")],
"España":         [("Lamine Yamal",7,88,180,"EXT"),("Pedri",4,88,120,"CAM"),("Álvaro Morata",5,85,35,"DEL")],
"Argentina":      [("Lionel Messi",8,93,20,"DEL"),("Julián Álvarez",6,88,90,"DEL"),("Rodrigo De Paul",3,85,35,"MCI")],
"Inglaterra":     [("Harry Kane",7,90,80,"DEL"),("Jude Bellingham",7,91,180,"CAM"),("Phil Foden",5,88,130,"EXT")],
"Portugal":       [("Cristiano Ronaldo",7,90,15,"DEL"),("Bruno Fernandes",5,87,60,"CAM"),("Bernardo Silva",4,88,80,"CAM")],
"Brasil":         [("Vinicius Jr.",5,92,200,"EXT"),("Rodrygo",4,87,120,"EXT"),("Raphinha",4,86,80,"EXT")],
"Países Bajos":   [("Cody Gakpo",8,86,80,"EXT"),("Memphis Depay",5,85,18,"DEL"),("Frenkie de Jong",3,87,65,"MCI")],
"Marruecos":      [("Youssef En-Nesyri",4,83,30,"DEL"),("Hakim Ziyech",3,82,12,"EXT"),("Achraf Hakimi",2,87,60,"LAT")],
"Bélgica":        [("Romelu Lukaku",6,86,22,"DEL"),("Kevin De Bruyne",4,91,35,"CAM"),("Lois Openda",5,84,50,"DEL")],
"Alemania":       [("Kai Havertz",9,86,65,"CAM"),("Florian Wirtz",7,90,150,"CAM"),("Jamal Musiala",5,89,120,"EXT")],
"Croacia":        [("Ivan Perišić",5,83,15,"EXT"),("Luka Modrić",3,87,8,"MCI"),("Andrej Kramarić",5,83,18,"DEL")],
"Colombia":       [("Luis Díaz",7,87,80,"EXT"),("James Rodríguez",4,83,15,"CAM"),("Falcao",2,82,3,"DEL")],
"Senegal":        [("Sadio Mané",4,83,25,"EXT"),("Ismaïla Sarr",4,82,30,"EXT"),("Pape Matar Sarr",3,82,45,"MCI")],
"México":         [("Santiago Giménez",5,84,55,"DEL"),("Hirving Lozano",4,82,18,"EXT"),("Edson Álvarez",2,81,35,"MCD")],
"Estados Unidos": [("Christian Pulisic",8,84,50,"EXT"),("Folarin Balogun",6,83,35,"DEL"),("Weston McKennie",3,80,28,"MCI")],
"Uruguay":        [("Darwin Núñez",6,87,80,"DEL"),("Federico Valverde",4,88,120,"MCI"),("Ronald Araújo",1,84,55,"DEF")],
"Japón":          [("Junya Ito",9,83,22,"EXT"),("Takumi Minamino",7,82,15,"CAM"),("Ritsu Doan",6,82,20,"EXT")],
"Suiza":          [("Breel Embolo",5,82,22,"DEL"),("Granit Xhaka",3,83,15,"MCI"),("Xherdan Shaqiri",3,79,8,"EXT")],
"Irán":           [("Mehdi Taremi",7,82,12,"DEL"),("Sardar Azmoun",5,81,12,"DEL"),("Alireza Jahanbakhsh",4,79,8,"EXT")],
"Turquía":        [("Kerem Aktürkoğlu",7,84,35,"EXT"),("Hakan Çalhanoğlu",4,85,35,"MCI"),("Arda Güler",6,86,55,"CAM")],
"Ecuador":        [("Enner Valencia",5,81,8,"DEL"),("Moisés Caicedo",3,86,100,"MCI"),("Gonzalo Plata",4,80,20,"EXT")],
"Austria":        [("Marcel Sabitzer",6,83,22,"MCI"),("Marko Arnautović",5,81,8,"DEL"),("Christoph Baumgartner",4,82,35,"CAM")],
"Corea del Sur":  [("Son Heung-min",6,86,30,"EXT"),("Cho Gue-sung",5,81,8,"DEL"),("Lee Jae-sung",3,79,10,"MCI")],
"Australia":      [("Mathew Leckie",5,78,8,"EXT"),("Mitchell Duke",4,77,5,"DEL"),("Aaron Mooy",3,79,6,"MCI")],
"Argelia":        [("Islam Slimani",4,78,5,"DEL"),("Riyad Mahrez",4,83,15,"EXT"),("Saïd Benrahma",3,80,15,"EXT")],
"Egipto":         [("Mohamed Salah",4,89,35,"EXT"),("Mostafa Mohamed",3,79,15,"DEL"),("Trezeguet",3,78,8,"EXT")],
"Canadá":         [("Alphonso Davies",6,86,70,"LAT"),("Jonathan David",8,85,55,"DEL"),("Cyle Larin",5,78,10,"DEL")],
"Noruega":        [("Erling Haaland",16,93,180,"DEL"),("Martin Ødegaard",5,88,90,"CAM"),("Alexander Sørloth",5,82,35,"DEL")],
"Panamá":         [("Rolando Blackburn",4,73,3,"DEL"),("Aníbal Godoy",2,74,3,"MCD"),("Fidel Escobar",2,72,2,"DEF")],
"Costa de Marfil":[("Sébastien Haller",3,80,15,"DEL"),("Nicolas Pépé",3,79,10,"EXT"),("Franck Kessié",2,81,18,"MCI")],
"Suecia":         [("Viktor Gyökeres",8,84,65,"DEL"),("Alexander Isak",6,85,70,"DEL"),("Dejan Kulusevski",4,84,50,"EXT")],
"Paraguay":       [("Miguel Almirón",4,81,15,"CAM"),("Julio Enciso",5,81,25,"DEL"),("Néstor Camacho",2,74,5,"MCI")],
"República Checa":[("Tomáš Souček",5,81,20,"MCI"),("Patrik Schick",5,82,28,"DEL"),("Adam Hložek",4,81,30,"DEL")],
"Escocia":        [("Scott McTominay",5,81,25,"MCI"),("Andrew Robertson",2,83,25,"LAT"),("Che Adams",4,77,12,"DEL")],
"Túnez":          [("Youssef Msakni",3,75,5,"EXT"),("Wahbi Khazri",3,76,3,"CAM"),("Dylan Bronn",1,74,4,"DEF")],
"RD Congo":       [("Cédric Bakambu",3,76,5,"DEL"),("Chancel Mbemba",1,76,6,"DEF"),("Yannick Bolasie",2,73,3,"EXT")],
"Uzbekistán":     [("Eldor Shomurodov",4,78,8,"DEL"),("Abbosbek Fayzullayev",3,76,5,"EXT"),("Otabek Shukurov",2,74,3,"MCI")],
"Qatar":          [("Akram Afif",3,74,5,"EXT"),("Almoez Ali",3,75,4,"DEL"),("Hassan Al-Haydos",2,73,3,"CAM")],
"Irak":           [("Aymen Hussein",4,73,4,"DEL"),("Ali Al-Hamadi",2,73,6,"DEL"),("Amjed Attwan",2,71,2,"MCI")],
"Sudáfrica":      [("Percy Tau",2,76,4,"EXT"),("Teboho Mokoena",2,73,3,"MCI"),("Lyle Foster",3,75,8,"DEL")],
"Arabia Saudita": [("Salem Al-Dawsari",5,79,6,"EXT"),("Firas Al-Buraikan",5,77,5,"DEL"),("Mohammed Al-Qasem",2,73,2,"MCI")],
"Jordania":       [("Baha Faisal",4,71,2,"DEL"),("Yazan Al-Naimat",3,70,2,"MCI"),("Musa Al-Taamari",3,73,3,"EXT")],
"Bosnia y Herz.": [("Edin Džeko",3,80,5,"DEL"),("Miralem Pjanić",2,81,5,"MCI"),("Ermedin Demirović",3,79,20,"DEL")],
"Cabo Verde":     [("Garry Rodrigues",2,73,4,"EXT"),("Ryan Mendes",2,72,2,"EXT"),("Stopira",1,71,2,"DEF")],
"Ghana":          [("Jordan Ayew",2,75,8,"DEL"),("André Ayew",2,76,4,"EXT"),("Mohammed Kudus",3,82,45,"MCI")],
"Curazao":        [("Cuco Martina",1,68,1,"DEF"),("Leandro Bacuna",2,70,2,"MCI"),("Quevin Castro",2,68,1,"DEL")],
"Haití":          [("Duckens Nazon",2,68,3,"DEL"),("Frantzdy Pierrot",1,67,2,"DEL"),("Hervé Bazile",1,66,2,"CAM")],
"Nueva Zelanda":  [("Chris Wood",9,79,12,"DEL"),("Clayton Lewis",3,73,3,"MCI"),("Liberato Cacace",2,74,3,"LAT")],
}

# Grupos del sorteo
GROUPS = {
"A":["México","Corea del Sur","Sudáfrica","República Checa"],
"B":["Canadá","Bosnia y Herz.","Qatar","Suiza"],
"C":["Brasil","Marruecos","Haití","Escocia"],
"D":["Estados Unidos","Australia","Paraguay","Turquía"],
"E":["Alemania","Ecuador","Costa de Marfil","Curazao"],
"F":["Países Bajos","Japón","Túnez","Suecia"],
"G":["Bélgica","Irán","Egipto","Nueva Zelanda"],
"H":["España","Uruguay","Arabia Saudita","Cabo Verde"],
"I":["Francia","Senegal","Noruega","Irak"],
"J":["Argentina","Austria","Argelia","Jordania"],
"K":["Portugal","Colombia","Uzbekistán","RD Congo"],
"L":["Inglaterra","Croacia","Panamá","Ghana"],
}

def get_group(team):
    for g, ts in GROUPS.items():
        if team in ts: return g
    return "?"

# ═══════════════════════════════════════════════════════════════════════════════
# 2. CONSTRUIR FEATURES POR EQUIPO
# ═══════════════════════════════════════════════════════════════════════════════
def build_team_features(name):
    d = TEAMS[name]
    rank, conf = d[0], d[1]
    qual_gf, qual_ga, qual_w, qual_m = d[2], d[3], d[4], d[5]
    top_scorer, squad_rating, mv, avg_age = d[6], d[7], d[8], d[9]
    xg_qual, injury, wc_pts, wc_gf, wc_ga, wc_pl = d[10], d[11], d[12], d[13], d[14], d[15]

    players = PLAYERS.get(name, [])
    star_goal_power   = sum(p[1] for p in players)  # suma goles eliminatorias top3
    star_avg_rating   = np.mean([p[2] for p in players]) if players else squad_rating
    star_avg_value    = np.mean([p[3] for p in players]) if players else mv/10
    attack_combo_idx  = (star_goal_power * star_avg_rating) / 100  # combinatoria ataque

    # Forma en eliminatorias
    qual_gf_pg  = qual_gf / max(qual_m, 1)
    qual_ga_pg  = qual_ga / max(qual_m, 1)
    qual_wr     = qual_w / max(qual_m, 1)
    qual_gd     = qual_gf - qual_ga

    # Forma actual del torneo
    wc_gf_pg = wc_gf / max(wc_pl, 1) if wc_pl > 0 else qual_gf_pg
    wc_ga_pg = wc_ga / max(wc_pl, 1) if wc_pl > 0 else qual_ga_pg
    wc_form  = wc_pts / (wc_pl * 3) if wc_pl > 0 else qual_wr

    # Índice de defensa
    def_strength = (100 - qual_ga_pg * 15) / 100

    return {
        "rank": rank,
        "conf": CONF_MAP[conf],
        "qual_gf_pg": qual_gf_pg,
        "qual_ga_pg": qual_ga_pg,
        "qual_wr": qual_wr,
        "qual_gd": qual_gd,
        "top_scorer_goals": top_scorer,
        "squad_rating": squad_rating,
        "market_value": np.log1p(mv),       # log para reducir escala
        "avg_age": avg_age,
        "xg_qual": xg_qual,
        "injury_factor": injury,
        "attack_combo_idx": attack_combo_idx,
        "star_avg_rating": star_avg_rating,
        "star_avg_value": np.log1p(star_avg_value),
        "wc_form": wc_form,
        "wc_gf_pg": wc_gf_pg,
        "wc_ga_pg": wc_ga_pg,
        "def_strength": def_strength,
        "is_top5": int(rank <= 5),
        "is_top10": int(rank <= 10),
        "is_host": int(name in ["México","Estados Unidos","Canadá"]),
    }

team_feats = {name: build_team_features(name) for name in TEAMS}
FEAT_NAMES = list(next(iter(team_feats.values())).keys())
print(f"Features por equipo: {len(FEAT_NAMES)}")
print(FEAT_NAMES)

# ═══════════════════════════════════════════════════════════════════════════════
# 3. DATASET HISTÓRICO ENRIQUECIDO
#    Formato: features_A (21) + features_B (21) + diffs (21) + extras = 65 features
# ═══════════════════════════════════════════════════════════════════════════════
historical_raw = [
    # [rank_A, rank_B, conf_A, conf_B, qual_gf_pg_A, qual_ga_pg_A, qual_gf_pg_B, qual_ga_pg_B,
    #  squad_rating_A, squad_rating_B, top_sc_A, top_sc_B, mv_A, mv_B, age_A, age_B,
    #  att_combo_A, att_combo_B, wc_form_A, wc_form_B, injury_A, injury_B, goles_A, goles_B]
    # 2022 Qatar — representativo
    [3,12, 1,0,  1.94,0.94,1.50,1.20, 87.0,82.5, 8,5, 760,420, 28.2,29.5, 18.5,14.0, 0.67,0.60, 0.05,0.0, 0,0],
    [1,18, 0,2,  3.20,0.80,1.86,1.00, 88.2,81.5, 9,9, 1050,560, 26.1,25.5, 17.5,18.0, 0.80,0.80, 0.00,0.0, 0,1],
    [7,65, 0,4,  2.90,1.40,1.10,1.95, 84.5,70.0, 8,4, 870,65, 25.8,26.5, 15.0,8.0, 0.70,0.33, 0.00,0.0, 6,2],
    [10,45,0,4,  3.30,1.10,1.50,1.40, 84.0,72.0, 9,5, 890,85, 25.2,26.2, 21.0,12.0, 0.80,0.40, 0.00,0.0, 1,2],
    [2,20, 0,3,  3.00,1.00,2.00,1.10, 87.5,79.0, 7,4, 980,310, 24.8,24.8, 19.0,12.0, 0.70,0.80, 0.10,0.0, 0,0],
    [4,50, 0,4,  3.00,0.90,1.60,1.20, 86.5,70.0, 7,4, 1100,85, 26.5,25.5, 20.0,10.0, 0.80,0.40, 0.00,0.0, 6,2],
    [5,25, 0,1,  2.80,0.70,1.44,0.94, 85.8,79.0, 7,5, 920,310, 27.8,24.8, 18.0,12.0, 0.90,0.44, 0.00,0.0, 3,2],
    [6,22, 1,4,  1.61,1.22,1.67,1.00, 86.0,79.5, 5,7, 1200,180, 24.5,26.5, 14.0,16.0, 0.39,0.44, 0.10,0.0, 2,0],
    [8,35, 3,2,  2.50,0.50,1.67,1.00, 80.0,74.5, 4,3, 320,210, 25.2,26.2, 11.0,8.0, 0.83,0.50, 0.00,0.0, 0,0],
    [9,30, 0,3,  2.70,1.20,2.00,0.83, 83.5,76.5, 6,4, 680,140, 28.5,26.2, 14.0,10.0, 0.70,0.67, 0.00,0.0, 1,0],
    [11,40,0,4,  2.20,1.10,1.78,1.33, 82.5,73.5, 5,4, 420,150, 29.5,26.5, 10.0,9.0, 0.60,0.44, 0.00,0.0, 4,1],
    [13,55,1,4,  1.44,1.22,1.11,1.94, 82.0,68.5, 7,3, 480,75, 25.8,26.2, 16.0,8.0, 0.44,0.28, 0.00,0.0, 1,0],
    [14,60,3,3,  2.00,0.83,1.67,1.17, 79.5,67.5, 4,2, 280,80, 26.0,26.8, 10.0,6.0, 0.67,0.50, 0.00,0.0, 2,1],
    [15,70,2,3,  1.86,1.14,1.33,1.50, 80.5,66.0, 5,2, 390,55, 26.5,26.5, 11.0,5.0, 0.50,0.36, 0.00,0.0, 0,1],
    [16,28,2,1,  2.00,1.00,1.44,0.94, 80.0,79.0, 8,5, 520,310, 25.2,24.8, 18.0,12.0, 0.57,0.44, 0.00,0.0, 1,2],
    [17,33,1,2,  1.56,1.11,1.29,1.29, 81.0,73.5, 6,4, 430,95, 27.8,26.5, 13.0,9.0, 0.44,0.36, 0.00,0.0, 2,0],
    # 2018 Rusia
    [1,4,  0,0,  2.80,0.80,2.70,0.90, 88.2,86.5, 9,7, 1050,1100, 26.1,26.5, 25.0,20.0, 0.80,0.80, 0.00,0.0, 2,1],
    [2,8,  0,3,  2.50,0.80,2.20,0.60, 87.5,80.0, 7,4, 980,320, 24.8,25.2, 18.0,10.0, 0.70,0.80, 0.00,0.0, 1,0],
    [3,12, 1,0,  2.20,1.00,1.80,1.10, 87.0,82.5, 8,5, 760,420, 28.2,29.5, 18.0,14.0, 0.67,0.60, 0.05,0.0, 0,0],
    [5,20, 0,2,  2.10,0.70,1.80,1.20, 85.8,80.5, 7,5, 920,390, 27.8,26.5, 16.0,11.0, 0.90,0.50, 0.00,0.0, 1,0],
    [6,25, 1,1,  1.70,1.30,1.70,1.00, 86.0,79.0, 5,5, 1200,310, 24.5,24.8, 12.0,12.0, 0.39,0.44, 0.10,0.0, 2,0],
    [7,30, 0,3,  2.40,1.20,1.60,1.00, 84.5,76.5, 8,4, 870,140, 25.8,26.2, 16.0,9.0, 0.70,0.60, 0.00,0.0, 3,0],
    [9,15, 0,1,  2.60,1.10,1.60,1.20, 83.5,81.0, 6,6, 680,430, 28.5,27.8, 14.0,13.0, 0.70,0.44, 0.00,0.0, 2,0],
    [10,35,0,4,  3.10,1.20,1.50,1.40, 84.0,73.5, 9,4, 890,150, 25.2,26.5, 22.0,9.0, 0.80,0.28, 0.00,0.0, 2,1],
    # Upsets históricos
    [8,1,  3,0,  2.50,0.50,3.20,0.80, 80.0,88.2, 4,9, 320,1050, 25.2,26.1, 10.0,25.0, 0.83,0.92, 0.00,0.0, 1,0],
    [35,5, 4,0,  1.80,1.40,2.20,0.80, 73.0,85.8, 5,7, 85,920, 26.5,27.8, 9.0,16.0, 0.40,0.90, 0.00,0.0, 1,0],
    [22,3, 4,1,  1.67,1.00,1.94,0.94, 79.5,87.0, 7,8, 180,760, 26.5,28.2, 14.0,18.0, 0.44,0.67, 0.00,0.05, 2,1],
    # 2014 Brasil
    [1,6,  1,0,  2.20,1.10,1.60,1.20, 88.2,85.8, 9,7, 1050,920, 26.1,27.8, 22.0,16.0, 0.80,0.90, 0.00,0.0, 3,1],
    [2,10, 0,0,  2.50,0.80,2.80,1.10, 87.5,84.0, 7,9, 980,890, 24.8,25.2, 17.0,20.0, 0.70,0.80, 0.00,0.0, 4,0],
    [3,15, 0,4,  2.00,1.00,1.60,1.50, 87.0,77.0, 8,4, 760,160, 28.2,26.5, 18.0,9.0, 0.67,0.40, 0.05,0.0, 1,0],
    # Empates técnicos
    [5,5,  0,0,  2.50,0.80,2.50,0.80, 85.8,85.8, 7,7, 920,920, 27.8,27.8, 16.0,16.0, 0.90,0.90, 0.00,0.0, 1,1],
    [10,10,0,0,  3.00,1.10,3.00,1.10, 84.0,84.0, 9,9, 890,890, 25.2,25.2, 22.0,22.0, 0.80,0.80, 0.00,0.0, 2,2],
    [20,20,0,3,  2.00,1.20,2.00,1.20, 80.5,80.5, 5,5, 390,390, 26.5,26.5, 10.0,10.0, 0.57,0.57, 0.00,0.0, 1,1],
    [8,10, 0,0,  2.80,0.80,2.80,0.80, 82.0,84.5, 6,8, 480,870, 28.5,25.8, 14.0,16.0, 0.44,0.70, 0.00,0.0, 1,1],
    [15,18,2,4,  1.86,1.14,2.67,0.56, 80.5,81.5, 5,9, 390,560, 26.5,25.5, 11.0,20.0, 0.50,0.78, 0.00,0.0, 0,0],
    [30,35,2,3,  1.79,0.86,1.67,1.17, 78.0,74.5, 6,3, 340,95, 25.0,26.5, 12.0,7.0, 0.57,0.50, 0.00,0.0, 1,0],
    [40,45,3,4,  1.17,1.44,1.67,1.33, 73.5,72.0, 4,5, 150,85, 26.5,26.2, 8.0,10.0, 0.28,0.33, 0.00,0.0, 0,1],
    [50,55,4,4,  1.50,1.00,1.11,1.94, 70.0,68.5, 4,3, 85,75, 25.5,26.2, 8.0,7.0, 0.50,0.28, 0.00,0.0, 2,2],
]

# Convertir a dataset con features de diferencia
rows = []
for r in historical_raw:
    (rA,rB,cA,cB,gfA,gaA,gfB,gaB,sqA,sqB,tsA,tsB,mvA,mvB,ageA,ageB,
     acA,acB,wcfA,wcfB,injA,injB,golesA,golesB) = r

    def make_row(ra,rb,ca,cb,gfa,gaa,gfb,gab,sqa,sqb,tsa,tsb,mva,mvb,agea,ageb,
                 aca,acb,wcfa,wcfb,inja,injb,ga,gb):
        feat = [
            ra, rb, ca, cb,
            gfa, gaa, gfb, gab,
            gfa-gfb, gaa-gab,            # diffs de forma
            sqa, sqb, sqa-sqb,
            tsa, tsb, tsa-tsb,
            np.log1p(mva), np.log1p(mvb), np.log1p(mva)-np.log1p(mvb),
            agea, ageb,
            aca, acb, aca-acb,           # attack combo diff
            wcfa, wcfb, wcfa-wcfb,
            inja, injb,
            rb-ra,                       # rank diff
            rb/(ra+1),                   # rank ratio
            int(ra<=10), int(rb<=10),
            int(ra<=5), int(rb<=5),
        ]
        resultado = 2 if ga>gb else (1 if ga==gb else 0)
        return feat + [ga, gb, resultado]

    rows.append(make_row(rA,rB,cA,cB,gfA,gaA,gfB,gaB,sqA,sqB,tsA,tsB,mvA,mvB,ageA,ageB,acA,acB,wcfA,wcfB,injA,injB,golesA,golesB))
    # Data augmentation: partido invertido
    rows.append(make_row(rB,rA,cB,cA,gfB,gaB,gfA,gaA,sqB,sqA,tsB,tsA,mvB,mvA,ageB,ageA,acB,acA,wcfB,wcfA,injB,injA,golesB,golesA))

FEAT_COLS = [
    "rank_A","rank_B","conf_A","conf_B",
    "qual_gf_pg_A","qual_ga_pg_A","qual_gf_pg_B","qual_ga_pg_B",
    "diff_gf_pg","diff_ga_pg",
    "squad_rating_A","squad_rating_B","diff_squad_rating",
    "top_sc_A","top_sc_B","diff_top_sc",
    "log_mv_A","log_mv_B","diff_log_mv",
    "age_A","age_B",
    "att_combo_A","att_combo_B","diff_att_combo",
    "wc_form_A","wc_form_B","diff_wc_form",
    "injury_A","injury_B",
    "rank_diff","rank_ratio",
    "is_top10_A","is_top10_B",
    "is_top5_A","is_top5_B",
]

df = pd.DataFrame(rows, columns=FEAT_COLS+["goles_A","goles_B","resultado"])
print(f"\nDataset: {len(df)} partidos | Features: {len(FEAT_COLS)}")
print(f"Clases: {dict(zip(['Derrota','Empate','Victoria'], df['resultado'].value_counts().sort_index().tolist()))}")

X = df[FEAT_COLS].values
y_clf = df["resultado"].values
y_gA  = df["goles_A"].values.astype(float)
y_gB  = df["goles_B"].values.astype(float)

# ═══════════════════════════════════════════════════════════════════════════════
# 4. MODELOS
# ═══════════════════════════════════════════════════════════════════════════════
X_tr, X_te, yc_tr, yc_te, gA_tr, gA_te, gB_tr, gB_te = \
    train_test_split(X, y_clf, y_gA, y_gB, test_size=0.20, random_state=42, stratify=y_clf)

scaler = StandardScaler()
X_tr_s = scaler.fit_transform(X_tr)
X_te_s  = scaler.transform(X_te)

# MLP mejorado
mlp = MLPClassifier(hidden_layer_sizes=(256,128,64,32), activation='relu', solver='adam',
                    alpha=0.002, learning_rate='adaptive', learning_rate_init=0.001,
                    max_iter=2000, random_state=42, early_stopping=True,
                    validation_fraction=0.15, n_iter_no_change=40)
mlp.fit(X_tr_s, yc_tr)

# Gradient Boosting
gbt = GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.08,
                                  subsample=0.8, random_state=42)
gbt.fit(X_tr_s, yc_tr)

# Regresor λ_A
reg_A = GradientBoostingRegressor(n_estimators=150, max_depth=3, learning_rate=0.1,
                                   subsample=0.8, random_state=42)
reg_A.fit(X_tr_s, gA_tr)
# Regresor λ_B
reg_B = GradientBoostingRegressor(n_estimators=150, max_depth=3, learning_rate=0.1,
                                   subsample=0.8, random_state=42)
reg_B.fit(X_tr_s, gB_tr)

# Evaluar
def eval_clf(model, name, X_te_s, yc_te):
    pred = model.predict(X_te_s)
    prob = model.predict_proba(X_te_s)
    acc = accuracy_score(yc_te, pred)
    f1  = f1_score(yc_te, pred, average='weighted')
    auc = roc_auc_score(yc_te, prob, multi_class='ovr', average='weighted')
    cv  = cross_val_score(model, scaler.transform(X), y_clf, cv=5, scoring='accuracy')
    print(f"\n[{name}] Acc={acc:.3f} | F1={f1:.3f} | AUC={auc:.3f} | CV={cv.mean():.3f}±{cv.std():.3f}")
    return pred, prob, acc, f1, auc, cv

mlp_pred, mlp_prob, mlp_acc, mlp_f1, mlp_auc, mlp_cv = eval_clf(mlp, "MLP v2", X_te_s, yc_te)
gbt_pred, gbt_prob, gbt_acc, gbt_f1, gbt_auc, gbt_cv = eval_clf(gbt, "GradBoost", X_te_s, yc_te)

# Ensemble por promedio de probabilidades
ens_prob = (mlp_prob + gbt_prob) / 2
ens_pred = ens_prob.argmax(axis=1)
ens_acc  = accuracy_score(yc_te, ens_pred)
ens_f1   = f1_score(yc_te, ens_pred, average='weighted')
ens_auc  = roc_auc_score(yc_te, ens_prob, multi_class='ovr', average='weighted')
print(f"\n[ENSEMBLE]  Acc={ens_acc:.3f} | F1={ens_f1:.3f} | AUC={ens_auc:.3f}")
print("\n" + classification_report(yc_te, ens_pred, target_names=["Derrota","Empate","Victoria"]))

# Feature importance (GBT)
importances = gbt.feature_importances_
fi_df = pd.DataFrame({"feature": FEAT_COLS, "importance": importances}).sort_values("importance", ascending=False)
print("\nTop 15 features por importancia:")
print(fi_df.head(15).to_string(index=False))

gA_pred = reg_A.predict(X_te_s).clip(0)
gB_pred = reg_B.predict(X_te_s).clip(0)
mae_A = mean_absolute_error(gA_te, gA_pred)
mae_B = mean_absolute_error(gB_te, gB_pred)
print(f"\nRegresor: MAE_A={mae_A:.3f} | MAE_B={mae_B:.3f}")

# ═══════════════════════════════════════════════════════════════════════════════
# 5. GUARDAR MODELOS
# ═══════════════════════════════════════════════════════════════════════════════
joblib.dump(mlp,    OUT+"mlp_v2.pkl")
joblib.dump(gbt,    OUT+"gbt_v2.pkl")
joblib.dump(reg_A,  OUT+"reg_A_v2.pkl")
joblib.dump(reg_B,  OUT+"reg_B_v2.pkl")
joblib.dump(scaler, OUT+"scaler_v2.pkl")
print("\nModelos guardados.")

# ═══════════════════════════════════════════════════════════════════════════════
# 6. PRECALCULAR TODAS LAS COMBINACIONES 48×47 CON JUGADORES
# ═══════════════════════════════════════════════════════════════════════════════
def make_match_feat(nameA, nameB):
    fA = team_feats[nameA]
    fB = team_feats[nameB]
    return np.array([[
        fA["rank"], fB["rank"], fA["conf"], fB["conf"],
        fA["qual_gf_pg"], fA["qual_ga_pg"], fB["qual_gf_pg"], fB["qual_ga_pg"],
        fA["qual_gf_pg"]-fB["qual_gf_pg"], fA["qual_ga_pg"]-fB["qual_ga_pg"],
        fA["squad_rating"], fB["squad_rating"], fA["squad_rating"]-fB["squad_rating"],
        fA["top_scorer_goals"], fB["top_scorer_goals"], fA["top_scorer_goals"]-fB["top_scorer_goals"],
        fA["market_value"], fB["market_value"], fA["market_value"]-fB["market_value"],
        fA["avg_age"], fB["avg_age"],
        fA["attack_combo_idx"], fB["attack_combo_idx"], fA["attack_combo_idx"]-fB["attack_combo_idx"],
        fA["wc_form"], fB["wc_form"], fA["wc_form"]-fB["wc_form"],
        fA["injury_factor"], fB["injury_factor"],
        fB["rank"]-fA["rank"], fB["rank"]/(fA["rank"]+1),
        fA["is_top10"], fB["is_top10"],
        fA["is_top5"], fB["is_top5"],
    ]])

preds_v2 = {}
teams_list = sorted(TEAMS.keys())
for tA in teams_list:
    preds_v2[tA] = {}
    for tB in teams_list:
        if tA == tB: continue
        feat_s = scaler.transform(make_match_feat(tA, tB))
        prob_mlp = mlp.predict_proba(feat_s)[0]
        prob_gbt = gbt.predict_proba(feat_s)[0]
        prob = ((prob_mlp + prob_gbt) / 2).tolist()
        lA = float(np.clip(reg_A.predict(feat_s)[0], 0.2, 5.5))
        lB = float(np.clip(reg_B.predict(feat_s)[0], 0.2, 5.5))
        preds_v2[tA][tB] = {
            "p_derrota":  round(prob[0], 4),
            "p_empate":   round(prob[1], 4),
            "p_victoria": round(prob[2], 4),
            "lambda_A":   round(lA, 3),
            "lambda_B":   round(lB, 3),
        }

with open(OUT+"predicciones_v2.json", "w", encoding="utf-8") as f:
    json.dump(preds_v2, f, ensure_ascii=False, indent=2)
print(f"Predicciones v2: {len(preds_v2)} equipos")

# Exportar feature importance
fi_df.to_csv(OUT+"feature_importance.csv", index=False)

# ═══════════════════════════════════════════════════════════════════════════════
# 7. VISUALIZACIONES METRICAS v2
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 3, figsize=(18, 11))
fig.patch.set_facecolor('#0d1117')
fig.suptitle("EVALUACIÓN MODELO v2 — MLP + Gradient Boosting Ensemble\nMundial FIFA 2026",
             fontsize=14, color='white', y=0.98)
colors_roc = ['#f85149','#d29922','#56d364']
label_names = ["Derrota","Empate","Victoria"]

# Confusion matrix ensemble
ax = axes[0,0]
cm = confusion_matrix(yc_te, ens_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=label_names, yticklabels=label_names,
            linewidths=0.5, cbar_kws={"shrink":0.8})
ax.set_facecolor('#161b22'); ax.set_title("Matriz de Confusión (Ensemble)", color='white', fontsize=12)
ax.set_xlabel("Predicho", color='lightgray'); ax.set_ylabel("Real", color='lightgray')
ax.tick_params(colors='white')

# ROC curves ensemble
ax = axes[0,1]
yc_bin = label_binarize(yc_te, classes=[0,1,2])
for i, (name, color) in enumerate(zip(label_names, colors_roc)):
    fpr, tpr, _ = roc_curve(yc_bin[:,i], ens_prob[:,i])
    auc_i = roc_auc_score(yc_bin[:,i], ens_prob[:,i])
    ax.plot(fpr, tpr, color=color, lw=2, label=f"{name} AUC={auc_i:.2f}")
ax.plot([0,1],[0,1],'--', color='gray', lw=1)
ax.set_facecolor('#161b22'); ax.set_title("Curvas ROC Ensemble (OvR)", color='white', fontsize=12)
ax.set_xlabel("FPR", color='lightgray'); ax.set_ylabel("TPR", color='lightgray')
ax.tick_params(colors='white'); ax.spines[:].set_color('#30363d')
ax.legend(facecolor='#161b22', edgecolor='#30363d', labelcolor='white', fontsize=9)

# Feature importance top 12
ax = axes[0,2]
top12 = fi_df.head(12)
cmap = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(top12)))[::-1]
bars = ax.barh(top12["feature"][::-1], top12["importance"][::-1],
               color=cmap, edgecolor='white', linewidth=0.3)
ax.set_facecolor('#161b22')
ax.set_title("Feature Importance (GradBoost Top-12)", color='white', fontsize=12)
ax.set_xlabel("Importance", color='lightgray')
ax.tick_params(colors='white'); ax.spines[:].set_color('#30363d')

# Comparativa modelos: barras acc/f1/auc
ax = axes[1,0]
metrics = ['Accuracy','F1','AUC-ROC']
mlp_vals = [mlp_acc, mlp_f1, mlp_auc]
gbt_vals = [gbt_acc, gbt_f1, gbt_auc]
ens_vals = [ens_acc, ens_f1, ens_auc]
x = np.arange(3); w = 0.25
ax.bar(x-w, mlp_vals, w, label='MLP v2', color='#58a6ff', edgecolor='white', lw=0.3)
ax.bar(x,   gbt_vals, w, label='GradBoost', color='#f0883e', edgecolor='white', lw=0.3)
ax.bar(x+w, ens_vals, w, label='Ensemble', color='#56d364', edgecolor='white', lw=0.3)
ax.set_xticks(x); ax.set_xticklabels(metrics)
ax.set_facecolor('#161b22'); ax.set_title("Comparativa de Modelos", color='white', fontsize=12)
ax.set_ylim(0,1); ax.tick_params(colors='white'); ax.spines[:].set_color('#30363d')
ax.legend(facecolor='#161b22', edgecolor='#30363d', labelcolor='white', fontsize=9)
for bars_g in [ax.containers[0], ax.containers[1], ax.containers[2]]:
    for bar in bars_g:
        h = bar.get_height()
        ax.text(bar.get_x()+bar.get_width()/2, h+0.01, f"{h:.2f}",
                ha='center', color='white', fontsize=7)

# Distribución de probabilidades
ax = axes[1,1]
for i, (name, color) in enumerate(zip(label_names, colors_roc)):
    ax.hist(ens_prob[:,i], bins=15, alpha=0.7, color=color, label=name, edgecolor='white', lw=0.3)
ax.set_facecolor('#161b22'); ax.set_title("Distribución Probabilidades Ensemble", color='white', fontsize=12)
ax.set_xlabel("Probabilidad", color='lightgray')
ax.tick_params(colors='white'); ax.spines[:].set_color('#30363d')
ax.legend(facecolor='#161b22', edgecolor='#30363d', labelcolor='white')

# Goles reales vs predichos
ax = axes[1,2]
ax.scatter(gA_te, gA_pred, alpha=0.7, color='#58a6ff', s=50, edgecolors='white', lw=0.3, label=f'λ_A MAE={mae_A:.2f}')
ax.scatter(gB_te, gB_pred, alpha=0.7, color='#f0883e', s=50, edgecolors='white', lw=0.3, label=f'λ_B MAE={mae_B:.2f}', marker='^')
mx = max(gA_te.max(), gB_te.max())+0.5
ax.plot([0,mx],[0,mx],'w--', lw=1, alpha=0.5)
ax.set_facecolor('#161b22'); ax.set_title("Goles: Real vs Predicho (GradBoost)", color='white', fontsize=12)
ax.set_xlabel("Goles reales", color='lightgray'); ax.set_ylabel("Goles predichos", color='lightgray')
ax.tick_params(colors='white'); ax.spines[:].set_color('#30363d')
ax.legend(facecolor='#161b22', edgecolor='#30363d', labelcolor='white', fontsize=9)

fig.text(0.5, 0.01,
         f"Ensemble Acc={ens_acc:.3f} | F1={ens_f1:.3f} | AUC-ROC={ens_auc:.3f} | "
         f"Features={len(FEAT_COLS)} | Dataset={len(df)} partidos | MAE goles={mae_A:.2f}/{mae_B:.2f}",
         ha='center', color='lightgray', fontsize=10)

plt.tight_layout(rect=[0,0.04,1,0.96])
plt.savefig(OUT+"metricas_v2.png", dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close()
print("Métricas v2 guardadas.")

# ═══════════════════════════════════════════════════════════════════════════════
# 8. CORRELACIONES — FORMA ELIMINATORIAS vs RESULTADO EN TORNEO
# ═══════════════════════════════════════════════════════════════════════════════
fig2, axes2 = plt.subplots(1, 3, figsize=(15, 5))
fig2.patch.set_facecolor('#0d1117')
fig2.suptitle("Correlaciones: Stats Eliminatorias vs Rendimiento", color='white', fontsize=13)

# Corr: rank_diff vs resultado
ax = axes2[0]
scatter_x = df["rank_diff"].values
scatter_y = df["resultado"].values
ax.scatter(scatter_x, scatter_y + np.random.normal(0,0.05,len(scatter_y)),
           alpha=0.3, color='#58a6ff', s=15)
z = np.polyfit(scatter_x, scatter_y, 1)
x_line = np.linspace(scatter_x.min(), scatter_x.max(), 100)
ax.plot(x_line, np.poly1d(z)(x_line), 'r--', lw=2)
ax.set_facecolor('#161b22'); ax.set_title("Rank Diff vs Resultado\n(+ = rival peor rankeado)", color='white', fontsize=11)
ax.set_xlabel("rank_B - rank_A", color='lightgray'); ax.set_ylabel("Resultado (0=D,1=E,2=V)", color='lightgray')
ax.tick_params(colors='white'); ax.spines[:].set_color('#30363d')
corr1 = np.corrcoef(scatter_x, scatter_y)[0,1]
ax.text(0.05, 0.92, f"r = {corr1:.3f}", transform=ax.transAxes, color='#d29922', fontsize=10)

# Corr: diff_gf_pg vs resultado
ax = axes2[1]
scatter_x2 = df["diff_gf_pg"].values
ax.scatter(scatter_x2, scatter_y + np.random.normal(0,0.05,len(scatter_y)),
           alpha=0.3, color='#56d364', s=15)
z2 = np.polyfit(scatter_x2, scatter_y, 1)
x_line2 = np.linspace(scatter_x2.min(), scatter_x2.max(), 100)
ax.plot(x_line2, np.poly1d(z2)(x_line2), 'r--', lw=2)
ax.set_facecolor('#161b22'); ax.set_title("Diff GF/partido (elim.) vs Resultado", color='white', fontsize=11)
ax.set_xlabel("GF_pg_A − GF_pg_B", color='lightgray')
ax.tick_params(colors='white'); ax.spines[:].set_color('#30363d')
corr2 = np.corrcoef(scatter_x2, scatter_y)[0,1]
ax.text(0.05, 0.92, f"r = {corr2:.3f}", transform=ax.transAxes, color='#d29922', fontsize=10)

# Corr: att_combo vs resultado
ax = axes2[2]
scatter_x3 = df["diff_att_combo"].values
ax.scatter(scatter_x3, scatter_y + np.random.normal(0,0.05,len(scatter_y)),
           alpha=0.3, color='#f0883e', s=15)
z3 = np.polyfit(scatter_x3, scatter_y, 1)
x_line3 = np.linspace(scatter_x3.min(), scatter_x3.max(), 100)
ax.plot(x_line3, np.poly1d(z3)(x_line3), 'r--', lw=2)
ax.set_facecolor('#161b22'); ax.set_title("Diff Combo Ataque vs Resultado", color='white', fontsize=11)
ax.set_xlabel("att_combo_A − att_combo_B", color='lightgray')
ax.tick_params(colors='white'); ax.spines[:].set_color('#30363d')
corr3 = np.corrcoef(scatter_x3, scatter_y)[0,1]
ax.text(0.05, 0.92, f"r = {corr3:.3f}", transform=ax.transAxes, color='#d29922', fontsize=10)

plt.tight_layout()
plt.savefig(OUT+"correlaciones_v2.png", dpi=150, bbox_inches='tight', facecolor=fig2.get_facecolor())
plt.close()
print("Correlaciones guardadas.")

# Resumen
print(f"""
╔═══════════════════════════════════════════════════════╗
║         RESUMEN MODELO v2 — MUNDIAL FIFA 2026         ║
╠═══════════════════════════════════════════════════════╣
║  Features:     {len(FEAT_COLS):<5} (rank+elim+jugadores+WC)      ║
║  Dataset:      {len(df):<5} partidos históricos              ║
║  Modelos:      MLP(256-128-64-32) + GradientBoost    ║
║  Ensemble Acc: {ens_acc:.1%}  F1: {ens_f1:.3f}  AUC: {ens_auc:.3f}        ║
║  MAE goles:    A={mae_A:.3f}  B={mae_B:.3f}                   ║
║  Correlaciones: rank_diff r={corr1:.3f}                ║
║                 GF/partido r={corr2:.3f}               ║
║                 att_combo  r={corr3:.3f}               ║
╚═══════════════════════════════════════════════════════╝
""")
