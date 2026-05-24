import streamlit as st
from datetime import date
import hashlib

from data.plan import WEEKS, PHASE_NAMES, PHASE_COLORS
from services.sheets import SheetsService

st.set_page_config(
    page_title="Canajagua 30K · Tracker",
    page_icon="🏔",
    layout="wide",
)

st.markdown("""
<style>
* { box-sizing: border-box; }
[data-testid="stAppViewContainer"] { background: #0b0c0e; }
[data-testid="stMainBlockContainer"] { padding: 0 !important; }
[data-testid="stHorizontalBlock"] { gap: 0 !important; }

/* Esconder sidebar nativo de Streamlit completamente */
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

.week-banner {
    background: linear-gradient(135deg, #1a1c20, #1f2228);
    border: 0.5px solid #2a2d35; border-radius: 12px;
    padding: 20px 24px; margin-bottom: 16px;
}
.week-num   { font-size:52px; font-weight:900; color:rgba(255,255,255,0.06); line-height:1; }
.week-title { font-size:22px; font-weight:700; color:#f0ede8; margin:4px 0; }
.week-dates { font-size:13px; color:#e05c1a; font-family:monospace; }
.week-desc  { font-size:13px; color:#6b6860; margin-top:6px; line-height:1.6; }
.phase-badge {
    display:inline-block; padding:3px 10px; border-radius:4px;
    font-size:10px; font-weight:700; letter-spacing:1.5px;
    text-transform:uppercase; margin-bottom:8px;
}
.chip {
    display:inline-block; background:#1f2228; border:0.5px solid #2a2d35;
    border-radius:4px; padding:3px 10px; font-size:11px; color:#6b6860;
    margin-right:6px; margin-top:4px;
}
.chip strong { color:#f0ede8; }
.tag { display:inline-block; padding:2px 7px; border-radius:3px;
       font-size:9px; font-weight:700; letter-spacing:1px; margin-right:3px; }
.tag-run  { background:rgba(82,201,122,0.15);  color:#52c97a; }
.tag-str  { background:rgba(224,92,26,0.15);   color:#ff7a3d; }
.tag-plio { background:rgba(212,168,50,0.15);  color:#d4a832; }
.tag-mob  { background:rgba(77,159,214,0.15);  color:#4d9fd6; }
.tag-rest { background:rgba(85,85,85,0.15);    color:#888; }
.block-hdr {
    font-size:11px; font-weight:700; letter-spacing:1.5px;
    text-transform:uppercase; padding:8px 0 6px;
    border-bottom:1px solid #1f2228; margin-bottom:4px;
}
.prog-track { background:#1f2228; border-radius:99px; height:6px; overflow:hidden; margin:8px 0; }
.prog-fill  { height:100%; border-radius:99px; background:linear-gradient(90deg,#2d7a47,#52c97a); }
.seg-label   { font-size:10px; font-weight:600; color:#6b6860;
               text-transform:uppercase; letter-spacing:0.5px; }
.seg-content { font-size:12px; color:#d0ccc4; line-height:1.6; }

/* Panel izquierdo propio */
.nav-panel {
    background: #111316;
    border-right: 1px solid #1f2228;
    padding: 16px 10px;
    min-height: 100vh;
    position: sticky;
    top: 0;
    overflow-y: auto;
    max-height: 100vh;
}
.nav-header {
    font-family: 'Courier New', monospace;
    font-size: 16px; font-weight: 900;
    color: #e05c1a; letter-spacing: 2px;
    margin-bottom: 2px;
}
.nav-sub { font-size: 10px; color: #6b6860; margin-bottom: 12px; }
.phase-lbl {
    font-size: 9px; font-weight: 700;
    letter-spacing: 2px; text-transform: uppercase;
    padding: 8px 0 4px;
}

div[data-testid="stExpander"] {
    background:#111316 !important; border:0.5px solid #1f2228 !important;
    border-radius:8px !important; margin-bottom:6px;
}
div[data-testid="stExpander"] summary { color:#f0ede8 !important; }
.stButton > button {
    background:#1f2228 !important; color:#d0ccc4 !important;
    border:0.5px solid #2a2d35 !important; border-radius:6px !important;
    font-size: 12px !important;
}
.stButton > button:hover { border-color:#52c97a !important; color:#52c97a !important; }
div[data-testid="stCheckbox"] label { color:#d0ccc4 !important; font-size:13px !important; }

/* Login */
.login-card {
    max-width:380px; margin:80px auto 0; background:#111316;
    border:0.5px solid #2a2d35; border-radius:14px; padding:36px 32px;
}
.login-title {
    font-size:28px; font-weight:900; color:#f0ede8;
    letter-spacing:1px; margin-bottom:4px; text-align:center;
}
.login-sub { font-size:13px; color:#6b6860; text-align:center; margin-bottom:28px; }
div[data-testid="stTextInput"] label { color:#d0ccc4 !important; font-size:12px !important; }
div[data-testid="stTextInput"] input {
    background:#1f2228 !important; color:#f0ede8 !important;
    border:0.5px solid #2a2d35 !important; border-radius:6px !important;
}

#MainMenu { visibility:hidden; }
footer    { visibility:hidden; }
header    { visibility:hidden; }

@media (max-width:768px) {
    .week-num { font-size:32px; }
    .week-title { font-size:16px; }
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def get_users() -> dict:
    try:
        return dict(st.secrets["users"])
    except Exception:
        return {"esteban": hash_pw("canajagua2026")}

def check_login(username: str, password: str) -> bool:
    users  = get_users()
    stored = users.get(username.lower().strip())
    return stored is not None and stored == hash_pw(password)

def render_login():
    st.markdown("""
    <div class="login-card">
        <div style="text-align:center;font-size:42px;margin-bottom:8px">🏔</div>
        <div class="login-title">CANAJAGUA</div>
        <div class="login-sub">30K · 16 Agosto 2026 · Tracker</div>
    </div>
    """, unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.form("login_form"):
            username  = st.text_input("Usuario", placeholder="esteban")
            password  = st.text_input("Contraseña", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Entrar →", use_container_width=True)
        if submitted:
            if check_login(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username.lower().strip()
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

def logout():
    for k in ["authenticated","username","sheets","checks","selected_week"]:
        st.session_state.pop(k, None)
    st.rerun()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    render_login()
    st.stop()

# ═══════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════
if "sheets" not in st.session_state:
    st.session_state.sheets = SheetsService()
if "checks" not in st.session_state:
    st.session_state.checks = st.session_state.sheets.load_all_checks()
if "selected_week" not in st.session_state:
    st.session_state.selected_week = 1

sheets: SheetsService = st.session_state.sheets

# ═══════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════
def get_check(week, day_idx, block_idx=None, ex_idx=None):
    key = f"w{week}_d{day_idx}_day" if block_idx is None \
          else f"w{week}_d{day_idx}_b{block_idx}_e{ex_idx}"
    return st.session_state.checks.get(key, False)

def set_check(week, day_idx, value, block_idx=None, ex_idx=None):
    key = f"w{week}_d{day_idx}_day" if block_idx is None \
          else f"w{week}_d{day_idx}_b{block_idx}_e{ex_idx}"
    st.session_state.checks[key] = value
    sheets.save_check(key, value, week, day_idx, block_idx, ex_idx)

def week_progress(week_num):
    w     = next(x for x in WEEKS if x["num"] == week_num)
    total = len(w["days"])
    done  = sum(1 for di in range(total) if get_check(week_num, di))
    return done, total

def global_progress():
    total = sum(len(w["days"]) for w in WEEKS)
    done  = sum(1 for w in WEEKS
                for di in range(len(w["days"]))
                if get_check(w["num"], di))
    return done, total

def ex_progress(week_num, day_idx):
    w   = next(x for x in WEEKS if x["num"] == week_num)
    day = w["days"][day_idx]
    total = done = 0
    for bi, block in enumerate(day["blocks"]):
        for ei in range(len(block.get("exercises", []))):
            total += 1
            if get_check(week_num, day_idx, bi, ei):
                done += 1
    return done, total

def week_dates(num):
    from datetime import timedelta
    start = date(2026, 5, 18)
    mon   = start + timedelta(weeks=num - 1)
    sun   = mon   + timedelta(days=6)
    ms    = ['','ene','feb','mar','abr','may','jun',
             'jul','ago','sep','oct','nov','dic']
    return f"{mon.day} {ms[mon.month]} → {sun.day} {ms[sun.month]} 2026"

TAG_LABELS  = {"run":"Running","str":"Fuerza","plio":"Plio",
               "mob":"Movilidad","rest":"Descanso"}
TYPE_COLORS = {"run":"#52c97a","str":"#e05c1a","plio":"#d4a832",
               "mob":"#4d9fd6","rest":"#555"}

# ═══════════════════════════════════════════
# LAYOUT — dos columnas propias
# ═══════════════════════════════════════════
wnum = st.session_state.selected_week
col_nav, col_main = st.columns([1, 4], gap="small")

# ── PANEL IZQUIERDO ─────────────────────────
with col_nav:
    gdone, gtotal = global_progress()
    gpct = round(gdone / gtotal * 100) if gtotal else 0

    st.markdown(f"""
    <div class="nav-panel">
        <div class="nav-header">CANAJAGUA</div>
        <div class="nav-sub">30K · 16 ago 2026</div>
        <div style="font-size:11px;color:#6b6860;margin-bottom:4px;
                    display:flex;justify-content:space-between">
            <span>Progreso</span>
            <span style="color:#f0ede8">{gdone}/{gtotal}</span>
        </div>
        <div class="prog-track">
            <div class="prog-fill" style="width:{gpct}%"></div>
        </div>
        <div style="font-size:10px;color:#6b6860;text-align:right;
                    margin-bottom:10px">{gpct}%</div>
        <div style="font-size:11px;color:#6b6860;padding:6px 0 10px;
                    border-top:0.5px solid #1f2228;margin-bottom:4px">
            👤 {st.session_state.username}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("⏏ Salir", use_container_width=True, key="logout_btn"):
        logout()

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    current_phase = None
    for w in WEEKS:
        if w["phase"] != current_phase:
            current_phase = w["phase"]
            pc = PHASE_COLORS[w["phase"]]
            pname = PHASE_NAMES[w["phase"]].split("·")[-1].strip()
            st.markdown(f"""
            <div class="phase-lbl" style="color:{pc}">● {pname}</div>
            """, unsafe_allow_html=True)

        wdone, wtotal = week_progress(w["num"])
        wpct_w = round(wdone / wtotal * 100) if wtotal else 0
        is_active = st.session_state.selected_week == w["num"]

        c1, c2 = st.columns([5, 1])
        with c1:
            btn_label = f"S{w['num']} · {w['title'][:18]}{'…' if len(w['title'])>18 else ''}"
            if st.button(
                btn_label,
                key=f"nav_w{w['num']}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.selected_week = w["num"]
                st.rerun()
        with c2:
            if wpct_w == 100:
                st.markdown(
                    "<div style='color:#52c97a;font-size:13px;padding-top:7px;text-align:center'>✓</div>",
                    unsafe_allow_html=True)
            elif wpct_w > 0:
                st.markdown(
                    f"<div style='color:#d4a832;font-size:9px;padding-top:9px;text-align:center'>{wpct_w}%</div>",
                    unsafe_allow_html=True)

# ── PANEL DERECHO (contenido) ────────────────
with col_main:
    week  = next(x for x in WEEKS if x["num"] == wnum)
    pc    = PHASE_COLORS[week["phase"]]
    wdone, wtotal = week_progress(wnum)
    wpct  = round(wdone / wtotal * 100) if wtotal else 0

    # Banner semana
    st.markdown(f"""
    <div class="week-banner">
        <div style="display:flex;align-items:flex-start;gap:16px">
            <div class="week-num">{str(wnum).zfill(2)}</div>
            <div style="flex:1">
                <div class="phase-badge"
                     style="background:{pc}22;color:{pc};border:0.5px solid {pc}55">
                    {PHASE_NAMES[week['phase']]}
                </div>
                <div class="week-title">{week['title']}</div>
                <div class="week-dates">{week_dates(wnum)}</div>
                <div class="week-desc">{week['desc']}</div>
                <div style="margin-top:10px">
                    <span class="chip">~<strong>{week['km']}</strong> km</span>
                    <span class="chip"><strong>{week['run_s']}</strong> running</span>
                    <span class="chip"><strong>{week['str_s']}</strong> fuerza</span>
                    {"<span class='chip'>Desnivel: <strong>" + week['desnivel'] + "</strong></span>" if week.get('desnivel') else ''}
                    <span class="chip" style="color:{'#52c97a' if wpct==100 else '#d4a832' if wpct>0 else '#6b6860'}">
                        <strong>{wdone}/{wtotal}</strong> días
                    </span>
                </div>
            </div>
        </div>
        <div class="prog-track" style="margin-top:12px">
            <div class="prog-fill"
                 style="width:{wpct}%;background:{'#52c97a' if wpct==100 else 'linear-gradient(90deg,#2d7a47,#52c97a)'}">
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Días
    for di, day in enumerate(week["days"]):
        day_done = get_check(wnum, di)
        ex_done, ex_total = ex_progress(wnum, di)
        tags_html = "".join(
            f'<span class="tag tag-{t}">{TAG_LABELS.get(t,t)}</span>'
            for t in day["tags"]
        )
        summary = f"{ex_done}/{ex_total} ejercicios" if ex_total > 0 \
                  else day.get("summary", "")
        icon = "✅" if day_done else "⬜"

        with st.expander(f"{icon} **{day['name']}** — {summary}", expanded=False):
            ct, cc = st.columns([3, 1])
            with ct:
                st.markdown(f'<div style="margin-bottom:4px">{tags_html}</div>',
                            unsafe_allow_html=True)
            with cc:
                new_day = st.checkbox("Día completo ✓", value=day_done,
                                      key=f"day_{wnum}_{di}")
                if new_day != day_done:
                    set_check(wnum, di, new_day)
                    st.rerun()

            st.divider()

            for bi, block in enumerate(day["blocks"]):
                btype  = block["type"]
                bc     = TYPE_COLORS.get(btype, "#888")
                blabel = {"run":"RUNNING","str":"FUERZA","plio":"PLIOMETRÍA",
                          "mob":"MOVILIDAD","rest":"DESCANSO"}.get(btype, btype.upper())

                st.markdown(f"""
                <div class="block-hdr" style="color:{bc};border-color:{bc}33">
                    {blabel} · {block['title']}
                </div>""", unsafe_allow_html=True)

                if "exercises" in block:
                    all_done = all(
                        get_check(wnum, di, bi, ei)
                        for ei in range(len(block["exercises"]))
                    )
                    if st.button(
                        "☑ Marcar todos" if not all_done else "☐ Desmarcar todos",
                        key=f"all_{wnum}_{di}_{bi}"
                    ):
                        for ei in range(len(block["exercises"])):
                            set_check(wnum, di, not all_done, bi, ei)
                        st.rerun()

                    for ei, ex in enumerate(block["exercises"]):
                        ex_val = get_check(wnum, di, bi, ei)
                        c1, c2 = st.columns([5, 2])
                        with c1:
                            note  = f"  \n_{ex[4]}_" if ex[4] else ""
                            new_v = st.checkbox(
                                f"**{ex[0]}**{note}",
                                value=ex_val,
                                key=f"ex_{wnum}_{di}_{bi}_{ei}"
                            )
                            if new_v != ex_val:
                                set_check(wnum, di, new_v, bi, ei)
                                st.rerun()
                        with c2:
                            st.markdown(f"""
                            <div style="text-align:right;padding-top:6px">
                                <span style="font-family:monospace;font-size:11px;color:#6b6860">
                                    {ex[1]} × {ex[2]} · {ex[3]}
                                </span>
                            </div>""", unsafe_allow_html=True)

                elif "segments" in block:
                    for seg_label, seg_content in block["segments"]:
                        st.markdown(f"""
                        <div style="display:grid;grid-template-columns:90px 1fr;gap:10px;
                                    padding:8px 0;border-bottom:0.5px solid #1a1c20">
                            <div class="seg-label">{seg_label}</div>
                            <div class="seg-content">{seg_content}</div>
                        </div>""", unsafe_allow_html=True)

                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Navegación
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    cp, cm, cn = st.columns([1, 2, 1])
    with cp:
        if wnum > 1:
            if st.button("← Anterior", use_container_width=True):
                st.session_state.selected_week = wnum - 1
                st.rerun()
    with cm:
        st.markdown(
            f"<div style='text-align:center;font-size:12px;color:#6b6860;padding-top:8px'>"
            f"Semana {wnum} de 13</div>",
            unsafe_allow_html=True
        )
    with cn:
        if wnum < 13:
            if st.button("Siguiente →", use_container_width=True):
                st.session_state.selected_week = wnum + 1
                st.rerun()