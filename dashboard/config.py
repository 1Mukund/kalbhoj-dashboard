# =============================================================================
# config.py — CENTRAL CONFIGURATION FILE
# Edit this file to connect your Google Sheets and adjust business logic.
# =============================================================================

# -----------------------------------------------------------------------------
# GOOGLE SHEETS AUTHENTICATION
# Option 1: Service Account JSON (recommended for multi-sheet access)
# Place your service_account.json inside the credentials/ folder.
# Option 2: Set USE_PUBLIC_CSV = True and fill PUBLIC_CSV_URLS below.
# -----------------------------------------------------------------------------
import os

USE_SERVICE_ACCOUNT = True
# Path is relative to app.py which lives inside dashboard/
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "credentials", "service_account.json")

USE_PUBLIC_CSV = False  # Set True if sheets are publicly shared as CSV

# -----------------------------------------------------------------------------
# SPREADSHEET IDs
# Find the ID in your Google Sheet URL:
# https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit
# Set ENABLED = False to disable a sheet without breaking the app.
# -----------------------------------------------------------------------------
SHEETS = {
    # Inncircles AI POOL Kalbhojaditya
    "assigned_leads": {
        "enabled": True,
        "spreadsheet_id": "17HQ6qjdPRUh9T3-yPGppz8BJle2aKj-a4JI0amF5WIA",
        "tab_name": "Sheet1",
        "public_csv_url": "",
    },
    # Periskope Automated First Touch
    "periskope_first_touch": {
        "enabled": True,
        "spreadsheet_id": "1peZ1_m4l8BILVGezYPUbAYALtI_y_OS4EhCJuvFrKkk",
        "tab_name": "Sheet1",
        "public_csv_url": "",
    },
    # Arrowhead To Anandita (main arrowhead sheet)
    "arrowhead": {
        "enabled": True,
        "spreadsheet_id": "1fYFZTt7S9yv_Q_IjDLpDa8LyolTJT-yk9rEV4edOawE",
        "tab_name": "Sheet1",
        "public_csv_url": "",
    },
    # Arrowhead Automation Sheet Kalbhoj — data is in Sheet3
    "arrowhead_kalbhoj": {
        "enabled": True,
        "spreadsheet_id": "1kLJbzc2eEJ5jF5Y1RSJYiX-WzSWFq29V31aaEyVbLbI",
        "tab_name": "Sheet3",
        "public_csv_url": "",
    },
    # Second & Third Touch Control Sheet
    "second_third_touch": {
        "enabled": True,
        "spreadsheet_id": "1aqPSKhkTFW_1uILRZASmXtkYl5DTxkJASwXlpQUvwUg",
        "tab_name": "Sheet1",
        "public_csv_url": "",
    },
    # Anandita Following Up (follow-up tracker)
    "followup_tracker": {
        "enabled": True,
        "spreadsheet_id": "1rDx3G-RJhclV2DXyGLP__mLoICQy6WYZo-YVjx8LKsA",
        "tab_name": "Followup Tracker",   # actual tab name
        "public_csv_url": "",
    },
    # Peribot Qualification — Sheet2 has qualification data
    "peribot_qualification": {
        "enabled": True,
        "spreadsheet_id": "1fevCTcYnhet8W-46qdjLXNqSLQ5_PFFGJWzQjpiyKxM",
        "tab_name": "Sheet2",
        "public_csv_url": "",
    },
    # Peribot Raw Log — Sheet1 of same spreadsheet
    "periskope_raw_log": {
        "enabled": True,
        "spreadsheet_id": "1fevCTcYnhet8W-46qdjLXNqSLQ5_PFFGJWzQjpiyKxM",
        "tab_name": "Sheet1",
        "public_csv_url": "",
    },
    # Site Visit & Calls Schedules Periskope
    "alert_log": {
        "enabled": True,
        "spreadsheet_id": "19vYqI4vb4ybwwiKME16FKPBF_-0I5xCAAkXS1UXYAWo",
        "tab_name": "Sheet1",
        "public_csv_url": "",
    },
    # Kalbhojaditya Daily Report
    "kalbhoj_daily_report": {
        "enabled": True,
        "spreadsheet_id": "1v1vtaAUeHDBsv7vtvPa287tc3_pUJ9C-V1XGfmS5o1E",
        "tab_name": "Daily Report",
        "public_csv_url": "",
    },
    # Kalbhojaditya Cumulative Report
    "kalbhoj_cumulative_report": {
        "enabled": True,
        "spreadsheet_id": "1v1vtaAUeHDBsv7vtvPa287tc3_pUJ9C-V1XGfmS5o1E",
        "tab_name": "Cumulative Report",
        "public_csv_url": "",
    },
    # Periskope raw log — disabled until needed
    "periskope_raw_log": {
        "enabled": False,
        "spreadsheet_id": "",
        "tab_name": "Sheet1",
        "public_csv_url": "",
    },
}

# -----------------------------------------------------------------------------
# COLUMN MAPPINGS
# If your sheet uses different column names, update the right-hand side.
# Left side = internal name used in the dashboard code (do NOT change).
# Right side = actual column header in your Google Sheet.
# -----------------------------------------------------------------------------
COLUMN_MAPS = {

    # --- Assigned Leads / InCircles Pool ---
    "assigned_leads": {
        "mlid":             "MLID",
        "phone":            "Phone Number",
        "name":             "Name",
        "project":          "Project",
        "assigned_channel": "Executive",   # "Executive" is the channel/assignment column
        "born_date":        "Born Date",
    },

    # --- Periskope Automated First Touch ---
    "periskope_first_touch": {
        "phone":                  "Phone",
        "status":                 "Status",
        "sent_at":                "Sent At",
        "sender_used":            "Sender Used",
        "replied":                "Replied",
        "replied_at":             "Replied At",
        "arrowhead":              "Arrowhead",
        "error":                  "Error",
        "moved_to_arrowhead":     "Moved To Arrowhead",
        "moved_to_arrowhead_at":  "Moved To Arrowhead At",
        "name":                   "Name",
    },

    # --- Arrowhead To Anandita (WhatsApp follow-up sheet, not calling) ---
    "arrowhead": {
        "phone":        "Phone",
        "name":         "Name",
        "call_status":  "Call Status",       # reusing call_status field
        "status":       "Sent Status",
        "sent_at":      "Sent At",
        "error":        "Error",
    },

    # --- Arrowhead Automation Sheet Kalbhoj (actual calling data, Sheet3) ---
    "arrowhead_kalbhoj": {
        "phone":                  "Phone",
        "customer_name":          "Customer Name",
        "status":                 "Status",
        "triggered_at":           "Triggered At",
        "external_customer_id":   "External Customer ID",
        "external_schedule_id":   "External Schedule ID",
        "response":               "Response",
        "error":                  "Error",
        "moved_to_periskope":     "Moved To Periskope",
        "moved_to_periskope_at":  "Moved To Periskope At",
        "call_status":            "Call Status",
        "call_duration":          "Call Duration",
        "call_id":                "Call ID",
        "completed_at":           "Completed At",
        "callback_payload":       "Callback Payload",
        "callback_received_at":   "Callback Received At",
    },

    # --- Second & Third Touch Control ---
    "second_third_touch": {
        "mlid":                   "MLID",
        "phone":                  "Phone",
        "name":                   "Name",
        "source_channel":         "Source Channel",
        "touch_stage":            "Touch Stage",
        "current_action":         "Current Action",
        "periskope_status":       "Periskope Status",
        "periskope_sent_at":      "Periskope Sent At",
        "arrowhead_status":       "Arrowhead Status",
        "arrowhead_triggered_at": "Arrowhead Triggered At",
        "call_status":            "Call Status",
        "call_duration":          "Call Duration",
        "last_outcome":           "Last Outcome",
        "next_action":            "Next Action",
        "moved_to_periskope":     "Moved To Periskope",
        "moved_to_arrowhead":     "Moved To Arrowhead",
        "logged_at":              "Logged At",
        "remarks":                "Remarks",
    },

    # --- Anandita Following Up (Follow-up Tracker) ---
    "followup_tracker": {
        "phone":                "Phone",
        "name":                 "Name",
        "project":              "Project",
        "followup_count":       "Followup Count",
        "last_message_at":      "Last Message At",
        "replied":              "Replied",
        "replied_at":           "Replied At",
        "next_followup_due_at": "Next Followup Due At",
        "status":               "Status",
        "remarks":              "Remarks",
        "last_sender_used":     "Last Sender Used",
    },

    # --- Peribot Qualification (Sheet2) ---
    "peribot_qualification": {
        "phone":              "sender_phone",
        "project":            "primary_project",
        "buying_intent":      "buying_intent",
        "buying_timeline":    "buying_timeline",
        "budget":             "budget",
        "size_preference":    "size_preference",
        "preferred_area":     "preferred_area",
        "last_user_message":  "last_user_message",
        "message_count":      "message_count",
    },

    # --- Kalbhojaditya Daily / Cumulative Report ---
    # Note: sheet has duplicate "LeadId" columns — loaded by position
    "kalbhoj_daily_report": {
        "date":                  "Date",
        "assigned_leads":        "Assigned No. Of Leads",
        "site_visit_booked":     "Site Visit Booked",
        "site_visit_booked_ids": "LeadId",
        "site_visit_done":       "Site Visit Done",
        "site_visit_done_ids":   "LeadId_2",
        "flat_blocked":          "Flat Blocked",
        "flat_blocked_ids":      "LeadId_3",
        "sale_closure":          "Sale Closure",
        "sale_closure_ids":      "LeadId_4",
    },
    "kalbhoj_cumulative_report": {
        "date":                  "Date",
        "assigned_leads":        "Assigned No. Of Leads",
        "site_visit_booked":     "Site Visit Booked",
        "site_visit_booked_ids": "Lead Id",
        "site_visit_done":       "Site Visit Done",
        "site_visit_done_ids":   "Lead Id_2",
        "flat_blocked":          "Flat Blocked",
        "flat_blocked_ids":      "Lead Id_3",
        "sale_closure":          "Sale Closure",
        "sale_closure_ids":      "LeadId_4",
    },

    # --- Periskope Raw Log (Sheet1 of Peribot sheet) ---
    "periskope_raw_log": {
        "event_timestamp": "event_timestamp",
        "message_id":      "message_id",
        "org_id":          "org_id",
        "ack":             "ack",
        "body":            "body",
        "from_phone":      "from",
        "chat_id":         "chat_id",
        "timestamp":       "timestamp",
        "org_phone":       "org_phone",
        "performed_by":    "performed_by",
        "sender_phone":    "sender_phone",
        "updated_at":      "updated_at",
    },

    # --- Site Visit & Calls Schedules Periskope ---
    # NOTE: This sheet has Periskope webhook structure (timestamp, user_phone, intent etc.)
    # Mapping to closest available fields
    "alert_log": {
        "phone":        "user_phone",
        "lead_name":    "user_name",
        "alert_type":   "intent",
        "status":       "status",
        "logged_at":    "timestamp",
        "chat_id":      "chat_id",
    },
}

# -----------------------------------------------------------------------------
# BUSINESS LOGIC THRESHOLDS
# Adjust these to match your operational definitions.
# -----------------------------------------------------------------------------
THRESHOLDS = {
    # Hours after which a lead is considered "stuck" if stage hasn't changed
    "stuck_lead_hours": 48,

    # Statuses in Arrowhead that count as "connected"
    "arrowhead_connected_statuses": ["connected"],

    # Statuses in Arrowhead that count as "not connected"
    "arrowhead_not_connected_statuses": ["not_connected", "no_answer", "busy", "failed", "unanswered"],

    # Statuses in Arrowhead that count as "busy"
    "arrowhead_busy_statuses": ["busy"],

    # Statuses in Arrowhead that count as "failed/error"
    "arrowhead_failed_statuses": ["failed", "error"],

    # Alert types that count as "site visit scheduled"
    "site_visit_alert_types": ["site_visit_request", "virtual_visit_request", "meeting_request"],

    # Alert types that count as "phone call scheduled"
    "phone_call_alert_types": ["call_request", "callback_request", "scheduling_request"],

    # Touch stages that indicate "third touch sent"
    "third_touch_stages": ["third touch", "touch 3", "3rd touch"],

    # WhatsApp statuses that mean "sent"
    "periskope_sent_statuses": ["sent", "delivered", "read"],

    # WhatsApp statuses that mean "replied"
    "periskope_replied_values": ["true", "yes", "1", True, 1],

    # Cache TTL in seconds (15 minutes)
    "cache_ttl_seconds": 900,

    # Indian phone number prefix patterns (used for Indian vs International split)
    "indian_phone_prefixes": ["91", "+91"],
    "indian_phone_10digit_start": ["6", "7", "8", "9"],
}

# -----------------------------------------------------------------------------
# APP DISPLAY SETTINGS
# -----------------------------------------------------------------------------
APP_TITLE = "Lead Operations Dashboard"
APP_ICON = "📊"
TIMEZONE = "Asia/Kolkata"  # for displaying timestamps

# -----------------------------------------------------------------------------
# AUTH — No password required, just username-based role selection
# -----------------------------------------------------------------------------
USERS = {
    "admin_kaalbhoj": {"role": "admin"},
    "user_kb":        {"role": "user"},
}
