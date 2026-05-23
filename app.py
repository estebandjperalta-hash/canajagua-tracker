import streamlit as st
from datetime import date
import json

# 1. PAGE CONFIG (Debe ser absolutamente el primer comando de Streamlit)
st.set_page_config(
    page_title="Canajagua 30K · Tracker",
    page_icon="🏔",
    layout="wide",
    initial_sidebar_state="expanded",
)

import streamlit_authenticator as stauth
from data.plan import WEEKS, PHASE_NAMES, PHASE_COLORS
from services.sheets import SheetsService

# ── AUTENTICACIÓN: VALIDACIÓN DE CREDENCIALES ─────────────────
# Cargamos de forma segura los diccionarios de configuración desde st.secrets
try:
    credentials = dict(st.secrets["credentials"])
    cookie = dict(st.secrets["cookie"])
except KeyError:
    st.error("Error: No se encontraron las configuraciones de '[credentials]' o '[cookie]' en los Secrets de Streamlit.")
    st.stop()

# Inicializamos el objeto de autenticación
authenticator = stauth.Authenticate(
    credentials,
    cookie["name"],
    cookie["key"],
    cookie["expiry_days"]
)

# Renderizamos el formulario de inicio de sesión
name, authentication_status, username = authenticator.login('Iniciar Sesión', 'main')

# ── CONTROL DE ACCESO ─────────────────────────────────────────
if authentication_status == False:
    st.error('Usuario o contraseña incorrectos')

elif authentication_status == None:
    st.warning('Por favor, ingresa tu usuario y contraseña para acceder al Tracker')

elif authentication_status:
    # A partir de aquí, el usuario está autenticado con éxito.
    # Todo tu código original se ejecuta dentro de este bloque.

    # ── CUSTOM CSS ───────────────────────────────────────────────
    st.markdown("""
    <style>
    /* Dark theme base */
    [data-testid="stAppViewContainer"] { background: #0b0c0e; }
    [data-testid="stSidebar"] { background: #111316; border-right: 1px solid #1f2228; }
    [data-testid="stSidebar"] * { color: #d0ccc4 !important; }

    /* Main content */
    .main-content { max-width: 800px; margin: 0 auto; }

    /* Week header */
    .week-banner {
        background: linear-gradient(135deg, #1a1c20, #1f2228);
        border: 0.5px solid #2a2d35;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 16px;
    }
    .week-num { font-size: 52px; font-weight: 900; color: rgba(255,255,255,0.06); line-height:1; }
    .week-title { font-size: 22px; font-weight: 700; color: #f0ede8; margin: 4px 0; }
    .week-dates { font-size: 13px; color: #e05c1a; font-family: monospace; }
    .week-desc { font-size: 13px; color: #6b6860; margin-top: 6px; line-height: 1.6; }

    /* Phase badge */
    .phase-badge {
        display: inline-block;
        padding: 3px 10px; border-radius: 4px;
        font-size: 10px; font-weight: 700;
        letter-spacing: 1.5px; text-transform: uppercase;
        margin-bottom: 8px;
    }

    /* Day card */
    .day-card {
        background: #111316;
        border: 0.5px solid #1f2228;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 8px;
    }
    .day-card.done { border-color: rgba(82,201,122,0.35); background: rgba(82,201,122,0.03); }
    .day-name { font-size: 13px; font-weight: 700; color: #f0ede8; font-family: monospace; }

    /* Metric chips */
    .chip {
        display: inline-block;
        background: #1f2228; border: 0.5px solid #2a2d35;
        border-radius: 4px; padding: 3px 10px;
        font-size: 11px; color: #6b6860;
        margin-right: 6px; margin-top: 4px;
    }
    .chip strong { color: #f0ede8; }

    /* Exercise row */
    .ex-row {
        padding: 8px 0;
        border-bottom: 0.5px solid #1a1c20;
        display: flex; align-items: flex-start; gap: 10px;
    }
    .ex-name { font-size: 13px; font-weight: 500; color: #f0ede8; }
    .ex-note { font-size: 11px; color: #6b6860; margin-top: 2px; }
    .ex-meta { font-family: monospace; font-size: 11px; color: #6b6860; white-space: nowrap; }

    /* Block header */
    .block-hdr {
        font-size: 11px; font-weight: 700;
        letter-spacing: 1.5px; text-transform: uppercase;
        padding: 8px 0 6px;
        border-bottom: 1px solid #1f2228;
        margin-bottom: 4px;
    }

    /* Progress bar */
    .prog-track {
        background: #1f2228; border-radius: 99px;
        height: 6px; overflow: hidden; margin: 8px 0;
    }
    .prog-fill {
        height: 100%; border-radius: 99px;
        background: linear-gradient(90deg, #2d7a47, #52c97a);
        transition: width 0.4s ease;
    }

    /* Tag pills */
    .tag { display:inline-block; padding:2px 7px; border-radius:3px;
           font-size:9px; font-weight:700; letter-spacing:1px; margin-right:3px; }
    .tag-run  { background:rgba(82,201,122,0.15); color:#52c97a; }
    .tag-str  { background:rgba(224,92,26,0.15);  color:#ff7a3d; }
    .tag-plio { background:rgba(212,168,50,0.15); color:#d4a832; }
    .tag-mob  { background:rgba(77,159,214,0.15); color:#4d9fd6; }
    .tag-rest { background:rgba(85,85,85,0.15);   color:#888; }

    /* Segment rows */
    .seg-label { font-size:10px; font-weight:600; color:#6b6860;
                 text-transform:uppercase; letter-spacing:0.5px; }
    .seg-content { font-size:12px; color:#d0ccc4; line-height:1.6; }

    /* Sidebar week items */
    .sb-week { padding: 6px 8px; border-radius: 6px; cursor:pointer; margin-bottom:2px; }
    .sb-week:hover { background: #1f2228; }
    .sb-active { background: #2a2d35 !important; }

    /* Global progress */
    .global-prog {
        background: #111316; border: 0.5px solid #1f2228;
        border-radius: 8px; padding: 12px 16px; margin-bottom: 16px;
    }

    /* Mobile tweaks */
    @media (max-width: 768px) {
        .week-num { font-size: 36px; }
        .week-title { font-size: 18px; }
        [data-testid="stSidebar"] { min-width: 200px !important; max-width: 240px !important; }
    }

    /* Streamlit element overrides */
    div[data-testid="stCheckbox"] label { color: #d0ccc4 !important; font-size: 13px !important; }
    div[data-testid="stExpander"] { background: #111316 !important; border: 0.5px solid #1f2228 !important; border-radius: 8px !important; }
    div[data-testid="stExpander"] summary { color: #f0ede8 !important; }
    .stButton > button { background: #1f2228 !important; color: #d0ccc4 !important; border: 0.5px solid #2a2d35 !important; }
    .stButton > button:hover { border-color: #52c97a !important; color: #52c97a !important; }

    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

    # ── SESSION STATE INIT ───────────────────────────────────────
    if "sheets" not in st.session_state:
        st.session_state.sheets = SheetsService()

    if "checks" not in st.session_state:
        st.session_state.checks = st.session_state.sheets.load_all_checks()

    if "selected_week" not in st.session_state:
        st.session_state.selected_week = 1

    sheets: SheetsService = st.session_state.sheets

    # ── HELPERS ─────────────────────────────────────────────────
    def get_check(week, day_idx, block_idx=None, ex_idx=None):
        if block_idx is None:
            key = f"w{week}_d{day_idx}_day"
        else:
            key = f"w{week}_d{day_idx}_b{block_idx}_e{ex_idx}"
        return st.session_state.checks.get(key, False)

    def set_check(week, day_idx, value, block_idx=None, ex_idx=None):
        if block_idx is None:
            key = f"w{week}_d{day_idx}_day"
        else:
            key = f"w{week}_d{day_idx}_b{block_idx}_e{ex_idx}"
        st.session_state.checks[key] = value
        sheets.save_check(key, value, week, day_idx, block_idx, ex_idx)

    def week_progress(week_num):
        w = next(x for x in WEEKS if x["num"] == week_num)
        total = len(w["days"])
        done = sum(1 for di in range(total) if get_check(week_num, di))
        return done, total

    def global_progress():
        total = sum(len(w["days"]) for w in WEEKS)
        done = sum(
            1 for w in WEEKS
            for di in range(len(w["days"]))
            if get_check(w["num"], di)
        )
        return done, total

    def ex_progress(week_num, day_idx):
        w = next(x for x in WEEKS if x["num"] == week_num)
        day = w["days"][day_idx]
        total, done = 0, 0
        for bi, block in enumerate(day["blocks"]):
            for ei in range(len(block.get("exercises", []))):
                total += 1
                if get_check(week_num, day_idx, bi, ei):
                    done += 1
        return done, total

    def week_dates(num):
        from datetime import timedelta
        start = date(2026, 5, 18)
        mon = start + timedelta(weeks=num - 1)
        sun = mon + timedelta(days=6)
        ms = ['','ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic']
        return f"{mon.day} {ms[mon.month]} → {sun.day} {ms[sun.month]} 2026"

    TAG_LABELS = {"run": "Running", "str": "Fuerza", "plio": "Plio", "mob": "Movilidad", "rest": "Descanso"}
    TYPE_COLORS = {"run": "#52c97a", "str": "#e05c1a", "plio": "#d4a832", "mob": "#4d9fd6", "rest": "#555"}

    # ── SIDEBAR ──────────────────────────────────────────────────
    with st.sidebar:
        gdone, gtotal = global_progress()
        gpct = round(gdone / gtotal * 100) if gtotal else 0

        st.markdown(f"""
        <div style="padding:8px 0 16px">
            <div style="font-family:'Courier New',monospace;font-size:20px;font-weight:900;color:#e05c1a;letter-spacing:2px">
                CANAJAGUA
            </div>
            <div style="font-size:11px;color:#6b6860;margin-top:2px">30K · 16 Agosto 2026</div>
            <div style="margin-top:10px">
                <div style="display:flex;justify-content:space-between;font-size:11px;color:#6b6860;margin-bottom:4px">
                    <span>Progreso global</span>
                    <span style="color:#f0ede8">{gdone}/{gtotal} días</span>
                </div>
                <div class="prog-track">
                    <div class="prog-fill" style="width:{gpct}%"></div>
                </div>
                <div style="font-size:11px;color:#6b6860;text-align:right">{gpct}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Botón de Cerrar Sesión integrado elegantemente en la barra lateral
        authenticator.logout('Cerrar Sesión 🔓', 'sidebar')

        st.divider()

        current_phase = None
        for w in WEEKS:
            if w["phase"] != current_phase:
                current_phase = w["phase"]
                pc = PHASE_COLORS[w["phase"]]
                st.markdown(f"""
                <div style="font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;
                            color:{pc};padding:8px 0 4px">
                    ● {PHASE_NAMES[w['phase']]}
                </div>""", unsafe_allow_html=True)

            wdone, wtotal = week_progress(w["num"])
            wpct = round(wdone / wtotal * 100) if wtotal else 0
            is_active = st.session_state.selected_week == w["num"]

            col1, col2 = st.columns([4, 1])
            with col1:
                label = f"**S{w['num']}** {w['title'][:28]}{'…' if len(w['title'])>28 else ''}"
                if st.button(label, key=f"sb_w{w['num']}",
                            use_container_width=True,
                            type="primary" if is_active else "secondary"):
                    st.session_state.selected_week = w["num"]
                    st.rerun()
            with col2:
                if wpct == 100:
                    st.markdown("<div style='text-align:center;color:#52c97a;font-size:16px;padding-top:6px'>✓</div>", unsafe_allow_html=True)
                elif wpct > 0:
                    st.markdown(f"<div style='text-align:center;color:#d4a832;font-size:11px;padding-top:8px'>{wpct}%</div>", unsafe_allow_html=True)

    # ── MAIN ─────────────────────────────────────────────────────
    wnum = st.session_state.selected_week
    week = next(x for x in WEEKS if x["num"] == wnum)
    pc = PHASE_COLORS[week["phase"]]
    wdone, wtotal = week_progress(wnum)
    wpct = round(wdone / wtotal * 100) if wtotal else 0

    # Week header
    st.markdown(f"""
    <div class="week-banner">
        <div style="display:flex;align-items:flex-start;gap:16px">
            <div class="week-num">{str(wnum).zfill(2)}</div>
            <div style="flex:1">
                <div class="phase-badge" style="background:{pc}22;color:{pc};border:0.5px solid {pc}55">
                    {PHASE_NAMES[week['phase']]}
                </div>
                <div class="week-title">{week['title']}</div>
                <div class="week-dates">{week_dates(wnum)}</div>
                <div class="week-desc">{week['desc']}</div>
                <div style="margin-top:10px">
                    <span class="chip">~<strong>{week['km']}</strong> km</span>
                    <span class="chip"><strong>{week['run_s']}</strong> ses. running</span>
                    <span class="chip"><strong>{week['str_s']}</strong> ses. fuerza</span>
                    {"<span class='chip'>Desnivel: <strong>" + week['desnivel'] + "</strong></span>" if week.get('desnivel') else ''}
                    <span class="chip" style="color:{'#52c97a' if wpct==100 else '#d4a832' if wpct>0 else '#6b6860'}">
                        <strong>{wdone}/{wtotal}</strong> días
                    </span>
                </div>
            </div>
        </div>
        <div class="prog-track" style="margin-top:12px">
            <div class="prog-fill" style="width:{wpct}%;background:{'#52c97a' if wpct==100 else 'linear-gradient(90deg,#2d7a47,#52c97a)'}"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── DAYS ─────────────────────────────────────────────────────
    for di, day in enumerate(week["days"]):
        day_done = get_check(wnum, di)
        ex_done, ex_total = ex_progress(wnum, di)
        tags_html = "".join(f'<span class="tag tag-{t}">{TAG_LABELS.get(t,t)}</span>' for t in day["tags"])
        summary = f"{ex_done}/{ex_total} ejercicios" if ex_total > 0 else day.get("summary", "")

        with st.expander(
            f"{'✅' if day_done else '⬜'} **{day['name']}** — {summary}",
            expanded=False
        ):
            # Day-level check
            col_check, col_info = st.columns([3, 1])
            with col_check:
                st.markdown(f'<div style="margin-bottom:6px">{tags_html}</div>', unsafe_allow_html=True)
            with col_info:
                new_day_done = st.checkbox(
                    "Día completo ✓",
                    value=day_done,
                    key=f"day_{wnum}_{di}"
                )
                if new_day_done != day_done:
                    set_check(wnum, di, new_day_done)
                    st.rerun()

            st.divider()

            # Blocks
            for bi, block in enumerate(day["blocks"]):
                btype = block["type"]
                bc = TYPE_COLORS.get(btype, "#888")
                blabel = {"run":"RUNNING","str":"FUERZA","plio":"PLIOMETRÍA","mob":"MOVILIDAD","rest":"DESCANSO"}.get(btype, btype.upper())

                st.markdown(f"""
                <div class="block-hdr" style="color:{bc};border-color:{bc}33">
                    {blabel} · {block['title']}
                </div>""", unsafe_allow_html=True)

                # Exercises
                if "exercises" in block:
                    # "Mark all" button
                    all_done = all(get_check(wnum, di, bi, ei) for ei in range(len(block["exercises"])))
                    if st.button(
                        "☑ Marcar todos" if not all_done else "☐ Desmarcar todos",
                        key=f"all_{wnum}_{di}_{bi}",
                        use_container_width=False
                    ):
                        for ei in range(len(block["exercises"])):
                            set_check(wnum, di, not all_done, bi, ei)
                        st.rerun()

                    for ei, ex in enumerate(block["exercises"]):
                        ex_done_val = get_check(wnum, di, bi, ei)
                        c1, c2 = st.columns([5, 2])
                        with c1:
                            new_val = st.checkbox(
                                f"**{ex[0]}**" + (f"  \n_{ex[4]}_" if ex[4] else ""),
                                value=ex_done_val,
                                key=f"ex_{wnum}_{di}_{bi}_{ei}"
                            )
                            if new_val != ex_done_val:
                                set_check(wnum, di, new_val, bi, ei)
                                st.rerun()
                        with c2:
                            st.markdown(f"""
                            <div style="text-align:right;padding-top:6px">
                                <span style="font-family:monospace;font-size:11px;color:#6b6860">
                                    {ex[1]} × {ex[2]} · {ex[3]}
                                </span>
                            </div>""", unsafe_allow_html=True)

                # Segments (run/mob/rest)
                elif "segments" in block:
                    for seg_label, seg_content in block["segments"]:
                        st.markdown(f"""
                        <div style="display:grid;grid-template-columns:90px 1fr;gap:10px;
                                    padding:8px 0;border-bottom:0.5px solid #1a1c20">
                            <div class="seg-label">{seg_label}</div>
                            <div class="seg-content">{seg_content}</div>
                        </div>""", unsafe_allow_html=True)

                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── WEEK NAV ─────────────────────────────────────────────────
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    col_prev, col_mid, col_next = st.columns([1, 2, 1])
    with col_prev:
        if wnum > 1:
            if st.button("← Semana anterior", use_container_width=True):
                st.session_state.selected_week = wnum - 1
                st.rerun()
    with col_mid:
        st.markdown(f"<div style='text-align:center;font-size:12px;color:#6b6860;padding-top:8px'>Semana {wnum} de 13</div>", unsafe_allow_html=True)
    with col_next:
        if wnum < 13:
            if st.button("Semana siguiente →", use_container_width=True):
                st.session_state.selected_week = wnum + 1
                st.rerun()