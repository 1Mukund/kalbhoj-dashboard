# =============================================================================
# metrics.py — All KPI computations as pure functions
# Edit the logic here if your business definitions change.
# All functions take DataFrames and return scalar values or filtered DFs.
# =============================================================================

import pandas as pd
from datetime import datetime, timezone
import pytz
from config import THRESHOLDS, TIMEZONE

IST = pytz.timezone(TIMEZONE)


def now_ist() -> datetime:
    return datetime.now(IST)


# =============================================================================
# A. LEAD INTAKE & ASSIGNMENT
# =============================================================================

def total_leads(df: pd.DataFrame) -> int:
    return len(df)


def new_leads_today(df: pd.DataFrame, date_col: str = "born_date") -> int:
    if date_col not in df.columns:
        return 0
    today = now_ist().date()
    def _check(x):
        if not pd.notna(x):
            return False
        try:
            ts = pd.Timestamp(x)
            if ts.tzinfo is not None:
                ts = ts.tz_localize(None)
            return ts.date() == today
        except Exception:
            return False
    return int(df[date_col].apply(_check).sum())


def new_leads_last_24h(df: pd.DataFrame, date_col: str = "born_date") -> int:
    if date_col not in df.columns:
        return 0
    cutoff = pd.Timestamp(now_ist()) - pd.Timedelta(hours=24)
    def _check(x):
        if not pd.notna(x):
            return False
        try:
            ts = pd.Timestamp(x)
            if ts.tzinfo is not None:
                ts = ts.tz_localize(None)
            return ts >= cutoff.replace(tzinfo=None)
        except Exception:
            return False
    return int(df[date_col].apply(_check).sum())


def assigned_leads(df: pd.DataFrame, channel_col: str = "assigned_channel") -> int:
    if channel_col not in df.columns:
        return 0
    return int(df[channel_col].notna().sum())


def leads_by_channel(df: pd.DataFrame, channel_col: str = "assigned_channel") -> pd.Series:
    if channel_col not in df.columns:
        return pd.Series(dtype=int)
    return df[channel_col].value_counts()


def indian_vs_international(df: pd.DataFrame) -> dict:
    from normalizer import is_indian_phone
    if "phone" not in df.columns:
        return {"Indian": 0, "International": 0}
    indian = int(df["phone"].apply(is_indian_phone).sum())
    return {"Indian": indian, "International": len(df) - indian}


# =============================================================================
# B. PERISKOPE / WHATSAPP
# =============================================================================

def total_engaged(df: pd.DataFrame) -> int:
    """
    Overall engaged = unique leads who either replied on WA OR had a connected call.
    """
    engaged = set()
    if "wa_replied" in df.columns and "phone_norm" in df.columns:
        wa_replied_mask = df["wa_replied"].apply(lambda x: x is True or str(x).lower() in {"true","yes","1"})
        engaged.update(df.loc[wa_replied_mask, "phone_norm"].dropna().tolist())
    if "ah_call_status" in df.columns and "phone_norm" in df.columns:
        connected_mask = df["ah_call_status"].isin(THRESHOLDS["arrowhead_connected_statuses"])
        engaged.update(df.loc[connected_mask, "phone_norm"].dropna().tolist())
    return len(engaged)


def daily_engagement_trend(data: dict) -> pd.DataFrame:
    """
    Daily count of engaged leads (WA replied + calls connected) by date.
    Uses raw sheets for accurate timestamps.
    """
    records = []

    # WA replied_at
    wa = data.get("periskope_first_touch")
    if wa is not None and not wa.empty and "replied_at" in wa.columns and "replied" in wa.columns:
        wa_rep = wa[wa["replied"].apply(lambda x: x is True or str(x).lower() in {"true","yes","1"})].copy()
        wa_rep["_date"] = wa_rep["replied_at"].apply(
            lambda x: pd.Timestamp(x).tz_localize(None).date() if pd.notna(x) else None
        )
        for d in wa_rep["_date"].dropna():
            records.append({"date": d, "type": "WA Replied"})

    # AH connected completed_at
    ah = data.get("arrowhead_kalbhoj")
    if ah is not None and not ah.empty and "completed_at" in ah.columns and "call_status" in ah.columns:
        ah_conn = ah[ah["call_status"].isin(THRESHOLDS["arrowhead_connected_statuses"])].copy()
        ah_conn["_date"] = ah_conn["completed_at"].apply(
            lambda x: pd.Timestamp(x).tz_localize(None).date() if pd.notna(x) else None
        )
        for d in ah_conn["_date"].dropna():
            records.append({"date": d, "type": "Call Connected"})

    if not records:
        return pd.DataFrame(columns=["date", "WA Replied", "Call Connected", "Total"])

    df_r = pd.DataFrame(records)
    pivot = df_r.groupby(["date", "type"]).size().unstack(fill_value=0).reset_index()
    for col in ["WA Replied", "Call Connected"]:
        if col not in pivot.columns:
            pivot[col] = 0
    pivot["Total"] = pivot["WA Replied"] + pivot["Call Connected"]
    pivot["date"] = pd.to_datetime(pivot["date"])
    return pivot.sort_values("date")
    """Leads where WhatsApp was sent (status in sent statuses)."""
    col = "wa_status"
    if col not in df.columns:
        return 0
    sent = THRESHOLDS["periskope_sent_statuses"]
    return int(df[col].isin(sent).sum())


def wa_sent(df: pd.DataFrame) -> int:
    """Leads where WhatsApp was sent (status in sent statuses)."""
    col = "wa_status"
    if col not in df.columns:
        return 0
    sent = THRESHOLDS["periskope_sent_statuses"]
    return int(df[col].isin(sent).sum())


def wa_replied(df: pd.DataFrame) -> int:
    col = "wa_replied"
    if col not in df.columns:
        return 0
    return int(df[col].apply(lambda x: x is True or str(x).lower() in {"true", "yes", "1"}).sum())


def wa_no_reply(df: pd.DataFrame) -> int:
    return max(0, wa_sent(df) - wa_replied(df))


def wa_moved_to_arrowhead(df: pd.DataFrame) -> int:
    col = "wa_moved_to_arrowhead"
    if col not in df.columns:
        return 0
    return int(df[col].apply(lambda x: x is True or str(x).lower() in {"true", "yes", "1"}).sum())


def wa_reply_rate(df: pd.DataFrame) -> float:
    sent = wa_sent(df)
    if sent == 0:
        return 0.0
    return round(wa_replied(df) / sent * 100, 1)


def third_touch_sent(df: pd.DataFrame) -> int:
    col = "tt_touch_stage"
    if col not in df.columns:
        return 0
    stages = THRESHOLDS["third_touch_stages"]
    return int(df[col].isin(stages).sum())


# =============================================================================
# C. ARROWHEAD / CALLING
# =============================================================================

def calls_triggered(df: pd.DataFrame) -> int:
    col = "ah_triggered_at"
    if col not in df.columns:
        return 0
    return int(df[col].notna().sum())


def calls_by_status(df: pd.DataFrame) -> pd.Series:
    col = "ah_call_status"
    if col not in df.columns:
        return pd.Series(dtype=int)
    return df[col].value_counts()


def calls_connected(df: pd.DataFrame) -> int:
    col = "ah_call_status"
    if col not in df.columns:
        return 0
    return int(df[col].isin(THRESHOLDS["arrowhead_connected_statuses"]).sum())


def calls_not_connected(df: pd.DataFrame) -> int:
    col = "ah_call_status"
    if col not in df.columns:
        return 0
    return int(df[col].isin(THRESHOLDS["arrowhead_not_connected_statuses"]).sum())


def calls_busy(df: pd.DataFrame) -> int:
    col = "ah_call_status"
    if col not in df.columns:
        return 0
    return int(df[col].isin(THRESHOLDS["arrowhead_busy_statuses"]).sum())


def calls_failed(df: pd.DataFrame) -> int:
    col = "ah_call_status"
    if col not in df.columns:
        return 0
    return int(df[col].isin(THRESHOLDS["arrowhead_failed_statuses"]).sum())


def avg_call_duration(df: pd.DataFrame) -> float:
    col = "ah_call_duration"
    if col not in df.columns:
        return 0.0
    numeric = pd.to_numeric(df[col], errors="coerce").dropna()
    if numeric.empty:
        return 0.0
    return round(float(numeric.mean()), 1)


def call_connection_rate(df: pd.DataFrame) -> float:
    triggered = calls_triggered(df)
    if triggered == 0:
        return 0.0
    return round(calls_connected(df) / triggered * 100, 1)


def arrowhead_error_count(df: pd.DataFrame) -> int:
    col = "ah_error"
    if col not in df.columns:
        return 0
    return int(df[col].apply(
        lambda x: pd.notna(x) and str(x).strip().lower() not in {"", "false", "no", "0", "none"}
    ).sum())


# =============================================================================
# D. SITE VISIT / BOOKING OUTCOMES
# =============================================================================

def site_visits_scheduled(df: pd.DataFrame) -> int:
    col = "al_alert_type"
    if col not in df.columns:
        return 0
    types = THRESHOLDS["site_visit_alert_types"]
    return int(df[col].apply(
        lambda x: any(t in str(x).lower() for t in types) if pd.notna(x) else False
    ).sum())


def phone_calls_scheduled(df: pd.DataFrame) -> int:
    col = "al_alert_type"
    if col not in df.columns:
        return 0
    types = THRESHOLDS["phone_call_alert_types"]
    return int(df[col].apply(
        lambda x: any(t in str(x).lower() for t in types) if pd.notna(x) else False
    ).sum())


def booked_leads(df: pd.DataFrame) -> int:
    """
    Booked = lead has a site visit OR call scheduled in alert log.
    Based on alert_log intent values: site_visit_request, virtual_visit_request,
    meeting_request, call_request, callback_request, scheduling_request
    """
    return int(df.apply(lambda row: _is_booked(row), axis=1).sum())


def done_leads(df: pd.DataFrame) -> int:
    """
    Done = follow-up exhausted — 3 messages gaye, koi reply nahi (fu_status = 'done').
    stopped_replied alag hai — wo WA replied count mein jaata hai.
    """
    return int(df.apply(lambda row: _is_done(row), axis=1).sum())


def replied_leads(df: pd.DataFrame) -> int:
    """
    Replied = lead ne WA pe reply kiya, follow-up stop hua (fu_status = 'stopped_replied').
    """
    col = "fu_status"
    if col not in df.columns:
        return 0
    return int(df[col].apply(lambda x: str(x).strip().lower() == "stopped_replied").sum())


def _is_booked(row) -> bool:
    alert_type = str(row.get("al_alert_type", "")).lower().strip()
    if not alert_type or alert_type in {"", "nan", "none"}:
        return False
    all_types = THRESHOLDS["site_visit_alert_types"] + THRESHOLDS["phone_call_alert_types"]
    return any(t in alert_type for t in all_types)


def _is_done(row) -> bool:
    # Done = 3 follow-ups exhausted, no reply
    fu_status = str(row.get("fu_status", "")).lower().strip()
    return fu_status == "done"


# =============================================================================
# E. BUSINESS RATES
# =============================================================================

def site_visit_scheduling_rate(df: pd.DataFrame) -> float:
    total = total_leads(df)
    if total == 0:
        return 0.0
    return round(site_visits_scheduled(df) / total * 100, 1)


def booking_rate(df: pd.DataFrame) -> float:
    total = total_leads(df)
    if total == 0:
        return 0.0
    return round(booked_leads(df) / total * 100, 1)


def done_rate(df: pd.DataFrame) -> float:
    total = total_leads(df)
    if total == 0:
        return 0.0
    return round(done_leads(df) / total * 100, 1)


def final_conversion_rate(df: pd.DataFrame) -> float:
    """Done / Total leads."""
    return done_rate(df)


# =============================================================================
# F. OPERATIONAL HEALTH
# =============================================================================

def _safe_ts_compare(val, cutoff_naive: pd.Timestamp) -> bool:
    """Compare a timestamp value against a tz-naive cutoff safely."""
    if not pd.notna(val):
        return False
    try:
        ts = pd.Timestamp(val)
        if ts.tzinfo is not None:
            ts = ts.tz_localize(None)
        return ts < cutoff_naive
    except Exception:
        return False


def stuck_leads_df(df: pd.DataFrame) -> pd.DataFrame:
    threshold_hours = THRESHOLDS["stuck_lead_hours"]
    cutoff = (pd.Timestamp(now_ist()) - pd.Timedelta(hours=threshold_hours)).replace(tzinfo=None)

    def _is_stuck(row) -> bool:
        if _is_done(row) or _is_booked(row):
            return False
        for col in ["tt_logged_at", "ah_triggered_at", "wa_sent_at", "born_date"]:
            val = row.get(col)
            if pd.notna(val):
                return _safe_ts_compare(val, cutoff)
        return False

    if df.empty:
        return df
    mask = df.apply(_is_stuck, axis=1)
    return df[mask].copy()


def overdue_followups_df(df: pd.DataFrame) -> pd.DataFrame:
    col_due = "fu_next_followup_due_at"
    col_replied = "fu_replied"
    if col_due not in df.columns:
        return pd.DataFrame()

    now_naive = pd.Timestamp(now_ist()).replace(tzinfo=None)

    def _is_overdue(row) -> bool:
        due = row.get(col_due)
        replied = row.get(col_replied)
        if not pd.notna(due):
            return False
        try:
            ts = pd.Timestamp(due)
            if ts.tzinfo is not None:
                ts = ts.tz_localize(None)
            if ts >= now_naive:
                return False
        except Exception:
            return False
        if replied is True or str(replied).lower() in {"true", "yes", "1"}:
            return False
        return True

    mask = df.apply(_is_overdue, axis=1)
    return df[mask].copy()


def error_leads_df(df: pd.DataFrame) -> pd.DataFrame:
    """Leads with any error flag set in Arrowhead or Periskope."""
    masks = []
    for col in ["ah_error", "wa_error"]:
        if col in df.columns:
            masks.append(df[col].apply(
                lambda x: pd.notna(x) and str(x).strip().lower() not in {"", "false", "no", "0", "none"}
            ))
    if not masks:
        return pd.DataFrame()
    combined = masks[0]
    for m in masks[1:]:
        combined = combined | m
    return df[combined].copy()


def pending_action_leads_df(df: pd.DataFrame) -> pd.DataFrame:
    """Leads where next_action is set but not yet done."""
    col = "tt_next_action"
    if col not in df.columns:
        return pd.DataFrame()
    mask = df[col].apply(
        lambda x: pd.notna(x) and str(x).strip().lower() not in {"", "none", "done", "completed"}
    )
    return df[mask].copy()


def followup_active_count(df: pd.DataFrame) -> int:
    col = "fu_status"
    if col not in df.columns:
        return 0
    return int(df[col].apply(
        lambda x: str(x).lower() in {"active", "pending", "open"}
    ).sum())


# =============================================================================
# DAILY TREND HELPER
# =============================================================================

def daily_trend(df: pd.DataFrame, date_col: str, label: str) -> pd.DataFrame:
    """Returns a daily count DataFrame for charting."""
    if date_col not in df.columns or df.empty:
        return pd.DataFrame(columns=["date", label])
    series = df[date_col].dropna()
    dates = series.apply(lambda x: pd.Timestamp(x).date() if pd.notna(x) else None).dropna()
    counts = dates.value_counts().sort_index().reset_index()
    counts.columns = ["date", label]
    counts["date"] = pd.to_datetime(counts["date"])
    return counts


# =============================================================================
# COMPUTE ALL KPIs AT ONCE
# Returns a flat dict for easy rendering in views.py
# =============================================================================

def compute_all_kpis(df: pd.DataFrame) -> dict:
    return {
        # A
        "total_leads":              total_leads(df),
        "new_leads_today":          new_leads_today(df),
        "new_leads_24h":            new_leads_last_24h(df),
        "assigned_leads":           assigned_leads(df),
        "total_engaged":            total_engaged(df),
        "indian_vs_intl":           indian_vs_international(df),
        # B
        "wa_sent":                  wa_sent(df),
        "wa_replied":               wa_replied(df),
        "wa_no_reply":              wa_no_reply(df),
        "wa_moved_to_arrowhead":    wa_moved_to_arrowhead(df),
        "wa_reply_rate":            wa_reply_rate(df),
        "followup_active":          followup_active_count(df),
        "overdue_followups":        len(overdue_followups_df(df)),
        "third_touch_sent":         third_touch_sent(df),
        "fu_replied":               replied_leads(df),
        "fu_exhausted":             done_leads(df),
        # C
        "calls_triggered":          calls_triggered(df),
        "calls_connected":          calls_connected(df),
        "calls_not_connected":      calls_not_connected(df),
        "calls_busy":               calls_busy(df),
        "calls_failed":             calls_failed(df),
        "avg_call_duration":        avg_call_duration(df),
        "call_connection_rate":     call_connection_rate(df),
        "arrowhead_errors":         arrowhead_error_count(df),
        # D
        "site_visits_scheduled":    site_visits_scheduled(df),
        "phone_calls_scheduled":    phone_calls_scheduled(df),
        "booked_leads":             booked_leads(df),
        "done_leads":               done_leads(df),
        # E
        "sv_scheduling_rate":       site_visit_scheduling_rate(df),
        "booking_rate":             booking_rate(df),
        "done_rate":                done_rate(df),
        "conversion_rate":          final_conversion_rate(df),
        # F
        "stuck_leads":              len(stuck_leads_df(df)),
        "pending_action_leads":     len(pending_action_leads_df(df)),
        "error_leads":              len(error_leads_df(df)),
    }
