# 🏆 Mundial FIFA 2026 — Dual Engine AI Predictor

Sistema de predicción de partidos del Mundial FIFA 2026 basado en dos modelos de machine learning independientes que generan probabilidades de victoria, empate y derrota, junto con estimación de goles por equipo.

**Demo en vivo →** [Vercel](https://mundial-fifa-2026.vercel.app) · Actualización automática diaria vía GitHub Actions.

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                  DUAL ENGINE AI v3                      │
│                                                         │
│  ┌──────────────────────┐  ┌──────────────────────┐    │
│  │     ENGINE A         │  │     ENGINE B          │    │
│  │  Deep MLP + Atención │  │  XGBoost Agresivo     │    │
│  │  512→256→128→64→32   │  │  depth=6 · 500 est.   │    │
│  │  T=0.55 (sharpening) │  │  T=0.55 (sharpening)  │    │
│  └──────────────────────┘  └──────────────────────┘    │
│                ↓                        ↓               │
│         P(victoria) · P(empate) · P(derrota)            │
│         λ_A goles esperados  ·  λ_B goles esperados     │
└─────────────────────────────────────────────────────────┘
```

### Engine A — Deep MLP + Self-Attention
| Parámetro | Valor |
|-----------|-------|
| Arquitectura | 512 → 256 → 128 → 64 → 32 |
| Activación | ReLU |
| Optimizador | Adam (lr adaptativa, init=0.001) |
| Regularización | L2 α=0.0005 |
| Early stopping | val=12%, patience=60 iter |
| Self-Attention | 4 cabezas, implementado en NumPy puro |
| Calibración T | 0.55 (agudiza predicciones) |

### Engine B — XGBoost Agresivo
| Parámetro | Valor |
|-----------|-------|
| n_estimators | 500 |
| max_depth | 6 |
| learning_rate | 0.04 |
| subsample | 0.80 |
| colsample_bytree | 0.80 |
| min_child_weight | 3 |
| gamma | 0.10 |
| reg_alpha / reg_lambda | 0.50 / 2.5 |
| Objetivo | multi:softprob (3 clases) |
| Calibración T | 0.55 |

---

## Features — 91 Variables de Entrada

### Ranking y Confederación (9 features)
| Feature | Descripción |
|---------|-------------|
| `rank_A`, `rank_B` | Ranking FIFA actual |
| `rank_diff`, `rank_ratio` | Diferencia y razón de rankings |
| `conf_A`, `conf_B` | Confederación codificada (0-5) |
| `cwe_A`, `cwe_B`, `diff_cwe` | Experiencia acumulada en mundiales |

### Rendimiento Histórico (16 features)
| Feature | Descripción |
|---------|-------------|
| `gf_pg_A/B` | Goles a favor por partido |
| `ga_pg_A/B` | Goles en contra por partido |
| `wr_A/B` | Win rate en fase eliminatoria |
| `gd_A/B` | Diferencia de goles acumulada |
| `diff_gf_pg`, `diff_ga_pg`, `diff_wr`, `diff_gd` | Diferencias entre equipos |

### Calidad de Plantilla (14 features)
| Feature | Descripción |
|---------|-------------|
| `sq_rat_A/B` | Rating promedio de jugadores (SofaScore/FM) |
| `log_mv_A/B` | Log del valor de mercado (M€) |
| `age_A/B` | Edad promedio del equipo |
| `top_sc_A/B` | Rating del máximo goleador |
| `att_A/B` | Rating del mejor mediocampista creativo |
| `star_rat_A/B` | Rating de la estrella del equipo |
| `log_sv_A/B` | Log del salario anual del portero |

### Experiencia en Mundiales (8 features)
| Feature | Descripción |
|---------|-------------|
| `wc_form_A/B` | Rendimiento en WC anteriores (0-1) |
| `wc_gf_A/B` | Goles a favor en WC (histórico) |
| `wc_ga_A/B` | Goles en contra en WC (histórico) |
| `top5_A/B`, `top10_A/B` | ¿Equipo históricamente top 5/10? |

### Tácticas por Formación (17 features)
| Feature | Descripción |
|---------|-------------|
| `fatk_A/B` | Potencia de ataque de la formación |
| `fdef_A/B` | Solidez defensiva de la formación |
| `width_A/B` | Amplitud de juego |
| `press_A/B` | Intensidad de presión |
| `sp_A/B` | Amenaza de pelota parada |
| `style_A/B` | Style score (attacking=1.18, defensive=0.82) |
| `tact_adv` | Ventaja táctica neta |
| `cross_ta`, `cross_tb` | Ataque A × Defensa B, B × A |
| `off_pow_A/B`, `net_off_pow` | Poder ofensivo efectivo |
| `diff_fatk`, `diff_fdef`, `diff_press`, `diff_style` | Diferencias tácticas |

### Factores Ambientales / Sede (8 features)
| Feature | Descripción |
|---------|-------------|
| `env_alt` | Altitud del estadio (metros) |
| `env_temp` | Temperatura estimada (°C) |
| `env_wind` | Velocidad del viento (km/h) |
| `env_hydration` | Factor de humedad/hidratación |
| `alt_pen_A/B` | Penalización de altitud por equipo |
| `heat_hydra_pen_A/B` | Penalización por calor/hidratación |

### Cuotas de Casa de Apuestas (3 features)
| Feature | Descripción |
|---------|-------------|
| `bk_win_A` | Probabilidad implícita victoria A (1/cuota) |
| `bk_draw` | Probabilidad implícita de empate |
| `bk_win_B` | Probabilidad implícita victoria B |

### Draw-Context Features (10 features)
| Feature | Descripción |
|---------|-------------|
| `draw_tendency` | Tendencia histórica a empatar |
| `rank_parity` | Paridad de ranking (equipos similares) |
| `sq_parity` | Paridad de calidad de plantillas |
| `conf_same` | ¿Misma confederación? (1/0) |
| `atk_vs_def_A/B` | Ratio ataque/defensa cruzado |
| `def_balance` | Equilibrio defensivo promedio |
| `cwe_parity` | Paridad experiencia WC |
| `mv_ratio` | Razón valores de mercado |
| `bk_draw_signal` | Señal de empate según cuotas (bk_draw - 0.25) |

---

## Importancia de Features (Top 20 — Engine B XGBoost)

| # | Feature | Importancia | Categoría |
|---|---------|-------------|-----------|
| 1 | `mv_ratio` | 4.43% | Calidad plantilla |
| 2 | `diff_style` | 4.30% | Táctica |
| 3 | `net_off_pow` | 3.64% | Táctica |
| 4 | `sp_A` | 3.51% | Táctica (set piece) |
| 5 | `fdef_A` | 2.83% | Táctica defensiva |
| 6 | `bk_win_A` | 2.79% | Cuotas |
| 7 | `wc_form_B` | 2.60% | Experiencia WC |
| 8 | `diff_fdef` | 2.41% | Táctica diferencial |
| 9 | `fatk_A` | 2.33% | Táctica ofensiva |
| 10 | `diff_gd` | 2.26% | Rendimiento histórico |
| 11 | `cwe_B` | 2.03% | Experiencia WC |
| 12 | `press_B` | 1.89% | Táctica |
| 13 | `gf_pg_A` | 1.79% | Rendimiento |
| 14 | `sq_parity` | 1.76% | Draw-context |
| 15 | `rank_ratio` | 1.75% | Ranking |
| 16 | `wc_gf_B` | 1.74% | Experiencia WC |
| 17 | `env_wind` | 1.73% | Ambiental |
| 18 | `cross_ta` | 1.62% | Táctica interacción |
| 19 | `bk_win_B` | 1.62% | Cuotas |
| 20 | `diff_log_mv` | 1.51% | Calidad plantilla |

> Las features tácticas (`diff_style`, `net_off_pow`, `sp_A`, `fdef_A`, `fatk_A`) suman >12% de importancia total, confirmando que la configuración de alineación es el factor diferenciador más relevante del modelo v3 vs v2.

---

## Dataset de Entrenamiento

| Componente | Partidos | Fuente |
|-----------|----------|--------|
| WC 2022 Qatar | 63 | Resultados históricos |
| WC 2018 Rusia (selección) | 18 | Resultados históricos |
| WC 2014 Brasil (selección) | 12 | Resultados históricos |
| Partidos adicionales balanceo | 90 | Datos sintéticos calibrados |
| WC 2026 (jornada 1, live) | 50+ | Actualización automática diaria |
| **Total (con mirror A↔B)** | **~430 filas** | — |

El dataset se espeja (equipo A ↔ equipo B) para garantizar que el modelo aprenda predicciones simétricas.

**Distribución de clases en entrenamiento:**
```
Victoria local (A): ~42%
Empate:             ~26%
Victoria visitante: ~32%
```

---

## Métricas de Entrenamiento y Validación

### Test Set (20% hold-out)
| Métrica | Engine A (MLP) | Engine B (XGBoost) |
|---------|---------------|-------------------|
| Accuracy | 0.591 | 0.545 |
| F1-weighted | 0.525 | 0.535 |
| AUC-OVR (weighted) | 0.642 | 0.711 |

### Validación Cruzada — Engine B (CV-5 StratifiedKFold)
```
F1-weighted: 0.622 ± 0.048  |  Min fold: 0.561
```

### Matriz de Confusión — Engine B (test set calibrado T=0.55)
```
                 Pred: Victoria  Pred: Empate  Pred: Derrota
Real: Victoria       24              0              3
Real: Empate          8              0              5
Real: Derrota         2              0             10
```
> La clase Empate es la más difícil de predecir. Los mundiales tienen ~26% de empates históricos; el modelo los detecta mediante el conjunto de draw-context features pero tiende a subestimar su frecuencia cuando los favoritos son claros.

---

## Resultados en Vivo — WC 2026 (actualizado 2026-06-20)

### Precisión acumulada sobre partidos jugados

| Engine | Correctos | Total | Precisión |
|--------|-----------|-------|-----------|
| Engine A — MLP | 28 | 50 | **56%** |
| Engine B — XGBoost | 26 | 50 | **52%** |

### Precisión por tipo de resultado

| Resultado | Engine A | Engine B | Partidos |
|-----------|---------|---------|---------|
| Victoria del favorito | 26/30 | 24/30 | 30 |
| Empate | 0/16 | 0/16 | 16 |
| Sorpresa (victoria del menos favorito) | 2/4 | 2/4 | 4 |

### Ejemplos de predicciones correctas ✓
| Partido | Real | Engine A | Engine B |
|---------|------|---------|---------|
| Alemania 7-1 Curazao | Alemania | Alemania (99.9%) | Alemania (97.2%) |
| Francia 3-1 Senegal | Francia | Francia (99%) | Francia (99%) |
| Argentina 3-0 Argelia | Argentina | Argentina (99.8%) | Argentina (99.7%) |
| Inglaterra 4-2 Croacia | Inglaterra | Inglaterra (87%) | Inglaterra (82%) |
| Canadá 6-0 Qatar | Canadá | Canadá (88%) | Canadá (79%) |

### Principales sorpresas no predichas ✗
| Partido | Real | Predicción (A/B) |
|---------|------|-----------------|
| España 0-0 Cabo Verde | Empate | España (99.9%) |
| Brasil 1-1 Marruecos | Empate | Brasil (99.8% / 99.9%) |
| Australia 2-0 Turquía | Australia | Turquía (91.5% / 99.4%) |
| Países Bajos 2-2 Japón | Empate | Países Bajos (93%+) |
| Bélgica 1-1 Egipto | Empate | Bélgica (96.7% / 99.9%) |

> Las sorpresas corresponden principalmente a empates de equipos que el modelo considera favoritos claros. Es el patrón más difícil para cualquier modelo basado en features pre-partido, ya que los empates entre equipos muy desiguales tienen baja frecuencia histórica.

---

## Pipeline Diario Automático

```
02:00 UTC ──► update_daily.py        → obtiene nuevos resultados (football-data.org API)
              ↓
         update_historial.py         → compara predicciones vs resultados reales
              ↓
         train_model_v3.py           → reentrenamiento completo con datos actualizados
              ↓
         build_index.py              → regenera el SPA con nuevas predicciones
              ↓
         git commit & push           → Vercel auto-deploys
```

### Archivos principales
| Archivo | Descripción |
|---------|-------------|
| `train_model_v3.py` | Entrenamiento completo de ambos engines |
| `build_index.py` | Generador del sitio estático (SPA) |
| `update_daily.py` | Fetcher de resultados (API + fallback manual) |
| `update_historial.py` | Comparador predicciones vs resultados reales |
| `fixtures.json` | Calendario Jornadas 1-3 (72 partidos, Grupos A-L) |
| `wc2026_updates.json` | Resultados reales WC 2026 (actualizado diariamente) |
| `predicciones_historial.json` | Historial de aciertos/errores por engine |
| `predicciones_v3_compact.json` | Predicciones pre-calculadas para todos los cruces |
| `lineup_config.json` | Formaciones y estilos por equipo |

---

## Instalación y Uso Local

```bash
# Clonar repositorio
git clone https://github.com/EdwinPuertas/mundial-fifa-2026.git
cd mundial-fifa-2026

# Instalar dependencias
pip install -r requirements.txt

# Entrenar modelo
python train_model_v3.py

# Reconstruir sitio
python build_index.py

# Actualizar historial (requiere wc2026_updates.json con resultados)
python update_historial.py

# Abrir el sitio
open index.html
```

### Variables de entorno (opcional)
```bash
export FOOTBALL_DATA_API_KEY=<tu_api_key>   # para fetch automático de resultados
```

---

## Formaciones y Estilos Soportados

### Formaciones (9)
`4-3-3` · `4-4-2` · `4-2-3-1` · `3-4-3` · `3-5-2` · `5-3-2` · `4-5-1` · `5-4-1` · `4-1-4-1`

### Estilos de Juego (4)
| Estilo | Mod. Ataque | Mod. Presión | Descripción |
|--------|------------|-------------|-------------|
| `attacking` | ×1.18 | ×1.12 | Presión alta, línea adelantada |
| `balanced` | ×1.00 | ×1.00 | Transiciones equilibradas |
| `defensive` | ×0.82 | ×0.82 | Bloque bajo, contraataque |
| `counterattack` | ×0.90 | ×0.78 | Rápida transición |

---

## Grupos — Mundial FIFA 2026

| Grupo | Equipos |
|-------|---------|
| A | México · Corea del Sur · Sudáfrica · República Checa |
| B | Canadá · Bosnia y Herz. · Qatar · Suiza |
| C | Brasil · Marruecos · Haití · Escocia |
| D | Estados Unidos · Australia · Paraguay · Turquía |
| E | Alemania · Ecuador · Costa de Marfil · Curazao |
| F | Países Bajos · Japón · Túnez · Suecia |
| G | Bélgica · Irán · Egipto · Nueva Zelanda |
| H | España · Uruguay · Arabia Saudita · Cabo Verde |
| I | Francia · Senegal · Noruega · Irak |
| J | Argentina · Austria · Argelia · Jordania |
| K | Portugal · Colombia · Uzbekistán · RD Congo |
| L | Inglaterra · Croacia · Panamá · Ghana |

---

## Stack Tecnológico

| Componente | Tecnología |
|-----------|-----------|
| Modelos ML | scikit-learn · XGBoost · NumPy |
| Self-Attention | Implementación propia en NumPy (sin TF/PyTorch) |
| Frontend | HTML/CSS/JS vanilla — SPA single-file |
| Build | Python script (`build_index.py`) |
| Deploy | Vercel (auto desde GitHub) |
| CI/CD | GitHub Actions (cron 2am UTC) |
| API resultados | football-data.org |

---

*Modelo v3 · Actualizado automáticamente · UTC 02:00 diario*
