import json

with open('predicciones_v3_compact.json') as f:
    preds_raw = f.read()

with open('lineup_config.json') as f:
    lineup_cfg = json.load(f)

lineup_js = json.dumps(lineup_cfg["LINEUP"], ensure_ascii=False)
formation_js = json.dumps(lineup_cfg["FORMATION_FEATURES"], ensure_ascii=False)
style_js = json.dumps(lineup_cfg["STYLE_SCORE"], ensure_ascii=False)

try:
    with open('predicciones_historial.json', encoding='utf-8') as f:
        historial_raw = f.read()
except FileNotFoundError:
    historial_raw = '{"generated":"","accuracy":{"engine_A":{"correct":0,"total":0},"engine_B":{"correct":0,"total":0}},"entries":[]}'

try:
    with open('fixtures.json', encoding='utf-8') as f:
        fixtures_raw = f.read()
except FileNotFoundError:
    fixtures_raw = '{"schedule":[]}'

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
<title>Mundial FIFA 2026 | Dual Engine AI</title>
<style>
:root{{
  --bg:#f0f2f5;--surface:#ffffff;--surface2:#f8f9fa;--border:#e2e8f0;
  --text:#1e293b;--text2:#475569;--text3:#94a3b8;
  --blue:#2563eb;--blue-light:#dbeafe;--blue-mid:#93c5fd;
  --yellow:#d97706;--yellow-light:#fef3c7;--yellow-mid:#fcd34d;
  --green:#059669;--green-light:#d1fae5;--green-mid:#6ee7b7;
  --red:#dc2626;--red-light:#fee2e2;--red-mid:#fca5a5;
  --purple:#7c3aed;--purple-light:#ede9fe;
  --eng-a:#2563eb;--eng-b:#d97706;
  --shadow:0 1px 3px rgba(0,0,0,.08),0 1px 2px rgba(0,0,0,.04);
  --shadow-md:0 4px 6px rgba(0,0,0,.07),0 2px 4px rgba(0,0,0,.05);
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh;line-height:1.5}}

/* ── Sticky Top Bar ── */
.topbar{{
  position:sticky;top:0;z-index:100;
  background:#ffffff;border-bottom:1px solid var(--border);
  padding:10px 20px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;
  box-shadow:var(--shadow-md);
}}
.topbar h1{{font-size:1.05rem;font-weight:800;color:var(--text);letter-spacing:-.01em;flex:1;min-width:200px}}
.topbar-badges{{display:flex;gap:6px;flex-wrap:wrap}}
.tbadge{{font-size:.62rem;font-weight:700;padding:2px 8px;border-radius:20px;border:1px solid}}
.tbadge.a{{border-color:var(--blue-mid);color:var(--blue);background:var(--blue-light)}}
.tbadge.b{{border-color:var(--yellow-mid);color:var(--yellow);background:var(--yellow-light)}}
.tbadge.g{{border-color:var(--green-mid);color:var(--green);background:var(--green-light)}}
.btn-analyze{{
  background:var(--blue);color:#fff;border:none;
  padding:9px 18px;border-radius:8px;font-size:.85rem;font-weight:700;
  cursor:pointer;display:flex;align-items:center;gap:6px;
  transition:background .18s,transform .1s;white-space:nowrap;
  box-shadow:0 2px 4px rgba(37,99,235,.3);
}}
.btn-analyze:hover{{background:#1d4ed8;transform:translateY(-1px)}}
.btn-analyze:active{{transform:translateY(0)}}
.btn-analyze.loading{{background:#64748b;cursor:not-allowed;transform:none}}

/* ── Layout ── */
.container{{max-width:1200px;margin:0 auto;padding:16px 12px}}

/* ── Cards ── */
.card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:14px;box-shadow:var(--shadow)}}
.card-title{{font-size:.72rem;color:var(--text3);margin-bottom:12px;text-transform:uppercase;letter-spacing:.07em;font-weight:700;display:flex;align-items:center;gap:6px}}

/* ── Team Selectors ── */
.team-col{{display:flex;flex-direction:column;gap:8px}}
label.lbl{{font-size:.7rem;color:var(--text2);text-transform:uppercase;letter-spacing:.05em;font-weight:600}}
select{{
  width:100%;background:#fff;color:var(--text);
  border:1px solid var(--border);padding:9px 12px;border-radius:8px;
  font-size:.9rem;cursor:pointer;appearance:none;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:right 10px center;
  box-shadow:var(--shadow);
}}
select:focus{{outline:none;border-color:var(--blue);box-shadow:0 0 0 3px rgba(37,99,235,.15)}}
.vs-divider{{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0 8px}}
.vs-text{{font-size:1.4rem;font-weight:900;color:var(--text3);line-height:1}}
.vs-sub{{font-size:.6rem;color:var(--text3);margin-top:4px;text-align:center}}
.swap-btn{{
  background:var(--surface2);border:1px solid var(--border);color:var(--text2);
  width:34px;height:34px;border-radius:8px;cursor:pointer;font-size:1rem;
  display:flex;align-items:center;justify-content:center;margin-top:6px;
  transition:all .18s;
}}
.swap-btn:hover{{border-color:var(--blue);color:var(--blue);background:var(--blue-light)}}

/* ── Formation / Style chips ── */
.form-row{{display:flex;gap:5px;flex-wrap:wrap;margin-top:4px}}
.form-chip{{
  font-size:.67rem;padding:3px 8px;border-radius:6px;cursor:pointer;
  border:1px solid var(--border);color:var(--text2);background:var(--surface2);
  transition:all .15s;
}}
.form-chip:hover{{border-color:var(--blue);color:var(--blue);background:var(--blue-light)}}
.form-chip.active{{background:var(--blue);border-color:var(--blue);color:#fff;font-weight:700}}
.style-row{{display:flex;gap:5px;margin-top:6px}}
.style-chip{{
  font-size:.67rem;padding:3px 10px;border-radius:6px;cursor:pointer;
  border:1px solid var(--border);color:var(--text2);background:var(--surface2);
  transition:all .15s;flex:1;text-align:center;
}}
.style-chip:hover{{border-color:var(--green);color:var(--green)}}
.style-chip.active.atk{{background:#dc2626;border-color:#dc2626;color:#fff;font-weight:700}}
.style-chip.active.bal{{background:var(--blue);border-color:var(--blue);color:#fff;font-weight:700}}
.style-chip.active.def{{background:#475569;border-color:#475569;color:#fff;font-weight:700}}
.style-chip.active.ctr{{background:var(--purple);border-color:var(--purple);color:#fff;font-weight:700}}
.lineup-badge{{font-size:.67rem;padding:2px 7px;border-radius:5px;display:inline-block;margin-top:4px;border:1px solid}}
.lineup-badge.atk{{background:var(--red-light);border-color:var(--red-mid);color:var(--red)}}
.lineup-badge.bal{{background:var(--blue-light);border-color:var(--blue-mid);color:var(--blue)}}
.lineup-badge.def{{background:#f1f5f9;border-color:#cbd5e1;color:#475569}}
.lineup-badge.ctr{{background:var(--purple-light);border-color:#c4b5fd;color:var(--purple)}}
.lineup-badge.tag-form{{background:var(--blue-light);border-color:var(--blue-mid);color:var(--blue)}}

/* ── Consensus box ── */
.consensus-box{{
  border-radius:10px;padding:10px 14px;display:flex;align-items:center;gap:10px;
  margin-bottom:14px;border:1px solid;
}}
.consensus-box.agree{{background:#f0fdf4;border-color:#bbf7d0}}
.consensus-box.disagree{{background:#fffbeb;border-color:var(--yellow-mid)}}
.consensus-box.split{{background:var(--purple-light);border-color:#c4b5fd}}
.consensus-icon{{font-size:1.4rem}}
.consensus-text .title{{font-size:.82rem;font-weight:700;color:var(--text)}}
.consensus-text .sub{{font-size:.72rem;color:var(--text2)}}

/* ── Engines row (simultaneous display) ── */
.engines-row{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}}
.engine-panel{{border-radius:10px;padding:14px;border:2px solid}}
.engine-panel.ep-a{{border-color:#93c5fd;background:#f0f7ff}}
.engine-panel.ep-b{{border-color:#fcd34d;background:#fffbf0}}
.engine-label{{font-size:.72rem;font-weight:800;text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px;display:flex;align-items:center;gap:6px}}
.engine-label.la{{color:var(--blue)}}
.engine-label.lb{{color:var(--yellow)}}
.engine-dot{{width:8px;height:8px;border-radius:50%;display:inline-block}}
.dot-a{{background:var(--blue)}} .dot-b{{background:var(--yellow)}}

/* ── Mini probabilities (inside engine panel) ── */
.mini-probs{{display:flex;gap:6px;margin-bottom:8px}}
.mini-p{{flex:1;text-align:center;padding:8px 4px;border-radius:8px;background:rgba(0,0,0,.04)}}
.mini-pct{{font-size:1.3rem;font-weight:800}}
.mini-lbl{{font-size:.6rem;color:var(--text2);text-transform:uppercase;margin-top:2px}}
.mp-win .mini-pct{{color:var(--green)}}
.mp-draw .mini-pct{{color:var(--yellow)}}
.mp-loss .mini-pct{{color:var(--red)}}

/* ── Prob bar ── */
.pbar{{height:8px;border-radius:5px;display:flex;overflow:hidden;background:var(--border)}}
.pb-w{{background:linear-gradient(90deg,#059669,#34d399);transition:width .5s}}
.pb-d{{background:linear-gradient(90deg,#b45309,#fcd34d);transition:width .5s}}
.pb-l{{background:linear-gradient(90deg,#dc2626,#fca5a5);transition:width .5s}}
.pbar-labels{{display:flex;justify-content:space-between;font-size:.67rem;margin-top:4px;color:var(--text2)}}

/* ── Score / Goals display ── */
.score-display{{display:flex;align-items:center;justify-content:center;gap:14px;padding:12px 0 6px;border-top:1px solid var(--border);margin-top:8px}}
.score-side{{text-align:center;flex:1}}
.score-num{{font-size:2.4rem;font-weight:900;color:var(--text);line-height:1}}
.score-name{{font-size:.72rem;color:var(--text2);margin-top:4px}}
.score-lambda{{font-size:.65rem;color:var(--text3);margin-top:2px}}
.score-colon{{font-size:2rem;color:var(--text3);font-weight:300}}

/* ── Verdict ── */
#verdict{{border-radius:10px;padding:12px 16px;font-size:.85rem;line-height:1.6;margin-top:2px}}
.verd-win{{background:#f0fdf4;border:1px solid #bbf7d0;color:var(--text)}}
.verd-draw{{background:#fffbeb;border:1px solid var(--yellow-mid);color:var(--text)}}
.verd-loss{{background:var(--red-light);border:1px solid var(--red-mid);color:var(--text)}}

/* ── Tactics ── */
.tact-row{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.tact-card{{background:var(--surface2);border-radius:10px;padding:14px;border:1px solid var(--border)}}
.tact-header{{font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:10px;font-weight:700}}
.tact-item{{display:flex;align-items:center;gap:8px;margin-bottom:6px}}
.tact-label{{font-size:.7rem;color:var(--text2);width:70px;flex-shrink:0}}
.tact-bar-wrap{{flex:1;background:var(--border);border-radius:4px;height:7px;overflow:hidden}}
.tact-bar{{height:100%;border-radius:4px;transition:width .4s}}
.tact-val{{font-size:.7rem;color:var(--text);width:32px;text-align:right;font-weight:600}}

/* ── Groups ── */
.groups-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}
.group-card{{background:var(--surface2);border-radius:8px;padding:10px;border:1px solid var(--border);cursor:pointer;transition:all .18s}}
.group-card:hover{{border-color:var(--blue);box-shadow:var(--shadow-md);transform:translateY(-1px)}}
.group-title{{font-size:.72rem;font-weight:800;color:var(--blue);margin-bottom:6px;letter-spacing:.05em}}
.group-team{{font-size:.72rem;padding:3px 6px;margin-bottom:3px;border-radius:4px;cursor:pointer;transition:all .15s;display:flex;align-items:center;gap:5px;color:var(--text2)}}
.group-team:hover{{background:var(--blue-light);color:var(--blue)}}
.rank-dot{{width:5px;height:5px;border-radius:50%;background:var(--green);flex-shrink:0}}

/* ── Stats ── */
.stat-grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.stat-row{{background:var(--surface2);border-radius:8px;padding:10px 12px;border:1px solid var(--border)}}
.stat-label{{font-size:.7rem;color:var(--text3);margin-bottom:6px;text-transform:uppercase;letter-spacing:.04em;font-weight:600}}
.stat-compare{{display:flex;align-items:center;gap:8px}}
.stat-val-a{{text-align:right;font-size:.88rem;font-weight:700;color:var(--blue);width:50px}}
.stat-val-b{{text-align:left;font-size:.88rem;font-weight:700;color:var(--yellow);width:50px}}
.stat-bar-dual{{flex:1;height:7px;border-radius:4px;background:var(--border);display:flex;overflow:hidden}}
.stat-bar-a{{background:var(--blue);border-radius:4px 0 0 4px;transition:width .4s}}
.stat-bar-b{{background:var(--yellow);border-radius:0 4px 4px 0;transition:width .4s}}

/* ── Feature importance ── */
.fi-item{{display:flex;align-items:center;gap:8px;margin-bottom:5px}}
.fi-name{{font-size:.7rem;color:var(--text);width:180px;flex-shrink:0}}
.fi-bar{{height:9px;border-radius:5px;transition:width .4s}}
.fi-pct{{font-size:.67rem;color:var(--text2);width:36px;text-align:right}}

/* ── Tabs ── */
.tabs{{display:flex;border-bottom:1px solid var(--border);margin-bottom:14px;overflow-x:auto}}
.tab{{padding:8px 16px;cursor:pointer;font-size:.8rem;color:var(--text2);border-bottom:2px solid transparent;white-space:nowrap;flex-shrink:0;transition:all .18s}}
.tab:hover{{color:var(--text)}}
.tab.active{{color:var(--blue);border-color:var(--blue);font-weight:600}}
.tab-pane{{display:none}} .tab-pane.active{{display:block}}

/* ── Util ── */
.divider{{height:1px;background:var(--border);margin:12px 0}}
.mt8{{margin-top:8px}} .mt12{{margin-top:12px}}
.flex{{display:flex}} .gap8{{gap:8px}} .items-center{{align-items:center}} .flex-wrap{{flex-wrap:wrap}}
.text-center{{text-align:center}}

/* ── Group match rows with result ── */
.gm-match{{border-bottom:1px solid var(--border);transition:background .15s}}
.gm-match:last-child{{border-bottom:none}}
.gm-match:hover{{background:var(--surface2)}}
.gm-match.gm-played{{cursor:default}}
.gm-header{{display:flex;align-items:center;gap:10px;padding:8px 6px;cursor:pointer}}
.gm-vs{{font-size:.72rem;font-weight:700;color:var(--text3);min-width:90px;text-align:center;padding:2px 6px;background:var(--surface2);border-radius:5px}}
.gm-result{{background:var(--surface2);border-top:1px solid var(--border);padding:10px 12px;display:grid;grid-template-columns:auto 1fr;align-items:center;gap:12px}}
.gm-scorebox{{text-align:center}}
.gm-score{{font-size:1.5rem;font-weight:900;color:var(--text);line-height:1}}
.gm-score-lbl{{font-size:.6rem;color:var(--text3);margin-top:2px;text-transform:uppercase;letter-spacing:.04em}}
.gm-preds{{display:flex;flex-direction:column;gap:5px}}
.gm-pred-row{{display:flex;align-items:center;gap:6px}}
.gm-eng{{font-size:.6rem;font-weight:800;padding:1px 5px;border-radius:4px;min-width:22px;text-align:center}}
.gm-eng.la{{background:var(--blue-light);color:var(--blue)}} .gm-eng.lb{{background:var(--yellow-light);color:var(--yellow)}}
.gm-pred-bar{{flex:1;height:6px;border-radius:3px;display:flex;overflow:hidden}}
.gm-pb-w{{background:var(--green)}} .gm-pb-d{{background:var(--yellow)}} .gm-pb-l{{background:var(--red)}}
.gm-pred-lbl{{font-size:.67rem;color:var(--text2);min-width:80px}}

/* ── Historial cards ── */
.hc-grid{{display:flex;flex-direction:column;gap:10px}}
.hc{{background:var(--surface2);border:1px solid var(--border);border-radius:10px;overflow:hidden}}
.hc-top{{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;padding:10px 14px;gap:10px;border-bottom:1px solid var(--border);background:var(--surface)}}
.hc-team-a{{font-size:.85rem;font-weight:700;color:var(--text)}}
.hc-team-b{{font-size:.85rem;font-weight:700;color:var(--text);text-align:right}}
.hc-center{{text-align:center}}
.hc-score{{font-size:1.4rem;font-weight:900;color:var(--text);line-height:1}}
.hc-date-grp{{font-size:.62rem;color:var(--text3);margin-top:1px}}
.hc-result-badge{{display:inline-block;padding:2px 8px;border-radius:5px;font-size:.67rem;font-weight:700;border:1px solid;margin-top:3px}}
.hc-result-badge.victoria_A{{background:var(--green-light);border-color:var(--green-mid);color:var(--green)}}
.hc-result-badge.victoria_B{{background:var(--red-light);border-color:var(--red-mid);color:var(--red)}}
.hc-result-badge.empate{{background:var(--yellow-light);border-color:var(--yellow-mid);color:var(--yellow)}}
.hc-body{{padding:10px 14px;display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.hc-eng-block{{display:flex;flex-direction:column;gap:4px}}
.hc-eng-title{{font-size:.65rem;font-weight:800;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px}}
.hc-eng-title.la{{color:var(--blue)}} .hc-eng-title.lb{{color:var(--yellow)}}
.hc-pbar{{height:7px;border-radius:4px;display:flex;overflow:hidden;margin-bottom:2px}}
.hc-pb-w{{background:var(--green)}} .hc-pb-d{{background:var(--yellow)}} .hc-pb-l{{background:var(--red)}}
.hc-pbar-vals{{display:flex;justify-content:space-between;font-size:.6rem;color:var(--text3)}}
.hc-verdict{{display:flex;align-items:center;gap:6px;margin-top:2px}}
.hc-ok{{width:18px;height:18px;border-radius:50%;font-size:.67rem;font-weight:800;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0}}
.hc-ok.yes{{background:var(--green-light);color:var(--green)}} .hc-ok.no{{background:var(--red-light);color:var(--red)}}
.hc-pred-txt{{font-size:.7rem;color:var(--text2)}}

/* ── Pronósticos del día ── */
.pron-date-header{{font-size:.78rem;font-weight:700;color:var(--text2);margin-bottom:10px;display:flex;align-items:center;gap:8px}}
.pron-badge{{font-size:.6rem;padding:2px 7px;border-radius:10px;background:var(--blue-light);color:var(--blue);border:1px solid var(--blue-mid);font-weight:700}}
.pron-grid{{display:flex;flex-direction:column;gap:8px}}
.pron-card{{background:var(--surface2);border:1px solid var(--border);border-radius:10px;overflow:hidden}}
.pron-card.pron-played{{border-color:var(--green-mid);background:#f0fdf4}}
.pron-header{{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;padding:9px 14px;gap:10px;background:var(--surface);border-bottom:1px solid var(--border)}}
.pron-team-a{{font-size:.85rem;font-weight:700;color:var(--text)}}
.pron-team-b{{font-size:.85rem;font-weight:700;color:var(--text);text-align:right}}
.pron-center{{text-align:center}}
.pron-grupo{{font-size:.6rem;color:var(--text3);text-transform:uppercase;letter-spacing:.05em}}
.pron-vs{{font-size:.72rem;font-weight:700;color:var(--text3)}}
.pron-score{{font-size:1.3rem;font-weight:900;color:var(--text);line-height:1}}
.pron-body{{padding:10px 14px;display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.pron-eng-block{{display:flex;flex-direction:column;gap:3px}}
.pron-eng-title{{font-size:.65rem;font-weight:800;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px}}
.pron-eng-title.la{{color:var(--blue)}} .pron-eng-title.lb{{color:var(--yellow)}}
.pron-pbar{{height:7px;border-radius:4px;display:flex;overflow:hidden;margin-bottom:2px}}
.pron-pb-w{{background:var(--green)}} .pron-pb-d{{background:var(--yellow)}} .pron-pb-l{{background:var(--red)}}
.pron-pbar-vals{{display:flex;justify-content:space-between;font-size:.6rem;color:var(--text3)}}
.pron-pred-chip{{display:inline-block;padding:2px 7px;border-radius:5px;font-size:.67rem;font-weight:700;border:1px solid;margin-top:2px}}
.pron-pred-chip.victoria_A{{background:var(--green-light);border-color:var(--green-mid);color:var(--green)}}
.pron-pred-chip.victoria_B{{background:var(--red-light);border-color:var(--red-mid);color:var(--red)}}
.pron-pred-chip.empate{{background:var(--yellow-light);border-color:var(--yellow-mid);color:var(--yellow)}}
.pron-played-chip{{display:inline-flex;align-items:center;gap:4px;font-size:.62rem;padding:1px 6px;border-radius:5px;background:var(--green-light);color:var(--green);border:1px solid var(--green-mid);font-weight:700}}
.pron-goal-pred{{font-size:.72rem;font-weight:800;color:var(--blue);margin-top:2px;letter-spacing:.02em}}
.pron-goal-footer{{padding:6px 14px 8px;border-top:1px solid var(--border);display:flex;align-items:center;gap:6px;flex-wrap:wrap;justify-content:center}}
.pron-lambda-chip{{font-size:.62rem;color:var(--text2);background:var(--surface);border:1px solid var(--border);border-radius:4px;padding:2px 7px}}
.pron-lambda-sep{{color:var(--text3);font-size:.7rem}}

/* ── Historial de Predicciones ── */
.hist-acc-grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px}}
.hist-acc-box{{border-radius:8px;padding:10px 14px;border:1px solid}}
.hist-acc-box.eng-a{{background:var(--blue-light);border-color:var(--blue-mid)}}
.hist-acc-box.eng-b{{background:var(--yellow-light);border-color:var(--yellow-mid)}}
.hist-acc-label{{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px}}
.hist-acc-label.la{{color:var(--blue)}} .hist-acc-label.lb{{color:var(--yellow)}}
.hist-acc-num{{font-size:1.6rem;font-weight:900;color:var(--text);line-height:1}}
.hist-acc-sub{{font-size:.68rem;color:var(--text2);margin-top:2px}}
.hist-table{{width:100%;border-collapse:collapse;font-size:.75rem}}
.hist-table th{{padding:6px 8px;text-align:left;font-size:.65rem;text-transform:uppercase;letter-spacing:.05em;color:var(--text3);border-bottom:2px solid var(--border);font-weight:700}}
.hist-table td{{padding:7px 8px;border-bottom:1px solid var(--border);vertical-align:middle}}
.hist-table tr:last-child td{{border-bottom:none}}
.hist-table tr:hover td{{background:var(--surface2)}}
.hist-pred{{display:inline-block;padding:2px 7px;border-radius:5px;font-size:.67rem;font-weight:700;border:1px solid}}
.hist-pred.victoria_A{{background:var(--green-light);border-color:var(--green-mid);color:var(--green)}}
.hist-pred.victoria_B{{background:var(--red-light);border-color:var(--red-mid);color:var(--red)}}
.hist-pred.empate{{background:var(--yellow-light);border-color:var(--yellow-mid);color:var(--yellow)}}
.hist-real{{font-weight:700;color:var(--text)}}
.hist-ok{{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:50%;font-size:.75rem;font-weight:800}}
.hist-ok.yes{{background:var(--green-light);color:var(--green)}} .hist-ok.no{{background:var(--red-light);color:var(--red)}}
.hist-empty{{text-align:center;padding:24px;color:var(--text3);font-size:.82rem}}
.hist-score{{font-weight:800;color:var(--text);white-space:nowrap}}
.hist-date{{color:var(--text3);font-size:.68rem;white-space:nowrap}}

@media(max-width:860px){{
  .engines-row,.tact-row,.groups-grid{{grid-template-columns:1fr}}
  .groups-grid{{grid-template-columns:repeat(2,1fr)}}
  .stat-grid{{grid-template-columns:1fr}}
  .topbar{{flex-direction:column;align-items:flex-start;gap:8px}}
  .topbar h1{{font-size:.95rem}}
}}
</style>
</head>
<body>

<!-- STICKY TOP BAR -->
<div class="topbar">
  <h1>Mundial FIFA 2026 | Dual Engine AI</h1>
  <div class="topbar-badges">
    <span class="tbadge a">Engine A · MLP+Atención</span>
    <span class="tbadge b">Engine B · XGBoost</span>
    <span class="tbadge g">74 features · T=0.55</span>
  </div>
  <button class="btn-analyze" id="analyzeBtn" onclick="runAnalysis()">⚡ Analizar Partido</button>
</div>

<div class="container">

<!-- PRONÓSTICOS DEL DÍA -->
<div class="card">
  <div class="card-title">🗓️ Pronósticos del Día &nbsp;<span id="fechaHoyLabel" style="font-weight:400;color:var(--text2);text-transform:none;letter-spacing:0"></span></div>
  <div id="pronosticosHoy"></div>
</div>

<!-- CONFIGURADOR DE PARTIDO -->
<div class="card">
  <div class="card-title">⚽ Configurar Partido &amp; Alineaciones</div>
  <div style="display:grid;grid-template-columns:1fr auto 1fr;gap:12px;align-items:start">

    <!-- TEAM A -->
    <div class="team-col">
      <label class="lbl">Equipo A</label>
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
      <label class="lbl">Equipo B</label>
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

  <!-- CONSENSUS -->
  <div id="consensusBox" class="consensus-box agree">
    <div class="consensus-icon" id="consensusIcon">✅</div>
    <div class="consensus-text">
      <div class="title" id="consensusTitle">Ambos engines coinciden</div>
      <div class="sub" id="consensusSub">Alta confianza en el resultado</div>
    </div>
  </div>

  <!-- ENGINES ROW (simultaneous) -->
  <div class="engines-row">
    <!-- Engine A -->
    <div class="engine-panel ep-a">
      <div class="engine-label la"><span class="engine-dot dot-a"></span>Engine A — Deep MLP + Self-Attention</div>
      <div class="mini-probs" id="probsA">
        <div class="mini-p mp-win"><div class="mini-pct" id="aVic">—</div><div class="mini-lbl" id="aLblA">A</div></div>
        <div class="mini-p mp-draw"><div class="mini-pct" id="aEmp">—</div><div class="mini-lbl">Empate</div></div>
        <div class="mini-p mp-loss"><div class="mini-pct" id="aDer">—</div><div class="mini-lbl" id="aLblB">B</div></div>
      </div>
      <div class="pbar" id="pbarA"><div class="pb-w" id="pbarAw" style="width:33%"></div><div class="pb-d" id="pbarAd" style="width:34%"></div><div class="pb-l" id="pbarAl" style="width:33%"></div></div>
      <div class="pbar-labels"><span id="lblAw" style="color:var(--green)">33%</span><span>Empate 34%</span><span id="lblAl" style="color:var(--red)">33%</span></div>
      <div class="score-display">
        <div class="score-side"><div class="score-num" id="aGoalA">—</div><div class="score-name" id="aNameA">A</div><div class="score-lambda">goles (discreto)</div></div>
        <div class="score-colon">:</div>
        <div class="score-side"><div class="score-num" id="aGoalB">—</div><div class="score-name" id="aNameB">B</div><div class="score-lambda">goles (discreto)</div></div>
      </div>
    </div>
    <!-- Engine B -->
    <div class="engine-panel ep-b">
      <div class="engine-label lb"><span class="engine-dot dot-b"></span>Engine B — XGBoost Agresivo</div>
      <div class="mini-probs" id="probsB">
        <div class="mini-p mp-win"><div class="mini-pct" id="bVic">—</div><div class="mini-lbl" id="bLblA">A</div></div>
        <div class="mini-p mp-draw"><div class="mini-pct" id="bEmp">—</div><div class="mini-lbl">Empate</div></div>
        <div class="mini-p mp-loss"><div class="mini-pct" id="bDer">—</div><div class="mini-lbl" id="bLblB">B</div></div>
      </div>
      <div class="pbar" id="pbarB"><div class="pb-w" id="pbarBw" style="width:33%"></div><div class="pb-d" id="pbarBd" style="width:34%"></div><div class="pb-l" id="pbarBl" style="width:33%"></div></div>
      <div class="pbar-labels"><span id="lblBw" style="color:var(--green)">33%</span><span>Empate 34%</span><span id="lblBl" style="color:var(--red)">33%</span></div>
      <div class="score-display">
        <div class="score-side"><div class="score-num" id="bGoalA">—</div><div class="score-name" id="bNameA">A</div><div class="score-lambda">goles (discreto)</div></div>
        <div class="score-colon">:</div>
        <div class="score-side"><div class="score-num" id="bGoalB">—</div><div class="score-name" id="bNameB">B</div><div class="score-lambda">goles (discreto)</div></div>
      </div>
    </div>
  </div>

  <!-- VERDICT (full width) -->
  <div id="verdict" class="verd-win">Selecciona dos equipos y pulsa ⚡ Analizar Partido.</div>
</div>

<!-- ANÁLISIS TÁCTICO -->
<div class="card">
  <div class="card-title">⚙️ Análisis Táctico Comparativo</div>
  <div class="tact-row" id="tactRow"></div>
</div>

<!-- TABS -->
<div class="card">
  <div class="tabs">
    <div class="tab active" onclick="switchTab('grupos',this)">🏟️ Grupos</div>
    <div class="tab" onclick="switchTab('stats',this)">📊 Comparativa</div>
    <div class="tab" onclick="switchTab('features',this)">🔬 Features</div>
    <div class="tab" onclick="switchTab('info',this)">ℹ️ Modelo</div>
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
    <div style="font-size:.78rem;color:var(--text2);margin-bottom:10px">
      Comparativa entre equipos seleccionados · <span style="color:var(--blue);font-weight:600">Azul = Equipo A</span> · <span style="color:var(--yellow);font-weight:600">Naranja = Equipo B</span>
    </div>
    <div class="stat-grid" id="statGrid"></div>
  </div>

  <!-- FEATURES -->
  <div class="tab-pane" id="tab-features">
    <div style="color:var(--text2);font-size:.77rem;margin-bottom:12px">Importancia de features — Engine B (XGBoost). <span style="color:var(--green);font-weight:600">✦ Nuevas features v3</span></div>
    <div id="featureList"></div>
  </div>

  <!-- INFO -->
  <div class="tab-pane" id="tab-info">
    <div style="font-size:.84rem;color:var(--text2);line-height:1.8">
      <div style="margin-bottom:10px"><strong style="color:var(--text)">Modelo v3 — Cambios vs v2</strong></div>
      <ul style="margin-left:16px;display:flex;flex-direction:column;gap:6px">
        <li><span style="color:var(--green)">✓</span> <strong>Alineaciones tácticas</strong>: formación (9 esquemas) + estilo de juego por equipo</li>
        <li><span style="color:var(--green)">✓</span> <strong>Engine A</strong>: Deep MLP (512→256→128→64→32) + Self-Attention 4 cabezas, implementado en sklearn/numpy</li>
        <li><span style="color:var(--green)">✓</span> <strong>Engine B</strong>: XGBoost agresivo calibrado con temperatura T=0.55 para predicciones más decisivas</li>
        <li><span style="color:var(--green)">✓</span> <strong>74 features</strong> vs 35 en v2: tácticas, experiencia confederación WC, interacciones cruzadas ataque×defensa</li>
        <li><span style="color:var(--green)">✓</span> <strong>Goles discretos</strong>: resultado redondeado al entero más cercano (0-5)</li>
        <li><span style="color:var(--green)">✓</span> <strong>Variables de experto eliminadas</strong>: injury_factor, is_host, xg_qual</li>
      </ul>
      <div class="divider"></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:.8rem">
        <div style="background:var(--blue-light);border-radius:8px;padding:10px;border:1px solid var(--blue-mid)">
          <div style="color:var(--blue);font-weight:700;margin-bottom:4px">Engine A — MLP + Self-Attention</div>
          <div>• Capas: 512→256→128→64→32</div>
          <div>• Self-Attention: 4 heads, T=0.45</div>
          <div>• Acc=0.591 | F1=0.525 | AUC=0.642</div>
        </div>
        <div style="background:var(--yellow-light);border-radius:8px;padding:10px;border:1px solid var(--yellow-mid)">
          <div style="color:var(--yellow);font-weight:700;margin-bottom:4px">Engine B — XGBoost Agresivo</div>
          <div>• depth=5 | n_est=300 | lr=0.07</div>
          <div>• min_child_w=3 | gamma=0.20</div>
          <div>• Acc=0.545 | F1=0.535 | AUC=0.711</div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- HISTORIAL DE PREDICCIONES -->
<div class="card" id="historialCard">
  <div class="card-title">📊 Predicciones vs Resultados Reales</div>
  <div class="hist-acc-grid" id="histAccGrid"></div>
  <div class="hc-grid" id="historialList"></div>
</div>

</div><!-- /container -->

<script>
// ═══════════════════════════════
// DATA
// ═══════════════════════════════
const PREDS = {preds_raw};
const LINEUP_DEFAULT = {lineup_js};
const FORMATION_FEATURES = {formation_js};
const STYLE_SCORE = {style_js};
const GROUPS = {groups_js};
const HISTORIAL = {historial_raw};
const FIXTURES = {fixtures_raw};

// Build fast lookup for played matches
const HIST_LOOKUP = {{}};
for (const e of (HISTORIAL.entries||[])) {{
  HIST_LOOKUP[e.teamA+'|'+e.teamB] = e;
}}

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

// ═══════════════════════════════
// STATE
// ═══════════════════════════════
let userFormA=null, userStyleA=null, userFormB=null, userStyleB=null;

// ═══════════════════════════════
// INIT
// ═══════════════════════════════
document.addEventListener('DOMContentLoaded', () => {{
  renderGroups();
  renderFeatureImportance();
  onTeamChange();
  renderPronosticosHoy();
  renderHistorial();
}});

// ═══════════════════════════════
// ANALYZE BUTTON
// ═══════════════════════════════
function runAnalysis() {{
  const btn = document.getElementById('analyzeBtn');
  btn.classList.add('loading');
  btn.textContent = 'Analizando...';
  setTimeout(() => {{
    updatePrediction();
    btn.classList.remove('loading');
    btn.innerHTML = '⚡ Analizar Partido';
    document.getElementById('predCard').scrollIntoView({{behavior:'smooth',block:'start'}});
  }}, 200);
}}

// ═══════════════════════════════
// DISCRETE GOALS
// ═══════════════════════════════
function discreteGoals(lambda) {{
  return Math.min(5, Math.max(0, Math.round(lambda)));
}}

// ═══════════════════════════════
// LINEUP CHIPS
// ═══════════════════════════════
function buildFormChips(containerId, team, side) {{
  const def = LINEUP_DEFAULT[team] || {{formation:'4-3-3',style:'balanced'}};
  const current = side==='A' ? (userFormA||def.formation) : (userFormB||def.formation);
  document.getElementById(containerId).innerHTML = FORMATIONS.map(f =>
    `<span class="form-chip${{f===current?' active':''}}" onclick="selectForm('${{side}}','${{f}}')">${{f}}</span>`
  ).join('');
}}

function buildStyleChips(containerId, team, side) {{
  const def = LINEUP_DEFAULT[team] || {{formation:'4-3-3',style:'balanced'}};
  const current = side==='A' ? (userStyleA||def.style) : (userStyleB||def.style);
  document.getElementById(containerId).innerHTML = STYLES.map(s =>
    `<span class="style-chip${{s===current?' active '+STYLE_CLASS[s]:''}}" onclick="selectStyle('${{side}}','${{s}}')">${{STYLE_LABEL[s]}}</span>`
  ).join('');
}}

function renderLineupBadge(side) {{
  const teamName = document.getElementById('team'+side).value;
  const def = LINEUP_DEFAULT[teamName] || {{formation:'4-3-3',style:'balanced'}};
  const form = (side==='A'?userFormA:userFormB)||def.formation;
  const style = (side==='A'?userStyleA:userStyleB)||def.style;
  const cls = STYLE_CLASS[style]||'bal';
  document.getElementById('badge'+side).innerHTML =
    `<span class="lineup-badge tag-form">${{form}}</span> <span class="lineup-badge ${{cls}}">${{STYLE_LABEL[style]}}</span>`;
}}

function selectForm(side, form) {{
  if (side==='A') userFormA=form; else userFormB=form;
  buildFormChips('formRow'+side, document.getElementById('team'+side).value, side);
  renderLineupBadge(side);
  updatePrediction();
}}

function selectStyle(side, style) {{
  if (side==='A') userStyleA=style; else userStyleB=style;
  buildStyleChips('styleRow'+side, document.getElementById('team'+side).value, side);
  renderLineupBadge(side);
  updatePrediction();
}}

// ═══════════════════════════════
// TACTICAL MODIFIER
// ═══════════════════════════════
function computeAttackPow(form, style) {{
  const ff = FORMATION_FEATURES[form]||FORMATION_FEATURES['4-3-3'];
  return ff.attack * (STYLE_SCORE[style]||1.0);
}}

function applyMod(baseP, tA, formA, styleA, tB, formB, styleB) {{
  const dA = LINEUP_DEFAULT[tA]||{{formation:'4-3-3',style:'balanced'}};
  const dB = LINEUP_DEFAULT[tB]||{{formation:'4-3-3',style:'balanced'}};
  const net = (computeAttackPow(formA,styleA)-computeAttackPow(dA.formation,dA.style))
             -(computeAttackPow(formB,styleB)-computeAttackPow(dB.formation,dB.style));
  const shift = net*0.22;
  let v=Math.max(0.01,Math.min(0.97,baseP.p_victoria+shift));
  let d=Math.max(0.01,Math.min(0.97,baseP.p_derrota-shift));
  let e=Math.max(0.01,baseP.p_empate);
  const s=v+e+d;
  return {{p_victoria:v/s,p_empate:e/s,p_derrota:d/s}};
}}

// ═══════════════════════════════
// TEAM CHANGE
// ═══════════════════════════════
function onTeamChange() {{
  const tA=document.getElementById('teamA').value;
  const tB=document.getElementById('teamB').value;
  userFormA=null;userStyleA=null;userFormB=null;userStyleB=null;
  buildFormChips('formRowA',tA,'A'); buildFormChips('formRowB',tB,'B');
  buildStyleChips('styleRowA',tA,'A'); buildStyleChips('styleRowB',tB,'B');
  renderLineupBadge('A'); renderLineupBadge('B');
  updatePrediction();
  renderStats(tA,tB);
}}

function swapTeams() {{
  const sA=document.getElementById('teamA'), sB=document.getElementById('teamB');
  [sA.value,sB.value]=[sB.value,sA.value];
  userFormA=null;userStyleA=null;userFormB=null;userStyleB=null;
  onTeamChange();
}}

// ═══════════════════════════════
// UPDATE PREDICTION
// ═══════════════════════════════
function updatePrediction() {{
  const tA=document.getElementById('teamA').value;
  const tB=document.getElementById('teamB').value;
  if (tA===tB) return;
  const match=PREDS[tA]&&PREDS[tA][tB];
  if (!match) return;

  const dA=LINEUP_DEFAULT[tA]||{{formation:'4-3-3',style:'balanced'}};
  const dB=LINEUP_DEFAULT[tB]||{{formation:'4-3-3',style:'balanced'}};
  const formA=userFormA||dA.formation, styleA=userStyleA||dA.style;
  const formB=userFormB||dB.formation, styleB=userStyleB||dB.style;

  const pA=applyMod(match.engine_A,tA,formA,styleA,tB,formB,styleB);
  const pB=applyMod(match.engine_B,tA,formA,styleA,tB,formB,styleB);
  const lA=match.lambda_A, lB=match.lambda_B;

  renderEngineA(pA,tA,tB,lA,lB);
  renderEngineB(pB,tA,tB,lA,lB);

  const wA=outcome(pA), wB=outcome(pB);
  renderConsensus(wA===wB,wA,wB,tA,tB,pA,pB);
  renderVerdict(pA,pB,tA,tB,lA,lB);
  renderTactics(tA,formA,styleA,tB,formB,styleB);
}}

function outcome(p) {{
  if (p.p_victoria>p.p_derrota&&p.p_victoria>p.p_empate) return 'A';
  if (p.p_derrota>p.p_empate) return 'B';
  return 'E';
}}

// ═══════════════════════════════
// RENDER ENGINE PANELS
// ═══════════════════════════════
function renderEngineA(p,tA,tB,lA,lB) {{
  document.getElementById('aVic').textContent=pct(p.p_victoria);
  document.getElementById('aEmp').textContent=pct(p.p_empate);
  document.getElementById('aDer').textContent=pct(p.p_derrota);
  document.getElementById('aLblA').textContent=tA;
  document.getElementById('aLblB').textContent=tB;
  document.getElementById('pbarAw').style.width=pct(p.p_victoria);
  document.getElementById('pbarAd').style.width=pct(p.p_empate);
  document.getElementById('pbarAl').style.width=pct(p.p_derrota);
  document.getElementById('lblAw').textContent=tA+' '+pct(p.p_victoria);
  document.getElementById('lblAl').textContent=tB+' '+pct(p.p_derrota);
  document.getElementById('aGoalA').textContent=discreteGoals(lA);
  document.getElementById('aGoalB').textContent=discreteGoals(lB);
  document.getElementById('aNameA').textContent=tA;
  document.getElementById('aNameB').textContent=tB;
}}

function renderEngineB(p,tA,tB,lA,lB) {{
  document.getElementById('bVic').textContent=pct(p.p_victoria);
  document.getElementById('bEmp').textContent=pct(p.p_empate);
  document.getElementById('bDer').textContent=pct(p.p_derrota);
  document.getElementById('bLblA').textContent=tA;
  document.getElementById('bLblB').textContent=tB;
  document.getElementById('pbarBw').style.width=pct(p.p_victoria);
  document.getElementById('pbarBd').style.width=pct(p.p_empate);
  document.getElementById('pbarBl').style.width=pct(p.p_derrota);
  document.getElementById('lblBw').textContent=tA+' '+pct(p.p_victoria);
  document.getElementById('lblBl').textContent=tB+' '+pct(p.p_derrota);
  document.getElementById('bGoalA').textContent=discreteGoals(lA);
  document.getElementById('bGoalB').textContent=discreteGoals(lB);
  document.getElementById('bNameA').textContent=tA;
  document.getElementById('bNameB').textContent=tB;
}}

// ═══════════════════════════════
// CONSENSUS
// ═══════════════════════════════
function renderConsensus(agree,wA,wB,tA,tB,pA,pB) {{
  const box=document.getElementById('consensusBox');
  const icon=document.getElementById('consensusIcon');
  const title=document.getElementById('consensusTitle');
  const sub=document.getElementById('consensusSub');
  const label=w=>w==='A'?`Victoria ${{tA}}`:w==='B'?`Victoria ${{tB}}`:'Empate';
  if (agree) {{
    const strong=Math.max(pA.p_victoria,pA.p_derrota)>0.65;
    box.className='consensus-box agree';
    icon.textContent=strong?'✅':'🟢';
    title.textContent=`Ambos engines coinciden: ${{label(wA)}}`;
    sub.textContent=strong?'Alta confianza · Favorito claro':'Resultado esperado con algo de incertidumbre';
  }} else {{
    box.className='consensus-box disagree';
    icon.textContent='⚠️';
    title.textContent='Engines divergen · Partido muy abierto';
    sub.textContent=`Engine A: ${{label(wA)}} · Engine B: ${{label(wB)}}`;
  }}
}}

// ═══════════════════════════════
// VERDICT
// ═══════════════════════════════
function renderVerdict(pA,pB,tA,tB,lA,lB) {{
  const el=document.getElementById('verdict');
  const avgV=(pA.p_victoria+pB.p_victoria)/2;
  const avgE=(pA.p_empate+pB.p_empate)/2;
  const avgD=(pA.p_derrota+pB.p_derrota)/2;
  const gA=discreteGoals(lA), gB=discreteGoals(lB);
  let cls,text;
  if (avgV>avgD&&avgV>avgE) {{
    cls='verd-win';
    const conf=avgV>0.75?'con alta confianza':avgV>0.55?'como favorito':'como leve favorito';
    text=`🏆 <strong>${{tA}}</strong> se proyecta ${{conf}} (promedio engines: ${{pct(avgV)}}). Resultado estimado: <strong>${{tA}} ${{gA}} — ${{tB}} ${{gB}}</strong>.`;
  }} else if (avgD>avgV&&avgD>avgE) {{
    cls='verd-loss';
    const conf=avgD>0.75?'con alta confianza':'como favorito';
    text=`🏆 <strong>${{tB}}</strong> se proyecta ${{conf}} (promedio engines: ${{pct(avgD)}}). Resultado estimado: <strong>${{tA}} ${{gA}} — ${{tB}} ${{gB}}</strong>.`;
  }} else {{
    cls='verd-draw';
    text=`⚖️ Partido equilibrado. Alta probabilidad de empate (${{pct(avgE)}}). Resultado estimado: <strong>${{tA}} ${{gA}} — ${{tB}} ${{gB}}</strong>.`;
  }}
  el.className=cls;
  el.innerHTML=text;
}}

// ═══════════════════════════════
// TACTICS
// ═══════════════════════════════
function renderTactics(tA,formA,styleA,tB,formB,styleB) {{
  const ffA=FORMATION_FEATURES[formA]||FORMATION_FEATURES['4-3-3'];
  const ffB=FORMATION_FEATURES[formB]||FORMATION_FEATURES['4-3-3'];
  const ssA=STYLE_SCORE[styleA]||1.0;
  const ssB=STYLE_SCORE[styleB]||1.0;
  const attrs=[
    {{label:'Ataque',vA:ffA.attack*ssA,vB:ffB.attack*ssB,max:1.2}},
    {{label:'Defensa',vA:ffA.defense,vB:ffB.defense,max:1.0}},
    {{label:'Pressing',vA:ffA.pressing,vB:ffB.pressing,max:1.0}},
    {{label:'Amplitud',vA:ffA.width,vB:ffB.width,max:1.0}},
    {{label:'Set Piece',vA:ffA.set_piece,vB:ffB.set_piece,max:1.0}},
  ];
  const row=(label,v,max,color)=>`<div class="tact-item">
    <div class="tact-label">${{label}}</div>
    <div class="tact-bar-wrap"><div class="tact-bar" style="width:${{Math.round(v/max*100)}}%;background:${{color}}"></div></div>
    <div class="tact-val">${{v.toFixed(2)}}</div>
  </div>`;
  const cA='var(--blue)', cB='var(--yellow)';
  document.getElementById('tactRow').innerHTML=`
    <div class="tact-card">
      <div class="tact-header" style="color:${{cA}}">${{tA}} — ${{formA}} / ${{STYLE_LABEL[styleA]}}</div>
      ${{attrs.map(a=>row(a.label,a.vA,a.max,cA)).join('')}}
    </div>
    <div class="tact-card">
      <div class="tact-header" style="color:${{cB}}">${{tB}} — ${{formB}} / ${{STYLE_LABEL[styleB]}}</div>
      ${{attrs.map(a=>row(a.label,a.vB,a.max,cB)).join('')}}
    </div>`;
}}

// ═══════════════════════════════
// GROUPS
// ═══════════════════════════════
function renderGroups() {{
  document.getElementById('groupsGrid').innerHTML=Object.entries(GROUPS).map(([g,teams])=>`
    <div class="group-card" onclick="showGroupMatches('${{g}}')">
      <div class="group-title">GRUPO ${{g}}</div>
      ${{teams.map(t=>`<div class="group-team" onclick="event.stopPropagation();setTeamA('${{t}}')">&nbsp;<span class="rank-dot"></span>&nbsp;${{t}}</div>`).join('')}}
    </div>`).join('');
}}

function setTeamA(team) {{
  const sA=document.getElementById('teamA'), sB=document.getElementById('teamB');
  if (sA.value===team) return;
  if (sB.value===team) sB.value=sA.value;
  sA.value=team;
  onTeamChange();
}}

// Helper: get historial entry normalized to (a vs b) perspective
function getHistEntry(a, b) {{
  const flip = r => r==='victoria_A'?'victoria_B':r==='victoria_B'?'victoria_A':r;
  const he = HIST_LOOKUP[a+'|'+b];
  if (he) return {{gA:he.goles_A,gB:he.goles_B,real:he.resultado_real,
    predA:he.engine_A.prediccion,okA:he.acierto_A,pA:he.engine_A,
    predB:he.engine_B.prediccion,okB:he.acierto_B,pB:he.engine_B}};
  const he2 = HIST_LOOKUP[b+'|'+a];
  if (he2) return {{gA:he2.goles_B,gB:he2.goles_A,real:flip(he2.resultado_real),
    predA:flip(he2.engine_A.prediccion),okA:he2.acierto_A,
    pA:{{p_victoria:he2.engine_A.p_derrota,p_empate:he2.engine_A.p_empate,p_derrota:he2.engine_A.p_victoria}},
    predB:flip(he2.engine_B.prediccion),okB:he2.acierto_B,
    pB:{{p_victoria:he2.engine_B.p_derrota,p_empate:he2.engine_B.p_empate,p_derrota:he2.engine_B.p_victoria}}}};
  return null;
}}

// Helper: get predictions for (a vs b) from PREDS
function getPredsFor(a, b) {{
  if (PREDS[a]&&PREDS[a][b]) return PREDS[a][b];
  if (PREDS[b]&&PREDS[b][a]) {{
    const m=PREDS[b][a];
    return {{
      engine_A:{{p_victoria:m.engine_A.p_derrota,p_empate:m.engine_A.p_empate,p_derrota:m.engine_A.p_victoria}},
      engine_B:{{p_victoria:m.engine_B.p_derrota,p_empate:m.engine_B.p_empate,p_derrota:m.engine_B.p_victoria}},
      lambda_A:m.lambda_B,lambda_B:m.lambda_A,
      lineup_A:m.lineup_B,lineup_B:m.lineup_A
    }};
  }}
  return null;
}}

function predLabel(pred, a, b) {{
  return pred==='victoria_A'?a:pred==='victoria_B'?b:'Empate';
}}

function outcomeOf(pv, pe, pd) {{
  if (pv>=pe&&pv>=pd) return 'victoria_A';
  if (pd>=pe) return 'victoria_B';
  return 'empate';
}}

function showGroupMatches(grp) {{
  const teams=GROUPS[grp];
  const matches=[];
  for(let i=0;i<teams.length;i++) for(let j=i+1;j<teams.length;j++) matches.push([teams[i],teams[j]]);
  document.getElementById('groupMatchesTitle').textContent=`Partidos Grupo ${{grp}}`;
  document.getElementById('groupMatchesList').innerHTML=matches.map(([a,b])=>{{
    const m=getPredsFor(a,b);
    if(!m) return '';
    const pA=m.engine_A, pB=m.engine_B;
    const avgV=(pA.p_victoria+pB.p_victoria)/2;
    const avgE=(pA.p_empate+pB.p_empate)/2;
    const avgD=(pA.p_derrota+pB.p_derrota)/2;
    const he=getHistEntry(a,b);

    const predOutA=outcomeOf(pA.p_victoria,pA.p_empate,pA.p_derrota);
    const predOutB=outcomeOf(pB.p_victoria,pB.p_empate,pB.p_derrota);

    const resultBox = he ? `
      <div class="gm-result">
        <div class="gm-scorebox">
          <div class="gm-score">${{he.gA}} — ${{he.gB}}</div>
          <div class="gm-score-lbl">Resultado</div>
        </div>
        <div class="gm-preds">
          <div class="gm-pred-row">
            <span class="gm-eng la">A</span>
            <div class="gm-pred-bar">
              <div class="gm-pb-w" style="width:${{Math.round(he.pA.p_victoria*100)}}%"></div>
              <div class="gm-pb-d" style="width:${{Math.round(he.pA.p_empate*100)}}%"></div>
              <div class="gm-pb-l" style="width:${{Math.round(he.pA.p_derrota*100)}}%"></div>
            </div>
            <span class="gm-pred-lbl">${{predLabel(he.predA,a,b)}}</span>
            <span class="hist-ok ${{he.okA?'yes':'no'}}">${{he.okA?'✓':'✗'}}</span>
          </div>
          <div class="gm-pred-row">
            <span class="gm-eng lb">B</span>
            <div class="gm-pred-bar">
              <div class="gm-pb-w" style="width:${{Math.round(he.pB.p_victoria*100)}}%"></div>
              <div class="gm-pb-d" style="width:${{Math.round(he.pB.p_empate*100)}}%"></div>
              <div class="gm-pb-l" style="width:${{Math.round(he.pB.p_derrota*100)}}%"></div>
            </div>
            <span class="gm-pred-lbl">${{predLabel(he.predB,a,b)}}</span>
            <span class="hist-ok ${{he.okB?'yes':'no'}}">${{he.okB?'✓':'✗'}}</span>
          </div>
        </div>
      </div>` : '';

    return `<div class="gm-match${{he?' gm-played':''}}">
      <div class="gm-header" onclick="document.getElementById('teamA').value='${{a}}';document.getElementById('teamB').value='${{b}}';onTeamChange()">
        <div style="flex:1;font-size:.82rem;font-weight:600;color:var(--text)">${{a}}</div>
        <div style="text-align:center;min-width:90px">
          ${{!he ? `<div style="display:flex;gap:3px;justify-content:center;font-size:.75rem">
            <span style="color:var(--green);font-weight:600">${{pct(avgV)}}</span>
            <span style="color:var(--text3)">|</span>
            <span style="color:var(--yellow);font-weight:600">${{pct(avgE)}}</span>
            <span style="color:var(--text3)">|</span>
            <span style="color:var(--red);font-weight:600">${{pct(avgD)}}</span>
          </div>
          <div style="font-size:.64rem;color:var(--text3);margin-top:2px">${{discreteGoals(m.lambda_A)}}-${{discreteGoals(m.lambda_B)}} goles</div>`
          : `<span class="pron-played-chip">✓ Jugado</span>`}}
        </div>
        <div style="flex:1;text-align:right;font-size:.82rem;font-weight:600;color:var(--text)">${{b}}</div>
      </div>
      ${{resultBox}}
    </div>`;
  }}).join('');
  document.getElementById('groupMatchesPanel').style.display='block';
}}

// ═══════════════════════════════
// STATS
// ═══════════════════════════════
function renderStats(tA,tB) {{
  const sA=TEAM_STATS[tA]||[50,70,100,26];
  const sB=TEAM_STATS[tB]||[50,70,100,26];
  const items=[
    {{label:'Ranking FIFA',a:sA[0],b:sB[0],lower:true}},
    {{label:'Rating Plantilla',a:sA[1],b:sB[1],lower:false}},
    {{label:'Valor Mercado (M€)',a:sA[2],b:sB[2],lower:false}},
    {{label:'Edad Promedio',a:sA[3],b:sB[3],lower:false}},
  ];
  document.getElementById('statGrid').innerHTML=items.map(item=>{{
    const tot=item.a+item.b||1;
    let pA=item.a/tot,pB=item.b/tot;
    if(item.lower){{pA=1-pA;pB=1-pB;const s=pA+pB;pA/=s;pB/=s;}}
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

// ═══════════════════════════════
// FEATURE IMPORTANCE
// ═══════════════════════════════
function renderFeatureImportance() {{
  const maxV=FEATURE_IMPORTANCE[0].v;
  document.getElementById('featureList').innerHTML=FEATURE_IMPORTANCE.map(fi=>`
    <div class="fi-item">
      <div class="fi-name">${{fi.f}}${{fi.new_?' <span style="color:var(--green);font-size:.6rem;font-weight:700">✦NEW</span>':''}}</div>
      <div class="fi-bar" style="width:${{Math.round(fi.v/maxV*200)}}px;background:${{fi.new_?'var(--green)':'var(--blue)'}};opacity:.8"></div>
      <div class="fi-pct">${{(fi.v*100).toFixed(2)}}%</div>
    </div>`).join('');
}}

// ═══════════════════════════════
// TABS
// ═══════════════════════════════
function switchTab(id,el) {{
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(p=>p.classList.remove('active'));
  if(el) el.classList.add('active');
  document.getElementById('tab-'+id).classList.add('active');
}}

// ═══════════════════════════════
// PRONÓSTICOS DEL DÍA
// ═══════════════════════════════
function renderPronosticosHoy() {{
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('fechaHoyLabel').textContent = today;

  const fixtures = (FIXTURES.schedule||[]).filter(f => f.fecha === today);
  const el = document.getElementById('pronosticosHoy');

  if (!fixtures.length) {{
    el.innerHTML = `<div style="text-align:center;color:var(--text3);padding:18px;font-size:.82rem">Sin partidos programados para hoy (${{today}}).</div>`;
    return;
  }}

  el.innerHTML = `<div class="pron-grid">${{
    fixtures.map(f => {{
      const {{teamA:a,teamB:b,grupo}} = f;
      const m = getPredsFor(a,b);
      if (!m) return '';
      const pA=m.engine_A, pB=m.engine_B;
      const predOutA = outcomeOf(pA.p_victoria,pA.p_empate,pA.p_derrota);
      const predOutB = outcomeOf(pB.p_victoria,pB.p_empate,pB.p_derrota);
      const he = getHistEntry(a,b);
      const lA = m.lambda_A ?? 0, lB = m.lambda_B ?? 0;
      const goalA = discreteGoals(lA), goalB = discreteGoals(lB);

      const headerCenter = he
        ? `<div class="pron-score">${{he.gA}}–${{he.gB}}</div>
           <div class="pron-grupo">Grupo ${{grupo}} · Jugado</div>
           <div class="pron-goal-pred">Pron. goles: ${{goalA}}–${{goalB}}</div>`
        : `<div class="pron-vs">VS</div>
           <div class="pron-grupo">Grupo ${{grupo}}</div>
           <div class="pron-goal-pred">⚽ ${{goalA}}–${{goalB}}</div>`;

      const bodyA = `
        <div class="pron-eng-block">
          <div class="pron-eng-title la">Engine A · MLP</div>
          <div class="pron-pbar">
            <div class="pron-pb-w" style="width:${{Math.round(pA.p_victoria*100)}}%"></div>
            <div class="pron-pb-d" style="width:${{Math.round(pA.p_empate*100)}}%"></div>
            <div class="pron-pb-l" style="width:${{Math.round(pA.p_derrota*100)}}%"></div>
          </div>
          <div class="pron-pbar-vals">
            <span style="color:var(--green)">${{Math.round(pA.p_victoria*100)}}%</span>
            <span style="color:var(--yellow)">${{Math.round(pA.p_empate*100)}}%</span>
            <span style="color:var(--red)">${{Math.round(pA.p_derrota*100)}}%</span>
          </div>
          <span class="pron-pred-chip ${{predOutA}}">${{predLabel(predOutA,a,b)}}</span>
          ${{he ? `<span class="hc-ok ${{he.okA?'yes':'no'}}" style="margin-top:3px">${{he.okA?'✓':'✗'}}</span>` : ''}}
        </div>`;
      const bodyB = `
        <div class="pron-eng-block">
          <div class="pron-eng-title lb">Engine B · XGBoost</div>
          <div class="pron-pbar">
            <div class="pron-pb-w" style="width:${{Math.round(pB.p_victoria*100)}}%"></div>
            <div class="pron-pb-d" style="width:${{Math.round(pB.p_empate*100)}}%"></div>
            <div class="pron-pb-l" style="width:${{Math.round(pB.p_derrota*100)}}%"></div>
          </div>
          <div class="pron-pbar-vals">
            <span style="color:var(--green)">${{Math.round(pB.p_victoria*100)}}%</span>
            <span style="color:var(--yellow)">${{Math.round(pB.p_empate*100)}}%</span>
            <span style="color:var(--red)">${{Math.round(pB.p_derrota*100)}}%</span>
          </div>
          <span class="pron-pred-chip ${{predOutB}}">${{predLabel(predOutB,a,b)}}</span>
          ${{he ? `<span class="hc-ok ${{he.okB?'yes':'no'}}" style="margin-top:3px">${{he.okB?'✓':'✗'}}</span>` : ''}}
        </div>`;

      const goalFooter = `
        <div class="pron-goal-footer">
          <span class="pron-lambda-chip">${{a}}: λ=${{lA.toFixed(2)}} · ${{goalA}} gol${{goalA!==1?'es':''}}</span>
          <span class="pron-lambda-sep">·</span>
          <span class="pron-lambda-chip">${{b}}: λ=${{lB.toFixed(2)}} · ${{goalB}} gol${{goalB!==1?'es':''}}</span>
        </div>`;

      return `<div class="pron-card${{he?' pron-played':''}}" onclick="document.getElementById('teamA').value='${{a}}';document.getElementById('teamB').value='${{b}}';onTeamChange()" style="cursor:pointer">
        <div class="pron-header">
          <div class="pron-team-a">${{a}}</div>
          <div class="pron-center">${{headerCenter}}</div>
          <div class="pron-team-b">${{b}}</div>
        </div>
        <div class="pron-body">${{bodyA}}${{bodyB}}</div>
        ${{goalFooter}}
      </div>`;
    }}).join('')
  }}</div>`;
}}

// ═══════════════════════════════
// HISTORIAL (cards)
// ═══════════════════════════════
function renderHistorial() {{
  const acc = HISTORIAL.accuracy || {{}};
  const eA  = acc.engine_A || {{correct:0,total:0}};
  const eB  = acc.engine_B || {{correct:0,total:0}};
  const entries = (HISTORIAL.entries||[]).slice().reverse();

  const pctA = eA.total ? Math.round(100*eA.correct/eA.total) : 0;
  const pctB = eB.total ? Math.round(100*eB.correct/eB.total) : 0;
  document.getElementById('histAccGrid').innerHTML = `
    <div class="hist-acc-box eng-a">
      <div class="hist-acc-label la">Engine A · MLP+Atención</div>
      <div class="hist-acc-num">${{pctA}}%</div>
      <div class="hist-acc-sub">${{eA.correct}} de ${{eA.total}} correctas · ${{eA.total}} partidos</div>
    </div>
    <div class="hist-acc-box eng-b">
      <div class="hist-acc-label lb">Engine B · XGBoost</div>
      <div class="hist-acc-num">${{pctB}}%</div>
      <div class="hist-acc-sub">${{eB.correct}} de ${{eB.total}} correctas · ${{eB.total}} partidos</div>
    </div>`;

  if (!entries.length) {{
    document.getElementById('historialList').innerHTML =
      `<div class="hist-empty">Sin predicciones registradas. Los resultados aparecen aquí a medida que se juegan los partidos.</div>`;
    return;
  }}

  // Find grupo for each entry from FIXTURES
  const fixtureGrp = {{}};
  for (const f of (FIXTURES.schedule||[])) {{
    fixtureGrp[f.teamA+'|'+f.teamB] = f.grupo;
    fixtureGrp[f.teamB+'|'+f.teamA] = f.grupo;
  }}

  document.getElementById('historialList').innerHTML = entries.map(e => {{
    const a=e.teamA, b=e.teamB;
    const pA=e.engine_A, pB=e.engine_B;
    const real=e.resultado_real;
    const grp = fixtureGrp[a+'|'+b] || '?';
    const realLabel = {{victoria_A:a,empate:'Empate',victoria_B:b}}[real];
    const predTextA = {{victoria_A:a,empate:'Empate',victoria_B:b}}[pA.prediccion];
    const predTextB = {{victoria_A:a,empate:'Empate',victoria_B:b}}[pB.prediccion];

    return `<div class="hc">
      <div class="hc-top">
        <div class="hc-team-a">${{a}}</div>
        <div class="hc-center">
          <div class="hc-score">${{e.goles_A}} — ${{e.goles_B}}</div>
          <div class="hc-date-grp">${{e.fecha}} · Grupo ${{grp}}</div>
          <span class="hc-result-badge ${{real}}">${{realLabel}}</span>
        </div>
        <div class="hc-team-b">${{b}}</div>
      </div>
      <div class="hc-body">
        <div class="hc-eng-block">
          <div class="hc-eng-title la">Engine A · MLP+Atención</div>
          <div class="hc-pbar">
            <div class="hc-pb-w" style="width:${{Math.round(pA.p_victoria*100)}}%"></div>
            <div class="hc-pb-d" style="width:${{Math.round(pA.p_empate*100)}}%"></div>
            <div class="hc-pb-l" style="width:${{Math.round(pA.p_derrota*100)}}%"></div>
          </div>
          <div class="hc-pbar-vals">
            <span style="color:var(--green)">${{Math.round(pA.p_victoria*100)}}%</span>
            <span style="color:var(--yellow)">${{Math.round(pA.p_empate*100)}}%</span>
            <span style="color:var(--red)">${{Math.round(pA.p_derrota*100)}}%</span>
          </div>
          <div class="hc-verdict">
            <span class="hc-ok ${{e.acierto_A?'yes':'no'}}">${{e.acierto_A?'✓':'✗'}}</span>
            <span class="hc-pred-txt">Predijo: <strong>${{predTextA}}</strong></span>
          </div>
        </div>
        <div class="hc-eng-block">
          <div class="hc-eng-title lb">Engine B · XGBoost</div>
          <div class="hc-pbar">
            <div class="hc-pb-w" style="width:${{Math.round(pB.p_victoria*100)}}%"></div>
            <div class="hc-pb-d" style="width:${{Math.round(pB.p_empate*100)}}%"></div>
            <div class="hc-pb-l" style="width:${{Math.round(pB.p_derrota*100)}}%"></div>
          </div>
          <div class="hc-pbar-vals">
            <span style="color:var(--green)">${{Math.round(pB.p_victoria*100)}}%</span>
            <span style="color:var(--yellow)">${{Math.round(pB.p_empate*100)}}%</span>
            <span style="color:var(--red)">${{Math.round(pB.p_derrota*100)}}%</span>
          </div>
          <div class="hc-verdict">
            <span class="hc-ok ${{e.acierto_B?'yes':'no'}}">${{e.acierto_B?'✓':'✗'}}</span>
            <span class="hc-pred-txt">Predijo: <strong>${{predTextB}}</strong></span>
          </div>
        </div>
      </div>
    </div>`;
  }}).join('');
}}

// ═══════════════════════════════
// UTILS
// ═══════════════════════════════
function pct(v){{return Math.round(v*100)+'%';}}
</script>
</body>
</html>"""

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"index.html generado: {len(html)} bytes ({len(html)//1024}KB)")
