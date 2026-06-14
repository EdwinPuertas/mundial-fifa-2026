import json

with open('predicciones_v3_compact.json') as f:
    preds_raw = f.read()

with open('lineup_config.json') as f:
    lineup_cfg = json.load(f)

lineup_js = json.dumps(lineup_cfg["LINEUP"], ensure_ascii=False)
formation_js = json.dumps(lineup_cfg["FORMATION_FEATURES"], ensure_ascii=False)
style_js = json.dumps(lineup_cfg["STYLE_SCORE"], ensure_ascii=False)

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
groups_js = json.dumps(GROUPS, ensure_ascii=False)

TEAMS_SORTED = sorted([
    "Alemania","Arabia Saudita","Argelia","Argentina","Australia","Austria",
    "Bosnia y Herz.","Brasil","Bélgica","Cabo Verde","Canadá","Colombia",
    "Corea del Sur","Costa de Marfil","Croacia","Curazao","Ecuador","Egipto",
    "Escocia","España","Estados Unidos","Francia","Ghana","Haití","Inglaterra",
    "Irak","Irán","Japón","Jordania","Marruecos","México","Noruega",
    "Nueva Zelanda","Panamá","Paraguay","Países Bajos","Portugal","Qatar",
    "RD Congo","República Checa","Senegal","Sudáfrica","Suecia","Suiza",
    "Turquía","Túnez","Uruguay","Uzbekistán"
])

options_A = '\n'.join(f'<option value="{t}"{" selected" if t=="Francia" else ""}>{t}</option>' for t in TEAMS_SORTED)
options_B = '\n'.join(f'<option value="{t}"{" selected" if t=="Argentina" else ""}>{t}</option>' for t in TEAMS_SORTED)

html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>⚡ Modelo v3 — Mundial FIFA 2026 | Dual Engine AI</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{{
  --bg:#0a0f1a;--panel:#111827;--panel2:#1a2235;--border:#1e2d45;
  --blue:#3b82f6;--blue2:#60a5fa;--green:#10b981;--green2:#34d399;
  --orange:#f59e0b;--red:#ef4444;--red2:#f87171;--yellow:#fbbf24;
  --purple:#8b5cf6;--purple2:#a78bfa;--white:#f1f5f9;--gray:#64748b;
  --gray2:#94a3b8;--teal:#06b6d4;--pink:#ec4899;
  --eng-a:#3b82f6;--eng-b:#f59e0b;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--white);font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh;line-height:1.5}}
a{{color:var(--blue2);text-decoration:none}}

/* ── Layout ── */
.container{{max-width:1320px;margin:0 auto;padding:16px 12px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.grid3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}}
.grid4{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}

/* ── Header ── */
header{{background:linear-gradient(135deg,#0f1f3d 0%,#0a0f1a 100%);border-bottom:2px solid var(--border);padding:14px 20px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}}
header h1{{font-size:1.2rem;font-weight:800;background:linear-gradient(90deg,var(--blue2),var(--teal));-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.hbadge{{font-size:.65rem;font-weight:700;padding:2px 9px;border-radius:20px;border:1px solid}}
.hbadge.a{{border-color:var(--blue);color:var(--blue2);background:rgba(59,130,246,.12)}}
.hbadge.b{{border-color:var(--orange);color:var(--yellow);background:rgba(245,158,11,.12)}}
.hbadge.g{{border-color:var(--green);color:var(--green2);background:rgba(16,185,129,.12)}}
.hbadge.p{{border-color:var(--purple);color:var(--purple2);background:rgba(139,92,246,.12)}}

/* ── Cards ── */
.card{{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:14px}}
.card-title{{font-size:.72rem;color:var(--gray2);margin-bottom:12px;text-transform:uppercase;letter-spacing:.07em;font-weight:700;display:flex;align-items:center;gap:6px}}

/* ── Selects ── */
.team-col{{display:flex;flex-direction:column;gap:8px}}
label.lbl{{font-size:.72rem;color:var(--gray2);text-transform:uppercase;letter-spacing:.05em;font-weight:600}}
select{{width:100%;background:#0d1a2d;color:var(--white);border:1px solid var(--border);padding:10px 12px;border-radius:8px;font-size:.9rem;cursor:pointer;appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 10px center}}
select:focus{{outline:none;border-color:var(--blue);box-shadow:0 0 0 3px rgba(59,130,246,.2)}}
.vs-divider{{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0 8px}}
.vs-text{{font-size:1.6rem;font-weight:900;color:var(--yellow);line-height:1}}
.vs-sub{{font-size:.62rem;color:var(--gray);margin-top:4px;text-align:center}}
.swap-btn{{background:var(--panel2);border:1px solid var(--border);color:var(--gray2);width:34px;height:34px;border-radius:8px;cursor:pointer;font-size:1.1rem;display:flex;align-items:center;justify-content:center;margin-top:4px;transition:all .2s}}
.swap-btn:hover{{border-color:var(--blue);color:var(--blue2)}}

/* ── Formation selector ── */
.form-row{{display:flex;gap:6px;flex-wrap:wrap;margin-top:4px}}
.form-chip{{font-size:.68rem;padding:3px 8px;border-radius:6px;cursor:pointer;border:1px solid var(--border);color:var(--gray2);background:transparent;transition:all .18s}}
.form-chip:hover{{border-color:var(--blue);color:var(--blue2)}}
.form-chip.active{{background:var(--blue);border-color:var(--blue);color:#000;font-weight:700}}
.style-row{{display:flex;gap:6px;margin-top:6px}}
.style-chip{{font-size:.68rem;padding:3px 10px;border-radius:6px;cursor:pointer;border:1px solid var(--border);color:var(--gray2);background:transparent;transition:all .18s;flex:1;text-align:center}}
.style-chip:hover{{border-color:var(--green);color:var(--green2)}}
.style-chip.active.atk{{background:var(--red);border-color:var(--red);color:#fff;font-weight:700}}
.style-chip.active.bal{{background:var(--blue);border-color:var(--blue);color:#fff;font-weight:700}}
.style-chip.active.def{{background:var(--gray);border-color:var(--gray);color:#000;font-weight:700}}
.style-chip.active.ctr{{background:var(--purple);border-color:var(--purple);color:#fff;font-weight:700}}
.lineup-badge{{font-size:.68rem;padding:2px 7px;border-radius:5px;display:inline-block;margin-top:4px}}
.lineup-badge.atk{{background:rgba(239,68,68,.15);border:1px solid var(--red);color:var(--red2)}}
.lineup-badge.bal{{background:rgba(59,130,246,.15);border:1px solid var(--blue);color:var(--blue2)}}
.lineup-badge.def{{background:rgba(100,116,139,.15);border:1px solid var(--gray);color:var(--gray2)}}
.lineup-badge.ctr{{background:rgba(139,92,246,.15);border:1px solid var(--purple);color:var(--purple2)}}

/* ── Engine Toggle ── */
.engine-toggle{{display:flex;gap:0;border-radius:10px;overflow:hidden;border:1px solid var(--border);background:var(--bg);margin-bottom:14px}}
.eng-btn{{flex:1;padding:9px 14px;cursor:pointer;border:none;background:transparent;color:var(--gray2);font-size:.8rem;font-weight:600;transition:all .2s;position:relative}}
.eng-btn.active.a{{background:rgba(59,130,246,.2);color:var(--blue2);box-shadow:inset 0 -2px 0 var(--blue)}}
.eng-btn.active.b{{background:rgba(245,158,11,.2);color:var(--yellow);box-shadow:inset 0 -2px 0 var(--orange)}}
.eng-btn.active.cmp{{background:rgba(139,92,246,.2);color:var(--purple2);box-shadow:inset 0 -2px 0 var(--purple)}}
.eng-dot{{width:7px;height:7px;border-radius:50%;display:inline-block;margin-right:5px}}
.dot-a{{background:var(--blue)}} .dot-b{{background:var(--orange)}} .dot-cmp{{background:var(--purple)}}

/* ── Probability display ── */
.prob-3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:14px}}
.prob-card{{border-radius:10px;padding:18px 10px;text-align:center;border:1px solid;position:relative;overflow:hidden;transition:all .3s}}
.prob-card::before{{content:'';position:absolute;bottom:0;left:0;right:0;height:3px;border-radius:0 0 10px 10px}}
.pc-win{{background:rgba(16,185,129,.08);border-color:rgba(16,185,129,.3)}}
.pc-win::before{{background:var(--green)}}
.pc-draw{{background:rgba(251,191,36,.08);border-color:rgba(251,191,36,.3)}}
.pc-draw::before{{background:var(--yellow)}}
.pc-loss{{background:rgba(239,68,68,.08);border-color:rgba(239,68,68,.3)}}
.pc-loss::before{{background:var(--red)}}
.pc-pct{{font-size:2.4rem;font-weight:900;line-height:1;margin:6px 0}}
.pc-win .pc-pct{{color:var(--green2)}}
.pc-draw .pc-pct{{color:var(--yellow)}}
.pc-loss .pc-pct{{color:var(--red2)}}
.pc-lbl{{font-size:.68rem;color:var(--gray2);text-transform:uppercase;letter-spacing:.06em;font-weight:600}}
.pc-team{{font-size:.72rem;color:var(--gray);margin-top:3px}}

/* Probability bar */
.pbar-wrap{{margin:10px 0}}
.pbar{{height:10px;border-radius:5px;display:flex;overflow:hidden;background:rgba(255,255,255,.05)}}
.pb-w{{background:linear-gradient(90deg,#10b981,#34d399);transition:width .5s}}
.pb-d{{background:linear-gradient(90deg,#ca8a04,#fbbf24);transition:width .5s}}
.pb-l{{background:linear-gradient(90deg,#dc2626,#f87171);transition:width .5s}}
.pbar-labels{{display:flex;justify-content:space-between;font-size:.7rem;margin-top:4px}}

/* Consensus */
.consensus-box{{border-radius:10px;padding:10px 14px;display:flex;align-items:center;gap:10px;margin-bottom:14px;border:1px solid}}
.consensus-box.agree{{background:rgba(16,185,129,.08);border-color:rgba(16,185,129,.3)}}
.consensus-box.disagree{{background:rgba(245,158,11,.08);border-color:rgba(245,158,11,.3)}}
.consensus-box.split{{background:rgba(139,92,246,.08);border-color:rgba(139,92,246,.3)}}
.consensus-icon{{font-size:1.5rem}}
.consensus-text .title{{font-size:.82rem;font-weight:700}}
.consensus-text .sub{{font-size:.72rem;color:var(--gray2)}}

/* Compare mode */
.compare-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px}}
.engine-block{{border-radius:10px;padding:14px;border:1px solid}}
.engine-block.blk-a{{border-color:rgba(59,130,246,.4);background:rgba(59,130,246,.05)}}
.engine-block.blk-b{{border-color:rgba(245,158,11,.4);background:rgba(245,158,11,.05)}}
.engine-name{{font-size:.72rem;font-weight:700;margin-bottom:10px;display:flex;align-items:center;gap:6px;text-transform:uppercase;letter-spacing:.05em}}
.engine-name.na{{color:var(--blue2)}} .engine-name.nb{{color:var(--yellow)}}
.mini-probs{{display:flex;gap:8px;margin-bottom:6px}}
.mini-p{{flex:1;text-align:center;padding:8px 4px;border-radius:8px;background:rgba(255,255,255,.04)}}
.mini-pct{{font-size:1.3rem;font-weight:800}}
.mini-lbl{{font-size:.6rem;color:var(--gray2);text-transform:uppercase}}

/* Score */
.score-display{{display:flex;align-items:center;justify-content:center;gap:16px;padding:16px 0;margin-bottom:14px}}
.score-side{{text-align:center;flex:1}}
.score-num{{font-size:3rem;font-weight:900;color:var(--blue2)}}
.score-name{{font-size:.8rem;color:var(--gray2);margin-top:4px}}
.score-lambda{{font-size:.7rem;color:var(--gray);margin-top:2px}}
.score-colon{{font-size:2.5rem;color:var(--border);font-weight:300}}

/* Tactic cards */
.tact-row{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.tact-card{{background:var(--panel2);border-radius:10px;padding:14px}}
.tact-header{{font-size:.72rem;color:var(--gray2);text-transform:uppercase;letter-spacing:.05em;margin-bottom:10px;font-weight:700}}
.tact-item{{display:flex;align-items:center;gap:8px;margin-bottom:6px}}
.tact-label{{font-size:.72rem;color:var(--gray2);width:70px;flex-shrink:0}}
.tact-bar-wrap{{flex:1;background:rgba(255,255,255,.05);border-radius:4px;height:8px;overflow:hidden}}
.tact-bar{{height:100%;border-radius:4px;transition:width .4s}}
.tact-val{{font-size:.7rem;color:var(--white);width:32px;text-align:right}}

/* Groups */
.groups-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}
.group-card{{background:var(--panel2);border-radius:8px;padding:10px;border:1px solid var(--border);cursor:pointer;transition:all .2s}}
.group-card:hover{{border-color:var(--blue);transform:translateY(-1px)}}
.group-title{{font-size:.72rem;font-weight:800;color:var(--yellow);margin-bottom:6px;letter-spacing:.05em}}
.group-team{{font-size:.72rem;padding:3px 6px;margin-bottom:3px;border-radius:4px;background:rgba(255,255,255,.03);cursor:pointer;transition:all .15s;display:flex;align-items:center;gap:5px}}
.group-team:hover{{background:rgba(59,130,246,.15);color:var(--blue2)}}
.rank-dot{{width:6px;height:6px;border-radius:50%;background:var(--green2);flex-shrink:0}}

/* Result verdict */
#verdict{{border-radius:10px;padding:12px 16px;font-size:.85rem;line-height:1.6}}
.verd-win{{background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.3)}}
.verd-draw{{background:rgba(251,191,36,.1);border:1px solid rgba(251,191,36,.3)}}
.verd-loss{{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3)}}

/* Stats */
.stat-grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.stat-row{{background:var(--panel2);border-radius:8px;padding:10px 12px}}
.stat-label{{font-size:.7rem;color:var(--gray2);margin-bottom:6px;text-transform:uppercase;letter-spacing:.04em;font-weight:600}}
.stat-compare{{display:flex;align-items:center;gap:8px}}
.stat-val-a{{text-align:right;font-size:.88rem;font-weight:700;color:var(--blue2);width:50px}}
.stat-val-b{{text-align:left;font-size:.88rem;font-weight:700;color:var(--yellow);width:50px}}
.stat-bar-dual{{flex:1;height:8px;border-radius:4px;background:rgba(255,255,255,.05);display:flex;overflow:hidden}}
.stat-bar-a{{background:var(--blue);border-radius:4px 0 0 4px;transition:width .4s}}
.stat-bar-b{{background:var(--orange);border-radius:0 4px 4px 0;transition:width .4s}}

/* Feature importance */
.fi-item{{display:flex;align-items:center;gap:8px;margin-bottom:5px}}
.fi-name{{font-size:.7rem;color:var(--white);width:140px;flex-shrink:0}}
.fi-bar{{height:10px;border-radius:5px;transition:width .4s}}
.fi-pct{{font-size:.68rem;color:var(--gray2);width:36px;text-align:right}}

/* Utility */
.text-center{{text-align:center}}
.mt8{{margin-top:8px}} .mt12{{margin-top:12px}} .mt16{{margin-top:16px}}
.flex{{display:flex}} .gap8{{gap:8px}} .gap12{{gap:12px}} .items-center{{align-items:center}} .flex-wrap{{flex-wrap:wrap}}
.badge{{font-size:.65rem;font-weight:700;padding:2px 7px;border-radius:5px}}
.tag-form{{background:rgba(59,130,246,.15);border:1px solid var(--blue);color:var(--blue2)}}
.tag-cwe{{background:rgba(139,92,246,.15);border:1px solid var(--purple);color:var(--purple2)}}
.divider{{height:1px;background:var(--border);margin:12px 0}}

/* Tabs */
.tabs{{display:flex;border-bottom:1px solid var(--border);margin-bottom:14px;overflow-x:auto}}
.tab{{padding:8px 16px;cursor:pointer;font-size:.8rem;color:var(--gray);border-bottom:2px solid transparent;white-space:nowrap;flex-shrink:0;transition:all .2s}}
.tab.active{{color:var(--white);border-color:var(--blue);font-weight:600}}
.tab-pane{{display:none}} .tab-pane.active{{display:block}}

@media(max-width:800px){{
  .grid2,.grid3,.grid4{{grid-template-columns:1fr}}
  .groups-grid{{grid-template-columns:repeat(2,1fr)}}
  .prob-3,.compare-grid,.tact-row{{grid-template-columns:1fr}}
  .stat-grid{{grid-template-columns:1fr}}
  header{{flex-direction:column;align-items:flex-start;gap:8px}}
}}
</style>
</head>
<body>

<header>
  <div style="font-size:1.9rem">⚡</div>
  <div>
    <h1>Modelo v3 — Mundial FIFA 2026 | Dual Engine AI</h1>
    <div style="color:var(--gray);font-size:.76rem;margin-top:3px">Engine A: Deep MLP + Self-Attention · Engine B: XGBoost Agresivo · 74 features · T=0.55</div>
  </div>
  <div style="margin-left:auto;display:flex;gap:6px;flex-wrap:wrap">
    <span class="hbadge a">Engine A · MLP+Atención</span>
    <span class="hbadge b">Engine B · XGBoost</span>
    <span class="hbadge g">AUC 0.711</span>
    <span class="hbadge p">74 features</span>
  </div>
</header>

<div class="container">

<!-- CONFIGURADOR DE PARTIDO -->
<div class="card">
  <div class="card-title">⚽ Configurar Partido &amp; Alineaciones</div>
  <div style="display:grid;grid-template-columns:1fr auto 1fr;gap:12px;align-items:start">

    <!-- TEAM A -->
    <div class="team-col">
      <label class="lbl">🟦 Equipo A</label>
      <select id="teamA" onchange="onTeamChange()">
{options_A}
      </select>
      <label class="lbl mt8">Formación A</label>
      <div class="form-row" id="formRowA"></div>
      <label class="lbl mt8">Estilo A</label>
      <div class="style-row" id="styleRowA"></div>
      <div id="badgeA" class="mt8"></div>
    </div>

    <!-- VS -->
    <div class="vs-divider">
      <div class="vs-text">VS</div>
      <div class="vs-sub">Sede<br>Neutral</div>
      <button class="swap-btn mt8" onclick="swapTeams()" title="Intercambiar equipos">⇄</button>
    </div>

    <!-- TEAM B -->
    <div class="team-col">
      <label class="lbl">🟥 Equipo B</label>
      <select id="teamB" onchange="onTeamChange()">
{options_B}
      </select>
      <label class="lbl mt8">Formación B</label>
      <div class="form-row" id="formRowB"></div>
      <label class="lbl mt8">Estilo B</label>
      <div class="style-row" id="styleRowB"></div>
      <div id="badgeB" class="mt8"></div>
    </div>
  </div>
</div>

<!-- PREDICTION PANEL -->
<div class="card" id="predCard">
  <div class="card-title">🎯 Predicción del Partido</div>

  <!-- ENGINE TOGGLE -->
  <div class="engine-toggle">
    <button class="eng-btn active a" id="btnEngA" onclick="setEngine('A')">
      <span class="eng-dot dot-a"></span>Engine A · MLP+Atención
    </button>
    <button class="eng-btn b" id="btnEngB" onclick="setEngine('B')">
      <span class="eng-dot dot-b"></span>Engine B · XGBoost
    </button>
    <button class="eng-btn cmp" id="btnEngCmp" onclick="setEngine('CMP')">
      <span class="eng-dot dot-cmp"></span>Comparar Engines
    </button>
  </div>

  <!-- SINGLE ENGINE VIEW (A or B) -->
  <div id="singleView">
    <!-- Consensus -->
    <div id="consensusBox" class="consensus-box agree">
      <div class="consensus-icon" id="consensusIcon">✅</div>
      <div class="consensus-text">
        <div class="title" id="consensusTitle">Ambos engines coinciden</div>
        <div class="sub" id="consensusSub">Alta confianza en el resultado</div>
      </div>
    </div>

    <!-- Probabilities -->
    <div class="prob-3" id="probCards">
      <div class="prob-card pc-win">
        <div class="pc-lbl">Victoria</div>
        <div class="pc-team" id="pcTeamA">Equipo A</div>
        <div class="pc-pct" id="pcVic">—</div>
      </div>
      <div class="prob-card pc-draw">
        <div class="pc-lbl">Empate</div>
        <div class="pc-pct" id="pcEmp">—</div>
      </div>
      <div class="prob-card pc-loss">
        <div class="pc-lbl">Victoria</div>
        <div class="pc-team" id="pcTeamB">Equipo B</div>
        <div class="pc-pct" id="pcDer">—</div>
      </div>
    </div>

    <!-- Probability bar -->
    <div class="pbar-wrap">
      <div class="pbar">
        <div class="pb-w" id="barW" style="width:33%"></div>
        <div class="pb-d" id="barD" style="width:34%"></div>
        <div class="pb-l" id="barL" style="width:33%"></div>
      </div>
      <div class="pbar-labels">
        <span id="lbarA" style="color:var(--green2)">33%</span>
        <span style="color:var(--yellow)">Empate 34%</span>
        <span id="lbarB" style="color:var(--red2)">33%</span>
      </div>
    </div>

    <!-- Score prediction -->
    <div class="score-display">
      <div class="score-side">
        <div class="score-num" id="scoreA">1.3</div>
        <div class="score-name" id="scoreNameA">Equipo A</div>
        <div class="score-lambda">goles esperados (λ)</div>
      </div>
      <div class="score-colon">—</div>
      <div class="score-side">
        <div class="score-num" id="scoreB">0.4</div>
        <div class="score-name" id="scoreNameB">Equipo B</div>
        <div class="score-lambda">goles esperados (λ)</div>
      </div>
    </div>

    <!-- Verdict -->
    <div id="verdict" class="verd-win">Cargando predicción...</div>
  </div>

  <!-- COMPARE VIEW (both engines) -->
  <div id="compareView" style="display:none">
    <div id="consensusBoxCmp" class="consensus-box agree" style="margin-bottom:14px">
      <div class="consensus-icon" id="cmpIcon">✅</div>
      <div class="consensus-text">
        <div class="title" id="cmpTitle">—</div>
        <div class="sub" id="cmpSub">—</div>
      </div>
    </div>
    <div class="compare-grid">
      <div class="engine-block blk-a">
        <div class="engine-name na">🔵 Engine A — Deep MLP + Self-Attention</div>
        <div class="mini-probs" id="cmpProbs_A"></div>
        <div class="pbar" id="cmpBar_A" style="height:8px;margin-top:8px"></div>
      </div>
      <div class="engine-block blk-b">
        <div class="engine-name nb">🟡 Engine B — XGBoost Agresivo</div>
        <div class="mini-probs" id="cmpProbs_B"></div>
        <div class="pbar" id="cmpBar_B" style="height:8px;margin-top:8px"></div>
      </div>
    </div>
    <div class="score-display" style="padding:10px 0">
      <div class="score-side"><div class="score-num" id="cmpScoreA">—</div><div class="score-name" id="cmpNameA">A</div><div class="score-lambda">λ goles</div></div>
      <div class="score-colon">—</div>
      <div class="score-side"><div class="score-num" id="cmpScoreB">—</div><div class="score-name" id="cmpNameB">B</div><div class="score-lambda">λ goles</div></div>
    </div>
  </div>
</div>

<!-- ANÁLISIS TÁCTICO -->
<div class="card">
  <div class="card-title">⚙️ Análisis Táctico</div>
  <div class="tact-row" id="tactRow">
    <!-- filled by JS -->
  </div>
</div>

<!-- TABS: GRUPOS / STATS / FEATURES -->
<div class="card">
  <div class="tabs">
    <div class="tab active" onclick="switchTab('grupos',this)">🏟️ Grupos</div>
    <div class="tab" onclick="switchTab('stats',this)">📊 Stats Comparativas</div>
    <div class="tab" onclick="switchTab('features',this)">🔬 Feature Importance</div>
    <div class="tab" onclick="switchTab('info',this)">ℹ️ Sobre el Modelo</div>
  </div>

  <!-- GRUPOS -->
  <div class="tab-pane active" id="tab-grupos">
    <div class="groups-grid" id="groupsGrid"></div>
    <div id="groupMatchesPanel" style="display:none;margin-top:14px">
      <div class="card-title" id="groupMatchesTitle">Partidos del Grupo</div>
      <div id="groupMatchesList"></div>
    </div>
  </div>

  <!-- STATS -->
  <div class="tab-pane" id="tab-stats">
    <div style="font-size:.8rem;color:var(--gray2);margin-bottom:10px">Comparativa entre los equipos seleccionados · <span style="color:var(--blue2)">Azul = Equipo A</span> · <span style="color:var(--yellow)">Naranja = Equipo B</span></div>
    <div class="stat-grid" id="statGrid"></div>
  </div>

  <!-- FEATURES -->
  <div class="tab-pane" id="tab-features">
    <div style="color:var(--gray2);font-size:.78rem;margin-bottom:12px">Importancia de features — Engine B (XGBoost). Las features tácticas (v3 nuevas) aparecen resaltadas.</div>
    <div id="featureList"></div>
  </div>

  <!-- INFO -->
  <div class="tab-pane" id="tab-info">
    <div style="font-size:.85rem;color:var(--gray2);line-height:1.8">
      <div style="margin-bottom:12px"><strong style="color:var(--white)">Modelo v3 — Cambios principales vs v2</strong></div>
      <ul style="margin-left:16px;display:flex;flex-direction:column;gap:6px">
        <li><span style="color:var(--green2)">✓</span> <strong>Configuración de alineaciones</strong>: formación táctica (4-3-3, 4-2-3-1, 5-3-2, etc.) + estilo de juego (attacking / balanced / defensive) por equipo</li>
        <li><span style="color:var(--green2)">✓</span> <strong>Engine A</strong>: Deep MLP (512→256→128→64→32) con mecanismo de Self-Attention de 4 cabezas — redes de 2ª generación, sin TensorFlow/PyTorch, ejecutado en sklearn/numpy</li>
        <li><span style="color:var(--green2)">✓</span> <strong>Engine B</strong>: XGBoost agresivo (max_depth=7, estimadores=400, lr=0.06) — calibrado a T=0.55 para predicciones más decisivas</li>
        <li><span style="color:var(--green2)">✓</span> <strong>Eliminadas variables de expertos</strong>: injury_factor, is_host, xg_qual (siempre cero en eliminatorias fuera del país)</li>
        <li><span style="color:var(--green2)">✓</span> <strong>74 features</strong> vs 35 en v2: nuevas features tácticas (formation_attack, pressing, set_piece, style_score), experiencia WC por confederación, interacciones cruzadas ataque×defensa</li>
        <li><span style="color:var(--green2)">✓</span> <strong>Calibración T=0.55</strong>: distribuciones de probabilidad más extremas (menos empates genéricos, más decisión)</li>
        <li><span style="color:var(--orange)">▸</span> <strong>Output dual</strong>: Engine A da predicciones balanceadas; Engine B da predicciones agresivas. Cuando coinciden = alta confianza.</li>
      </ul>
      <div class="divider"></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:.8rem">
        <div><div style="color:var(--blue2);font-weight:700;margin-bottom:4px">Engine A — MLP + Self-Attention</div>
          <div>• Capas: 512→256→128→64→32</div>
          <div>• Self-Attention: 4 heads, T=0.45</div>
          <div>• Acc=0.591 | F1=0.525 | AUC=0.642</div></div>
        <div><div style="color:var(--yellow);font-weight:700;margin-bottom:4px">Engine B — XGBoost Agresivo</div>
          <div>• depth=7 | n_est=400 | lr=0.06</div>
          <div>• min_child_w=1 | gamma=0.05</div>
          <div>• Acc=0.545 | F1=0.535 | AUC=0.711</div></div>
      </div>
    </div>
  </div>
</div>

</div><!-- /container -->

<script>
// ═══════════════════════════════════
// DATA
// ═══════════════════════════════════
const PREDS = {preds_raw};

const LINEUP_DEFAULT = {lineup_js};
const FORMATION_FEATURES = {formation_js};
const STYLE_SCORE = {style_js};

const GROUPS = {groups_js};

const FORMATIONS = ["4-3-3","4-4-2","4-2-3-1","3-4-3","3-5-2","5-3-2","4-5-1","5-4-1","4-1-4-1"];
const STYLES = ["attacking","balanced","defensive","counterattack"];
const STYLE_LABEL = {{attacking:"Ataque",balanced:"Balanceado",defensive:"Defensa",counterattack:"Contra"}};
const STYLE_CLASS = {{attacking:"atk",balanced:"bal",defensive:"def",counterattack:"ctr"}};

const FEATURE_IMPORTANCE = [
  {{f:"diff_att (combo ofensivo)",v:0.0429,new_:true}},
  {{f:"diff_sq_rat (rating plantilla)",v:0.0394,new_:false}},
  {{f:"sq_rat_A",v:0.0361,new_:false}},
  {{f:"cross_tb (interacción táctica)",v:0.0343,new_:true}},
  {{f:"cwe_A (exp. confederación WC)",v:0.0342,new_:true}},
  {{f:"diff_log_mv (valor mercado)",v:0.0316,new_:false}},
  {{f:"rank_diff",v:0.0278,new_:false}},
  {{f:"net_off_pow (poder ofensivo neto)",v:0.0277,new_:true}},
  {{f:"rank_ratio",v:0.0274,new_:false}},
  {{f:"log_mv_B",v:0.0268,new_:false}},
  {{f:"conf_A",v:0.0258,new_:false}},
  {{f:"rank_A",v:0.0243,new_:false}},
  {{f:"diff_cwe (diff exp. WC)",v:0.0228,new_:true}},
  {{f:"wr_A (win rate elim.)",v:0.0212,new_:true}},
  {{f:"cwe_B",v:0.0200,new_:true}},
  {{f:"fatk_A (formación ataque A)",v:0.0188,new_:true}},
  {{f:"style_A",v:0.0175,new_:true}},
  {{f:"tact_adv (ventaja táctica)",v:0.0166,new_:true}},
];

const TEAM_STATS = {{
  "Francia":[1,88.2,1050,26.1],"España":[2,87.5,980,24.8],"Argentina":[3,87.0,760,28.2],
  "Inglaterra":[4,86.5,1100,26.5],"Portugal":[5,85.8,920,27.8],"Brasil":[6,86.0,1200,24.5],
  "Países Bajos":[7,84.5,870,25.8],"Marruecos":[8,80.0,320,25.2],"Bélgica":[9,83.5,680,28.5],
  "Alemania":[10,84.0,890,25.2],"Croacia":[11,82.5,420,29.5],"Colombia":[13,82.0,480,25.8],
  "Senegal":[14,79.5,280,26.0],"México":[15,80.5,390,26.5],"Estados Unidos":[16,80.0,520,25.2],
  "Uruguay":[17,81.0,430,27.8],"Japón":[18,81.5,560,25.5],"Suiza":[19,80.5,450,27.2],
  "Irán":[21,77.5,180,26.5],"Turquía":[22,79.5,490,26.2],"Ecuador":[23,79.0,310,24.8],
  "Austria":[24,79.5,410,26.5],"Corea del Sur":[25,79.0,380,26.0],"Australia":[27,77.5,220,26.8],
  "Argelia":[28,77.0,160,26.5],"Egipto":[29,76.5,140,26.2],"Canadá":[30,78.0,340,25.0],
  "Noruega":[31,79.5,560,25.5],"Panamá":[33,73.5,95,26.5],"Costa de Marfil":[34,74.5,210,26.2],
  "Suecia":[38,76.0,360,26.8],"Paraguay":[40,73.5,150,26.5],"República Checa":[41,74.0,220,27.0],
  "Escocia":[43,72.5,180,27.2],"Túnez":[44,71.5,120,26.8],"RD Congo":[46,70.5,95,26.0],
  "Uzbekistán":[50,70.0,85,25.5],"Qatar":[55,68.5,75,26.2],"Irak":[57,68.0,65,26.5],
  "Sudáfrica":[60,67.5,80,26.8],"Arabia Saudita":[61,68.0,110,26.5],"Jordania":[63,66.5,55,26.2],
  "Bosnia y Herz.":[65,69.0,95,27.5],"Cabo Verde":[69,66.0,55,26.5],"Ghana":[74,65.0,70,26.0],
  "Curazao":[82,61.5,30,25.8],"Haití":[83,60.5,25,25.5],"Nueva Zelanda":[85,60.0,40,26.5]
}};

// ═══════════════════════════════════
// STATE
// ═══════════════════════════════════
let currentEngine = 'A';
let userFormA = null, userStyleA = null;
let userFormB = null, userStyleB = null;

// ═══════════════════════════════════
// INIT
// ═══════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {{
  renderGroups();
  renderFeatureImportance();
  onTeamChange();
}});

// ═══════════════════════════════════
// LINEUP CHIPS BUILDER
// ═══════════════════════════════════
function buildFormChips(containerId, team, side) {{
  const def = LINEUP_DEFAULT[team] || {{formation:'4-3-3',style:'balanced'}};
  const current = side === 'A' ? (userFormA || def.formation) : (userFormB || def.formation);
  const container = document.getElementById(containerId);
  container.innerHTML = FORMATIONS.map(f => {{
    const isActive = f === current ? ' active' : '';
    return `<span class="form-chip${{isActive}}" onclick="selectForm('${{side}}','${{f}}')">${{f}}</span>`;
  }}).join('');
}}

function buildStyleChips(containerId, team, side) {{
  const def = LINEUP_DEFAULT[team] || {{formation:'4-3-3',style:'balanced'}};
  const current = side === 'A' ? (userStyleA || def.style) : (userStyleB || def.style);
  const container = document.getElementById(containerId);
  container.innerHTML = STYLES.map(s => {{
    const isActive = s === current ? ` active ${{STYLE_CLASS[s]}}` : '';
    return `<span class="style-chip${{isActive}}" onclick="selectStyle('${{side}}','${{s}}')">${{STYLE_LABEL[s]}}</span>`;
  }}).join('');
}}

function renderLineupBadge(side) {{
  const teamName = document.getElementById('team' + side).value;
  const def = LINEUP_DEFAULT[teamName] || {{formation:'4-3-3',style:'balanced'}};
  const form = (side==='A' ? userFormA : userFormB) || def.formation;
  const style = (side==='A' ? userStyleA : userStyleB) || def.style;
  const cls = STYLE_CLASS[style] || 'bal';
  document.getElementById('badge'+side).innerHTML =
    `<span class="lineup-badge tag-form">${{form}}</span> <span class="lineup-badge ${{cls}}">${{STYLE_LABEL[style]}}</span>`;
}}

function selectForm(side, form) {{
  if (side === 'A') userFormA = form; else userFormB = form;
  const team = document.getElementById('team' + side).value;
  buildFormChips('formRow'+side, team, side);
  renderLineupBadge(side);
  updatePrediction();
}}

function selectStyle(side, style) {{
  if (side === 'A') userStyleA = style; else userStyleB = style;
  const team = document.getElementById('team' + side).value;
  buildStyleChips('styleRow'+side, team, side);
  renderLineupBadge(side);
  updatePrediction();
}}

// ═══════════════════════════════════
// ENGINE TOGGLE
// ═══════════════════════════════════
function setEngine(eng) {{
  currentEngine = eng;
  ['A','B','CMP'].forEach(e => {{
    document.getElementById('btnEng'+e).classList.remove('active','a','b','cmp');
  }});
  const btn = document.getElementById('btnEng'+eng);
  btn.classList.add('active');
  if (eng === 'A') btn.classList.add('a');
  else if (eng === 'B') btn.classList.add('b');
  else btn.classList.add('cmp');

  document.getElementById('singleView').style.display = eng !== 'CMP' ? 'block' : 'none';
  document.getElementById('compareView').style.display = eng === 'CMP' ? 'block' : 'none';
  updatePrediction();
}}

// ═══════════════════════════════════
// TACTICAL MODIFIER
// ═══════════════════════════════════
function computeAttackPow(form, style) {{
  const ff = FORMATION_FEATURES[form] || FORMATION_FEATURES['4-3-3'];
  const ss = STYLE_SCORE[style] || 1.0;
  return ff.attack * ss;
}}

function applyLineupModifier(baseP, teamA, formA, styleA, teamB, formB, styleB) {{
  const defA = LINEUP_DEFAULT[teamA] || {{formation:'4-3-3',style:'balanced'}};
  const defB = LINEUP_DEFAULT[teamB] || {{formation:'4-3-3',style:'balanced'}};
  const powA_cur = computeAttackPow(formA, styleA);
  const powA_def = computeAttackPow(defA.formation, defA.style);
  const powB_cur = computeAttackPow(formB, styleB);
  const powB_def = computeAttackPow(defB.formation, defB.style);
  const net = (powA_cur - powA_def) - (powB_cur - powB_def);
  const shift = net * 0.22;
  let v = Math.max(0.01, Math.min(0.97, baseP.p_victoria + shift));
  let d = Math.max(0.01, Math.min(0.97, baseP.p_derrota - shift));
  let e = Math.max(0.01, baseP.p_empate);
  const sum = v + e + d;
  return {{ p_victoria: v/sum, p_empate: e/sum, p_derrota: d/sum }};
}}

// ═══════════════════════════════════
// TEAM CHANGE HANDLER
// ═══════════════════════════════════
function onTeamChange() {{
  const tA = document.getElementById('teamA').value;
  const tB = document.getElementById('teamB').value;
  userFormA = null; userStyleA = null;
  userFormB = null; userStyleB = null;
  buildFormChips('formRowA', tA, 'A');
  buildFormChips('formRowB', tB, 'B');
  buildStyleChips('styleRowA', tA, 'A');
  buildStyleChips('styleRowB', tB, 'B');
  renderLineupBadge('A');
  renderLineupBadge('B');
  updatePrediction();
  renderStats(tA, tB);
}}

function swapTeams() {{
  const sA = document.getElementById('teamA');
  const sB = document.getElementById('teamB');
  [sA.value, sB.value] = [sB.value, sA.value];
  userFormA = null; userStyleA = null;
  userFormB = null; userStyleB = null;
  onTeamChange();
}}

// ═══════════════════════════════════
// UPDATE PREDICTION
// ═══════════════════════════════════
function updatePrediction() {{
  const tA = document.getElementById('teamA').value;
  const tB = document.getElementById('teamB').value;
  if (tA === tB) return;
  const match = PREDS[tA] && PREDS[tA][tB];
  if (!match) return;

  const defA = LINEUP_DEFAULT[tA] || {{formation:'4-3-3',style:'balanced'}};
  const defB = LINEUP_DEFAULT[tB] || {{formation:'4-3-3',style:'balanced'}};
  const formA = userFormA || defA.formation;
  const styleA = userStyleA || defA.style;
  const formB = userFormB || defB.formation;
  const styleB = userStyleB || defB.style;

  const rawA = match.engine_A;
  const rawB = match.engine_B;

  const probA = applyLineupModifier(rawA, tA, formA, styleA, tB, formB, styleB);
  const probB = applyLineupModifier(rawB, tA, formA, styleA, tB, formB, styleB);

  const lA = match.lambda_A;
  const lB = match.lambda_B;

  // Consensus
  const winnerA = probA.p_victoria > probA.p_derrota && probA.p_victoria > probA.p_empate ? 'A'
    : probA.p_derrota > probA.p_empate ? 'B' : 'E';
  const winnerB = probB.p_victoria > probB.p_derrota && probB.p_victoria > probB.p_empate ? 'A'
    : probB.p_derrota > probB.p_empate ? 'B' : 'E';
  const agree = winnerA === winnerB;

  renderConsensus(agree, winnerA, winnerB, tA, tB, probA, probB);

  if (currentEngine === 'CMP') {{
    renderCompare(probA, probB, tA, tB, lA, lB);
  }} else {{
    const prob = currentEngine === 'A' ? probA : probB;
    renderSingle(prob, tA, tB, lA, lB);
  }}

  renderTactics(tA, formA, styleA, tB, formB, styleB);
}}

// ═══════════════════════════════════
// RENDER SINGLE ENGINE
// ═══════════════════════════════════
function renderSingle(prob, tA, tB, lA, lB) {{
  const v = prob.p_victoria, e = prob.p_empate, d = prob.p_derrota;
  document.getElementById('pcVic').textContent = pct(v);
  document.getElementById('pcEmp').textContent = pct(e);
  document.getElementById('pcDer').textContent = pct(d);
  document.getElementById('pcTeamA').textContent = tA;
  document.getElementById('pcTeamB').textContent = tB;
  document.getElementById('barW').style.width = pct(v);
  document.getElementById('barD').style.width = pct(e);
  document.getElementById('barL').style.width = pct(d);
  document.getElementById('lbarA').textContent = tA + ' ' + pct(v);
  document.getElementById('lbarB').textContent = tB + ' ' + pct(d);
  document.getElementById('scoreA').textContent = lA.toFixed(1);
  document.getElementById('scoreB').textContent = lB.toFixed(1);
  document.getElementById('scoreNameA').textContent = tA;
  document.getElementById('scoreNameB').textContent = tB;
  renderVerdict(v, e, d, tA, tB, lA, lB);
}}

// ═══════════════════════════════════
// RENDER COMPARE
// ═══════════════════════════════════
function renderCompare(pA, pB, tA, tB, lA, lB) {{
  document.getElementById('cmpScoreA').textContent = lA.toFixed(1);
  document.getElementById('cmpScoreB').textContent = lB.toFixed(1);
  document.getElementById('cmpNameA').textContent = tA;
  document.getElementById('cmpNameB').textContent = tB;

  ['A','B'].forEach(side => {{
    const p = side === 'A' ? pA : pB;
    const el = document.getElementById('cmpProbs_' + side);
    const barEl = document.getElementById('cmpBar_' + side);
    const colorV = '#10b981', colorE = '#fbbf24', colorD = '#ef4444';
    el.innerHTML = `
      <div class="mini-p" style="background:rgba(16,185,129,.1)">
        <div class="mini-pct" style="color:#34d399">${{pct(p.p_victoria)}}</div>
        <div class="mini-lbl">V ${{tA}}</div>
      </div>
      <div class="mini-p" style="background:rgba(251,191,36,.1)">
        <div class="mini-pct" style="color:#fbbf24">${{pct(p.p_empate)}}</div>
        <div class="mini-lbl">Empate</div>
      </div>
      <div class="mini-p" style="background:rgba(239,68,68,.1)">
        <div class="mini-pct" style="color:#f87171">${{pct(p.p_derrota)}}</div>
        <div class="mini-lbl">V ${{tB}}</div>
      </div>`;
    barEl.innerHTML = `
      <div class="pb-w" style="width:${{pct(p.p_victoria)}}"></div>
      <div class="pb-d" style="width:${{pct(p.p_empate)}}"></div>
      <div class="pb-l" style="width:${{pct(p.p_derrota)}}"></div>`;
  }});
}}

// ═══════════════════════════════════
// CONSENSUS
// ═══════════════════════════════════
function renderConsensus(agree, wA, wB, tA, tB, pA, pB) {{
  const box = document.getElementById('consensusBox');
  const icon = document.getElementById('consensusIcon');
  const title = document.getElementById('consensusTitle');
  const sub = document.getElementById('consensusSub');

  const cmpBox = document.getElementById('consensusBoxCmp');
  const cmpIcon = document.getElementById('cmpIcon');
  const cmpTitle = document.getElementById('cmpTitle');
  const cmpSub = document.getElementById('cmpSub');

  const winnerLabel = (w) => w === 'A' ? `Victoria ${{tA}}` : w === 'B' ? `Victoria ${{tB}}` : 'Empate';
  const maxDiff = Math.abs(pA.p_victoria - pB.p_victoria);

  let boxClass, iconStr, titleStr, subStr;
  if (agree) {{
    const conf = Math.min(pA.p_victoria, pA.p_derrota);
    const highConf = Math.max(pA.p_victoria, pA.p_derrota) > 0.65;
    if (highConf) {{
      boxClass = 'agree'; iconStr = '✅';
      titleStr = `Ambos engines coinciden: ${{winnerLabel(wA)}}`;
      subStr = 'Alta confianza · Partido con favorito claro';
    }} else {{
      boxClass = 'agree'; iconStr = '🟢';
      titleStr = `Engines coinciden: ${{winnerLabel(wA)}}`;
      subStr = 'Resultado esperado, pero con margen de incertidumbre';
    }}
  }} else {{
    boxClass = 'disagree'; iconStr = '⚠️';
    titleStr = `Engines divergen · Partido muy abierto`;
    subStr = `Engine A: ${{winnerLabel(wA)}} · Engine B: ${{winnerLabel(wB)}}`;
  }}

  [box, cmpBox].forEach(b => {{
    b.className = 'consensus-box ' + boxClass;
  }});
  icon.textContent = iconStr; cmpIcon.textContent = iconStr;
  title.textContent = titleStr; cmpTitle.textContent = titleStr;
  sub.textContent = subStr; cmpSub.textContent = subStr;
}}

// ═══════════════════════════════════
// VERDICT
// ═══════════════════════════════════
function renderVerdict(v, e, d, tA, tB, lA, lB) {{
  const el = document.getElementById('verdict');
  const engLabel = currentEngine === 'A' ? 'Engine A (MLP+Atención)' : 'Engine B (XGBoost)';
  let cls, text;
  if (v > d && v > e) {{
    cls = 'verd-win';
    const conf = v > 0.75 ? 'con alta confianza' : v > 0.55 ? 'como favorito' : 'como leve favorito';
    text = `🏆 <strong>${{tA}}</strong> se proyecta ${{conf}} (${{pct(v)}} según ${{engLabel}}). Goles esperados: ${{tA}} ${{lA.toFixed(1)}} — ${{tB}} ${{lB.toFixed(1)}}.`;
  }} else if (d > v && d > e) {{
    cls = 'verd-loss';
    const conf = d > 0.75 ? 'con alta confianza' : 'como favorito';
    text = `🏆 <strong>${{tB}}</strong> se proyecta ${{conf}} (${{pct(d)}} según ${{engLabel}}). Goles esperados: ${{tA}} ${{lA.toFixed(1)}} — ${{tB}} ${{lB.toFixed(1)}}.`;
  }} else {{
    cls = 'verd-draw';
    text = `⚖️ Partido equilibrado. Alta probabilidad de empate (${{pct(e)}}). Goles esperados: ${{tA}} ${{lA.toFixed(1)}} — ${{tB}} ${{lB.toFixed(1)}}. Resultado muy abierto.`;
  }}
  el.className = cls;
  el.innerHTML = text;
}}

// ═══════════════════════════════════
// TACTICS
// ═══════════════════════════════════
function renderTactics(tA, formA, styleA, tB, formB, styleB) {{
  const ffA = FORMATION_FEATURES[formA] || FORMATION_FEATURES['4-3-3'];
  const ffB = FORMATION_FEATURES[formB] || FORMATION_FEATURES['4-3-3'];
  const ssA = STYLE_SCORE[styleA] || 1.0;
  const ssB = STYLE_SCORE[styleB] || 1.0;
  const attrs = [
    {{label:'Ataque', keyA: ffA.attack*ssA, keyB: ffB.attack*ssB, max:1.2}},
    {{label:'Defensa', keyA: ffA.defense, keyB: ffB.defense, max:1.0}},
    {{label:'Pressing', keyA: ffA.pressing, keyB: ffB.pressing, max:1.0}},
    {{label:'Amplitud', keyA: ffA.width, keyB: ffB.width, max:1.0}},
    {{label:'Set Piece', keyA: ffA.set_piece, keyB: ffB.set_piece, max:1.0}},
  ];
  const colorA = '#3b82f6', colorB = '#f59e0b';
  document.getElementById('tactRow').innerHTML = `
    <div class="tact-card">
      <div class="tact-header" style="color:${{colorA}}">🔵 ${{tA}} — ${{formA}} / ${{STYLE_LABEL[styleA]}}</div>
      ${{attrs.map(a => `
        <div class="tact-item">
          <div class="tact-label">${{a.label}}</div>
          <div class="tact-bar-wrap"><div class="tact-bar" style="width:${{Math.round(a.keyA/a.max*100)}}%;background:${{colorA}}"></div></div>
          <div class="tact-val">${{(a.keyA).toFixed(2)}}</div>
        </div>`).join('')}}
    </div>
    <div class="tact-card">
      <div class="tact-header" style="color:${{colorB}}">🟡 ${{tB}} — ${{formB}} / ${{STYLE_LABEL[styleB]}}</div>
      ${{attrs.map(a => `
        <div class="tact-item">
          <div class="tact-label">${{a.label}}</div>
          <div class="tact-bar-wrap"><div class="tact-bar" style="width:${{Math.round(a.keyB/a.max*100)}}%;background:${{colorB}}"></div></div>
          <div class="tact-val">${{(a.keyB).toFixed(2)}}</div>
        </div>`).join('')}}
    </div>`;
}}

// ═══════════════════════════════════
// GROUPS
// ═══════════════════════════════════
function renderGroups() {{
  const el = document.getElementById('groupsGrid');
  el.innerHTML = Object.entries(GROUPS).map(([g, teams]) => `
    <div class="group-card" onclick="showGroupMatches('${{g}}')">
      <div class="group-title">GRUPO ${{g}}</div>
      ${{teams.map(t => `<div class="group-team" onclick="event.stopPropagation();selectTeamForMatch('${{t}}')">&nbsp;<span class="rank-dot"></span>&nbsp;${{t}}</div>`).join('')}}
    </div>`).join('');
}}

function selectTeamForMatch(team) {{
  const sA = document.getElementById('teamA');
  const sB = document.getElementById('teamB');
  if (sA.value === team) return;
  if (sB.value !== team) {{
    sA.value = team;
  }} else {{
    sB.value = sA.value;
    sA.value = team;
  }}
  onTeamChange();
  switchTab('grupos', document.querySelector('.tab'));
}}

function showGroupMatches(grp) {{
  const teams = GROUPS[grp];
  const panel = document.getElementById('groupMatchesPanel');
  const list = document.getElementById('groupMatchesList');
  const title = document.getElementById('groupMatchesTitle');
  title.textContent = `Partidos Grupo ${{grp}}`;
  const matches = [];
  for (let i=0;i<teams.length;i++) for (let j=i+1;j<teams.length;j++) matches.push([teams[i],teams[j]]);
  list.innerHTML = matches.map(([a,b]) => {{
    const m = PREDS[a]&&PREDS[a][b];
    if (!m) return '';
    const engA = m.engine_A, engB = m.engine_B;
    const avgV = (engA.p_victoria+engB.p_victoria)/2;
    const avgE = (engA.p_empate+engB.p_empate)/2;
    const avgD = (engA.p_derrota+engB.p_derrota)/2;
    const winner = avgV>avgD&&avgV>avgE ? a : avgD>avgE ? b : 'Empate';
    return `<div style="display:flex;align-items:center;gap:10px;padding:8px;border-bottom:1px solid var(--border);cursor:pointer"
                  onclick="document.getElementById('teamA').value='${{a}}';document.getElementById('teamB').value='${{b}}';onTeamChange()">
      <div style="flex:1;font-size:.82rem;font-weight:600">${{a}}</div>
      <div style="text-align:center;min-width:80px">
        <div style="display:flex;gap:3px;justify-content:center;font-size:.75rem">
          <span style="color:var(--green2)">${{pct(avgV)}}</span>
          <span style="color:var(--gray)">|</span>
          <span style="color:var(--yellow)">${{pct(avgE)}}</span>
          <span style="color:var(--gray)">|</span>
          <span style="color:var(--red2)">${{pct(avgD)}}</span>
        </div>
        <div style="font-size:.65rem;color:var(--gray);margin-top:2px">λ ${{m.lambda_A.toFixed(1)}}-${{m.lambda_B.toFixed(1)}}</div>
      </div>
      <div style="flex:1;text-align:right;font-size:.82rem;font-weight:600">${{b}}</div>
    </div>`;
  }}).join('');
  panel.style.display = 'block';
}}

// ═══════════════════════════════════
// STATS
// ═══════════════════════════════════
function renderStats(tA, tB) {{
  const sA = TEAM_STATS[tA] || [50,70,100,26];
  const sB = TEAM_STATS[tB] || [50,70,100,26];
  const items = [
    {{label:'Ranking FIFA',a:sA[0],b:sB[0],lower_better:true}},
    {{label:'Rating Plantilla',a:sA[1],b:sB[1],lower_better:false}},
    {{label:'Valor Mercado (M€)',a:sA[2],b:sB[2],lower_better:false}},
    {{label:'Edad Promedio',a:sA[3],b:sB[3],lower_better:false}},
  ];
  document.getElementById('statGrid').innerHTML = items.map(item => {{
    const total = item.a + item.b || 1;
    let pA = item.a/total, pB = item.b/total;
    if (item.lower_better) {{ pA = 1-pA; pB = 1-pB; const s=pA+pB; pA/=s; pB/=s; }}
    return `<div class="stat-row">
      <div class="stat-label">${{item.label}}</div>
      <div class="stat-compare">
        <div class="stat-val-a">${{item.a}}</div>
        <div class="stat-bar-dual">
          <div class="stat-bar-a" style="width:${{Math.round(pA*100)}}%"></div>
          <div class="stat-bar-b" style="width:${{Math.round(pB*100)}}%"></div>
        </div>
        <div class="stat-val-b">${{item.b}}</div>
      </div>
    </div>`;
  }}).join('');
}}

// ═══════════════════════════════════
// FEATURES
// ═══════════════════════════════════
function renderFeatureImportance() {{
  const maxVal = FEATURE_IMPORTANCE[0].v;
  document.getElementById('featureList').innerHTML = FEATURE_IMPORTANCE.map(fi => `
    <div class="fi-item">
      <div class="fi-name">${{fi.f}}${{fi.new_?' <span style="color:var(--green2);font-size:.6rem">✦NEW</span>':''}}</div>
      <div class="fi-bar" style="width:${{Math.round(fi.v/maxVal*200)}}px;background:${{fi.new_?'var(--green)':'var(--blue)'}}"></div>
      <div class="fi-pct">${{(fi.v*100).toFixed(2)}}%</div>
    </div>`).join('');
}}

// ═══════════════════════════════════
// TABS
// ═══════════════════════════════════
function switchTab(id, el) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  if (el) el.classList.add('active');
  else document.querySelectorAll('.tab')[0].classList.add('active');
  document.getElementById('tab-'+id).classList.add('active');
}}

// ═══════════════════════════════════
// UTILS
// ═══════════════════════════════════
function pct(v) {{ return Math.round(v*100)+'%'; }}
</script>
</body>
</html>"""

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"index.html generado: {len(html)} bytes ({len(html)//1024}KB)")
