# =============================================================================
# views.py — All Streamlit UI sections
# Premium analytics look: styled KPI cards, Plotly charts, color badges.
# No plain tables. Everything is visual and operational.
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from metrics import (
    compute_all_kpis, stuck_leads_df, overdue_followups_df,
    error_leads_df, pending_action_leads_df, daily_trend,
    calls_by_status, leads_by_channel,
)
from config import THRESHOLDS

# =============================================================================
# STYLE HELPERS
# =============================================================================

CARD_CSS = """
<style>
.kpi-card {
    background: #161b22;
    border-radius: 12px;
    padding: 18px 20px 14px 20px;
    margin-bottom: 10px;
    border: 1px solid #30363d;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: #1f6feb;
}
.kpi-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    color: #6e7681;
    margin-bottom: 8px;
}
.kpi-value {
    font-size: 30px;
    font-weight: 800;
    color: #e6edf3;
    line-height: 1.15;
}
.kpi-sub {
    font-size: 12px;
    color: #6e7681;
    margin-top: 6px;
    font-weight: 500;
}
.kpi-delta-up   { color: #3fb950; font-size: 12px; font-weight: 600; margin-top: 5px; }
.kpi-delta-down { color: #f85149; font-size: 12px; font-weight: 600; margin-top: 5px; }
.kpi-delta-warn { color: #d29922; font-size: 12px; font-weight: 600; margin-top: 5px; }
.rate-card {
    background: #161b22;
    border-radius: 12px;
    padding: 18px 20px 14px 20px;
    margin-bottom: 10px;
    border: 1px solid #30363d;
}
.badge-green  { background:#0d2818; color:#3fb950; border-radius:6px; padding:3px 10px; font-size:11px; font-weight:700; border:1px solid #238636; }
.badge-red    { background:#2d0f0f; color:#f85149; border-radius:6px; padding:3px 10px; font-size:11px; font-weight:700; border:1px solid #da3633; }
.badge-yellow { background:#2d1f00; color:#d29922; border-radius:6px; padding:3px 10px; font-size:11px; font-weight:700; border:1px solid #9e6a03; }
.badge-blue   { background:#0d1f38; color:#58a6ff; border-radius:6px; padding:3px 10px; font-size:11px; font-weight:700; border:1px solid #1f6feb; }
.badge-grey   { background:#21262d; color:#8b949e; border-radius:6px; padding:3px 10px; font-size:11px; font-weight:700; border:1px solid #30363d; }
.section-divider { border-top: 1px solid #30363d; margin: 22px 0 16px 0; }
</style>
"""

PLOTLY_THEME = dict(
    paper_bgcolor="#161b22",
    plot_bgcolor="#161b22",
    font=dict(color="#8b949e", family="Inter, sans-serif", size=12),
    margin=dict(l=20, r=20, t=40, b=20),
)

COLOR_SEQ = ["#1f6feb", "#3fb950", "#d29922", "#f85149", "#58a6ff", "#bc8cff", "#79c0ff", "#56d364"]


def _chart_layout(fig, title=""):
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#1e1b4b", weight=700)),
        **PLOTLY_THEME,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#6b7280")),
        xaxis=dict(gridcolor="#f3f4f6", zerolinecolor="#e5e7eb", linecolor="#e5e7eb"),
        yaxis=dict(gridcolor="#f3f4f6", zerolinecolor="#e5e7eb", linecolor="#e5e7eb"),
    )
    return fig


def kpi_card(label: str, value, sub: str = "", delta: str = "", delta_type: str = "up"):
    delta_class = {"up": "kpi-delta-up", "down": "kpi-delta-down", "warn": "kpi-delta-warn"}.get(delta_type, "kpi-delta-up")
    delta_html = f'<div class="{delta_class}">{delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {f'<div class="kpi-sub">{sub}</div>' if sub else ""}
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def rate_card(label: str, rate: float, sub: str = ""):
    color = "#3fb950" if rate >= 60 else "#d29922" if rate >= 30 else "#f85149"
    bar_width = min(rate, 100)
    st.markdown(f"""
    <div class="rate-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="color:{color}">{rate}%</div>
        <div style="background:#21262d;border-radius:99px;height:5px;margin-top:10px;overflow:hidden">
            <div style="width:{bar_width}%;height:100%;background:{color};border-radius:99px"></div>
        </div>
        {f'<div class="kpi-sub">{sub}</div>' if sub else ""}
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# SECTION 1 — EXECUTIVE SUMMARY
# =============================================================================

def render_executive_summary(df: pd.DataFrame, kpis: dict, role: str = "user", data: dict = None):
    st.markdown(CARD_CSS, unsafe_allow_html=True)
    st.markdown("### 📊 Executive Summary")

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Total Leads", kpis["total_leads"], sub=f"Today: {kpis['new_leads_today']}")
    with c2: kpi_card("New (Last 24h)", kpis["new_leads_24h"])
    with c3: kpi_card("Assigned Leads", kpis["assigned_leads"])
    with c4:
        intl = kpis["indian_vs_intl"]
        kpi_card("Indian / Intl", f"{intl['Indian']} / {intl['International']}")

    c5, c6, c7, c8 = st.columns(4)
    with c5: kpi_card("WhatsApp Sent", kpis["wa_sent"], sub=f"Replied: {kpis['wa_replied']}")
    with c6: kpi_card("Calls Triggered", kpis["calls_triggered"], sub=f"Connected: {kpis['calls_connected']}")
    with c7: kpi_card("Booked Leads", kpis["booked_leads"])
    with c8: kpi_card("FU Replied / Exhausted", f"{kpis.get('fu_replied',0)} / {kpis.get('fu_exhausted',0)}", sub="Replied = stopped | Exhausted = 3 msgs sent")

    # Engagement row
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    total = kpis["total_leads"]
    engaged = kpis.get("total_engaged", 0)
    not_engaged = max(0, total - engaged)
    engagement_rate = round(engaged / total * 100, 1) if total > 0 else 0

    e1, e2, e3, e4 = st.columns(4)
    with e1: kpi_card("Overall Assigned", total, sub="Total leads in system")
    with e2: kpi_card("Overall Engaged", engaged, sub="WA replied OR call connected", delta=f"{engagement_rate}% engagement rate", delta_type="up")
    with e3: kpi_card("Not Yet Engaged", not_engaged, sub="No reply, no connected call", delta_type="warn")
    with e4: rate_card("Engagement Rate", engagement_rate, sub=f"{engaged} / {total}")
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    r1, r2, r3, r4 = st.columns(4)
    with r1: rate_card("WA Reply Rate", kpis["wa_reply_rate"], sub=f"{kpis['wa_replied']} / {kpis['wa_sent']}")
    with r2: rate_card("Call Connect Rate", kpis["call_connection_rate"], sub=f"{kpis['calls_connected']} / {kpis['calls_triggered']}")
    with r3: rate_card("Booking Rate", kpis["booking_rate"])
    with r4: rate_card("Conversion Rate", kpis["conversion_rate"])

    # Daily engagement trend chart
    from metrics import daily_engagement_trend
    eng_trend = daily_engagement_trend(data) if data else pd.DataFrame()
    if not eng_trend.empty:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown("**📅 Daily Engagement (WA Replied + Calls Connected)**")
        fig_eng = go.Figure()
        if "WA Replied" in eng_trend.columns:
            fig_eng.add_trace(go.Bar(
                x=eng_trend["date"], y=eng_trend["WA Replied"],
                name="WA Replied", marker_color="#1f6feb",
                hovertemplate="<b>%{x|%d %b}</b><br>WA Replied: %{y}<extra></extra>",
            ))
        if "Call Connected" in eng_trend.columns:
            fig_eng.add_trace(go.Bar(
                x=eng_trend["date"], y=eng_trend["Call Connected"],
                name="Call Connected", marker_color="#3fb950",
                hovertemplate="<b>%{x|%d %b}</b><br>Call Connected: %{y}<extra></extra>",
            ))
        fig_eng.update_layout(barmode="stack")
        _chart_layout(fig_eng, "Daily Engagement Trend")
        st.plotly_chart(fig_eng, use_container_width=True)

    # Operational risk strip — admin only
    if role == "admin":
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown("**⚠️ Operational Alerts**")
        a1, a2, a3, a4 = st.columns(4)
        with a1: kpi_card("Stuck Leads", kpis["stuck_leads"], sub=f">{THRESHOLDS['stuck_lead_hours']}h no progress", delta="⚠ Needs attention" if kpis["stuck_leads"] > 0 else "", delta_type="warn")
        with a2: kpi_card("Overdue Follow-ups", kpis["overdue_followups"], delta_type="down")
        with a3: kpi_card("Error Leads", kpis["error_leads"], delta_type="down")
        with a4: kpi_card("Pending Actions", kpis["pending_action_leads"])


# =============================================================================
# SECTION 2 — FUNNEL VIEW
# =============================================================================

def render_funnel(kpis: dict):
    st.markdown("### 🔽 Lead Funnel")

    stages = [
        ("Total Leads",              kpis["total_leads"]),
        ("Assigned",                 kpis["assigned_leads"]),
        ("WA Sent",                  kpis["wa_sent"]),
        ("WA Replied (stopped)",     kpis.get("fu_replied", 0)),
        ("Calls Triggered",          kpis["calls_triggered"]),
        ("Calls Connected",          kpis["calls_connected"]),
        ("Booked",                   kpis["booked_leads"]),
        ("Follow-up Exhausted",      kpis.get("fu_exhausted", 0)),
    ]

    labels = [s[0] for s in stages]
    values = [s[1] for s in stages]

    fig = go.Figure(go.Funnel(
        y=labels,
        x=values,
        textinfo="value+percent initial",
        marker=dict(color=COLOR_SEQ[:len(labels)]),
        connector=dict(line=dict(color="#3a3a5c", width=1)),
    ))
    fig.update_layout(title="Lead Conversion Funnel", **PLOTLY_THEME)
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# SECTION 3 — CHANNEL PERFORMANCE
# =============================================================================

def render_channel_performance(df: pd.DataFrame):
    st.markdown("### 📡 Channel Performance")

    col_a, col_b = st.columns(2)

    with col_a:
        ch = leads_by_channel(df, "assigned_channel")
        if not ch.empty:
            fig = px.pie(
                values=ch.values, names=ch.index,
                color_discrete_sequence=COLOR_SEQ,
                hole=0.55,
                title="Assigned Channel Split",
            )
            fig.update_traces(
                textinfo="percent+label",
                textfont_size=12,
                hovertemplate="<b>%{label}</b><br>Leads: %{value}<br>Share: %{percent}<extra></extra>",
            )
            _chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True)

            # Clickable breakdown
            selected_ch = st.selectbox("Drill into channel", ["All"] + list(ch.index), key="ch_drill")
            if selected_ch != "All":
                sub = df[df["assigned_channel"] == selected_ch]
                c1, c2, c3 = st.columns(3)
                with c1: kpi_card("Leads", len(sub))
                with c2: kpi_card("WA Replied", int(sub.get("wa_replied", pd.Series()).apply(lambda x: x is True).sum()) if "wa_replied" in sub.columns else 0)
                with c3: kpi_card("Connected Calls", int(sub.get("ah_call_status", pd.Series()).isin(THRESHOLDS["arrowhead_connected_statuses"]).sum()) if "ah_call_status" in sub.columns else 0)
        else:
            st.info("No channel data available.")

    with col_b:
        if "assigned_channel" in df.columns:
            chart_rows = []
            for ch, grp in df.groupby("assigned_channel"):
                total = len(grp)
                ch_lower = str(ch).lower()
                if "arrowhead" in ch_lower:
                    triggered = grp["ah_triggered_at"].notna().sum() if "ah_triggered_at" in grp.columns else 0
                    connected = grp["ah_call_status"].isin(THRESHOLDS["arrowhead_connected_statuses"]).sum() if "ah_call_status" in grp.columns else 0
                    rate = round(connected / triggered * 100, 1) if triggered > 0 else 0
                    label = f"Call Connect ({connected}/{triggered})"
                else:
                    sent = grp["wa_status"].isin(THRESHOLDS["periskope_sent_statuses"]).sum() if "wa_status" in grp.columns else total
                    replied = grp["wa_replied"].apply(lambda x: x is True or str(x).lower() in {"true","yes","1"}).sum() if "wa_replied" in grp.columns else 0
                    rate = round(replied / sent * 100, 1) if sent > 0 else 0
                    label = f"WA Reply ({replied}/{sent})"
                chart_rows.append({"Channel": ch, "Rate": rate, "Metric": label})

            if chart_rows:
                import pandas as _pd
                chart_df = _pd.DataFrame(chart_rows)
                fig = px.bar(
                    chart_df, x="Channel", y="Rate",
                    color="Rate",
                    color_continuous_scale=["#f85149", "#d29922", "#3fb950"],
                    title="Channel Performance Rate (%)",
                    text="Rate",
                    hover_data={"Metric": True, "Rate": True},
                )
                fig.update_traces(
                    texttemplate="%{text}%",
                    textposition="outside",
                    hovertemplate="<b>%{x}</b><br>%{customdata[0]}<br>Rate: %{y}%<extra></extra>",
                )
                _chart_layout(fig)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Channel data not available.")


# =============================================================================
# SECTION 4 — WHATSAPP / FOLLOW-UP PERFORMANCE
# =============================================================================

def render_followup_performance(df: pd.DataFrame, kpis: dict, role: str = "user"):
    st.markdown("### 💬 WhatsApp & Follow-up Performance")

    c1, c2 = st.columns(2)

    with c1:
        wa_data = {
            "Sent (No Reply)": kpis["wa_no_reply"],
            "Replied":         kpis["wa_replied"],
            "Moved to AH":     kpis["wa_moved_to_arrowhead"],
        }
        fig = go.Figure(go.Bar(
            x=list(wa_data.keys()),
            y=list(wa_data.values()),
            marker_color=["#ffab40", "#00e676", "#7c6af7"],
            text=list(wa_data.values()),
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>",
        ))
        _chart_layout(fig, "WhatsApp Outcome Breakdown")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        # Follow-up status from actual sheet data
        fu_df = df[df["fu_status"].notna()] if "fu_status" in df.columns else pd.DataFrame()
        if not fu_df.empty:
            fu_counts = fu_df["fu_status"].value_counts()
            color_map_fu = {
                "done":            "#00e676",
                "stopped_replied": "#40c4ff",
                "waiting":         "#ffab40",
                "in_progress":     "#7c6af7",
            }
            colors = [color_map_fu.get(s, "#888888") for s in fu_counts.index]
            fig = go.Figure(go.Bar(
                x=fu_counts.index,
                y=fu_counts.values,
                marker_color=colors,
                text=fu_counts.values,
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>",
            ))
            _chart_layout(fig, "Follow-up Status Breakdown")
            st.plotly_chart(fig, use_container_width=True)
        else:
            fig = px.pie(
                values=[kpis["followup_active"], kpis["overdue_followups"], kpis["third_touch_sent"]],
                names=["Active", "Overdue", "3rd Touch"],
                color_discrete_sequence=["#40c4ff", "#ff5252", "#f06292"],
                hole=0.6,
                title="Follow-up Status Distribution",
            )
            fig.update_traces(textinfo="percent+label")
            _chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True)

    # Project-wise WA performance
    if "project" in df.columns and "wa_replied" in df.columns:
        st.markdown("**Project-wise WhatsApp Performance**")
        proj_wa = df.groupby("project").agg(
            total=("phone_norm", "count"),
            replied=("wa_replied", lambda x: x.apply(lambda v: v is True).sum()),
        ).reset_index()
        proj_wa["not_replied"] = proj_wa["total"] - proj_wa["replied"]
        proj_wa["reply_rate"] = (proj_wa["replied"] / proj_wa["total"] * 100).round(1)
        fig = px.bar(
            proj_wa, x="project", y=["replied", "not_replied"],
            barmode="stack",
            color_discrete_map={"replied": "#00e676", "not_replied": "#ff5252"},
            title="WA Replied vs No Reply by Project",
            text_auto=True,
        )
        fig.update_traces(hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y}<extra></extra>")
        _chart_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

    # Overdue follow-ups table — admin only
    overdue = overdue_followups_df(df)
    if not overdue.empty and role == "admin":
        st.markdown(f"**🔴 Overdue Follow-ups ({len(overdue)})**")
        _render_styled_table(overdue, highlight_col="fu_next_followup_due_at", highlight_type="overdue")


# =============================================================================
# SECTION 5 — CALLING PERFORMANCE
# =============================================================================

def render_calling_performance(df: pd.DataFrame, kpis: dict):
    st.markdown("### 📞 Calling Performance")

    c1, c2, c3 = st.columns(3)
    with c1: kpi_card("Calls Triggered",    kpis["calls_triggered"])
    with c2: kpi_card("Connected",          kpis["calls_connected"],     delta_type="up")
    with c3: kpi_card("Not Connected",      kpis["calls_not_connected"], delta_type="down")

    c4, c5, c6 = st.columns(3)
    with c4: kpi_card("Busy",               kpis["calls_busy"],          delta_type="warn")
    with c5: kpi_card("Failed / Error",     kpis["calls_failed"],        delta_type="down")
    with c6: kpi_card("Avg Duration (s)",   kpis["avg_call_duration"])

    col_a, col_b = st.columns(2)

    with col_a:
        call_s = calls_by_status(df)
        if not call_s.empty:
            color_map = {
                "connected":     "#00e676",
                "not_connected": "#ff5252",
                "busy":          "#ffab40",
                "failed":        "#f06292",
                "error":         "#ff5252",
            }
            colors = [color_map.get(s, "#7c6af7") for s in call_s.index]
            fig = go.Figure(go.Bar(
                x=call_s.index,
                y=call_s.values,
                marker_color=colors,
                text=call_s.values,
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>",
            ))
            _chart_layout(fig, "Call Status Distribution")
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        # Connected vs Not Connected donut
        connected = kpis["calls_connected"]
        not_connected = kpis["calls_not_connected"]
        total_triggered = kpis["calls_triggered"]
        other = max(0, total_triggered - connected - not_connected)
        fig = px.pie(
            values=[connected, not_connected, other],
            names=["Connected", "Not Connected", "Other"],
            color_discrete_sequence=["#00e676", "#ff5252", "#ffab40"],
            hole=0.6,
            title=f"Connection Rate: {kpis['call_connection_rate']}%",
        )
        fig.update_traces(
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
        )
        _chart_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

    # Project-wise call breakdown
    if "project" in df.columns and "ah_call_status" in df.columns:
        st.markdown("**Project-wise Call Breakdown**")
        proj_grp = df.groupby("project").agg(
            triggered=("ah_triggered_at", lambda x: x.notna().sum()) if "ah_triggered_at" in df.columns else ("ah_call_status", "count"),
            connected=("ah_call_status", lambda x: x.isin(THRESHOLDS["arrowhead_connected_statuses"]).sum()),
            not_connected=("ah_call_status", lambda x: x.isin(THRESHOLDS["arrowhead_not_connected_statuses"]).sum()),
        ).reset_index()
        fig = px.bar(
            proj_grp, x="project", y=["connected", "not_connected"],
            barmode="stack",
            color_discrete_map={"connected": "#00e676", "not_connected": "#ff5252"},
            title="Calls by Project",
            labels={"value": "Calls", "project": "Project"},
        )
        fig.update_traces(hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y}<extra></extra>")
        _chart_layout(fig)
        st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# SECTION 6 — SITE VISIT / BOOKING VIEW
# =============================================================================

def render_booking_view(df: pd.DataFrame, kpis: dict):
    st.markdown("### 🏠 Site Visit & Booking View")

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Site Visits Scheduled", kpis["site_visits_scheduled"])
    with c2: kpi_card("Phone Calls Scheduled", kpis["phone_calls_scheduled"])
    with c3: kpi_card("Booked Leads",          kpis["booked_leads"])
    with c4: kpi_card("Done Leads",            kpis["done_leads"])

    # Booked vs Done gauge
    col_a, col_b = st.columns(2)
    with col_a:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=kpis["booked_leads"],
            title={"text": "Site Visits / Calls Booked", "font": {"color": "#8b949e", "size": 13}},
            gauge={
                "axis": {"range": [0, max(kpis["total_leads"], 1)], "tickcolor": "#30363d", "tickfont": {"color": "#6e7681"}},
                "bar": {"color": "#1f6feb"},
                "steps": [
                    {"range": [0, kpis["done_leads"]], "color": "#0d2818"},
                    {"range": [kpis["done_leads"], kpis["booked_leads"]], "color": "#0d1f38"},
                ],
                "bgcolor": "#21262d",
                "bordercolor": "#30363d",
            },
            number={"font": {"color": "#e6edf3", "size": 40}},
        ))
        fig.update_layout(**PLOTLY_THEME)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        # Project-wise booking breakdown
        if "project" in df.columns:
            proj = df.groupby("project").apply(
                lambda g: pd.Series({
                    "Total":  len(g),
                    "Booked": g.apply(lambda r: _is_booked_row(r), axis=1).sum(),
                })
            ).reset_index()
            fig = px.bar(
                proj, x="project", y=["Total", "Booked"],
                barmode="group",
                color_discrete_sequence=["#1f6feb", "#d29922"],
                title="Project-wise Booking Breakdown",
            )
            _chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True)


def _is_booked_row(row) -> bool:
    alert_type = str(row.get("al_alert_type", "")).lower().strip()
    if not alert_type or alert_type in {"", "nan", "none"}:
        return False
    all_types = THRESHOLDS["site_visit_alert_types"] + THRESHOLDS["phone_call_alert_types"]
    return any(t in alert_type for t in all_types)


def _is_done_row(row) -> bool:
    fu_status = str(row.get("fu_status", "")).lower().strip()
    if fu_status in {"done", "stopped_replied"}:
        return True
    last_outcome = str(row.get("tt_last_outcome", "")).lower().strip()
    return any(w in last_outcome for w in ["done", "completed", "booked", "visit done"])


# =============================================================================
# SECTION 7 — OPERATIONAL RISK / EXCEPTIONS
# =============================================================================

def render_operational_risk(df: pd.DataFrame, kpis: dict):
    st.markdown("### 🚨 Operational Risk & Exceptions")

    c1, c2, c3 = st.columns(3)
    with c1: kpi_card("Stuck Leads",       kpis["stuck_leads"],          delta="⚠ No progress", delta_type="warn")
    with c2: kpi_card("Error Leads",       kpis["error_leads"],          delta_type="down")
    with c3: kpi_card("Pending Actions",   kpis["pending_action_leads"], delta_type="warn")

    tabs = st.tabs(["🔴 Stuck", "❌ Errors", "⏳ Pending Actions", "📅 Overdue Follow-ups"])

    with tabs[0]:
        stuck = stuck_leads_df(df)
        if stuck.empty:
            st.success("No stuck leads right now.")
        else:
            _render_styled_table(stuck, highlight_col=None, highlight_type="stuck")

    with tabs[1]:
        errors = error_leads_df(df)
        if errors.empty:
            st.success("No error leads.")
        else:
            _render_styled_table(errors, highlight_col=None, highlight_type="error")

    with tabs[2]:
        pending = pending_action_leads_df(df)
        if pending.empty:
            st.success("No pending action leads.")
        else:
            _render_styled_table(pending, highlight_col="tt_next_action", highlight_type="pending")

    with tabs[3]:
        overdue = overdue_followups_df(df)
        if overdue.empty:
            st.success("No overdue follow-ups.")
        else:
            _render_styled_table(overdue, highlight_col="fu_next_followup_due_at", highlight_type="overdue")


# =============================================================================
# SECTION 8 — LEAD DRILLDOWN
# =============================================================================

def render_lead_drilldown(df: pd.DataFrame):
    st.markdown("### 🔍 Lead Drilldown")

    search = st.text_input("Search by MLID, Phone, or Name", placeholder="e.g. ML1234 or 9876543210 or Rahul")

    if not search.strip():
        st.info("Enter a MLID, phone number, or name to look up a lead.")
        return

    q = search.strip().lower()
    mask = pd.Series([False] * len(df))

    for col in ["mlid", "phone", "name", "phone_norm", "mlid_norm"]:
        if col in df.columns:
            mask = mask | df[col].astype(str).str.lower().str.contains(q, na=False)

    results = df[mask]

    if results.empty:
        st.warning("No lead found matching that search.")
        return

    if len(results) > 1:
        st.info(f"{len(results)} leads matched. Showing first result. Refine your search for a specific lead.")

    row = results.iloc[0]

    # --- Identity block ---
    st.markdown("---")
    id1, id2, id3 = st.columns(3)
    with id1:
        st.markdown(f"**MLID:** `{row.get('mlid', 'N/A')}`")
        st.markdown(f"**Phone:** `{row.get('phone', 'N/A')}`")
    with id2:
        st.markdown(f"**Name:** {row.get('name', 'N/A')}")
        st.markdown(f"**Project:** {row.get('project', 'N/A')}")
    with id3:
        st.markdown(f"**Assigned Channel:** {row.get('assigned_channel', 'N/A')}")
        st.markdown(f"**Born Date:** {row.get('born_date', 'N/A')}")

    st.markdown("---")

    # --- Status badges ---
    def badge(label, val, good_vals=None, bad_vals=None):
        v = str(val).lower() if pd.notna(val) else "n/a"
        if v in {"n/a", "", "none", "nan"}:
            cls = "badge-grey"
        elif good_vals and v in good_vals:
            cls = "badge-green"
        elif bad_vals and v in bad_vals:
            cls = "badge-red"
        else:
            cls = "badge-yellow"
        return f'<span class="{cls}">{label}: {val}</span>&nbsp;&nbsp;'

    badges_html = ""
    badges_html += badge("WA Status",   row.get("wa_status"),    good_vals={"sent","delivered","read"}, bad_vals={"failed","error"})
    badges_html += badge("WA Replied",  row.get("wa_replied"),   good_vals={"true","yes"}, bad_vals={"false","no"})
    badges_html += badge("Call Status", row.get("ah_call_status"), good_vals=set(THRESHOLDS["arrowhead_connected_statuses"]), bad_vals=set(THRESHOLDS["arrowhead_failed_statuses"]))
    badges_html += badge("Touch Stage", row.get("tt_touch_stage"))
    badges_html += badge("Next Action", row.get("tt_next_action"))
    st.markdown(CARD_CSS, unsafe_allow_html=True)
    st.markdown(badges_html, unsafe_allow_html=True)

    st.markdown("---")

    # --- Timeline ---
    timeline_events = []
    ts_fields = [
        ("born_date",              "Lead Created"),
        ("wa_sent_at",             "WA Sent"),
        ("wa_replied_at",          "WA Replied"),
        ("wa_moved_to_arrowhead_at","Moved to Arrowhead"),
        ("ah_triggered_at",        "Call Triggered"),
        ("ah_completed_at",        "Call Completed"),
        ("ah_moved_to_periskope_at","Moved to Periskope"),
        ("tt_logged_at",           "Touch Logged"),
        ("fu_last_message_at",     "Last Follow-up"),
        ("fu_next_followup_due_at","Next Follow-up Due"),
        ("al_scheduled_datetime",  "Scheduled Event"),
    ]
    for col, label in ts_fields:
        val = row.get(col)
        if pd.notna(val) and str(val).strip() not in {"", "nan", "None", "NaT"}:
            timeline_events.append({"Event": label, "Time": str(val)})

    if timeline_events:
        st.markdown("**📅 Lead Timeline**")
        tl_df = pd.DataFrame(timeline_events)
        fig = px.scatter(
            tl_df, x="Time", y="Event",
            color="Event",
            color_discrete_sequence=COLOR_SEQ,
            title="",
        )
        fig.update_traces(marker=dict(size=14))
        _chart_layout(fig, "Lead Activity Timeline")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No timeline events available for this lead.")

    # --- Raw details expander ---
    with st.expander("View all raw fields for this lead"):
        clean = {k: v for k, v in row.items() if pd.notna(v) and str(v).strip() not in {"", "nan", "None"}}
        st.json(clean)


# =============================================================================
# SECTION 9 — TRENDS
# =============================================================================

def render_trends(df: pd.DataFrame):
    st.markdown("### 📈 Daily Trends")

    c1, c2 = st.columns(2)

    with c1:
        trend = daily_trend(df, "born_date", "New Leads")
        if not trend.empty:
            fig = px.area(
                trend, x="date", y="New Leads",
                color_discrete_sequence=["#7c6af7"],
                title="New Leads Over Time",
            )
            _chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        trend_wa = daily_trend(df, "wa_sent_at", "WA Sent")
        trend_ah = daily_trend(df, "ah_triggered_at", "Calls Triggered")
        if not trend_wa.empty or not trend_ah.empty:
            fig = go.Figure()
            if not trend_wa.empty:
                fig.add_trace(go.Scatter(x=trend_wa["date"], y=trend_wa["WA Sent"],
                    name="WA Sent", line=dict(color="#00e5ff", width=2), fill="tozeroy", fillcolor="rgba(0,229,255,0.08)"))
            if not trend_ah.empty:
                fig.add_trace(go.Scatter(x=trend_ah["date"], y=trend_ah["Calls Triggered"],
                    name="Calls Triggered", line=dict(color="#ffab40", width=2), fill="tozeroy", fillcolor="rgba(255,171,64,0.08)"))
            _chart_layout(fig, "WA Sent vs Calls Triggered Over Time")
            st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# SECTION 10 — RAW EXPORT TABLES
# =============================================================================

def render_export_tables(df: pd.DataFrame):
    st.markdown("### 📤 Filtered Export Tables")
    st.caption("All tables are read-only. Use the download button to export as CSV.")

    export_views = {
        "All Leads":            df,
        "Arrowhead Leads":      df[df.get("assigned_channel", pd.Series(dtype=str)).astype(str).str.lower().str.contains("arrowhead", na=False)] if "assigned_channel" in df.columns else pd.DataFrame(),
        "Periskope Leads":      df[df.get("assigned_channel", pd.Series(dtype=str)).astype(str).str.lower().str.contains("periskope", na=False)] if "assigned_channel" in df.columns else pd.DataFrame(),
        "No Reply Leads":       df[df.get("wa_replied", pd.Series(dtype=object)).apply(lambda x: x is not True and str(x).lower() not in {"true","yes","1"})] if "wa_replied" in df.columns else pd.DataFrame(),
        "Overdue Follow-ups":   overdue_followups_df(df),
        "Stuck Leads":          stuck_leads_df(df),
        "Error Leads":          error_leads_df(df),
        "Pending Actions":      pending_action_leads_df(df),
    }

    selected = st.selectbox("Select table to view", list(export_views.keys()))
    view_df = export_views[selected]

    if view_df is None or view_df.empty:
        st.info(f"No data for '{selected}'.")
        return

    st.caption(f"{len(view_df)} rows")
    _render_styled_table(view_df, highlight_col=None, highlight_type=None, max_rows=200)

    csv = view_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"⬇ Download '{selected}' as CSV",
        data=csv,
        file_name=f"{selected.lower().replace(' ', '_')}.csv",
        mime="text/csv",
    )


# =============================================================================
# STYLED TABLE RENDERER
# Uses Streamlit's dataframe with column config for a premium look.
# =============================================================================

DISPLAY_COLS = [
    "mlid", "phone", "name", "project", "assigned_channel",
    "born_date", "wa_status", "wa_replied", "wa_sent_at",
    "ah_call_status", "ah_call_duration", "ah_triggered_at",
    "tt_touch_stage", "tt_current_action", "tt_next_action", "tt_logged_at",
    "fu_status", "fu_next_followup_due_at", "fu_followup_count",
    "al_alert_type", "al_scheduled_datetime",
]


def _render_styled_table(df: pd.DataFrame, highlight_col=None, highlight_type=None, max_rows=100):
    """Render a styled, read-only dataframe with column config."""
    # Only show columns that exist and are in our display list
    show_cols = [c for c in DISPLAY_COLS if c in df.columns]
    if not show_cols:
        show_cols = list(df.columns[:20])  # fallback: first 20 cols

    display_df = df[show_cols].head(max_rows).copy()

    # Build column config for nicer display
    col_config = {}
    for col in show_cols:
        label = col.replace("_", " ").title()
        if any(x in col for x in ["_at", "date", "time", "due"]):
            col_config[col] = st.column_config.TextColumn(label)  # show as text to avoid tz issues
        elif col in {"wa_replied", "ah_error", "wa_error"}:
            col_config[col] = st.column_config.CheckboxColumn(label)
        elif col in {"ah_call_duration", "fu_followup_count"}:
            col_config[col] = st.column_config.NumberColumn(label)
        else:
            col_config[col] = st.column_config.TextColumn(label)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config=col_config,
    )


# =============================================================================
# DATA SOURCE STATUS PANEL
# =============================================================================

def render_data_source_status(statuses: dict):
    with st.expander("Data Source Status", expanded=False):
        for key, msg in statuses.items():
            if msg.startswith("✅"):
                st.success(msg)
            elif msg.startswith("ℹ️"):
                st.info(msg)
            elif msg.startswith("⚠️"):
                st.warning(msg)
            else:
                st.error(msg)


# =============================================================================
# SECTION — KALBHOJADITYA REPORT VIEW
# Uses Daily + Cumulative report sheets directly for accurate business outcomes
# =============================================================================

def render_kalbhoj_report(data: dict):
    st.markdown("### 📋 Kalbhojaditya Report")

    daily = data.get("kalbhoj_daily_report")
    cumul = data.get("kalbhoj_cumulative_report")

    if (daily is None or daily.empty) and (cumul is None or cumul.empty):
        st.warning("Kalbhojaditya report sheets not loaded.")
        return

    tab1, tab2 = st.tabs(["📈 Cumulative Report", "📅 Daily Report"])

    with tab1:
        if cumul is None or cumul.empty:
            st.info("Cumulative report not available.")
        else:
            _render_report_section(cumul, "Cumulative")

    with tab2:
        if daily is None or daily.empty:
            st.info("Daily report not available.")
        else:
            _render_report_section(daily, "Daily")


def _render_report_section(df: pd.DataFrame, label: str):

    num_cols = ["assigned_leads", "site_visit_booked", "site_visit_done", "flat_blocked", "sale_closure"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    is_cumulative = label == "Cumulative"

    # For cumulative — build running total df for charts
    if is_cumulative:
        df_display = df.copy()
        for col in num_cols:
            if col in df_display.columns:
                df_display[col] = df_display[col].cumsum()
        last = df_display.iloc[-1] if not df_display.empty else {}
        total_assigned     = int(last.get("assigned_leads", 0))
        total_sv_booked    = int(last.get("site_visit_booked", 0))
        total_sv_done      = int(last.get("site_visit_done", 0))
        total_flat_blocked = int(last.get("flat_blocked", 0))
        total_sale_closure = int(last.get("sale_closure", 0))
        card_sub = "Overall total"
    else:
        df_display = df.copy()
        # KPI = latest day's values
        last = df_display.iloc[-1] if not df_display.empty else {}
        total_assigned     = int(last.get("assigned_leads", 0))
        total_sv_booked    = int(last.get("site_visit_booked", 0))
        total_sv_done      = int(last.get("site_visit_done", 0))
        total_flat_blocked = int(last.get("flat_blocked", 0))
        total_sale_closure = int(last.get("sale_closure", 0))
        card_sub = "Latest day"

    sv_booking_rate = round(total_sv_booked / total_assigned * 100, 1) if total_assigned > 0 else 0
    sv_done_rate    = round(total_sv_done / total_sv_booked * 100, 1) if total_sv_booked > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: kpi_card("Leads Assigned",    total_assigned,     sub=card_sub)
    with c2: kpi_card("Site Visit Booked", total_sv_booked,    sub=card_sub)
    with c3: kpi_card("Site Visit Done",   total_sv_done,      sub=card_sub)
    with c4: kpi_card("Flat Blocked",      total_flat_blocked, sub=card_sub)
    with c5: kpi_card("Sale Closure",      total_sale_closure, sub=card_sub)

    r1, r2 = st.columns(2)
    with r1: rate_card("SV Booking Rate", sv_booking_rate, sub=f"{total_sv_booked} / {total_assigned}")
    with r2: rate_card("SV Done Rate",    sv_done_rate,    sub=f"{total_sv_done} / {total_sv_booked}")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # Daily table — show every day's raw numbers
    if not is_cumulative:
        st.markdown("**📅 Day-wise Breakdown**")
        display_cols = [c for c in ["date","assigned_leads","site_visit_booked","site_visit_done","flat_blocked","sale_closure"] if c in df_display.columns]
        show_df = df_display[display_cols].copy()
        show_df["date"] = show_df["date"].dt.strftime("%d %b %Y")
        show_df.columns = [c.replace("_", " ").title() for c in show_df.columns]
        st.dataframe(show_df, use_container_width=True, hide_index=True)
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # Charts
    col_a, col_b = st.columns(2)
    with col_a:
        fig = go.Figure()
        if "assigned_leads" in df_display.columns:
            fig.add_trace(go.Bar(x=df_display["date"], y=df_display["assigned_leads"],
                name="Assigned", marker_color="#1f6feb",
                hovertemplate="<b>%{x|%d %b}</b><br>Assigned: %{y}<extra></extra>"))
        if "site_visit_booked" in df_display.columns:
            fig.add_trace(go.Scatter(x=df_display["date"], y=df_display["site_visit_booked"],
                name="SV Booked", line=dict(color="#3fb950", width=2), mode="lines+markers",
                hovertemplate="<b>%{x|%d %b}</b><br>SV Booked: %{y}<extra></extra>"))
        _chart_layout(fig, f"{label} — Assigned vs SV Booked")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig2 = go.Figure()
        for col, color, name in [
            ("site_visit_booked","#3fb950","SV Booked"),
            ("site_visit_done","#58a6ff","SV Done"),
            ("flat_blocked","#d29922","Flat Blocked"),
            ("sale_closure","#f85149","Sale Closure"),
        ]:
            if col in df_display.columns:
                fig2.add_trace(go.Scatter(x=df_display["date"], y=df_display[col],
                    name=name, line=dict(color=color, width=2), mode="lines+markers",
                    hovertemplate=f"<b>%{{x|%d %b}}</b><br>{name}: %{{y}}<extra></extra>"))
        _chart_layout(fig2, f"{label} — Outcome Trends")
        st.plotly_chart(fig2, use_container_width=True)

    # Funnel
    funnel_stages = [(l, v) for l, v in [
        ("Leads Assigned", total_assigned), ("Site Visit Booked", total_sv_booked),
        ("Site Visit Done", total_sv_done), ("Flat Blocked", total_flat_blocked),
        ("Sale Closure", total_sale_closure)] if v > 0]
    if funnel_stages:
        fig3 = go.Figure(go.Funnel(
            y=[s[0] for s in funnel_stages], x=[s[1] for s in funnel_stages],
            textinfo="value+percent initial",
            marker=dict(color=["#1f6feb","#3fb950","#58a6ff","#d29922","#f85149"]),
            connector=dict(line=dict(color="#30363d", width=1)),
        ))
        fig3.update_layout(**PLOTLY_THEME)
        st.plotly_chart(fig3, use_container_width=True)

    if is_cumulative:
        with st.expander("View cumulative raw data"):
            display_cols = [c for c in ["date","assigned_leads","site_visit_booked","site_visit_done","flat_blocked","sale_closure"] if c in df_display.columns]
            show_df = df_display[display_cols].copy()
            show_df["date"] = show_df["date"].dt.strftime("%d %b %Y")
            show_df.columns = [c.replace("_", " ").title() for c in show_df.columns]
            st.dataframe(show_df, use_container_width=True, hide_index=True)

