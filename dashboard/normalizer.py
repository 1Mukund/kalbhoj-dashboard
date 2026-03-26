# =============================================================================
# normalizer.py — Data cleaning and normalization helpers
# All functions are pure (no side effects). Safe to call on any column.
# =============================================================================

import re
import pandas as pd
import pytz
from config import THRESHOLDS, TIMEZONE

IST = pytz.timezone(TIMEZONE)


# -----------------------------------------------------------------------------
# PHONE NORMALIZATION
# Strips all non-digit characters, removes leading country code if present,
# returns a consistent 10-digit string for Indian numbers.
# For international numbers, returns digits only (no leading +).
# -----------------------------------------------------------------------------
def normalize_phone(phone_val) -> str:
    """
    Normalize a phone number to a consistent string for joining.
    Returns empty string if input is null/empty.
    """
    if pd.isna(phone_val) or str(phone_val).strip() == "":
        return ""
    raw = re.sub(r"[^\d]", "", str(phone_val).strip())
    # Remove leading 91 for Indian numbers (making them 10-digit)
    if len(raw) == 12 and raw.startswith("91"):
        return raw[2:]
    if len(raw) == 13 and raw.startswith("091"):
        return raw[3:]
    return raw


def is_indian_phone(phone_val) -> bool:
    """
    Returns True if the phone number appears to be Indian.
    Checks for +91/91 prefix or 10-digit starting with 6-9.
    """
    raw = str(phone_val).strip()
    for prefix in THRESHOLDS["indian_phone_prefixes"]:
        if raw.startswith(prefix):
            return True
    digits = re.sub(r"[^\d]", "", raw)
    if len(digits) == 10 and digits[0] in THRESHOLDS["indian_phone_10digit_start"]:
        return True
    if len(digits) == 12 and digits.startswith("91") and digits[2] in THRESHOLDS["indian_phone_10digit_start"]:
        return True
    return False


# -----------------------------------------------------------------------------
# MLID NORMALIZATION
# Strips whitespace, uppercases, removes common noise characters.
# -----------------------------------------------------------------------------
def normalize_mlid(mlid_val) -> str:
    """Normalize MLID to uppercase stripped string."""
    if pd.isna(mlid_val) or str(mlid_val).strip() == "":
        return ""
    return str(mlid_val).strip().upper()


# -----------------------------------------------------------------------------
# TIMESTAMP PARSING
# Tries multiple common formats. Returns pd.NaT on failure.
# -----------------------------------------------------------------------------
TIMESTAMP_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%d/%m/%Y %H:%M:%S",
    "%d-%m-%Y %H:%M:%S",
    "%m/%d/%Y %H:%M:%S",
    "%Y-%m-%d",
    "%d/%m/%Y",
]


def parse_timestamp(val) -> pd.Timestamp:
    """
    Try to parse a timestamp value using multiple formats.
    Returns pd.NaT if parsing fails.
    """
    if pd.isna(val) or str(val).strip() in ("", "nan", "None", "NaT"):
        return pd.NaT
    val_str = str(val).strip()
    try:
        return pd.to_datetime(val_str, dayfirst=True)
    except Exception:
        pass
    for fmt in TIMESTAMP_FORMATS:
        try:
            return pd.to_datetime(val_str, format=fmt)
        except Exception:
            continue
    return pd.NaT


def parse_timestamp_column(series: pd.Series) -> pd.Series:
    """Apply parse_timestamp to an entire column."""
    return series.apply(parse_timestamp)


# -----------------------------------------------------------------------------
# BOOLEAN NORMALIZATION
# Handles True/False/Yes/No/1/0/"true"/"false" etc.
# -----------------------------------------------------------------------------
TRUTHY = {"true", "yes", "1", "y", "sent", "done", "replied"}
FALSY  = {"false", "no", "0", "n", "", "nan", "none"}


def normalize_bool(val) -> bool | None:
    """
    Normalize a value to True/False/None.
    Returns None if the value is ambiguous or missing.
    """
    if pd.isna(val):
        return None
    s = str(val).strip().lower()
    if s in TRUTHY:
        return True
    if s in FALSY:
        return False
    return None


def normalize_bool_column(series: pd.Series) -> pd.Series:
    """Apply normalize_bool to an entire column."""
    return series.apply(normalize_bool)


# -----------------------------------------------------------------------------
# STATUS NORMALIZATION
# Lowercases and strips status strings for consistent comparison.
# -----------------------------------------------------------------------------
def normalize_status(val) -> str:
    """Lowercase and strip a status string. Returns '' for null."""
    if pd.isna(val) or str(val).strip() == "":
        return ""
    return str(val).strip().lower()


def normalize_status_column(series: pd.Series) -> pd.Series:
    """Apply normalize_status to an entire column."""
    return series.apply(normalize_status)


# -----------------------------------------------------------------------------
# APPLY NORMALIZATIONS TO A DATAFRAME
# Given a dataframe and its column map, apply standard normalizations
# to known phone, mlid, timestamp, boolean, and status columns.
# -----------------------------------------------------------------------------
PHONE_INTERNAL_NAMES   = {"phone", "from_phone", "sender_phone", "org_phone"}
MLID_INTERNAL_NAMES    = {"mlid", "external_customer_id"}
TIMESTAMP_INTERNAL_NAMES = {
    "born_date", "sent_at", "replied_at", "moved_to_arrowhead_at",
    "triggered_at", "moved_to_periskope_at", "completed_at",
    "callback_received_at", "periskope_sent_at", "arrowhead_triggered_at",
    "logged_at", "last_message_at", "next_followup_due_at", "replied_at",
    "scheduled_datetime", "reminder_datetime", "reminder_at_iso",
    "event_timestamp", "timestamp", "updated_at",
    # NOTE: call_duration is intentionally excluded — it's seconds (numeric), not a timestamp
}
BOOL_INTERNAL_NAMES = {
    "replied", "arrowhead", "error", "moved_to_arrowhead",
    "moved_to_periskope", "instant_alert_sent", "reminder_alert_sent",
}
STATUS_INTERNAL_NAMES = {
    "status", "call_status", "periskope_status", "arrowhead_status",
    "current_action", "next_action", "touch_stage", "last_outcome",
    "alert_type", "source_channel", "assigned_channel",
}


def normalize_dataframe(df: pd.DataFrame, col_map: dict) -> pd.DataFrame:
    """
    Given a dataframe with renamed internal columns, apply normalizations.
    col_map: the internal-name -> sheet-column-name mapping (from config).
    Only processes columns that actually exist in the dataframe.
    """
    df = df.copy()
    internal_cols = set(df.columns)

    for internal_name in internal_cols:
        if internal_name in PHONE_INTERNAL_NAMES:
            df[f"{internal_name}_norm"] = df[internal_name].apply(normalize_phone)
        if internal_name in MLID_INTERNAL_NAMES:
            df[f"{internal_name}_norm"] = df[internal_name].apply(normalize_mlid)
        if internal_name in TIMESTAMP_INTERNAL_NAMES:
            df[internal_name] = parse_timestamp_column(df[internal_name])
        if internal_name in BOOL_INTERNAL_NAMES:
            df[internal_name] = normalize_bool_column(df[internal_name])
        if internal_name in STATUS_INTERNAL_NAMES:
            df[internal_name] = normalize_status_column(df[internal_name])

    return df
