# app.py

import streamlit as st
import pandas as pd
import subprocess
import time
from datetime import datetime

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="KDE SMS Notice System",
    layout="wide"
)

st.title("📩 KDE Connect SMS System")

st.markdown("""
This system sends SMS using your Android phone through KDE Connect.
""")

# =========================
# GOOGLE SHEET
# =========================

GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1FwTi33gbgjNfoJpTcDzImh87tooq4HHIG8QdYB6roRQ/edit?usp=sharing"

sheet_id = GOOGLE_SHEET_URL.split("/d/")[1].split("/")[0]

CSV_URL = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

# =========================
# LOAD DATA
# =========================

try:

    df = pd.read_csv(CSV_URL)

    st.success("Google Sheet Loaded Successfully")

except Exception as e:

    st.error(f"Error loading Google Sheet: {e}")
    st.stop()

# =========================
# SHOW DATA
# =========================

st.subheader("📋 Student Data")

st.dataframe(df)

# =========================
# REQUIRED COLUMNS
# =========================

required_columns = [
    "name",
    "phone",
    "course",
    "semester",
    "university"
]

missing = [c for c in required_columns if c not in df.columns]

if missing:
    st.error(f"Missing columns: {missing}")
    st.stop()

# =========================
# FILTERS
# =========================

st.subheader("🎯 Filters")

courses = ["All"] + sorted(df["course"].astype(str).unique().tolist())

semesters = ["All"] + sorted(df["semester"].astype(str).unique().tolist())

universities = ["All"] + sorted(df["university"].astype(str).unique().tolist())

col1, col2, col3 = st.columns(3)

with col1:
    selected_course = st.selectbox(
        "Select Course",
        courses
    )

with col2:
    selected_semester = st.selectbox(
        "Select Semester",
        semesters
    )

with col3:
    selected_university = st.selectbox(
        "Select University",
        universities
    )

filtered_df = df.copy()

if selected_course != "All":
    filtered_df = filtered_df[
        filtered_df["course"].astype(str) == selected_course
    ]

if selected_semester != "All":
    filtered_df = filtered_df[
        filtered_df["semester"].astype(str) == selected_semester
    ]

if selected_university != "All":
    filtered_df = filtered_df[
        filtered_df["university"].astype(str) == selected_university
    ]

st.info(f"Selected Students: {len(filtered_df)}")

# =========================
# MESSAGE TEMPLATE
# =========================

st.subheader("✉ SMS Template")

template = st.text_area(
    "Write Message",
    height=180,
    value="""Dear {name},

Important notice for {course} Semester {semester} students of {university}.

Please check college notice board.

- Office Administration"""
)

st.markdown("""
### Available Variables
- `{name}`
- `{course}`
- `{semester}`
- `{university}`
""")

# =========================
# PREVIEW
# =========================

if len(filtered_df) > 0:

    sample = filtered_df.iloc[0]

    preview = template.format(
        name=sample["name"],
        course=sample["course"],
        semester=sample["semester"],
        university=sample["university"]
    )

    st.subheader("👀 Preview")

    st.code(preview)

# =========================
# KDE CONNECT SMS FUNCTION
# =========================

def send_sms_kde(phone, message):

    try:

        command = [
            "kdeconnect-cli",
            "--send-sms",
            message,
            "--destination",
            str(phone)
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return True, "Sent"

        return False, result.stderr

    except Exception as e:

        return False, str(e)

# =========================
# SEND BUTTON
# =========================

if st.button("🚀 Send SMS"):

    if len(filtered_df) == 0:
        st.warning("No students selected")
        st.stop()

    progress = st.progress(0)

    status_box = st.empty()

    logs = []

    success_count = 0
    failed_count = 0

    total = len(filtered_df)

    for i, row in filtered_df.iterrows():

        try:

            personalized_message = template.format(
                name=row["name"],
                course=row["course"],
                semester=row["semester"],
                university=row["university"]
            )

            status_box.info(
                f"Sending to {row['name']} ({row['phone']})"
            )

            success, response = send_sms_kde(
                row["phone"],
                personalized_message
            )

            logs.append({
                "time": datetime.now(),
                "name": row["name"],
                "phone": row["phone"],
                "status": "Success" if success else "Failed",
                "response": response
            })

            if success:
                success_count += 1
            else:
                failed_count += 1

            progress.progress((len(logs)) / total)

            # Delay to avoid SIM block
            time.sleep(3)

        except Exception as e:

            failed_count += 1

            logs.append({
                "time": datetime.now(),
                "name": row["name"],
                "phone": row["phone"],
                "status": "Failed",
                "response": str(e)
            })

    # =========================
    # RESULTS
    # =========================

    st.success("SMS Sending Completed")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("✅ Success", success_count)

    with col2:
        st.metric("❌ Failed", failed_count)

    log_df = pd.DataFrame(logs)

    st.subheader("📄 Logs")

    st.dataframe(log_df)

    csv = log_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇ Download Logs",
        csv,
        "sms_logs.csv",
        "text/csv"
    )
