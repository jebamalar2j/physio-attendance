import smtplib
from email.mime.text import MIMEText
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from geopy.distance import geodesic
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval


# -------------------------
# CONFIG
# -------------------------
CLINIC_LAT = 10.7905
CLINIC_LON = 78.7047
MAX_DISTANCE_METERS = 50

# -------------------------
# DATABASE
# -------------------------
engine = create_engine("sqlite:///clinic.db")

# -------------------------
# CREATE TABLES
# -------------------------
with engine.begin() as conn:

    conn.exec_driver_sql("""
    CREATE TABLE IF NOT EXISTS patients (
    patient_id TEXT PRIMARY KEY,
    name TEXT,
    phone TEXT,
    email TEXT,
    sessions_total INTEGER,
    sessions_used INTEGER
)

    conn.exec_driver_sql("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT,
        timestamp TEXT,
        latitude REAL,
        longitude REAL
    )
    """)

# -------------------------
# SIDEBAR MENU
# =====================================================
# -------------------------
# SIDEBAR
# -------------------------

role = st.sidebar.radio(
    "Select Role",
    ["Patient", "Admin"]
)

# -------------------------
# PATIENT
# -------------------------

if role == "Patient":

    menu = "Patient Check-In"

# -------------------------
# ADMIN
# -------------------------

elif role == "Admin":

    password = st.sidebar.text_input(
        "Admin Password",
        type="password"
    )

    if password == "physio123":

        menu = st.sidebar.selectbox(
            "Menu",
            [
                "Admin Panel",
                "Attendance History"
            ]
        )

    else:

        st.warning("Enter correct admin password")
        st.stop()
# PATIENT CHECK-IN
# =====================================================
if menu == "Patient Check-In":

st.set_page_config(
    page_title="Sheela Physiocare",
    page_icon="images/logo.png",
    layout="centered"
)    

st.title("Physio Attendance System")

    patient_id = st.text_input("Enter Patient ID")

    location = streamlit_js_eval(
        js_expressions="""
        new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
                (pos) => resolve({
                    lat: pos.coords.latitude,
                    lon: pos.coords.longitude
                }),
                (err) => reject(err)
            );
        })
        """,
        key="get_location"
    )

    if st.button("Check In"):

        if not patient_id:
            st.error("Enter Patient ID")
            st.stop()

        if not location:
            st.error("Location access required")
            st.stop()

        user_lat = location["lat"]
        user_lon = location["lon"]

        distance = geodesic(
            (CLINIC_LAT, CLINIC_LON),
            (user_lat, user_lon)
        ).meters

        st.write(f"Distance from clinic: {distance:.2f} meters")

        if distance > MAX_DISTANCE_METERS:
            st.error("You are not inside clinic area")
            st.stop()

        patients_df = pd.read_sql(
            "SELECT * FROM patients",
            engine
        )

        patient = patients_df[
            patients_df["patient_id"] == patient_id
        ]

        if patient.empty:
            st.error("Patient not found")
            st.stop()
# -------------------------
# PATIENT DETAILS
# -------------------------
st.subheader("Patient Details")

st.write(
    f"Name: {patient.iloc[0]['name']}"
)

remaining_sessions = (
    patient.iloc[0]['sessions_total']
    - patient.iloc[0]['sessions_used']
)

st.write(
    f"Sessions Remaining: {remaining_sessions}"
)

attendance_df = pd.read_sql(
    "SELECT * FROM attendance",
    engine
)

patient_history = attendance_df[
    attendance_df["patient_id"] == patient_id
]

st.subheader("Attendance History")

if patient_history.empty:

    st.info("No attendance records yet")

else:

    st.dataframe(
        patient_history[
            ["timestamp"]
        ]
    )

        sessions_total = patient.iloc[0]["sessions_total"]
        sessions_used = patient.iloc[0]["sessions_used"]

        if sessions_used >= sessions_total:
            st.error("No sessions remaining")
            st.stop()

        attendance_df = pd.read_sql(
            "SELECT * FROM attendance",
            engine
        )

        today = datetime.now().date()

        already_checked = False

        for _, row in attendance_df.iterrows():

            row_date = datetime.fromisoformat(
                row["timestamp"]
            ).date()

            if (
                row["patient_id"] == patient_id
                and row_date == today
            ):
                already_checked = True
                break

        if already_checked:
            st.warning("Already checked in today")
            st.stop()

        new_row = pd.DataFrame([{
            "patient_id": patient_id,
            "timestamp": datetime.now().isoformat(),
            "latitude": user_lat,
            "longitude": user_lon
        }])

        new_row.to_sql(
            "attendance",
            engine,
            if_exists="append",
            index=False
        )

        new_sessions_used = sessions_used + 1

        with engine.begin() as conn:
            conn.exec_driver_sql(f"""
            UPDATE patients
            SET sessions_used = {new_sessions_used}
            WHERE patient_id = '{patient_id}'
            """)

        remaining = sessions_total - new_sessions_used

        st.success("Attendance marked")
        st.success(f"Sessions remaining: {remaining}")

# =====================================================
# ADMIN PANEL
# =====================================================
elif menu == "Admin Panel":

    st.title("Admin Panel")

    st.subheader("Add New Patient")

    patient_id = st.text_input("Patient ID")
    name = st.text_input("Patient Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")
    sessions_total = st.number_input(
        "Total Sessions",
        min_value=1,
        step=1
    )

    if st.button("Add Patient"):

        new_patient = pd.DataFrame([{
    "patient_id": patient_id,
    "name": name,
    "phone": phone,
    "email": email,
    "sessions_total": sessions_total,
    "sessions_used": 0
}])

        new_patient.to_sql(
            "patients",
            engine,
            if_exists="append",
            index=False
        )

        st.success("Patient added successfully")

    st.subheader("All Patients")

    patients_df = pd.read_sql(
        "SELECT * FROM patients",
        engine
    )

    patients_df["sessions_remaining"] = (
        patients_df["sessions_total"]
        - patients_df["sessions_used"]
    )

    st.dataframe(patients_df)

# =====================================================
# ATTENDANCE HISTORY
# =====================================================
elif menu == "Attendance History":

    st.title("Attendance History")

    attendance_df = pd.read_sql(
        "SELECT * FROM attendance",
        engine
    )

    st.dataframe(attendance_df)