# =============================================================================
# data_loader.py — Loads each Google Sheet into a pandas DataFrame
# Handles missing sheets, disabled sheets, and column renaming.
# Uses parallel loading for speed.
# =============================================================================

import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import (
    SHEETS, COLUMN_MAPS,
    USE_SERVICE_ACCOUNT, SERVICE_ACCOUNT_FILE,
    USE_PUBLIC_CSV, THRESHOLDS,
)
from normalizer import normalize_dataframe

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# -----------------------------------------------------------------------------
# GOOGLE SHEETS CLIENT (cached so we don't re-auth on every refresh)
# -----------------------------------------------------------------------------
@st.cache_resource
def get_gspread_client():
    """Authenticate using Streamlit Secrets (deploy) or local JSON file (local)."""
    try:
        # Streamlit Cloud — secrets mein credentials hain
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    except (KeyError, FileNotFoundError):
        # Local — JSON file se
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return gspread.authorize(creds)


# -----------------------------------------------------------------------------
# LOAD ONE SHEET
# Returns (DataFrame or None, status_message string)
# -----------------------------------------------------------------------------
def load_sheet(sheet_key: str) -> tuple[pd.DataFrame | None, str]:
    """
    Load a single sheet by its config key.
    Returns (df, message). df is None if loading failed or sheet is disabled.
    """
    cfg = SHEETS.get(sheet_key)
    if cfg is None:
        return None, f"⚠️ '{sheet_key}' not found in config."

    if not cfg.get("enabled", False):
        return None, f"ℹ️ '{sheet_key}' is disabled in config."

    col_map = COLUMN_MAPS.get(sheet_key, {})

    # --- Option 1: Public CSV ---
    if USE_PUBLIC_CSV:
        url = cfg.get("public_csv_url", "")
        if not url:
            return None, f"⚠️ '{sheet_key}': public_csv_url is empty."
        try:
            df = pd.read_csv(url)
            df = _rename_and_normalize(df, col_map, sheet_key)
            return df, f"✅ '{sheet_key}' loaded via CSV ({len(df)} rows)"
        except Exception as e:
            return None, f"❌ '{sheet_key}' CSV load failed: {e}"

    # --- Option 2: Service Account ---
    if USE_SERVICE_ACCOUNT:
        try:
            client = get_gspread_client()
            spreadsheet = client.open_by_key(cfg["spreadsheet_id"])
            worksheet = spreadsheet.worksheet(cfg["tab_name"])
            # Use get_all_values to handle duplicate headers gracefully
            all_values = worksheet.get_all_values()
            if not all_values or len(all_values) < 2:
                return pd.DataFrame(), f"⚠️ '{sheet_key}' loaded but is empty."
            headers = all_values[0]
            # Deduplicate headers by appending _2, _3 etc.
            seen = {}
            clean_headers = []
            for h in headers:
                if h in seen:
                    seen[h] += 1
                    clean_headers.append(f"{h}_{seen[h]}")
                else:
                    seen[h] = 1
                    clean_headers.append(h)
            rows = all_values[1:]
            df = pd.DataFrame(rows, columns=clean_headers)
            df = df.replace("", pd.NA)
            df = _rename_and_normalize(df, col_map, sheet_key)
            return df, f"✅ '{sheet_key}' loaded ({len(df)} rows)"
        except gspread.exceptions.SpreadsheetNotFound:
            return None, f"❌ '{sheet_key}': Spreadsheet not found. Check spreadsheet_id in config."
        except gspread.exceptions.WorksheetNotFound:
            return None, f"❌ '{sheet_key}': Tab '{cfg['tab_name']}' not found. Check tab_name in config."
        except FileNotFoundError:
            return None, f"❌ Service account file not found at: {SERVICE_ACCOUNT_FILE}"
        except Exception as e:
            return None, f"❌ '{sheet_key}' failed to load: {e}"

    return None, f"❌ '{sheet_key}': No load method configured (set USE_SERVICE_ACCOUNT or USE_PUBLIC_CSV)."


def _rename_and_normalize(df: pd.DataFrame, col_map: dict, sheet_key: str) -> pd.DataFrame:
    """
    Rename sheet columns to internal names using col_map.
    Only renames columns that exist. Adds normalized variants.
    """
    # Build reverse map: sheet_column_name -> internal_name
    rename_map = {v: k for k, v in col_map.items() if v in df.columns}
    df = df.rename(columns=rename_map)
    # Drop fully empty rows
    df = df.dropna(how="all")
    # Apply normalizations
    df = normalize_dataframe(df, col_map)
    return df


# -----------------------------------------------------------------------------
# LOAD ALL SHEETS
# Returns dict of {sheet_key: DataFrame or None} and a status dict.
# -----------------------------------------------------------------------------
@st.cache_data(ttl=THRESHOLDS["cache_ttl_seconds"])
def load_all_sheets() -> tuple[dict, dict]:
    """
    Load all enabled sheets in parallel for speed.
    Returns:
    - data: dict of {sheet_key: DataFrame or None}
    - statuses: dict of {sheet_key: status_message}
    """
    enabled_keys = [k for k, v in SHEETS.items() if v.get("enabled", False)]
    data = {}
    statuses = {}

    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_key = {executor.submit(load_sheet, key): key for key in enabled_keys}
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                df, msg = future.result()
                data[key] = df
                statuses[key] = msg
            except Exception as e:
                data[key] = None
                statuses[key] = f"❌ '{key}' unexpected error: {e}"

    # Mark disabled sheets
    for key in SHEETS:
        if key not in data:
            data[key] = None
            statuses[key] = f"ℹ️ '{key}' is disabled in config."

    return data, statuses


# -----------------------------------------------------------------------------
# SAFE COLUMN GETTER
# Returns a column from a df if it exists, else a Series of default values.
# -----------------------------------------------------------------------------
def safe_col(df: pd.DataFrame, col: str, default=None) -> pd.Series:
    """Return df[col] if it exists, else a Series filled with default."""
    if df is not None and col in df.columns:
        return df[col]
    return pd.Series([default] * (len(df) if df is not None else 0))
