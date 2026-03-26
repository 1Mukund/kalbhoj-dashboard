# Lead Operations Dashboard — Run Guide

## Folder Structure

```
dashboard/
├── app.py              ← Main app (run this)
├── config.py           ← ALL sheet IDs, tab names, column mappings, thresholds
├── data_loader.py      ← Loads Google Sheets
├── normalizer.py       ← Phone, MLID, timestamp, boolean normalization
├── merger.py           ← Builds unified lead model
├── metrics.py          ← All KPI calculations
├── views.py            ← All UI sections and charts
├── requirements.txt
└── credentials/
    └── service_account.json   ← YOU place this here (see step 3)
```

---

## Step 1 — Install dependencies

```bash
pip install -r requirements.txt
```

---

## Step 2 — Set up Google Cloud Service Account

1. Go to https://console.cloud.google.com
2. Create a new project (or use existing)
3. Enable these two APIs:
   - Google Sheets API
   - Google Drive API
4. Go to IAM & Admin → Service Accounts → Create Service Account
5. Give it any name (e.g. "dashboard-reader")
6. Click the service account → Keys → Add Key → JSON
7. Download the JSON file
8. Rename it to `service_account.json`
9. Place it inside the `credentials/` folder

---

## Step 3 — Share your Google Sheets with the service account

1. Open the downloaded JSON file
2. Find the `client_email` field (looks like: `dashboard-reader@your-project.iam.gserviceaccount.com`)
3. Open each Google Sheet you want to connect
4. Click Share → paste that email → set role to Viewer → Share
5. Repeat for every sheet

---

## Step 4 — Edit config.py

Open `config.py` and fill in:

```python
SHEETS = {
    "assigned_leads": {
        "enabled": True,
        "spreadsheet_id": "YOUR_ACTUAL_SPREADSHEET_ID_HERE",
        "tab_name": "Sheet1",   # exact tab name as shown in Google Sheets
    },
    ...
}
```

To find the spreadsheet ID:
- Open the sheet in browser
- URL looks like: `https://docs.google.com/spreadsheets/d/THIS_IS_THE_ID/edit`
- Copy the part between `/d/` and `/edit`

Also update `COLUMN_MAPS` if your column headers differ from the defaults.

---

## Step 5 — Run the dashboard

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## If a sheet is not ready yet

In `config.py`, set `"enabled": False` for that sheet:

```python
"periskope_raw_log": {
    "enabled": False,
    ...
}
```

The app will show a notice but will not crash.

---

## Deployment options

**Option A — Streamlit Community Cloud (free)**
1. Push this folder to a GitHub repo
2. Go to https://share.streamlit.io
3. Connect your repo, set main file as `app.py`
4. Add your service_account.json content as a Secret (Streamlit Secrets)

**Option B — Run on any server / VPS**
```bash
pip install -r requirements.txt
streamlit run app.py --server.port 8501 --server.headless true
```

**Option C — Docker**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.headless=true"]
```

---

## Assumptions

1. `assigned_leads` sheet is the primary spine for the unified lead model.
   If it's missing, the app falls back to `second_third_touch` as the spine.

2. Phone number is the primary join key across sheets.
   MLID is used as a secondary join key where available.

3. "Booked" = lead has an entry in the alert log with a site visit or call type.
   Edit `THRESHOLDS["site_visit_alert_types"]` and `phone_call_alert_types` in config.py.

4. "Done" = Arrowhead call status is in connected statuses, OR touch sheet last_outcome contains "done"/"completed".
   Edit `THRESHOLDS["arrowhead_connected_statuses"]` in config.py.

5. "Stuck" = lead's last activity timestamp is older than 48 hours and not done/booked.
   Edit `THRESHOLDS["stuck_lead_hours"]` in config.py.

6. "Overdue follow-up" = next_followup_due_at is in the past and replied is not True.

7. Indian phone = starts with +91/91 or is a 10-digit number starting with 6-9.

8. All timestamps are displayed in IST. Edit `TIMEZONE` in config.py to change.

9. Data is cached for 15 minutes. Click "Refresh Data" in the sidebar to force reload.

10. This dashboard is strictly READ-ONLY. No sheet is ever written to.
