# =============================================================================
# merger.py — Builds the unified lead-centric merged DataFrame
# Conservative join strategy: Assigned Leads is the spine.
# All other sheets are left-joined. No over-merging.
# =============================================================================

import pandas as pd
from data_loader import safe_col


def build_unified_leads(data: dict) -> pd.DataFrame:
    """
    Merge all available sheets into one lead-centric DataFrame.
    'data' is the dict returned by load_all_sheets().
    Returns a DataFrame. Each row = one lead.
    """
    spine = data.get("assigned_leads")

    # If assigned_leads is missing, try to build spine from second_third_touch
    if spine is None or spine.empty:
        spine = _build_spine_from_touch(data)

    if spine is None or spine.empty:
        return pd.DataFrame()

    df = spine.copy()

    # Ensure join keys exist
    if "phone_norm" not in df.columns:
        df["phone_norm"] = ""
    if "mlid_norm" not in df.columns:
        df["mlid_norm"] = ""

    # --- Join: Periskope First Touch (on phone_norm) ---
    df = _left_join(
        df, data.get("periskope_first_touch"),
        on="phone_norm",
        prefix="wa_",
        exclude_cols={"phone", "phone_norm", "name"},
    )

    # --- Join: Arrowhead Kalbhoj calling sheet (primary calling data) ---
    # Prefer arrowhead_kalbhoj (has full call data). Fall back to arrowhead if missing.
    ah_df = data.get("arrowhead_kalbhoj")
    if ah_df is None or ah_df.empty:
        ah_df = data.get("arrowhead")
    df = _left_join(
        df, ah_df,
        on="phone_norm",
        prefix="ah_",
        exclude_cols={"phone", "phone_norm", "customer_name"},
    )

    # --- Join: Arrowhead Anandita (WA follow-up sheet) as secondary ---
    df = _left_join(
        df, data.get("arrowhead"),
        on="phone_norm",
        prefix="ah_wa_",
        exclude_cols={"phone", "phone_norm", "name"},
    )

    # --- Join: Second & Third Touch (on mlid_norm first, fallback phone_norm) ---
    touch_df = data.get("second_third_touch")
    if touch_df is not None and not touch_df.empty:
        if "mlid_norm" in touch_df.columns and df["mlid_norm"].ne("").any():
            df = _left_join(
                df, touch_df,
                on="mlid_norm",
                prefix="tt_",
                exclude_cols={"mlid", "mlid_norm", "phone", "phone_norm", "name"},
            )
        else:
            df = _left_join(
                df, touch_df,
                on="phone_norm",
                prefix="tt_",
                exclude_cols={"mlid", "mlid_norm", "phone", "phone_norm", "name"},
            )

    # --- Join: Follow-up Tracker (on phone_norm) ---
    df = _left_join(
        df, data.get("followup_tracker"),
        on="phone_norm",
        prefix="fu_",
        exclude_cols={"phone", "phone_norm", "name", "project"},
    )

    # --- Join: Alert Log (on phone_norm) ---
    df = _left_join(
        df, data.get("alert_log"),
        on="phone_norm",
        prefix="al_",
        exclude_cols={"phone", "phone_norm", "lead_name"},
    )

    return df


def _left_join(
    base: pd.DataFrame,
    right: pd.DataFrame | None,
    on: str,
    prefix: str,
    exclude_cols: set,
) -> pd.DataFrame:
    """
    Left-join base with right on the given key column.
    Prefixes right-side columns with prefix to avoid collisions.
    Skips columns in exclude_cols from the right side.
    Returns base unchanged if right is None/empty or key missing.
    """
    if right is None or right.empty:
        return base
    if on not in base.columns or on not in right.columns:
        return base

    # Keep only one row per join key from right (take first match)
    right_deduped = right.drop_duplicates(subset=[on], keep="first").copy()

    # Select and rename right columns
    right_cols = [on] + [
        c for c in right_deduped.columns
        if c != on and c not in exclude_cols
    ]
    right_deduped = right_deduped[right_cols].copy()
    rename_map = {c: f"{prefix}{c}" for c in right_cols if c != on}
    right_deduped = right_deduped.rename(columns=rename_map)

    merged = base.merge(right_deduped, on=on, how="left")
    return merged


def _build_spine_from_touch(data: dict) -> pd.DataFrame | None:
    """Fallback: use second_third_touch as spine if assigned_leads is missing."""
    touch = data.get("second_third_touch")
    if touch is not None and not touch.empty:
        return touch.copy()
    return None


# -----------------------------------------------------------------------------
# ORPHAN RECORDS
# Rows in non-spine sheets that didn't match any lead in the spine.
# Useful for the Exceptions view.
# -----------------------------------------------------------------------------
def get_orphan_records(data: dict, unified: pd.DataFrame) -> dict:
    """
    Returns dict of {sheet_key: DataFrame} for rows that didn't join
    to any lead in the unified model.
    """
    orphans = {}
    matched_phones = set(unified.get("phone_norm", pd.Series(dtype=str)).dropna())

    for key in ["periskope_first_touch", "arrowhead", "followup_tracker", "alert_log"]:
        df = data.get(key)
        if df is not None and not df.empty and "phone_norm" in df.columns:
            unmatched = df[~df["phone_norm"].isin(matched_phones)]
            if not unmatched.empty:
                orphans[key] = unmatched

    return orphans
