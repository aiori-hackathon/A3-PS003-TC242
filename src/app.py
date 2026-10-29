import base64
import re
import time
import sqlite3
from pathlib import Path
from intro_screen import render_intro, render_replay_button

import numpy as np
import plotly.graph_objects as go
import streamlit as st
import json

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                  TableStyle, PageBreak)
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TechKnights | Federated Traffic-Flow Prediction",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&display=swap');
:root{--line:#14304F;--mut:#8FB0D0;--txt:#E6F0FF}
html,body,.stApp,.stMarkdown,label,p,button,input{font-family:'Inter',sans-serif}
.stApp{background:radial-gradient(1100px 480px at 88% -8%,rgba(0,120,255,.13),transparent 60%),linear-gradient(180deg,#07101F,#081528);color:var(--txt)}
#MainMenu,footer,[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"]{display:none!important}
.block-container{padding:1rem 1.6rem 1rem!important;max-width:100%!important}
div[data-testid="stVerticalBlock"]{gap:.85rem}
svg.ico{flex-shrink:0;vertical-align:middle}

/* header */
.hdr{display:flex;align-items:center;justify-content:space-between;gap:1rem;flex-wrap:wrap;padding:4px 2px}
.hdr-l{display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.logo{width:60px;height:60px;border-radius:14px;box-shadow:0 0 0 1px rgba(0,212,255,.35),0 0 18px rgba(0,160,255,.28)}
.logo-fb{display:flex;align-items:center;justify-content:center;background:#0A2442;color:#2DB6FF}
.brand{font-size:1.75rem;font-weight:700;color:#fff;letter-spacing:-.01em}
.vsep{width:1px;height:46px;background:linear-gradient(transparent,#2A5B8C,transparent)}
.ttl{font-size:1.45rem;font-weight:700;color:#fff;line-height:1.2}
.sub{font-size:.88rem;color:var(--mut);margin-top:3px}.sub b{color:#2DB6FF;margin:0 6px}
.hdr-r{display:flex;gap:14px}
.pbox{display:flex;flex-direction:column;align-items:center;gap:5px}
.pl{display:flex;align-items:center;gap:8px;padding:7px 20px;border-radius:999px;font-family:'JetBrains Mono',monospace;font-weight:700;font-size:.85rem;border:1px solid}
.pl-green{color:#2DFFB0;border-color:rgba(45,255,176,.45);background:rgba(45,255,176,.08)}
.pl-violet{color:#B79CFF;border-color:rgba(167,139,250,.5);background:rgba(167,139,250,.09)}
.pl-amber{color:#FFB547;border-color:rgba(255,181,71,.5);background:rgba(255,181,71,.09)}
.pl .dot{width:10px;height:10px;border-radius:50%;background:currentColor;box-shadow:0 0 8px currentColor}
.pulse .dot{animation:pulse 1s infinite}
@keyframes pulse{50%{opacity:.25}}
.plab{font-size:.72rem;color:var(--mut)}

/* control bar */
.st-key-ctrlbar{background:rgba(9,22,40,.85);border:1px solid var(--line);border-radius:14px;padding:14px 16px 12px}
.st-key-ctrlbar [data-testid="stHorizontalBlock"]{align-items:flex-end;gap:.8rem}
[data-testid="stWidgetLabel"] p{font-size:.76rem;color:var(--mut);font-weight:500}
[data-baseweb="select"]>div{background:#0B1A2E!important;border:1px solid #1E3A5F!important;border-radius:8px!important;min-height:42px}
[data-baseweb="select"]>div:focus-within{border-color:#00D4FF!important}
[data-baseweb="select"] *{color:#E6F0FF}
[data-baseweb="popover"] ul{background:#0B1A2E}
.st-key-ctrlbar [data-testid="stBaseButton-primary"]{background:linear-gradient(135deg,#1677FF,#0B5BD3);border:none;color:#fff;font-weight:600;min-height:46px;border-radius:9px;box-shadow:0 4px 18px rgba(22,119,255,.35)}
.st-key-ctrlbar [data-testid="stBaseButton-primary"]:hover{filter:brightness(1.12)}
.st-key-ctrlbar [data-testid="stBaseButton-secondary"]{background:rgba(255,255,255,.02);border:1px solid #2A4B73;color:#DCE9FA;font-weight:600;min-height:46px;border-radius:9px}
.st-key-ctrlbar [data-testid="stBaseButton-secondary"]:hover{border-color:#00D4FF;color:#00D4FF}
.st-key-w_dist [role="radiogroup"]{gap:0!important;flex-wrap:nowrap}
.st-key-w_dist label[data-baseweb="radio"]{margin:0;padding:9px 22px;background:#0D1B2E;border:1px solid #1E3A5F;cursor:pointer}
.st-key-w_dist label[data-baseweb="radio"]>div:first-child{display:none}
.st-key-w_dist label[data-baseweb="radio"]:first-of-type{border-radius:8px 0 0 8px}
.st-key-w_dist label[data-baseweb="radio"]:last-of-type{border-radius:0 8px 8px 0}
.st-key-w_dist label[data-baseweb="radio"]:has(input:checked){background:#0B6BFF;border-color:#2B8CFF}
.st-key-w_dist label p{font-size:.88rem;font-weight:600;color:#9DB6D3}
.st-key-w_dist label:has(input:checked) p{color:#fff}

/* KPI cards */
.kpi{--c:0,212,255;border:1px solid rgba(var(--c),.55);border-left:4px solid rgb(var(--c));border-radius:12px;padding:14px 18px 12px;min-height:128px;background:linear-gradient(135deg,rgba(var(--c),.11),rgba(8,18,34,.92) 58%)}
.kpi.green{--c:0,255,136}.kpi.amber{--c:255,181,71}.kpi.violet{--c:167,139,250}
.kpi-top{display:flex;align-items:center;gap:10px;color:rgb(var(--c))}
.kpi-lab{flex:1;font-size:.74rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase}
.kpi-info{color:#6F8FB0;display:flex}
.kpi-val{font-family:'JetBrains Mono',monospace;font-size:2.2rem;font-weight:700;color:rgb(var(--c));line-height:1.15;margin:8px 0 4px}
.kpi-sub{font-size:.8rem;color:#B8CCE3;display:flex;align-items:center;gap:7px}
.kbar{height:6px;border-radius:4px;background:#1A2745;margin:2px 0 8px;overflow:hidden}
.kbar i{display:block;height:100%;background:linear-gradient(90deg,#7C5CFF,#A78BFA);border-radius:4px;transition:width .3s}

/* tabs + panel */
[data-baseweb="tab-list"]{gap:4px;background:#091728;border:1px solid var(--line);border-radius:12px;padding:5px}
[data-baseweb="tab-highlight"],[data-baseweb="tab-border"]{display:none}
button[data-baseweb="tab"]{height:42px;padding:0 20px;border-radius:9px;background:transparent;color:#9DB6D3;font-size:.88rem;font-weight:500}
button[data-baseweb="tab"][aria-selected="true"]{background:linear-gradient(180deg,rgba(14,110,255,.38),rgba(14,110,255,.16));color:#7FDBFF;box-shadow:inset 0 -2px 0 #1AA3FF}
[data-baseweb="tab-panel"]{margin-top:12px;padding:14px 18px 16px!important;border:1px solid var(--line);border-radius:12px;background:linear-gradient(180deg,rgba(10,24,48,.85),rgba(7,16,31,.9))}
.ph{display:flex;align-items:center;gap:10px;font-weight:600;font-size:1.02rem;color:#EAF3FF;padding-bottom:10px;margin-bottom:6px;border-bottom:1px solid #12304F}
.ph svg{color:#2DB6FF}
.empty{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:6px}
.e-t{font-size:1.08rem;font-weight:600;color:#EAF3FF;margin-top:6px}
.e-s{font-size:.9rem;color:#9DB6D3;max-width:420px}

/* side panels */
.sp{border:1px solid var(--line);border-radius:12px;padding:12px 14px 6px;margin-bottom:12px;background:linear-gradient(180deg,rgba(10,24,48,.85),rgba(7,16,31,.9))}
.sp-t{font-size:.74rem;font-weight:700;letter-spacing:.17em;color:var(--mut);margin-bottom:10px}
.ag{--c:0,212,255;display:flex;align-items:center;gap:12px;padding:10px 12px;margin-bottom:9px;border-radius:10px;border:1px solid rgba(var(--c),.45);border-left:4px solid rgb(var(--c));background:linear-gradient(90deg,rgba(var(--c),.11),rgba(8,18,34,.6))}
.ag.green{--c:0,255,136}.ag.violet{--c:167,139,250}.ag.amber{--c:255,181,71}.ag.blue{--c:76,154,255}
.ag-ico{color:rgb(var(--c));display:flex}
.ag-main{flex:1;min-width:0}
.ag-t{font-weight:600;font-size:.95rem;color:rgb(var(--c))}
.ag-t em{font-style:normal;font-weight:400;font-size:.76rem;color:#7F9BBA;margin-left:6px}
.ag-p{font-size:.75rem;color:#B8CCE3;margin:4px 0 6px}
.ag-bar{height:5px;background:#10233D;border-radius:4px;overflow:hidden}
.ag-bar i{display:block;height:100%;background:rgb(var(--c));border-radius:4px;transition:width .3s}
.ag-r{display:flex;flex-direction:column;align-items:flex-end;gap:6px}
.pill{font-size:.7rem;padding:3px 12px;border-radius:7px;border:1px solid #2A4B73;color:#BCD0E8;background:rgba(255,255,255,.03)}
.pill.run{color:#FFB547;border-color:rgba(255,181,71,.55)}
.pill.done{color:#00FF88;border-color:rgba(0,255,136,.55)}
.act{height:118px;overflow-y:auto;margin-bottom:8px;border:1px solid #12304F;border-radius:9px;padding:8px 12px;background:#060D1B;font-family:'JetBrains Mono',monospace;font-size:.7rem;line-height:1.75;color:#4A7A9B}
.act-empty{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:3px;color:#9DB6D3;font-family:'Inter',sans-serif;font-size:.85rem}
.act-empty small{font-size:.72rem;color:#6F8FB0}
.act-empty svg{color:#2DB6FF}
.log-ts{color:#2A4A6A}.log-ok{color:#00FF88}.log-warn{color:#FFB547}.log-info{color:#00D4FF}

/* tables */
.cmp-table,.kv{width:100%;border-collapse:collapse;font-size:.78rem}
.cmp-table th{color:#6F8FB0;font-weight:500;text-align:left;padding:.6rem .8rem;border-bottom:1px solid #1A2535;font-size:.7rem;text-transform:uppercase;letter-spacing:.06em}
.cmp-table td,.kv td{padding:.5rem .8rem;border-bottom:1px solid #111D2C;color:#C8D8E8;font-family:'JetBrains Mono',monospace}
.kv td:first-child{color:#6F8FB0;width:34%}
.cmp-table tr:last-child td,.kv tr:last-child td{border-bottom:none}
.cmp-table .win{color:#00FF88;font-weight:600}.cmp-table .lose{color:#FF6B6B}
.round-badge{display:inline-block;background:rgba(0,212,255,.08);border:1px solid rgba(0,212,255,.2);border-radius:6px;padding:.15rem .5rem;font-size:.72rem;color:#00D4FF}
.note{margin-top:14px;padding:12px 16px;border:1px solid #14304F;border-radius:10px;background:#0A1628;font-size:.8rem;color:#9DB6D3;line-height:1.7}

/* footer */
.foot{display:flex;flex-wrap:wrap;align-items:center;padding:10px 14px;border:1px solid var(--line);border-radius:10px;background:rgba(8,20,38,.7);font-size:.75rem;color:#9DB6D3;row-gap:8px}
.foot span{display:flex;align-items:center;gap:8px;padding:0 16px;border-right:1px solid #1B3A5C}
.foot span:first-child{padding-left:0}.foot span:last-child{border-right:none}
.foot svg{color:#2DB6FF}
</style>
""", unsafe_allow_html=True)


# ─── ICONS / HTML HELPERS ────────────────────────────────────────────────────
ICONS = {
    "line":   '<path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-6"/>',
    "bars":   '<path d="M3 21h18"/><rect x="5" y="12" width="3" height="7"/><rect x="10.5" y="8" width="3" height="11"/><rect x="16" y="4" width="3" height="15"/>',
    "cloud":  '<path d="M7 18a4 4 0 010-8 5 5 0 019.6-1A4.5 4.5 0 0117 18"/><path d="M12 12v7M9 15l3-3 3 3"/>',
    "refresh":'<path d="M20 11a8 8 0 10-2.3 5.7"/><path d="M20 4v7h-7"/>',
    "users":  '<circle cx="9" cy="8" r="3"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17" cy="9" r="2.4"/><path d="M17 14c2.5 0 4 1.8 4 4.5"/>',
    "user":   '<circle cx="12" cy="8" r="3.5"/><path d="M5 20c0-4 3.1-6.5 7-6.5s7 2.5 7 6.5"/>',
    "info":   '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
    "node":   '<circle cx="12" cy="12" r="2.4"/><circle cx="12" cy="4" r="1.6"/><circle cx="12" cy="20" r="1.6"/><circle cx="4" cy="12" r="1.6"/><circle cx="20" cy="12" r="1.6"/><path d="M12 6v3.6M12 14.4V18M6 12h3.6M14.4 12H18"/>',
    "bolt":   '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
    "db":     '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "doc":    '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/>',
    "clock":  '<path d="M6 3h8l4 4v6M6 3v18h6"/><circle cx="17" cy="17" r="4.5"/><path d="M17 15v2l1.5 1"/>',
    "scale":  '<path d="M12 4v16M7 20h10M5 8h14"/><path d="M5 8l-3 7a3.5 3.5 0 006 0zM19 8l-3 7a3.5 3.5 0 006 0z"/>',
    "repeat": '<path d="M4 9a6 6 0 016-5h7M17 1l3 3-3 3M20 15a6 6 0 01-6 5H7M7 23l-3-3 3-3"/>',
}


def ico(name, size=18):
    return (f'<svg class="ico" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
            f'stroke-linejoin="round">{ICONS[name]}</svg>')


def H(s):
    """Collapse multi-line HTML so Streamlit's markdown never sees indented code blocks."""
    return re.sub(r"\s*\n\s*", "", s.strip())


@st.cache_data
def load_logo_b64():
    for name in ("logo.png", "techknights_logo.png"):
        p = Path(__file__).parent / name
        if p.exists():
            return base64.b64encode(p.read_bytes()).decode()
    return None


LOGO_B64 = load_logo_b64()
DB_PATH = Path(__file__).parent / "results" / "experiments.db"

def load_experiment(mode: str, seed: int, num_clients: int):
    """Fetch all rounds for one (mode, seed, num_clients) combo from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT * FROM rounds WHERE mode=? AND seed=? AND num_clients=? ORDER BY round",
        (mode, seed, num_clients)
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    for r in rows:
        r["client_maes"] = json.loads(r["client_maes"])
    return rows

def available_seeds(mode: str):
    conn = sqlite3.connect(DB_PATH)
    seeds = [r[0] for r in conn.execute(
        "SELECT DISTINCT seed FROM rounds WHERE mode=? ORDER BY seed", (mode,)
    )]
    conn.close()
    return seeds
SPEED_MAP = {"🐢 Slow": 1.0, "⚡ Normal": 0.35, "🚀 Fast": 0.05}
AGENT_CLASS = ["cyan", "green", "violet", "amber", "blue"]
AGENT_HEX = ["#00D4FF", "#00FF88", "#A78BFA", "#FFB547", "#4C9AFF"]
INTERSECTION_NAMES = ["Intersection A", "Intersection B", "Intersection C", "Intersection D", "Intersection E"]


def _node(x, y, light):
    return (f'<g transform="translate({x},{y})"><ellipse rx="52" ry="21" fill="url(#g1)"/>'
            f'<ellipse rx="40" ry="15" fill="#0A2442" stroke="#2DB6FF" stroke-opacity=".6"/>'
            f'<path d="M-34 -4L34 4M-30 8L30 -8" stroke="#5CC8FF" stroke-width="5" stroke-linecap="round" opacity=".45"/>'
            f'<rect x="-1" y="-24" width="2" height="16" fill="#2DB6FF"/><circle cy="-26" r="3.2" fill="{light}"/></g>')


EMPTY_SVG = H(f'''
<svg width="340" viewBox="0 0 360 210" fill="none">
<defs><radialGradient id="g1"><stop offset="0" stop-color="#1AA3FF" stop-opacity=".5"/><stop offset="1" stop-color="#1AA3FF" stop-opacity="0"/></radialGradient></defs>
<g stroke="#2DB6FF" stroke-width="1.2" stroke-dasharray="4 4" opacity=".7"><path d="M180 58L70 138"/><path d="M180 58V150"/><path d="M180 58L290 138"/></g>
<circle cx="180" cy="34" r="34" fill="url(#g1)"/>
<rect x="150" y="14" width="60" height="42" rx="9" fill="#0B2A4D" stroke="#2DB6FF"/>
<path d="M162 27h36M162 35h36M162 43h36" stroke="#5CC8FF" stroke-width="2.4" stroke-linecap="round"/>
{_node(70, 150, "#00FF88")}{_node(180, 168, "#FF5C5C")}{_node(290, 150, "#FFB547")}
</svg>''')


def empty_state(h):
    return H(f'''<div class="empty" style="height:{h}px">{EMPTY_SVG}
        <div class="e-t">No training data available yet</div>
        <div class="e-s">Run an experiment to visualize prediction error and convergence across training rounds.</div></div>''')


def ph(icon, title):
    return H(f'<div class="ph">{ico(icon, 20)}<span>{title}</span></div>')


# ─── SESSION STATE ───────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "fed_mae": [], "fed_rmse": [],
        "central_mae": [], "central_rmse": [],
        "comm_bytes": [], "rounds_done": 0,
        "running": False, "paused": False,
        "mode": "IID", "num_clients": 3,
        "total_rounds": 10, "seed": 42,
        "logs": [], "client_status": [], "client_hist": [],
        "dataset": "METR-LA", "speed": "⚡ Normal",
        "render_tick": 0,
        "intro_done": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()
if not st.session_state.intro_done:
    render_intro()
    st.stop()          # nothing below (dashboard) runs until the intro finishes


# ─── EXPERIMENT LOGIC (unchanged) ────────────────────────────────────────────
def add_log(msg, kind="info"):
    ts = time.strftime("%H:%M:%S")
    st.session_state.logs.append((ts, msg, kind))
    if len(st.session_state.logs) > 50:
        st.session_state.logs.pop(0)


def simulate_round(rnd, mode, num_clients, seed):
    np.random.seed(seed + rnd)
    noise    = 0.4 if mode == "Non-IID" else 0.15
    decay    = np.exp(-0.18 * rnd)
    fed_mae  = max(0.4, round(3.8 * decay + np.random.normal(0, noise), 3))
    fed_rmse = max(0.6, round(5.1 * decay + np.random.normal(0, noise * 1.2), 3))
    cen_mae  = max(0.3, round(3.2 * decay + np.random.normal(0, 0.08), 3))
    cen_rmse = max(0.5, round(4.4 * decay + np.random.normal(0, 0.10), 3))
    comm     = 48_320 * 4 * 2 * num_clients
    client_maes = [round(fed_mae + np.random.normal(0, noise * 0.5), 3) for _ in range(num_clients)]
    return dict(fed_mae=fed_mae, fed_rmse=fed_rmse, cen_mae=cen_mae,
                cen_rmse=cen_rmse, comm=comm, client_maes=client_maes)


# ─── CHARTS ──────────────────────────────────────────────────────────────────
def chart_height():
    """Match the left chart panel to the height of the Client Agents + Agent Activity column."""
    return 385 + 92 * (active_cfg()["clients"] - 3)


def build_convergence_chart(height, total_rounds):
    s = st.session_state
    x = list(range(1, len(s.fed_mae) + 1))
    series = [
        ("Federated MAE",   s.fed_mae,      "#00D4FF", "solid"),
        ("Federated RMSE",  s.fed_rmse,     "#00FF88", "solid"),
        ("Centralized MAE", s.central_mae,  "#A78BFA", "dot"),
        ("Centralized RMSE", s.central_rmse, "#FFB547", "dot"),
    ]
    fig = go.Figure()
    for name, vals, color, dash in series:
        solid = dash == "solid"
        fig.add_trace(go.Scatter(
            x=x, y=vals, name=name, mode="lines+markers",
            line=dict(color=color, width=2.8 if solid else 1.8, dash=dash),
            marker=dict(size=7 if solid else 4, color=color, line=dict(width=1.5, color="#07101F")),
        ))
    fig.update_layout(
        height=height, hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#8FB0D0", size=11),
        xaxis=dict(title="Round", gridcolor="#0F2440", linecolor="#14304F",
                   range=[0.6, total_rounds + 0.4], dtick=1),
        yaxis=dict(title="Error (MAE / RMSE)", gridcolor="#0F2440", linecolor="#14304F", rangemode="tozero"),
        legend=dict(orientation="h", x=0, y=1.07, bgcolor="rgba(0,0,0,0)", font=dict(size=11, color="#B8CCE3")),
        margin=dict(l=8, r=8, t=34, b=8),
    )
    return fig


def build_comm_chart(bytes_list, total_rounds):
    rounds = list(range(1, len(bytes_list) + 1))
    fig = go.Figure(go.Bar(x=rounds, y=[b / 1024 for b in bytes_list],
                           marker_color="#A78BFA", marker_line_width=0, width=0.6))
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#8FB0D0", size=11),
        xaxis=dict(title="Round", gridcolor="#0F2440", linecolor="#14304F",
                   range=[0.5, total_rounds + 0.5], dtick=1),
        yaxis=dict(title="KB per round", gridcolor="#0F2440", linecolor="#14304F"),
        margin=dict(l=8, r=8, t=16, b=8), height=240,
    )
    return fig


def spark(vals, color, w=116, h=30):
    if len(vals) < 2:   # decorative idle waveform
        pts = [(x, h / 2 + 5 * np.sin(x / 9.0) + 2 * np.sin(x / 3.1)) for x in range(0, w + 1, 4)]
        opacity = 0.35
    else:
        lo, hi = min(vals), max(vals)
        rng = (hi - lo) or 1
        pts = [(i * w / (len(vals) - 1), h - 3 - (v - lo) / rng * (h - 6)) for i, v in enumerate(vals)]
        opacity = 1
    d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}"><polyline points="{d}" fill="none" '
            f'stroke="{color}" stroke-width="1.7" stroke-linejoin="round" stroke-linecap="round" '
            f'opacity="{opacity}"/></svg>')


# ─── LAYOUT PLACEHOLDERS + CONTROL BAR ───────────────────────────────────────
header_ph = st.empty()

with st.container(key="ctrlbar"):
    cc = st.columns([1.7, 1.5, 1.0, 1.0, 1.55, 0.95, 1.35, 1.2])
    with cc[0]:
        run_clicked = st.button("Run Experiment", icon=":material/play_arrow:", type="primary",
                                width="stretch", key="btn_run")
    with cc[1]:
        reset_clicked = st.button("Reset Experiment", icon=":material/refresh:",
                                  width="stretch", key="btn_reset")
    with cc[2]:
        sel_clients = st.selectbox(":material/group: Number of Clients", [3, 4, 5], index=0, key="w_clients")
    with cc[3]:
        sel_rounds = st.selectbox(":material/autorenew: Training Rounds", list(range(5, 21)), index=5, key="w_rounds")
    with cc[4]:
        sel_mode = st.radio(":material/database: Data Distribution", ["IID", "Non-IID"],
                            index=0, horizontal=True, key="w_dist")
    with cc[5]:
        sel_seed = st.selectbox(":material/casino: Random Seed", [42, 7, 123], index=0, key="w_seed")
    with cc[6]:
        sel_dataset = sel_dataset = st.selectbox(":material/dataset: Dataset", ["METR-LA"],
                                   index=0, key="w_dataset", disabled=True)
    with cc[7]:
        sel_speed = st.selectbox(":material/speed: Training Speed", list(SPEED_MAP.keys()),
                                 index=1, key="w_speed")

metric_ph = st.empty()
col_main, col_side = st.columns([3.15, 1.25], gap="medium")
with col_main:
    tabs_ph = st.empty()
with col_side:
    side_ph = st.empty()

st.markdown(H(f'''<div class="foot">
<span>{ico("db", 16)}Public Traffic Dataset (Partitioned across virtual intersections)</span>
<span>{ico("shield", 16)}Local training data stays on each client</span>
<span>{ico("repeat", 16)}Model updates are aggregated centrally</span>
<span>{ico("bars", 16)}Measures: MAE, RMSE, Communication Cost</span>
<span>Supports IID &amp; Non-IID</span>
<span>Chronological train/test split</span>
<span>3 Seeds</span></div>'''), unsafe_allow_html=True)
render_replay_button()

def active_cfg():
    """Show the finished/running experiment's config, otherwise the live control selections."""
    s = st.session_state
    if s.running or s.rounds_done > 0:
        return dict(mode=s.mode, clients=s.num_clients, total=s.total_rounds, speed=s.speed)
    return dict(mode=sel_mode, clients=sel_clients, total=sel_rounds, speed=sel_speed)

# ─── COMMUNICATION-COST ACCOUNTING ───────────────────────────────────────────
# Federated and Centralized costs are both measured in real float32 bytes
# with the SAME accounting convention, so the comparison is apples-to-apples
# and nothing here is an invented/hardcoded total:
#
#   • Federated, per round: exactly the `comm_bytes` already stored in
#     experiments.db for that round — the real bytes the FedAvg simulator
#     exchanged (global-model DOWNLOAD + local-update UPLOAD, for every
#     client): 2 * num_clients * model_params * FLOAT_BYTES. The federated
#     TOTAL is simply the sum of that real per-round figure across all
#     completed rounds — no change from what the dashboard already computed.
#   • The one-way MODEL payload size is back-solved from that same real
#     number (comm_bytes / (2 * num_clients)). The model doesn't change size
#     between rounds, so this is exact, not estimated.
#   • Centralized has no per-round weight exchange — instead every client's
#     RAW sensor data has to reach the server (upload only; a centralized
#     trainer does not need to broadcast anything back during training, so
#     there is no applicable download leg to add here). That one-time raw
#     payload is SENSORS * TRAIN_TIMESTEPS * FLOAT_BYTES, where SENSORS and
#     TRAIN_TIMESTEPS are pulled directly from fed_backend/data_loader.py
#     rather than assumed:
#       - data_loader.py's build_federated_dataset() truncates METR-LA to
#         its `max_sensors` parameter, DEFAULT 60 (not the full 207 —
#         this is also why the README's architecture section says
#         "input=60 sensors"). Only the TRAIN split needs to reach a
#         central server (val/test aren't needed for training), and
#         data_loader.py's own TRAIN_FRAC (0.7) says how much of the
#         34,272-step METR-LA series that is.
#     We try to import SENSORS_DEFAULT and TRAIN_FRAC directly from
#     data_loader.py so this number updates automatically if those values
#     ever change; if the module can't be imported (e.g. app.py deployed
#     without fed_backend on the path), we fall back to the same defaults,
#     clearly labeled below so they're easy to correct.
FLOAT_BYTES = 4                 # float32
METR_LA_TIMESTEPS = 34_272      # official METR-LA length (5-min steps, ~4 months)

try:
    import inspect
    from fed_backend.data_loader import TRAIN_FRAC as _DL_TRAIN_FRAC
    from fed_backend.data_loader import build_federated_dataset as _DL_BUILD
    SENSORS_DEFAULT = inspect.signature(_DL_BUILD).parameters["max_sensors"].default
    TRAIN_FRAC = _DL_TRAIN_FRAC
except Exception:
    # Fallback — matches data_loader.py's current defaults exactly. Update
    # these two if data_loader.py's max_sensors / TRAIN_FRAC ever change
    # and this import isn't available in your deployment.
    SENSORS_DEFAULT = 60
    TRAIN_FRAC = 0.7


def model_bytes_per_direction(comm_bytes_values, num_clients: int) -> float:
    """One-way (upload OR download) model payload size, in bytes, back-solved
    from the real stored comm_bytes of completed rounds. Model size is
    constant across rounds, so this is exact — not a guess."""
    if not comm_bytes_values or not num_clients:
        return 0.0
    avg_round_bytes = sum(comm_bytes_values) / len(comm_bytes_values)
    return avg_round_bytes / (2 * num_clients)


def centralized_comm_bytes(num_sensors: int = None) -> int:
    """Bytes required to ship the raw TRAINING-split sensor data to a
    central server once — the real centralized-training requirement being
    compared against the federated run's cumulative weight-update traffic.
    Uses the actual sensor count this run trained on (from the DB/run
    config) when available, falling back to data_loader.py's default."""
    sensors = num_sensors or SENSORS_DEFAULT
    train_timesteps = round(TRAIN_FRAC * METR_LA_TIMESTEPS)
    return sensors * train_timesteps * FLOAT_BYTES


def _fmt_bytes(b: float) -> str:
    """Human-friendly byte formatting shared by the dashboard, PDF and DOCX
    reports so every surface prints the exact same figure."""
    if b >= 1024 * 1024:
        return f"{b / (1024 * 1024):.2f} MB"
    return f"{b / 1024:.2f} KB"


# ─── CONVERGENCE DETECTION ────────────────────────────────────────────────────
# A round is only reported as "converged" once the metric has STAYED stable
# for CONVERGENCE_WINDOW consecutive rounds — not just one lucky small
# round-over-round dip. The previous one-liner compared only ONE pair of
# consecutive rounds, so a single small fluctuation (common early in
# Non-IID runs, which have higher injected noise) was enough to report
# "converged" even though later rounds kept swinging — e.g. Round 5 being
# reported for seed=42, 15 rounds, Non-IID, despite later fluctuations.
CONVERGENCE_WINDOW = 3   # consecutive rounds required to confirm stability
CONVERGENCE_EPS = 0.05   # max allowed |MAE[r] - MAE[r-1]| within that window


def detect_convergence(series, window=CONVERGENCE_WINDOW, eps=CONVERGENCE_EPS):
    """
    Returns the 1-indexed round at which `series` first becomes stable for
    `window` consecutive rounds (every round-over-round change inside that
    window is below `eps`), or None if it never stabilises for that long.
    """
    n = len(series)
    if n < window:
        return None
    deltas = [abs(series[i] - series[i - 1]) for i in range(1, n)]
    needed = window - 1  # deltas needed to confirm `window` stable rounds
    for start in range(len(deltas) - needed + 1):
        if all(d < eps for d in deltas[start:start + needed]):
            return start + 1   # 1-indexed round where the stable streak begins
    return None


def convergence_label(series, window=CONVERGENCE_WINDOW, eps=CONVERGENCE_EPS):
    r = detect_convergence(series, window, eps)
    return f"Round {r}" if r else "Not Converged"


# ─── REPORT GENERATION ───────────────────────────────────────────────────────
def _report_data():
    """Collect everything needed for a report from current session state."""
    s = st.session_state
    fm, fr = s.fed_mae[-1], s.fed_rmse[-1]
    cm_, cr = s.central_mae[-1], s.central_rmse[-1]

    fed_total_bytes = sum(s.comm_bytes)                      # unchanged — already accurate
    total_kb = fed_total_bytes / 1024
    per_rnd = total_kb / s.rounds_done if s.rounds_done else 0

    model_bytes = model_bytes_per_direction(s.comm_bytes, s.num_clients)
    # `sensors_used` isn't in the current DB schema (see build_db.py), so this
    # falls back to data_loader.py's own default (SENSORS_DEFAULT) unless a
    # future schema change adds a real per-run sensor count to read instead.
    cen_total_bytes = centralized_comm_bytes(getattr(s, "sensors_used", None))
    comm_reduction_pct = (
        (cen_total_bytes - fed_total_bytes) / cen_total_bytes * 100
        if cen_total_bytes else 0.0
    )

    conv = detect_convergence(s.fed_mae)
    conv_label = f"Round {conv}" if conv else "Not Converged"

    rounds_table = list(zip(
        range(1, len(s.fed_mae) + 1), s.fed_mae, s.fed_rmse,
        s.central_mae, s.central_rmse, s.comm_bytes
    ))
    return dict(
        dataset=s.dataset, mode=s.mode, clients=s.num_clients, rounds=s.rounds_done,
        seed=s.seed, speed=s.speed, final_mae=fm, final_rmse=fr,
        central_mae=cm_, central_rmse=cr, total_kb=total_kb, per_rnd=per_rnd,
        fed_total_bytes=fed_total_bytes, cen_total_bytes=cen_total_bytes,
        model_bytes=model_bytes, comm_reduction_pct=comm_reduction_pct,
        convergence=conv, convergence_label=conv_label,
        rounds_table=rounds_table,
        client_maes=s.client_status,
    )


def build_pdf_report() -> bytes:
    d = _report_data()
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             topMargin=1.5*cm, bottomMargin=1.5*cm,
                             leftMargin=1.8*cm, rightMargin=1.8*cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TK_Title", parent=styles["Title"], textColor=colors.HexColor("#0B5BD3"))
    h2 = ParagraphStyle("TK_H2", parent=styles["Heading2"], textColor=colors.HexColor("#0B5BD3"),
                         spaceBefore=14, spaceAfter=6)
    body = styles["BodyText"]

    elems = [
        Paragraph("TechKnights — Federated Traffic-Flow Prediction", title_style),
        Paragraph("Experiment Evaluation Report", styles["Heading3"]),
        Spacer(1, 10),
    ]

    # Config table
    cfg_rows = [
        ["Dataset", d["dataset"]], ["Distribution", d["mode"]],
        ["Clients", str(d["clients"])], ["Rounds completed", str(d["rounds"])],
        ["Seed", str(d["seed"])], ["Speed", d["speed"]],
    ]
    elems += [Paragraph("Configuration", h2), _table(cfg_rows, [6*cm, 9*cm])]

    # Summary metrics
    metric_rows = [
        ["Final Federated MAE", f"{d['final_mae']:.4f}"],
        ["Final Federated RMSE", f"{d['final_rmse']:.4f}"],
        ["Final Centralized MAE", f"{d['central_mae']:.4f}"],
        ["Final Centralized RMSE", f"{d['central_rmse']:.4f}"],
        ["Convergence round", d["convergence_label"]],
        ["Total communication (federated)", f"{d['total_kb']:.2f} KB"],
        ["Communication per round", f"{d['per_rnd']:.2f} KB/round"],
    ]
    elems += [Paragraph("Summary Metrics", h2), _table(metric_rows, [6*cm, 9*cm])]

    # Communication cost comparison (federated vs centralized, same methodology)
    comm_rows = [
        ["Federated total (cumulative, actual)", _fmt_bytes(d["fed_total_bytes"])],
        [f"Centralized total (one-time, {SENSORS_DEFAULT} sensors × {TRAIN_FRAC:.0%} train split)",
         _fmt_bytes(d["cen_total_bytes"])],
        ["Model payload per transfer", _fmt_bytes(d["model_bytes"])],
        ["Reduction vs Centralized", f"{d['comm_reduction_pct']:.1f}%"],
    ]
    elems += [Paragraph("Communication Cost Comparison", h2), _table(comm_rows, [8*cm, 7*cm])]

    # Round-wise table
    rt_header = ["Round", "Fed MAE", "Fed RMSE", "Cen MAE", "Cen RMSE", "Comm (KB)"]
    rt_rows = [rt_header] + [
        [str(r), f"{fm:.4f}", f"{fr:.4f}", f"{cm_:.4f}", f"{cr:.4f}", f"{cb/1024:.2f}"]
        for r, fm, fr, cm_, cr, cb in d["rounds_table"]
    ]
    elems += [Paragraph("Round-wise Metrics", h2), _table(rt_rows, [2*cm]*6, header=True)]

    # Client performance
    if d["client_maes"]:
        cp_rows = [["Client", "Final MAE"]] + [
            [f"Client {i+1}", f"{v:.4f}"] for i, v in enumerate(d["client_maes"])
        ]
        elems += [Paragraph("Client Performance (final round)", h2), _table(cp_rows, [7*cm, 7*cm], header=True)]

    # Fed vs Centralized comparison
    comp_rows = [
        ["Metric", "Federated", "Centralized", "Gap"],
        ["MAE", f"{d['final_mae']:.4f}", f"{d['central_mae']:.4f}",
         f"{(d['final_mae']-d['central_mae'])/d['central_mae']*100:+.1f}%"],
        ["RMSE", f"{d['final_rmse']:.4f}", f"{d['central_rmse']:.4f}",
         f"{(d['final_rmse']-d['central_rmse'])/d['central_rmse']*100:+.1f}%"],
        ["Privacy", "No raw data shared", "Raw data centralised", "—"],
        ["Bandwidth", "Weights only", "Full raw stream", "—"],
    ]
    elems += [Paragraph("Federated vs Centralized", h2), _table(comp_rows, [4*cm]*4, header=True)]

    doc.build(elems)
    return buf.getvalue()


def _table(rows, col_widths, header=False):
    t = Table(rows, colWidths=col_widths)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#1A2535")),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B5BD3")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]
    t.setStyle(TableStyle(style))
    return t


def build_docx_report() -> bytes:
    d = _report_data()
    doc = Document()

    title = doc.add_heading("TechKnights — Federated Traffic-Flow Prediction", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph("Experiment Evaluation Report")
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_heading("Configuration", level=1)
    _docx_kv_table(doc, [
        ("Dataset", d["dataset"]), ("Distribution", d["mode"]),
        ("Clients", str(d["clients"])), ("Rounds completed", str(d["rounds"])),
        ("Seed", str(d["seed"])), ("Speed", d["speed"]),
    ])

    doc.add_heading("Summary Metrics", level=1)
    _docx_kv_table(doc, [
        ("Final Federated MAE", f"{d['final_mae']:.4f}"),
        ("Final Federated RMSE", f"{d['final_rmse']:.4f}"),
        ("Final Centralized MAE", f"{d['central_mae']:.4f}"),
        ("Final Centralized RMSE", f"{d['central_rmse']:.4f}"),
        ("Convergence round", d["convergence_label"]),
        ("Total communication (federated)", f"{d['total_kb']:.2f} KB"),
        ("Communication per round", f"{d['per_rnd']:.2f} KB/round"),
    ])

    doc.add_heading("Communication Cost Comparison", level=1)
    _docx_kv_table(doc, [
        ("Federated total (cumulative, actual)", _fmt_bytes(d["fed_total_bytes"])),
        (f"Centralized total (one-time, {SENSORS_DEFAULT} sensors × {TRAIN_FRAC:.0%} train split)",
         _fmt_bytes(d["cen_total_bytes"])),
        ("Model payload per transfer", _fmt_bytes(d["model_bytes"])),
        ("Reduction vs Centralized", f"{d['comm_reduction_pct']:.1f}%"),
    ])

    doc.add_heading("Round-wise Metrics", level=1)
    rt = doc.add_table(rows=1, cols=6)
    rt.style = "Light Grid Accent 1"
    hdr = rt.rows[0].cells
    for i, h in enumerate(["Round", "Fed MAE", "Fed RMSE", "Cen MAE", "Cen RMSE", "Comm (KB)"]):
        hdr[i].text = h
    for r, fm, fr, cm_, cr, cb in d["rounds_table"]:
        row = rt.add_row().cells
        row[0].text, row[1].text, row[2].text = str(r), f"{fm:.4f}", f"{fr:.4f}"
        row[3].text, row[4].text, row[5].text = f"{cm_:.4f}", f"{cr:.4f}", f"{cb/1024:.2f}"

    if d["client_maes"]:
        doc.add_heading("Client Performance (final round)", level=1)
        ct = doc.add_table(rows=1, cols=2)
        ct.style = "Light Grid Accent 1"
        ct.rows[0].cells[0].text, ct.rows[0].cells[1].text = "Client", "Final MAE"
        for i, v in enumerate(d["client_maes"]):
            row = ct.add_row().cells
            row[0].text, row[1].text = f"Client {i+1}", f"{v:.4f}"

    doc.add_heading("Federated vs Centralized", level=1)
    _docx_kv_table(doc, [
        ("MAE — Federated", f"{d['final_mae']:.4f}"),
        ("MAE — Centralized", f"{d['central_mae']:.4f}"),
        ("RMSE — Federated", f"{d['final_rmse']:.4f}"),
        ("RMSE — Centralized", f"{d['central_rmse']:.4f}"),
        ("Privacy", "Federated: no raw data shared  |  Centralized: raw data centralised"),
        ("Bandwidth", "Federated: weights only  |  Centralized: full raw stream"),
    ])

    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _docx_kv_table(doc, pairs):
    t = doc.add_table(rows=0, cols=2)
    t.style = "Light List Accent 1"
    for k, v in pairs:
        row = t.add_row().cells
        row[0].text, row[1].text = k, v


# ─── RENDER FUNCTIONS ────────────────────────────────────────────────────────
def render_header():
    cfg = active_cfg()
    s = st.session_state
    if s.running:
        lab, cls = "TRAINING", "pl-amber pulse"
    elif s.rounds_done > 0:
        lab, cls = "COMPLETE", "pl-green"
    else:
        lab, cls = "IDLE", "pl-green"
    speed_lab = cfg["speed"].split(" ", 1)[-1]
    if LOGO_B64:
        logo = f'<img class="logo" src="data:image/png;base64,{LOGO_B64}" alt="TechKnights"/>'
    else:
        logo = f'<span class="logo logo-fb">{ico("shield", 34)}</span>'
    header_ph.markdown(H(f'''<div class="hdr"><div class="hdr-l">{logo}
<span class="brand">TechKnights</span><span class="vsep"></span>
<div><div class="ttl">Federated Traffic-Flow Prediction</div>
<div class="sub">Federated Learning<b>•</b>Traffic Analytics Simulator</div></div></div>
<div class="hdr-r">
<div class="pbox"><div class="pl {cls}"><span class="dot"></span>{lab}</div><div class="plab">System Status</div></div>
<div class="pbox"><div class="pl pl-violet">{ico("user", 16)}{cfg["mode"]}</div><div class="plab">Data Distribution</div></div>
<div class="pbox"><div class="pl pl-amber">{ico("bolt", 16)}{speed_lab}</div><div class="plab">Training Mode</div></div>
</div></div>'''), unsafe_allow_html=True)


def kpi(cls, icon, label, value, tip, sub="", bar=None):
    bar_html = f'<div class="kbar"><i style="width:{bar}%"></i></div>' if bar is not None else ""
    return H(f'''<div class="kpi {cls}"><div class="kpi-top"><span>{ico(icon, 20)}</span>
<span class="kpi-lab">{label}</span><span class="kpi-info" title="{tip}">{ico("info", 16)}</span></div>
<div class="kpi-val">{value}</div>{bar_html}<div class="kpi-sub">{sub}</div></div>''')


def render_metrics():
    s, cfg = st.session_state, active_cfg()
    fm = s.fed_mae[-1] if s.fed_mae else 0.0
    fr = s.fed_rmse[-1] if s.fed_rmse else 0.0
    kb = sum(s.comm_bytes) / 1024 if s.comm_bytes else 0.0
    pct = int(s.rounds_done / cfg["total"] * 100) if cfg["total"] else 0
    with metric_ph.container():
        c1, c2, c3, c4 = st.columns(4, gap="medium")
        c1.markdown(kpi("cyan", "line", "Federated MAE", f"{fm:.3f}",
                        "Mean absolute error of the global model (latest round)", "vehicles / 5-min slot"),
                    unsafe_allow_html=True)
        c2.markdown(kpi("green", "bars", "Federated RMSE", f"{fr:.3f}",
                        "Root mean square error of the global model (latest round)", "root mean square error"),
                    unsafe_allow_html=True)
        c3.markdown(kpi("amber", "cloud", "Communication Cost (Total)", f"{kb:.1f}",
                        "Total bytes exchanged between clients and server", "KB transmitted so far"),
                    unsafe_allow_html=True)
        c4.markdown(kpi("violet", "refresh", "Training Round", f"{s.rounds_done} / {cfg['total']}",
                        "Completed federated rounds", f'{ico("users", 15)}{cfg["clients"]} clients', bar=pct),
                    unsafe_allow_html=True)


def render_tabs():
    s, cfg = st.session_state, active_cfg()
    s.render_tick += 1
    tick = s.render_tick
    h = chart_height()
    with tabs_ph.container():
        tab1, tab2, tab3, tab4 = st.tabs([
            ":material/bar_chart: Training Progress",
            ":material/table_rows: Round Details",
            ":material/balance: Federated vs Centralized",
            ":material/description: Evaluation Report",
        ])

        with tab1:
            st.markdown(ph("bars", "Prediction Error Over Rounds"), unsafe_allow_html=True)
            if s.fed_mae:
                st.plotly_chart(build_convergence_chart(h, cfg["total"]), width="stretch",
                                config={"displayModeBar": False}, key=f"conv_{tick}")
            else:
                st.markdown(empty_state(h), unsafe_allow_html=True)

        with tab2:
            st.markdown(ph("repeat", "Communication Cost per Round"), unsafe_allow_html=True)
            if s.comm_bytes:
                st.plotly_chart(build_comm_chart(s.comm_bytes, cfg["total"]), width="stretch",
                                config={"displayModeBar": False}, key=f"comm_{tick}")
                rows = ""
                for i, (fm, fr, cm, cr, cb) in enumerate(zip(s.fed_mae, s.fed_rmse, s.central_mae,
                                                             s.central_rmse, s.comm_bytes), 1):
                    rows += (f"<tr><td><span class='round-badge'>R{i:02d}</span></td><td>{fm:.4f}</td>"
                             f"<td>{fr:.4f}</td><td>{cm:.4f}</td><td>{cr:.4f}</td><td>{cb/1024:.2f} KB</td></tr>")
                st.markdown(H(f'''<table class="cmp-table"><thead><tr><th>Round</th><th>Fed MAE</th><th>Fed RMSE</th>
<th>Central MAE</th><th>Central RMSE</th><th>Comm.</th></tr></thead><tbody>{rows}</tbody></table>'''),
                            unsafe_allow_html=True)
            else:
                st.markdown(empty_state(300), unsafe_allow_html=True)

        with tab3:
            st.markdown(ph("scale", "Federated vs Centralized"), unsafe_allow_html=True)
            if s.fed_mae and s.central_mae:
                fm, fr = s.fed_mae[-1], s.fed_rmse[-1]
                cm, cr = s.central_mae[-1], s.central_rmse[-1]
                wm = "win" if fm <= cm else "lose"
                wr = "win" if fr <= cr else "lose"
                st.markdown(H(f'''<table class="cmp-table"><thead><tr><th>Metric</th><th>Federated</th>
<th>Centralized</th><th>Gap</th></tr></thead><tbody>
<tr><td>MAE</td><td class="{wm}">{fm:.4f}</td><td>{cm:.4f}</td><td>{(fm-cm)/cm*100:+.1f}%</td></tr>
<tr><td>RMSE</td><td class="{wr}">{fr:.4f}</td><td>{cr:.4f}</td><td>{(fr-cr)/cr*100:+.1f}%</td></tr>
<tr><td>Privacy</td><td class="win">✓ No raw data shared</td><td class="lose">✗ Raw data centralised</td><td>—</td></tr>
<tr><td>Bandwidth</td><td class="win">Weights only</td><td class="lose">Full raw stream</td><td>—</td></tr>
</tbody></table>'''), unsafe_allow_html=True)
                note = ("⚠️ Non-IID causes client drift — local models diverge before aggregation."
                        if s.mode == "Non-IID"
                        else "✓ IID distribution — FedAvg converges close to the centralized baseline.")
                st.markdown(H(f'<div class="note">Mode: <b style="color:#A78BFA">{s.mode}</b><br>{note}</div>'),
                            unsafe_allow_html=True)
            else:
                st.markdown(empty_state(300), unsafe_allow_html=True)

        with tab4:
            st.markdown(ph("doc", "Experiment Summary Report"), unsafe_allow_html=True)
            if s.fed_mae:
                d = _report_data()
                obs = ("Non-IID distribution introduced client drift, widening the error gap vs centralized."
                       if s.mode == "Non-IID"
                       else "IID distribution — FedAvg converged close to the centralized baseline.")
                st.markdown(H(f'''<table class="kv">
<tr><td>Dataset</td><td>{s.dataset}</td></tr><tr><td>Distribution</td><td>{s.mode}</td></tr>
<tr><td>Clients</td><td>{s.num_clients}</td></tr><tr><td>Rounds</td><td>{s.rounds_done}</td></tr>
<tr><td>Seed</td><td>{s.seed}</td></tr><tr><td>Speed</td><td>{s.speed}</td></tr>
<tr><td>Final MAE</td><td style="color:#00FF88">{d['final_mae']:.4f}</td></tr>
<tr><td>Final RMSE</td><td style="color:#00FF88">{d['final_rmse']:.4f}</td></tr>
<tr><td>Convergence</td><td style="color:#FFB547">{d['convergence_label']}</td></tr>
<tr><td>Total comm. (federated)</td><td style="color:#FFB547">{d['total_kb']:.2f} KB</td></tr>
<tr><td>Per round</td><td>{d['per_rnd']:.2f} KB/round</td></tr></table>
<div class="note" style="font-size:1.05rem;line-height:1.9"><b style="color:#00D4FF;font-size:1.15rem">Communication Cost Comparison</b><br>
Federated total (cumulative, {s.rounds_done} rounds, {s.num_clients} clients):
<b style="color:#00D4FF">{_fmt_bytes(d["fed_total_bytes"])}</b><br>
Centralized total (one-time raw upload, {SENSORS_DEFAULT} sensors × {TRAIN_FRAC:.0%} train split):
<b style="color:#FFB547">{_fmt_bytes(d["cen_total_bytes"])}</b><br>
Model payload per transfer (back-solved from real round data):
{_fmt_bytes(d["model_bytes"])}<br>
Reduction vs Centralized: <b style="color:#00FF88">{d["comm_reduction_pct"]:.1f}%</b></div>
<div class="note"><b style="color:#00D4FF">Observations</b><br>{obs}<br>
Communication cost scales linearly with client count.<br>
No raw data left local devices — privacy preserved ✓</div>'''),
                            unsafe_allow_html=True)

                # ── Download buttons (only shown when valid results exist) ──
                if not s.running:   # only generate reports once training has finished
                    dl1, dl2 = st.columns(2)
                    with dl1:
                        st.download_button(
                            "📄 Download PDF Report", data=build_pdf_report(),
                            file_name=f"TechKnights_Report_{s.mode}_seed{s.seed}.pdf",
                            mime="application/pdf", width="stretch",
                            key=f"pdf_dl_{tick}",
                        )
                    with dl2:
                        st.download_button(
                            "📝 Download Word Report", data=build_docx_report(),
                            file_name=f"TechKnights_Report_{s.mode}_seed{s.seed}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            width="stretch",
                            key=f"docx_dl_{tick}",
                        )
            else:
                st.markdown(empty_state(300), unsafe_allow_html=True)


def render_side():
    s, cfg = st.session_state, active_cfg()
    total = cfg["total"]
    pct = int(s.rounds_done / total * 100) if total else 0
    if s.running:
        pill, pcls = "Training", "run"
    elif s.rounds_done > 0:
        pill, pcls = "Complete", "done"
    else:
        pill, pcls = "Waiting", ""
    cards = ""
    for i in range(cfg["clients"]):
        hist = [r[i] for r in s.client_hist if i < len(r)]
        mae_txt = f" &nbsp;|&nbsp; MAE {hist[-1]:.3f}" if hist else ""
        cards += H(f'''<div class="ag {AGENT_CLASS[i]}"><span class="ag-ico">{ico("node", 30)}</span>
<div class="ag-main"><div class="ag-t">{INTERSECTION_NAMES[i]}<em>(Client {i + 1})</em></div>
<div class="ag-p">Round {s.rounds_done} / {total} &nbsp;|&nbsp; {pct}%{mae_txt}</div>
<div class="ag-bar"><i style="width:{pct}%"></i></div></div>
<div class="ag-r"><span class="pill {pcls}">{pill}</span>{spark(hist, AGENT_HEX[i])}</div></div>''')
    if s.logs:
        lines = ""
        for ts, msg, kind in reversed(s.logs[-14:]):
            css = {"ok": "log-ok", "warn": "log-warn", "info": "log-info"}.get(kind, "")
            lines += f'<span class="log-ts">[{ts}]</span> <span class="{css}">{msg}</span><br>'
        act = f'<div class="act">{lines}</div>'
    else:
        act = H(f'''<div class="act"><div class="act-empty">{ico("clock", 30)}<span>No activity yet...</span>
<small>Events will appear here once you run an experiment.</small></div></div>''')
    side_ph.markdown(H(f'''<div class="sp"><div class="sp-t">CLIENT AGENTS</div>{cards}</div>
<div class="sp"><div class="sp-t">AGENT ACTIVITY</div>{act}</div>'''), unsafe_allow_html=True)


def render_all():
    render_header()
    render_metrics()
    render_tabs()
    render_side()


# ─── RESET ───────────────────────────────────────────────────────────────────
if reset_clicked:
    for k in ["fed_mae", "fed_rmse", "central_mae", "central_rmse", "comm_bytes",
              "logs", "client_status", "client_hist"]:
        st.session_state[k] = []
    st.session_state.rounds_done = 0
    st.session_state.running = False
    st.rerun()

# ─── INITIAL RENDER ──────────────────────────────────────────────────────────
render_all()

# ─── LIVE TRAINING LOOP ──────────────────────────────────────────────────────
if run_clicked:
    if run_clicked:
        st.session_state.mode         = sel_mode
        st.session_state.num_clients  = sel_clients
        st.session_state.total_rounds = sel_rounds          # ← the missing line
        st.session_state.seed         = sel_seed
        st.session_state.dataset      = sel_dataset
        st.session_state.speed        = sel_speed
        st.session_state.fed_mae      = []
        st.session_state.fed_rmse     = []
        st.session_state.central_mae  = []
        st.session_state.central_rmse = []
        st.session_state.comm_bytes   = []
        st.session_state.client_hist  = []
        st.session_state.client_status = []
        st.session_state.rounds_done  = 0
        st.session_state.logs         = []
        st.session_state.running      = True
    rows = load_experiment(sel_mode, sel_seed, sel_clients)
    if not rows:
        add_log(f"No stored results for mode={sel_mode}, seed={sel_seed}. Run the Colab sweep first.", "warn")
        st.session_state.running = False
    else:
        add_log(f"Loaded {len(rows)} rounds — {sel_mode}, seed={sel_seed}", "info")
        render_all()
        delay = SPEED_MAP.get(sel_speed, 0.35)

        for row in rows[:sel_rounds]:
            st.session_state.fed_mae.append(row["fed_mae"])
            st.session_state.fed_rmse.append(row["fed_rmse"])
            st.session_state.central_mae.append(row["cen_mae"])
            st.session_state.central_rmse.append(row["cen_rmse"])
            st.session_state.comm_bytes.append(row["comm_bytes"])
            st.session_state.client_status = row["client_maes"]
            st.session_state.client_hist.append(row["client_maes"])
            st.session_state.rounds_done = row["round"]

            add_log(f"Round {row['round']:02d} · Fed MAE={row['fed_mae']} · RMSE={row['fed_rmse']}", "ok")
            render_metrics(); render_tabs(); render_side()
            time.sleep(delay)

        st.session_state.running = False
        add_log("All rounds complete ✓", "ok")
        render_all()