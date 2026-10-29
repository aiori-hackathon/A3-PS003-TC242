"""
intro_screen.py  —  Cinematic landing sequence for the TechKnights dashboard (storyboard version).

Stages (match the storyboard):
  1. Landing      : glowing car-icon ring over a neon road + the one cyan button
  2. Approach     : light pillars power up, car drives in from the distance (front view)
  3. Docking/Sync : charging stations connect with energy cables, spinner + progress 0 -> 100 %
  4. READY !!!    : big glowing text, rear-view car speeds away with light trails
  5. Dashboard    : glow/fade transition, then the existing TechKnights dashboard

Integration contract with app.py (unchanged from the previous version):
  * st.session_state.intro_done  (bool)  — False = show intro, True = show dashboard
  * render_intro()               — call before the dashboard layout, then st.stop()
  * render_replay_button()       — optional tiny "Replay intro" button

Hand-off: the animation runs in the browser (HTML/CSS/JS in components.html). When it finishes,
the JS clicks the small "Skip intro" Streamlit button in the parent page, which sets
intro_done = True. The same button is a manual skip and the fallback if auto-click can't run.
"""
import sqlite3
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

DB_PATH = Path(__file__).parent / "results" / "experiments.db"
INTRO_HEIGHT = 660


# ─── helpers ────────────────────────────────────────────────────────────────
@st.cache_data
def _payload_kb() -> float:
    """Real one-way per-client payload from stored results:
    comm_bytes = 2 * num_clients * model_bytes  ->  model KB = comm_bytes / (2*clients) / 1024.
    Falls back to a sensible default if the DB isn't readable."""
    try:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute("SELECT comm_bytes, num_clients FROM rounds LIMIT 1").fetchone()
        conn.close()
        return round(row[0] / (2 * row[1]) / 1024, 2)
    except Exception:
        return 42.8


def _finish_intro():
    st.session_state.intro_done = True


def _replay_intro():
    st.session_state.intro_done = False


_SKIP_CSS = """
<style>
.st-key-btn_skip_intro{display:flex;justify-content:center;margin-top:-2px}
.st-key-btn_skip_intro button{background:transparent;border:1px solid #1E3A5F;color:#6F8FB0;
  border-radius:8px;font-size:.78rem;min-height:34px;padding:0 16px}
.st-key-btn_skip_intro button:hover{border-color:#00D4FF;color:#00D4FF}
.st-key-btn_replay_intro{display:flex;justify-content:center}
.st-key-btn_replay_intro button{background:transparent;border:1px solid #14304F;color:#5F7F9F;
  border-radius:8px;font-size:.72rem;min-height:30px;padding:0 14px}
.st-key-btn_replay_intro button:hover{border-color:#00D4FF;color:#00D4FF}
</style>
"""


def render_intro():
    """Render the landing animation. Caller should st.stop() right after."""
    st.markdown(_SKIP_CSS, unsafe_allow_html=True)
    html = INTRO_HTML.replace("__PAYLOAD_KB__", str(_payload_kb()))
    try:
        components.html(html, height=INTRO_HEIGHT, scrolling=False)
    except TypeError:
        # newer Streamlit builds: no `scrolling` kwarg
        components.html(html, height=INTRO_HEIGHT)
    st.button("Skip intro", icon=":material/skip_next:", key="btn_skip_intro",
              on_click=_finish_intro)


def render_replay_button():
    """Small ghost button for the bottom of the dashboard. Does not touch experiment state."""
    st.markdown(_SKIP_CSS, unsafe_allow_html=True)
    st.button("↺ Replay intro", key="btn_replay_intro", on_click=_replay_intro)


# ─── the animation (plain HTML/CSS/JS; raw string so braces/backslashes are safe) ──
INTRO_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700;800&display=swap');
:root{--cy:0,212,255;--mono:'JetBrains Mono',ui-monospace,Menlo,Consolas,monospace}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;overflow:hidden;background:transparent;font-family:'Inter',system-ui,sans-serif;color:#E6F0FF}
.vp{position:absolute;inset:0;padding:4px}
.frame{position:relative;width:100%;height:100%;border-radius:18px;overflow:hidden;border:1px solid rgba(var(--cy),.28);
  background:radial-gradient(900px 420px at 50% 36%,rgba(0,110,255,.17),transparent 65%),linear-gradient(180deg,#050D1B,#061326 55%,#040B16);
  box-shadow:0 0 38px rgba(var(--cy),.12);animation:enter .9s ease backwards;
  transition:opacity .9s ease,transform .9s ease,filter .9s ease}
.frame.exit{opacity:0;transform:scale(1.045);filter:blur(6px) brightness(1.7)}
.frame::after{content:"";position:absolute;left:0;right:0;bottom:0;height:72px;pointer-events:none;z-index:4;
  background:linear-gradient(transparent,#040B16 88%)}
@keyframes enter{from{opacity:0;transform:translateY(12px) scale(.985)}to{opacity:1;transform:none}}

/* world: fixed 1200x600 logical canvas, scaled to fit the iframe by JS */
.world{position:absolute;left:50%;top:50%;width:1200px;height:600px;transform-origin:50% 50%}
.world>*{position:absolute}
#roadsvg{left:-40px;top:0;width:1280px;height:600px;overflow:visible}

/* stations (light pillars -> charging stations) */
.stn{top:150px;width:120px;height:330px;opacity:0;transition:opacity .9s ease;z-index:2}
.stn.l{left:150px}.stn.r{left:930px;transform:scaleX(-1)}
.powered .stn{opacity:1}
.stn svg{width:100%;height:100%;overflow:visible}
.stn .bar{filter:drop-shadow(0 0 7px #19B8FF)}
.powered .stn .bar{animation:barp 2.4s ease-in-out infinite}
.stn .strip{opacity:.35;transition:opacity .6s}
.docked .stn .strip{opacity:1;animation:barp 1.1s ease-in-out infinite}
@keyframes barp{50%{filter:drop-shadow(0 0 18px #4FD8FF) brightness(1.45)}}

.pad{left:400px;top:490px;width:400px;height:44px;border-radius:50%;border:1px solid rgba(var(--cy),.4);z-index:3;opacity:0;
  background:radial-gradient(ellipse,rgba(var(--cy),.35),transparent 70%);transition:opacity .5s}
.docked .pad{opacity:1;animation:padp 1.3s ease-in-out infinite}
@keyframes padp{50%{box-shadow:0 0 30px rgba(var(--cy),.7)}}

/* sensor on the left edge */
.sensor{left:6px;top:262px;width:110px;height:90px;z-index:3;filter:drop-shadow(0 0 6px rgba(var(--cy),.7))}
.run .sensor{animation:barp 2s ease-in-out infinite}
.syncing .sensor{animation:barp .9s ease-in-out infinite}

/* cars */
.car{left:600px;top:330px;width:360px;height:190px;margin-left:-180px;transform-origin:50% 100%;z-index:5;opacity:0;
  will-change:transform,opacity;filter:drop-shadow(0 0 14px rgba(0,150,255,.65));
  -webkit-box-reflect:below 2px linear-gradient(transparent 60%,rgba(255,255,255,.22))}
.car svg{width:100%;height:100%;overflow:visible}
.syncing .car{filter:drop-shadow(0 0 26px rgba(30,180,255,.95))}

/* cables */
#cables{left:0;top:0;width:1200px;height:600px;z-index:6;pointer-events:none;overflow:visible}
.cab-base{opacity:0;transition:opacity .6s}.docked .cab-base{opacity:1}
.cab-draw{stroke-dasharray:100;stroke-dashoffset:100;transition:stroke-dashoffset 1s ease}
.docked .cab-draw{stroke-dashoffset:0}
.cab-flow{opacity:0;stroke-dasharray:3 9;transition:opacity .4s}
.syncing .cab-flow{opacity:1;animation:cflow .5s linear infinite}
.syncing .cab-draw{animation:cflick .18s steps(2) infinite}
@keyframes cflow{to{stroke-dashoffset:-12}}
@keyframes cflick{50%{filter:brightness(1.6)}}
.pts{left:400px;top:250px;width:400px;height:260px;z-index:7;pointer-events:none}
.pt{position:absolute;width:4px;height:4px;border-radius:50%;background:#9AF3FF;box-shadow:0 0 8px #19D8FF;opacity:0}
.syncing .pt{animation:flt 2.4s linear infinite}
@keyframes flt{0%{transform:translate(0,0);opacity:0}20%{opacity:1}100%{transform:translate(var(--dx),-110px);opacity:0}}

/* speed streaks */
#streaks{left:0;top:0;width:1200px;height:600px;z-index:4;opacity:0;transition:opacity .5s;pointer-events:none;overflow:visible}
.leaving #streaks{opacity:1}
.sl{stroke-dasharray:14 86;animation:streak .55s linear infinite}
@keyframes streak{from{stroke-dashoffset:14}to{stroke-dashoffset:-100}}

/* HUD layers (inside world, top centre) */
.hud{left:0;width:1200px;text-align:center;z-index:9;transition:opacity .6s ease,transform .6s ease}
.h-land{top:30px;display:flex;flex-direction:column;align-items:center}
.run .h-land{opacity:0;transform:translateY(-12px);pointer-events:none}
.ring{filter:drop-shadow(0 0 14px rgba(var(--cy),.7));animation:ringp 2.6s ease-in-out infinite}
@keyframes ringp{50%{filter:drop-shadow(0 0 30px rgba(var(--cy),.95))}}
.cap{font-family:var(--mono);font-size:12px;letter-spacing:.16em;color:#7FB4DA;margin:10px 0 14px}
.go{font-family:var(--mono);font-weight:700;font-size:13px;letter-spacing:.07em;color:#02121E;white-space:nowrap;
  background:linear-gradient(135deg,#00E5FF,#00B8E6);border:none;border-radius:10px;padding:14px 30px;cursor:pointer;
  box-shadow:0 0 24px rgba(0,212,255,.6);animation:glow 2s ease-in-out infinite;transition:transform .15s,filter .2s}
.go:hover:not(:disabled){transform:translateY(-1px);filter:brightness(1.12)}
.go:disabled{cursor:default;animation:none;filter:saturate(.55) brightness(.7)}
@keyframes glow{50%{box-shadow:0 0 44px rgba(0,212,255,.95)}}

.h-sync{top:14px;opacity:0;pointer-events:none;display:flex;flex-direction:column;align-items:center}
.sync .h-sync{opacity:1}
.spin{animation:rot 1.1s linear infinite;filter:drop-shadow(0 0 8px rgba(var(--cy),.8))}
@keyframes rot{to{transform:rotate(360deg)}}
.sy-t{font-family:var(--mono);font-weight:700;font-size:15px;letter-spacing:.14em;color:#19D8FF;margin-top:10px;text-shadow:0 0 12px rgba(var(--cy),.7)}
.sy-bar{width:380px;height:16px;border-radius:9px;margin-top:12px;border:1px solid rgba(var(--cy),.55);background:rgba(2,16,34,.85);padding:2px;
  box-shadow:0 0 14px rgba(var(--cy),.25)}
.sy-bar i{display:block;height:100%;width:0;border-radius:6px;background:linear-gradient(90deg,#0095FF,#19E5FF);box-shadow:0 0 14px #19D8FF;position:relative;overflow:hidden}
.syncing .sy-bar i::after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,transparent,rgba(255,255,255,.55),transparent);animation:shim 1s linear infinite}
@keyframes shim{from{transform:translateX(-100%)}to{transform:translateX(100%)}}
.sy-p{font-family:var(--mono);font-weight:700;font-size:34px;color:#19E5FF;margin-top:8px;text-shadow:0 0 16px rgba(var(--cy),.8)}

.h-ready{top:58px;opacity:0;pointer-events:none}
.ready .h-ready{opacity:1;animation:pop .75s cubic-bezier(.2,1.4,.4,1) both}
.h-ready b{font-family:var(--mono);font-weight:800;font-size:84px;letter-spacing:.1em;color:#EFFFFF;
  text-shadow:0 0 8px #00E5FF,0 0 26px #00D4FF,0 0 60px rgba(0,212,255,.9),0 0 120px rgba(0,150,255,.7)}
.ready .h-ready b{animation:flick 2.2s ease-in-out .75s infinite}
@keyframes pop{from{opacity:0;transform:scale(.55);filter:blur(10px)}to{opacity:1;transform:scale(1);filter:none}}
@keyframes flick{50%{filter:brightness(1.35)}}

/* overlays outside the world */
.tl,.tr{position:absolute;top:14px;z-index:12;font-family:var(--mono);font-size:11px;letter-spacing:.08em}
.tl{left:18px;display:flex;align-items:center;gap:10px;color:#CFE6FF;font-weight:700}
.tl .dot{width:9px;height:9px;border-radius:50%;background:#12384F;transition:.4s}
.run .tl .dot{background:#00D4FF;box-shadow:0 0 12px #00D4FF}
.badge{font-size:9px;padding:2px 7px;border-radius:4px;border:1px solid rgba(var(--cy),.5);color:#00D4FF;background:rgba(var(--cy),.1)}
.tr{right:18px;color:#E6F0FF;font-weight:700;padding:5px 11px;border:1px solid rgba(255,255,255,.16);border-radius:6px;background:rgba(255,255,255,.05)}
.bar{position:absolute;left:16px;right:16px;bottom:12px;z-index:12;display:flex;justify-content:space-between;align-items:center;gap:14px;
  padding:9px 14px;border-radius:8px;border:1px solid rgba(var(--cy),.18);background:rgba(3,9,20,.85);
  font-family:var(--mono);font-size:10.5px;color:#7FA3C4;letter-spacing:.05em}
.bar i{display:inline-block;width:7px;height:7px;border-radius:50%;background:#00D4FF;box-shadow:0 0 8px #00D4FF;margin-right:8px}
.bar #stat{color:#19D8FF;font-weight:600;text-align:center;flex:1}

.flash{position:absolute;inset:0;pointer-events:none;opacity:0;transition:opacity .55s ease;z-index:20;
  background:radial-gradient(circle at 50% 50%,rgba(0,212,255,.6),transparent 62%)}
.flash.on{opacity:1}
.fb{position:absolute;left:0;right:0;bottom:60px;text-align:center;display:none;font-size:13px;color:#8FB0D0;z-index:30}
</style></head>
<body>
<div class="vp" id="vp">
 <div class="frame" id="frame">

  <div class="world" id="world">
   <!-- road -->
   <svg id="roadsvg" viewBox="-40 0 1280 600">
    <defs>
     <filter id="glow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
     <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0A2548" stop-opacity=".25"/><stop offset="1" stop-color="#06162C" stop-opacity=".9"/></linearGradient>
    </defs>
    <polygon points="400,330 800,330 1240,600 -40,600" fill="url(#floor)"/>
    <g id="grid"></g>
    <line x1="400" y1="330" x2="-40" y2="600" stroke="#19D8FF" stroke-width="2.4" filter="url(#glow)"/>
    <line x1="800" y1="330" x2="1240" y2="600" stroke="#19D8FF" stroke-width="2.4" filter="url(#glow)"/>
    <line x1="400" y1="330" x2="800" y2="330" stroke="#19D8FF" stroke-width="1.5" opacity=".6"/>
    <g id="dashes" filter="url(#glow)"></g>
   </svg>

   <!-- left sensor -->
   <svg class="sensor" viewBox="0 0 110 90"><g stroke="#2DE0FF" stroke-width="2.4" fill="none" stroke-linecap="round" stroke-linejoin="round">
     <path d="M20 30L74 24L76 44L20 52"/><circle cx="22" cy="42" r="14"/><circle cx="22" cy="42" r="5" fill="#2DE0FF"/>
     <path d="M32 54V76M18 76H46"/><path d="M80 34H96" stroke="#fff"/></g></svg>

   <!-- stations -->
   <div class="stn l"><svg viewBox="0 0 120 330">
     <rect class="bar" x="96" y="0" width="4" height="330" fill="#25C4FF"/><rect x="108" y="40" width="1.5" height="290" fill="#25C4FF" opacity=".5"/>
     <rect x="34" y="70" width="54" height="240" rx="10" fill="#061426" stroke="#1E7FCF" stroke-width="1.6"/>
     <rect class="strip" x="44" y="94" width="6" height="190" rx="3" fill="#1AA3FF"/>
     <rect x="56" y="96" width="22" height="44" rx="3" fill="#0A2B4D" stroke="#2DB6FF"/>
     <path d="M60 106H74M60 114H74M60 122H70" stroke="#19D8FF" stroke-width="1.5"/>
     <rect x="24" y="302" width="74" height="14" rx="4" fill="#0A2B4D" stroke="#1E7FCF"/>
     <circle cx="88" cy="250" r="7" fill="#00D4FF" filter="url(#glow)"/></svg></div>
   <div class="stn r"><svg viewBox="0 0 120 330">
     <rect class="bar" x="96" y="0" width="4" height="330" fill="#25C4FF"/><rect x="108" y="40" width="1.5" height="290" fill="#25C4FF" opacity=".5"/>
     <rect x="34" y="70" width="54" height="240" rx="10" fill="#061426" stroke="#1E7FCF" stroke-width="1.6"/>
     <rect class="strip" x="44" y="94" width="6" height="190" rx="3" fill="#1AA3FF"/>
     <rect x="56" y="96" width="22" height="44" rx="3" fill="#0A2B4D" stroke="#2DB6FF"/>
     <path d="M60 106H74M60 114H74M60 122H70" stroke="#19D8FF" stroke-width="1.5"/>
     <rect x="24" y="302" width="74" height="14" rx="4" fill="#0A2B4D" stroke="#1E7FCF"/>
     <circle cx="88" cy="250" r="7" fill="#00D4FF" filter="url(#glow)"/></svg></div>

   <div class="pad"></div>
   <svg id="streaks" viewBox="0 0 1200 600"></svg>

   <!-- front-view car (arrives) -->
   <div class="car" id="carF"><svg viewBox="0 0 360 190" fill="none">
    <defs>
     <linearGradient id="cb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1B5C9E"/><stop offset="1" stop-color="#06182E"/></linearGradient>
     <linearGradient id="cg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1D6FB5"/><stop offset="1" stop-color="#071B33"/></linearGradient>
     <radialGradient id="cu"><stop offset="0" stop-color="#19A6FF" stop-opacity=".6"/><stop offset="1" stop-color="#19A6FF" stop-opacity="0"/></radialGradient>
    </defs>
    <ellipse cx="180" cy="180" rx="175" ry="14" fill="url(#cu)"/>
    <rect x="34" y="138" width="44" height="46" rx="9" fill="#03101F" stroke="#1B6FB5" stroke-width="1.5"/>
    <rect x="282" y="138" width="44" height="46" rx="9" fill="#03101F" stroke="#1B6FB5" stroke-width="1.5"/>
    <path d="M22 130C22 113 34 105 56 101L90 93H270L304 101C326 105 338 113 338 130V150C338 158 330 162 320 162H40C30 162 22 158 22 150Z" fill="url(#cb)" stroke="#2DB6FF" stroke-width="1.6"/>
    <path d="M88 95L112 46C116 37 124 33 134 33H226C236 33 244 37 248 46L272 95Z" fill="url(#cg)" stroke="#2DB6FF" stroke-width="1.6"/>
    <path d="M118 90L134 51C136 46 140 44 146 44H214C220 44 224 46 226 51L242 90Z" fill="#0A2B4F" stroke="#4FC8FF"/>
    <path d="M140 88L152 52H170L158 88Z" fill="#fff" opacity=".08"/>
    <path d="M64 106H296" stroke="#4FC8FF" opacity=".6"/>
    <path d="M44 113L98 106L104 121L52 129Z" fill="#E8FCFF" filter="url(#glow)"/>
    <path d="M316 113L262 106L256 121L308 129Z" fill="#E8FCFF" filter="url(#glow)"/>
    <path d="M52 134L100 127M308 134L260 127" stroke="#9BE9FF" stroke-width="2" opacity=".8"/>
    <rect x="140" y="120" width="80" height="24" rx="7" fill="#03101F" stroke="#2DB6FF"/>
    <path d="M148 128H212M148 134H212" stroke="#1B6FB5" stroke-width="1.5"/>
    <path d="M70 148H290L280 158H80Z" fill="#03101F" stroke="#2DB6FF"/>
    <rect x="170" y="28" width="20" height="5" rx="2.5" fill="#00E5FF"/>
    <rect x="76" y="84" width="14" height="8" rx="3" fill="#0A2B4F" stroke="#2DB6FF"/>
    <rect x="270" y="84" width="14" height="8" rx="3" fill="#0A2B4F" stroke="#2DB6FF"/>
   </svg></div>

   <!-- rear-view car (departs) -->
   <div class="car" id="carR"><svg viewBox="0 0 360 190" fill="none">
    <defs>
     <linearGradient id="rb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1B5C9E"/><stop offset="1" stop-color="#06182E"/></linearGradient>
     <radialGradient id="ru"><stop offset="0" stop-color="#FF4D7A" stop-opacity=".45"/><stop offset="1" stop-color="#FF4D7A" stop-opacity="0"/></radialGradient>
    </defs>
    <ellipse cx="180" cy="180" rx="175" ry="14" fill="url(#ru)"/>
    <rect x="34" y="138" width="44" height="46" rx="9" fill="#03101F" stroke="#1B6FB5" stroke-width="1.5"/>
    <rect x="282" y="138" width="44" height="46" rx="9" fill="#03101F" stroke="#1B6FB5" stroke-width="1.5"/>
    <path d="M22 130C22 113 34 105 56 101L90 93H270L304 101C326 105 338 113 338 130V150C338 158 330 162 320 162H40C30 162 22 158 22 150Z" fill="url(#rb)" stroke="#2DB6FF" stroke-width="1.6"/>
    <path d="M92 95L114 50C118 41 126 37 136 37H224C234 37 242 41 246 50L268 95Z" fill="url(#rb)" stroke="#2DB6FF" stroke-width="1.6"/>
    <path d="M122 90L136 55C138 51 142 49 148 49H212C218 49 222 51 224 55L238 90Z" fill="#071F3A" stroke="#4FC8FF"/>
    <path d="M38 112L106 108L110 121L46 129Z" fill="#FF3B5C" filter="url(#glow)"/>
    <path d="M322 112L254 108L250 121L314 129Z" fill="#FF3B5C" filter="url(#glow)"/>
    <path d="M106 114H254" stroke="#FF5C7A" stroke-width="3" filter="url(#glow)"/>
    <rect x="150" y="128" width="60" height="18" rx="3" fill="#0A2B4F" stroke="#2DB6FF"/>
    <path d="M70 150H290L282 158H78Z" fill="#03101F" stroke="#2DB6FF"/>
   </svg></div>

   <!-- cables -->
   <svg id="cables" viewBox="0 0 1200 600">
    <g fill="none" stroke-linecap="round">
     <path d="M238 400C290 330 330 520 372 440S420 470 446 455" class="cab-base" stroke="#06203F" stroke-width="8"/>
     <path d="M962 400C910 330 870 520 828 440S780 470 754 455" class="cab-base" stroke="#06203F" stroke-width="8"/>
     <path class="cab-draw" pathLength="100" d="M238 400C290 330 330 520 372 440S420 470 446 455" stroke="#19B8FF" stroke-width="3.2" filter="url(#glow)"/>
     <path class="cab-draw" pathLength="100" d="M962 400C910 330 870 520 828 440S780 470 754 455" stroke="#19B8FF" stroke-width="3.2" filter="url(#glow)"/>
     <path class="cab-flow" d="M238 400C290 330 330 520 372 440S420 470 446 455" stroke="#D6FAFF" stroke-width="1.8"/>
     <path class="cab-flow" d="M962 400C910 330 870 520 828 440S780 470 754 455" stroke="#D6FAFF" stroke-width="1.8"/>
    </g></svg>
   <div class="pts" id="pts"></div>

   <!-- HUD: landing -->
   <div class="hud h-land">
    <svg class="ring" width="140" height="140" viewBox="-70 -70 140 140" fill="none">
     <circle r="62" stroke="#19D8FF" stroke-width="4"/><circle r="68" stroke="#19D8FF" stroke-width="1" opacity=".35"/>
     <g stroke="#2DE0FF" stroke-width="3" stroke-linejoin="round" stroke-linecap="round">
      <path d="M-24 -4L-17 -24H17L24 -4"/><path d="M-34 2C-34 -3 -30 -5 -24 -4H24C30 -5 34 -3 34 2V16H-34Z"/>
      <path d="M-14 -6L-10 -18H10L14 -6"/><path d="M-27 7H-15M15 7H27"/><path d="M-28 16V25H-18V16M18 16V25H28V16"/></g></svg>
    <div class="cap">AWAITING PROBE VEHICLE</div>
    <button class="go" id="go">&#9679; SIMULATE VEHICLE ARRIVAL &amp; SYNC</button>
   </div>
   <!-- HUD: syncing -->
   <div class="hud h-sync">
    <svg class="spin" width="54" height="54" viewBox="0 0 54 54" fill="none"><circle cx="27" cy="27" r="21" stroke="#0E3556" stroke-width="5"/>
     <circle cx="27" cy="27" r="21" stroke="#19D8FF" stroke-width="5" stroke-dasharray="34 100" stroke-linecap="round"/></svg>
    <div class="sy-t">SYNCING VEHICLE DATA...</div>
    <div class="sy-bar"><i id="bar"></i></div>
    <div class="sy-p" id="pct">0%</div>
   </div>
   <!-- HUD: ready -->
   <div class="hud h-ready"><b>READY !!!</b></div>
  </div>

  <div class="tr" id="phase">PHASE 0: READY</div>
  <div class="bar"><span><i></i>V2X FREQ: 5.9 GHz (DSRC)</span><span id="stat">AWAITING PROBE HANDSHAKE</span><span>CARRIER: AIORI-MESH-DOWNTOWN</span></div>
  <div class="flash" id="flash"></div>
 </div>
 <div class="fb" id="fb">Intro complete &mdash; press &ldquo;Skip intro&rdquo; below to open the dashboard.</div>
</div>

<script>
(function(){
  var $=function(id){return document.getElementById(id)};
  var sleep=function(ms){return new Promise(function(r){setTimeout(r,ms)})};
  var NS='http://www.w3.org/2000/svg';
  function mk(tag,attrs,parent){var e=document.createElementNS(NS,tag);for(var k in attrs)e.setAttribute(k,attrs[k]);parent.appendChild(e);return e}
  var PAYLOAD_KB=__PAYLOAD_KB__;      // real per-client payload read from experiments.db
  var PACKETS=128;
  var vp=$('vp'),frame=$('frame'),world=$('world'),carF=$('carF'),carR=$('carR'),go=$('go'),flash=$('flash');
  var started=false;

  /* ---- scale the 1200x600 world to the iframe ---- */
  function fit(){
    var s=Math.min(vp.clientWidth/1200,vp.clientHeight/600);
    world.style.transform='translate(-50%,-50%) scale('+s+')';
  }
  window.addEventListener('resize',fit); fit();

  /* ---- road grid + perspective centre dashes ---- */
  var g=$('grid');
  for(var i=0;i<=10;i++){var k=i/10;mk('line',{x1:400+400*k,y1:330,x2:-40+1280*k,y2:600,stroke:'#0F4A7A','stroke-width':1,opacity:.55},g)}
  for(var j=1;j<=8;j++){var t=Math.pow(j/8,1.7),y=330+270*t;mk('line',{x1:400-440*t,y1:y,x2:800+440*t,y2:y,stroke:'#0F4A7A','stroke-width':1,opacity:.5},g)}
  var D=[[.03,.10],[.17,.29],[.38,.58],[.68,1.0]], dg=$('dashes');
  D.forEach(function(d){
    var y0=330+270*d[0],y1=330+270*d[1],w0=2+16*d[0],w1=2+16*d[1];
    mk('polygon',{points:(600-w0)+','+y0+' '+(600+w0)+','+y0+' '+(600+w1)+','+y1+' '+(600-w1)+','+y1,fill:'#19B8FF',opacity:.92},dg);
  });

  /* ---- speed streaks (shown while the car leaves) ---- */
  var st=$('streaks');
  for(var n=0;n<16;n++){
    var u=(n-7.5), c=n%2?'#8B7CFF':'#3FD2FF';
    mk('line',{x1:600+u*5,y1:338,x2:600+u*70,y2:600,pathLength:100,stroke:c,'stroke-width':1+(n%3)*.8,opacity:.5+(n%4)*.12,'class':'sl',
      style:'animation-delay:'+(-(n*37%100)/100*0.55)+'s'},st);
  }

  /* ---- sync particles ---- */
  var pts=$('pts');
  for(var p=0;p<34;p++){
    var d=document.createElement('span'); d.className='pt';
    d.style.left=(Math.random()*100)+'%'; d.style.top=(30+Math.random()*65)+'%';
    d.style.setProperty('--dx',((Math.random()-.5)*50)+'px');
    d.style.animationDelay=(-Math.random()*2.4)+'s'; pts.appendChild(d);
  }

  /* ---- phases / status ---- */
  var PH=[['PHASE 0: READY','AWAITING PROBE HANDSHAKE'],['PHASE 1: APPROACH','PROBE VEHICLE INBOUND'],
          ['PHASE 2: DOCKING','HANDSHAKE LOCKED \u00B7 CHARGING CABLES ENGAGED'],['PHASE 3: SYNC','INGESTING WEIGHTS'],
          ['PHASE 4: READY','SYNC COMPLETE \u00B7 GLOBAL MODEL READY'],['PHASE 5: DEPART','PROBE RELEASED \u00B7 LAUNCHING DASHBOARD']];
  function setPhase(n){$('phase').textContent=PH[n][0];$('stat').textContent=PH[n][1]}

  /* ---- car positions (bottom-centre origin) ---- */
  var FAR='translate(0px,-185px) scale(.12)', NEAR='translate(0px,0px) scale(1)';
  carF.style.transition='none'; carF.style.transform=FAR;
  carR.style.transition='none'; carR.style.transform=NEAR;

  function progress(ms){
    return new Promise(function(res){
      var t0=performance.now();
      (function tick(now){
        var t=Math.min(1,(now-t0)/ms), pct=t*100;
        $('bar').style.width=pct.toFixed(2)+'%';
        $('pct').textContent=Math.floor(pct)+'%';
        $('stat').textContent='INGESTING WEIGHTS \u00B7 '+(PAYLOAD_KB*t).toFixed(1)+' / '+PAYLOAD_KB+' KB \u00B7 '+Math.round(PACKETS*t)+' / '+PACKETS+' PACKETS';
        if(t<1) requestAnimationFrame(tick); else res();
      })(t0);
    });
  }
  function enterDashboard(){
    try{
      var btns=window.parent.document.querySelectorAll('button');
      for(var i=0;i<btns.length;i++){ if(/Skip intro/i.test(btns[i].textContent)){ btns[i].click(); return; } }
    }catch(e){}
    frame.classList.remove('exit'); flash.classList.remove('on'); $('fb').style.display='block';
  }

  async function run(){
    if(started) return; started=true;
    go.disabled=true;
    /* 2. approach */
    setPhase(1); frame.classList.add('run','powered');
    await sleep(700);
    void carF.offsetWidth;
    carF.style.transition='transform 3800ms cubic-bezier(.16,.7,.25,1), opacity .8s ease';
    carF.style.opacity=1; carF.style.transform=NEAR;
    await sleep(3900);
    /* 3. docking + sync */
    setPhase(2); frame.classList.add('docked','sync');
    await sleep(1400);
    setPhase(3); frame.classList.add('syncing');
    await progress(6500);
    frame.classList.remove('syncing');
    /* 4. ready + departure */
    setPhase(4); frame.classList.remove('sync'); frame.classList.add('ready');
    await sleep(1700);
    setPhase(5); frame.classList.remove('docked'); frame.classList.add('leaving');
    carF.style.transition='opacity .25s ease'; carF.style.opacity=0;
    carR.style.transition='opacity .25s ease'; carR.style.opacity=1;
    await sleep(300);
    carR.style.transition='transform 3000ms cubic-bezier(.5,0,.9,.55), opacity .6s ease';
    carR.style.transform=FAR;
    await sleep(2400);
    carR.style.opacity=0;
    await sleep(700);
    /* 5. transition to dashboard */
    frame.classList.add('exit'); flash.classList.add('on');
    await sleep(1000);
    enterDashboard();
  }
  go.addEventListener('click',run);
})();
</script>
</body></html>
"""