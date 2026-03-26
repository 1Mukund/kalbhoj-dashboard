# =============================================================================
# app.py — Main Streamlit entry point
# READ-ONLY analytics dashboard for Lead Operations.
# Run with: streamlit run app.py
# =============================================================================

import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

from config import APP_TITLE, APP_ICON, TIMEZONE, THRESHOLDS, USERS
from data_loader import load_all_sheets
from merger import build_unified_leads
from metrics import compute_all_kpis
from normalizer import normalize_phone
import views

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Dark theme override — replaced by MAIN_CSS injected after login


IST = pytz.timezone(TIMEZONE)


# =============================================================================
# AUTH
# =============================================================================

CARD_CSS_LOGIN = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif !important; }

.stApp {
    background: radial-gradient(ellipse at 30% 20%, #0d1f3c 0%, #0a0a0f 50%, #0d0d1a 100%) !important;
}

/* Glowing orbs */
.stApp::before {
    content: '';
    position: fixed;
    top: -200px; left: -200px;
    width: 600px; height: 600px;
    background: radial-gradient(circle, rgba(31,111,235,0.15) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
    z-index: 0;
}
.stApp::after {
    content: '';
    position: fixed;
    bottom: -200px; right: -200px;
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(139,92,246,0.12) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
    z-index: 0;
}

/* Input field */
.stTextInput input {
    background: rgba(255,255,255,0.05) !important;
    color: #e6edf3 !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
    padding: 14px 16px !important;
    font-size: 15px !important;
    box-shadow: 0 0 0 0 transparent !important;
    transition: border 0.2s, box-shadow 0.2s !important;
}
.stTextInput input:focus {
    border: 1px solid #1f6feb !important;
    box-shadow: 0 0 16px rgba(31,111,235,0.25) !important;
    background: rgba(31,111,235,0.06) !important;
}
.stTextInput input::placeholder { color: rgba(255,255,255,0.2) !important; }
.stTextInput label { display: none !important; }

/* Form card */
.stForm {
    background: rgba(255,255,255,0.04) !important;
    backdrop-filter: blur(24px) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 20px !important;
    padding: 36px 32px !important;
    box-shadow: 0 0 60px rgba(31,111,235,0.08), 0 25px 50px rgba(0,0,0,0.4) !important;
}

/* Submit button */
.stFormSubmitButton button {
    background: linear-gradient(135deg, #1f6feb, #7c3aed) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    padding: 13px !important;
    margin-top: 10px !important;
    box-shadow: 0 0 24px rgba(31,111,235,0.35) !important;
    width: 100% !important;
    transition: all 0.2s !important;
}
.stFormSubmitButton button:hover {
    box-shadow: 0 0 36px rgba(31,111,235,0.55) !important;
    transform: translateY(-1px) !important;
}

/* Hide streamlit chrome */
header { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }
[data-testid="stSidebarCollapseButton"] { display: none !important; }
</style>
"""

MAIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

/* ── App background ── */
.stApp { background: #0d1117 !important; color: #e6edf3 !important; }

/* ── Sidebar ── */
.stSidebar { background: #161b22 !important; border-right: 1px solid #30363d !important; }
.stSidebar section { padding-top: 1rem !important; }
.stSidebar .stMarkdown p { color: #8b949e !important; font-size: 12px !important; }
.stSidebar h2 { color: #e6edf3 !important; font-size: 15px !important; font-weight: 700 !important; }
.stSidebar label { color: #8b949e !important; font-size: 10px !important; text-transform: uppercase; letter-spacing: 1px; font-weight: 600 !important; }
.stSidebar [data-baseweb="select"] > div { background: #21262d !important; border: 1px solid #30363d !important; color: #e6edf3 !important; border-radius: 8px !important; }
.stSidebar [data-baseweb="select"] span { color: #e6edf3 !important; }
.stSidebar .stTextInput input { background: #21262d !important; border: 1px solid #30363d !important; color: #e6edf3 !important; border-radius: 8px !important; }
.stSidebar button { background: #21262d !important; color: #e6edf3 !important; border: 1px solid #30363d !important; border-radius: 8px !important; font-weight: 600 !important; font-size: 13px !important; }
.stSidebar button:hover { background: #30363d !important; border-color: #58a6ff !important; }
.stSidebar .stCaption { color: #6e7681 !important; font-size: 11px !important; }
[data-testid="stSidebarNav"] { display: none; }

/* ── Main content ── */
.block-container { padding: 1.2rem 2rem 2rem 2rem !important; max-width: 1400px !important; }

/* ── Headings ── */
h3 { color: #e6edf3 !important; font-size: 17px !important; font-weight: 700 !important; margin-bottom: 14px !important; }
p, span, div { color: #e6edf3; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #161b22 !important;
    border-radius: 10px !important;
    padding: 4px 5px !important;
    border: 1px solid #30363d !important;
    gap: 2px !important;
    margin-bottom: 18px !important;
}
.stTabs [data-baseweb="tab"] {
    color: #8b949e !important;
    border-radius: 7px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    padding: 7px 14px !important;
    border: none !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    background: #1f6feb !important;
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* ── Permanently hide sidebar collapse button (causes keyboard_double_arrow_right) ── */
[data-testid="stSidebarCollapseButton"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
.material-symbols-rounded {
    font-family: 'Material Symbols Rounded' !important;
    font-size: 20px !important;
    color: #6e7681 !important;
    line-height: 1 !important;
}

/* ── Hide expand/collapse arrow on expanders ── */
[data-testid="stExpanderToggleIcon"] { display: none !important; }
summary svg { display: none !important; }
details summary span[data-testid] { display: none !important; }

/* ── Expander styling ── */
.streamlit-expanderHeader { color: #8b949e !important; font-size: 13px !important; font-weight: 600 !important; background: #161b22 !important; border-radius: 8px !important; padding: 10px 14px !important; }
.streamlit-expanderContent { background: #161b22 !important; border: 1px solid #30363d !important; border-radius: 0 0 8px 8px !important; }

/* ── Dataframe ── */
.stDataFrame { border-radius: 10px !important; border: 1px solid #30363d !important; }
[data-testid="stDataFrameResizable"] { background: #161b22 !important; }

/* ── Alerts ── */
.stSuccess { background: #0d2818 !important; border: 1px solid #238636 !important; color: #3fb950 !important; border-radius: 8px !important; }
.stInfo    { background: #0d1f38 !important; border: 1px solid #1f6feb !important; color: #58a6ff !important; border-radius: 8px !important; }
.stWarning { background: #2d1f00 !important; border: 1px solid #9e6a03 !important; color: #d29922 !important; border-radius: 8px !important; }
.stError   { background: #2d0f0f !important; border: 1px solid #da3633 !important; color: #f85149 !important; border-radius: 8px !important; }

/* ── Selectbox / inputs ── */
[data-baseweb="select"] > div { background: #21262d !important; border: 1px solid #30363d !important; color: #e6edf3 !important; border-radius: 8px !important; }
[data-baseweb="select"] span { color: #e6edf3 !important; }
.stTextInput input { background: #21262d !important; border: 1px solid #30363d !important; color: #e6edf3 !important; border-radius: 8px !important; }
[data-baseweb="popover"] { background: #21262d !important; border: 1px solid #30363d !important; }
[role="option"] { background: #21262d !important; color: #e6edf3 !important; }
[role="option"]:hover { background: #30363d !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #58a6ff; }

/* ── Hide Streamlit default top header bar ── */
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }

/* ── Banner ── */
.readonly-banner {
    background: #161b22;
    border: 1px solid #30363d;
    border-left: 3px solid #1f6feb;
    border-radius: 8px;
    padding: 9px 16px;
    font-size: 13px;
    color: #8b949e;
    margin-bottom: 16px;
    font-weight: 500;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: #1f6feb !important; }

/* ── Download button ── */
.stDownloadButton button { background: #21262d !important; color: #58a6ff !important; border: 1px solid #30363d !important; border-radius: 8px !important; font-weight: 600 !important; }
.stDownloadButton button:hover { background: #30363d !important; border-color: #58a6ff !important; }
</style>
"""

def render_login():
    st.markdown(CARD_CSS_LOGIN, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.1, 1])
    with col2:
        st.markdown(f"""
        <div style="text-align:center; padding: 48px 0 28px 0;">
            <div style="font-size:52px; filter:drop-shadow(0 4px 12px rgba(0,0,0,0.3))">📊</div>
            <div style="font-size:24px; font-weight:800; color:#ffffff; margin-top:10px; text-shadow:0 2px 8px rgba(0,0,0,0.2)">{APP_TITLE}</div>
            <div style="font-size:11px; color:rgba(255,255,255,0.7); margin-top:6px; letter-spacing:2px; text-transform:uppercase">Kalbhojaditya Operations</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            st.markdown('<p style="color:rgba(255,255,255,0.7);font-size:13px;margin-bottom:4px">Enter your username to continue</p>', unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="", label_visibility="collapsed")
            submitted = st.form_submit_button("Continue →", use_container_width=True)

            if submitted:
                user = USERS.get(username.strip().lower())
                if user:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username.strip().lower()
                    st.session_state["role"] = user["role"]
                    st.rerun()
                else:
                    st.error("Invalid username. Please contact your administrator.")

        st.markdown("""
        <div style="text-align:center;font-size:11px;color:rgba(255,255,255,0.4);margin-top:20px">
            🔒 Read-only · No data is modified
        </div>""", unsafe_allow_html=True)


# =============================================================================
# LOAD DATA (cached with TTL)
# =============================================================================
@st.cache_data(ttl=THRESHOLDS["cache_ttl_seconds"], show_spinner=False)
def get_data():
    data, statuses = load_all_sheets()
    unified = build_unified_leads(data)
    return data, statuses, unified


# =============================================================================
# SIDEBAR
# =============================================================================
def render_sidebar(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.markdown(f"## {APP_ICON} {APP_TITLE}")
    st.sidebar.markdown("---")

    # Refresh
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    last_refresh = datetime.now(IST).strftime("%d %b %Y, %I:%M %p IST")
    st.sidebar.caption(f"Last refreshed: {last_refresh}")
    st.sidebar.markdown("---")

    st.sidebar.markdown("### Filters")

    filtered = df.copy()

    # Date range filter
    if "born_date" in df.columns:
        valid_dates = df["born_date"].dropna()
        if not valid_dates.empty:
            def _to_date(x):
                try:
                    ts = pd.Timestamp(x)
                    if ts.tzinfo is not None:
                        ts = ts.tz_localize(None)
                    return ts.date()
                except Exception:
                    return None
            date_vals = valid_dates.apply(_to_date).dropna()
            if not date_vals.empty:
                min_d = date_vals.min()
                max_d = date_vals.max()
                date_range = st.sidebar.date_input(
                    "Date Range (Born Date)",
                    value=(min_d, max_d),
                    min_value=min_d,
                    max_value=max_d,
                )
                if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
                    start, end = date_range
                    filtered = filtered[
                        filtered["born_date"].apply(
                            lambda x: pd.notna(x) and _to_date(x) is not None and start <= _to_date(x) <= end
                        )
                    ]

    # Project filter
    if "project" in df.columns:
        projects = ["All"] + sorted(df["project"].dropna().unique().tolist())
        sel_proj = st.sidebar.selectbox("Project", projects)
        if sel_proj != "All":
            filtered = filtered[filtered["project"] == sel_proj]

    # Assigned channel filter
    if "assigned_channel" in df.columns:
        channels = ["All"] + sorted(df["assigned_channel"].dropna().unique().tolist())
        sel_ch = st.sidebar.selectbox("Assigned Channel", channels)
        if sel_ch != "All":
            filtered = filtered[filtered["assigned_channel"] == sel_ch]

    # Touch stage filter
    if "tt_touch_stage" in df.columns:
        stages = ["All"] + sorted(df["tt_touch_stage"].dropna().unique().tolist())
        sel_stage = st.sidebar.selectbox("Touch Stage", stages)
        if sel_stage != "All":
            filtered = filtered[filtered["tt_touch_stage"] == sel_stage]

    # Call status filter
    if "ah_call_status" in df.columns:
        call_statuses = ["All"] + sorted(df["ah_call_status"].dropna().unique().tolist())
        sel_cs = st.sidebar.selectbox("Call Status", call_statuses)
        if sel_cs != "All":
            filtered = filtered[filtered["ah_call_status"] == sel_cs]

    # WA reply status filter
    if "wa_replied" in df.columns:
        wa_reply_opt = st.sidebar.selectbox("WA Reply Status", ["All", "Replied", "Not Replied"])
        if wa_reply_opt == "Replied":
            filtered = filtered[filtered["wa_replied"].apply(lambda x: x is True or str(x).lower() in {"true","yes","1"})]
        elif wa_reply_opt == "Not Replied":
            filtered = filtered[~filtered["wa_replied"].apply(lambda x: x is True or str(x).lower() in {"true","yes","1"})]

    # Follow-up status filter
    if "fu_status" in df.columns:
        fu_statuses = ["All"] + sorted(df["fu_status"].dropna().unique().tolist())
        sel_fu = st.sidebar.selectbox("Follow-up Status", fu_statuses)
        if sel_fu != "All":
            filtered = filtered[filtered["fu_status"] == sel_fu]

    # Indian / International filter
    if "phone" in df.columns:
        from normalizer import is_indian_phone
        geo_opt = st.sidebar.selectbox("Geography", ["All", "Indian", "International"])
        if geo_opt == "Indian":
            filtered = filtered[filtered["phone"].apply(is_indian_phone)]
        elif geo_opt == "International":
            filtered = filtered[~filtered["phone"].apply(is_indian_phone)]

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Showing {len(filtered):,} of {len(df):,} leads")

    return filtered


# =============================================================================
# MAIN APP
# =============================================================================
def main():
    # --- Auth gate ---
    if not st.session_state.get("authenticated"):
        render_login()
        st.stop()

    role = st.session_state.get("role", "user")
    username = st.session_state.get("username", "")

    # Inject main app CSS
    st.markdown(MAIN_CSS, unsafe_allow_html=True)

    # Read-only banner
    role_badge = "🔴 ADMIN" if role == "admin" else "🟢 USER"
    st.markdown(
        f'<div class="readonly-banner">🔒 Read-only Dashboard &nbsp;·&nbsp; {role_badge} &nbsp;·&nbsp; Logged in as <b>{username}</b> &nbsp;·&nbsp; No source data is modified</div>',
        unsafe_allow_html=True,
    )

    # Load data
    with st.spinner("Loading data from Google Sheets..."):
        data, statuses, unified = get_data()

    # Show data source status
    views.render_data_source_status(statuses)

    if unified.empty:
        st.error("No data loaded. Please check your config.py sheet IDs and credentials.")
        st.stop()

    # Apply sidebar filters
    filtered_df = render_sidebar(unified)

    # Compute KPIs on filtered data
    kpis = compute_all_kpis(filtered_df)

    # --- Role-based tab list ---
    tab_defs = [
        ("📊 Summary",       True),
        ("🔽 Funnel",        True),
        ("📡 Channels",      True),
        ("💬 WhatsApp",      True),
        ("📞 Calling",       True),
        ("🏠 Bookings",      True),
        ("📋 Kalbhoj Report",True),
        ("🚨 Risk",          role == "admin"),   # admin only
        ("📈 Trends",        role == "admin"),   # admin only
        ("🔍 Drilldown",     True),
        ("📤 Export",        role == "admin"),   # admin only
    ]

    visible_tabs = [label for label, visible in tab_defs if visible]
    tabs = st.tabs(visible_tabs)

    # Map tab index dynamically
    idx = {label: i for i, (label, _) in enumerate([(l, v) for l, v in tab_defs if v])}

    tabs[idx["📊 Summary"]].write("")  # activate
    with tabs[idx["📊 Summary"]]:
        views.render_executive_summary(filtered_df, kpis, role=role)

    with tabs[idx["🔽 Funnel"]]:
        views.render_funnel(kpis)

    with tabs[idx["📡 Channels"]]:
        views.render_channel_performance(filtered_df)

    with tabs[idx["💬 WhatsApp"]]:
        views.render_followup_performance(filtered_df, kpis, role=role)

    with tabs[idx["📞 Calling"]]:
        views.render_calling_performance(filtered_df, kpis)

    with tabs[idx["🏠 Bookings"]]:
        views.render_booking_view(filtered_df, kpis)

    with tabs[idx["📋 Kalbhoj Report"]]:
        views.render_kalbhoj_report(data)

    if role == "admin":
        with tabs[idx["🚨 Risk"]]:
            views.render_operational_risk(filtered_df, kpis)

    with tabs[idx["📈 Trends"]]:
        views.render_trends(filtered_df)

    with tabs[idx["🔍 Drilldown"]]:
        views.render_lead_drilldown(filtered_df)

    with tabs[idx["📤 Export"]]:
        views.render_export_tables(filtered_df)

    # Logout button in sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()


if __name__ == "__main__":
    main()
