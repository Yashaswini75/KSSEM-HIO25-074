# apply.py
import pandas as pd
import os
import time
import json
from pathlib import Path
from datetime import datetime, timedelta

# -------------------------
# Paths
# -------------------------
DATA_DIR = Path("data")
APPLICATIONS_CSV = DATA_DIR / "applications.csv"
APPOINTMENTS_CSV = DATA_DIR / "appointments.csv"

# -------------------------
# Utility: Safe CSV Read
# -------------------------
def safe_read_csv(path, columns):
    """Safely read or create CSV with given columns."""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        df = pd.DataFrame(columns=columns)
        df.to_csv(path, index=False)
        return df
    try:
        df = pd.read_csv(path)
        if df.empty:
            df = pd.DataFrame(columns=columns)
        return df
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=columns)
        df.to_csv(path, index=False)
        return df

# -------------------------
# Add New Loan Application
# -------------------------
def append_application(user_email, bank_id, filled_fields):
    """
    Add new loan application to applications.csv and return app_id.
    Supports both old (user_id as int) and new (user_email as str) data.
    """
    cols = ["app_id", "user_email", "bank_id", "status", "filled_form_fields_json", "timestamp"]
    df = safe_read_csv(APPLICATIONS_CSV, cols)

    # determine next id
    if len(df) == 0:
        app_id = 1
    else:
        try:
            app_id = int(df['app_id'].max()) + 1
        except Exception:
            app_id = len(df) + 1

    new_row = {
        "app_id": app_id,
        "user_email": str(user_email),
        "bank_id": int(bank_id),
        "status": "Pending",
        "filled_form_fields_json": json.dumps(filled_fields, ensure_ascii=False),
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(APPLICATIONS_CSV, index=False)
    return app_id

# -------------------------
# List Applications for User
# -------------------------
def list_user_applications(user_email):
    """Return all loan applications for the given user email."""
    if not APPLICATIONS_CSV.exists():
        return pd.DataFrame()

    df = pd.read_csv(APPLICATIONS_CSV)

    if "user_email" in df.columns:
        user_apps = df[df["user_email"] == user_email]
    elif "user_id" in df.columns:
        # fallback for older data formats
        user_apps = df[df["user_id"].astype(str) == str(user_email)]
    else:
        user_apps = pd.DataFrame()

    return user_apps.to_dict("records")

# -------------------------
# Schedule Appointment
# -------------------------
def schedule_appointment(user_email, app_id, bank_id, days_from_now=3):
    """Create a simple appointment record scheduled days_from_now in the future."""
    cols = ["appointment_id", "app_id", "user_email", "bank_id", "scheduled_time", "created_at", "status"]
    df = safe_read_csv(APPOINTMENTS_CSV, cols)

    if len(df) == 0:
        appointment_id = 1
    else:
        try:
            appointment_id = int(df['appointment_id'].max()) + 1
        except Exception:
            appointment_id = len(df) + 1

    scheduled = (datetime.utcnow() + timedelta(days=days_from_now)).strftime("%Y-%m-%d %H:%M:%S")
    new_row = {
        "appointment_id": appointment_id,
        "app_id": int(app_id),
        "user_email": str(user_email),
        "bank_id": int(bank_id),
        "scheduled_time": scheduled,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Scheduled"
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(APPOINTMENTS_CSV, index=False)
    return appointment_id, scheduled


def schedule_appointment_custom(user_email, app_id, bank_id, scheduled_time_str):
    """Schedule an appointment at a specific datetime string (ISO or '%Y-%m-%d %H:%M')."""
    cols = ["appointment_id", "app_id", "user_email", "bank_id", "scheduled_time", "created_at", "status"]
    df = safe_read_csv(APPOINTMENTS_CSV, cols)

    if len(df) == 0:
        appointment_id = 1
    else:
        try:
            appointment_id = int(df['appointment_id'].max()) + 1
        except Exception:
            appointment_id = len(df) + 1

    # Normalize scheduled time string
    try:
        # Accept either ISO or common format
        scheduled = datetime.fromisoformat(scheduled_time_str).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        try:
            scheduled = datetime.strptime(scheduled_time_str, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            # Fallback: use raw string
            scheduled = scheduled_time_str

    new_row = {
        "appointment_id": appointment_id,
        "app_id": int(app_id),
        "user_email": str(user_email),
        "bank_id": int(bank_id),
        "scheduled_time": scheduled,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Scheduled"
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(APPOINTMENTS_CSV, index=False)
    return appointment_id, scheduled
