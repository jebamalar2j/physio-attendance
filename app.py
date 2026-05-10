import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from geopy.distance import geodesic
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(
    page_title="Sheela Physiocare",
    layout="centered"
)

CLINIC_LAT = 13.0371531
CLINIC_LON = 80.2616611
MAX_DISTANCE_METERS = 75

engine = create_engine("sqlite:///clinic.db")

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
    """)

    conn.exec_driver_sql("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT,
        timestamp TEXT,
        latitude REAL,
        longitude REAL
    )
    """)

role = st.sidebar.radio(
    "Select Role",
    ["Patient", "Admin"]
)

if role == "Patient":

    menu = "Patient Check-In"

else:

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

if menu == "Patient Check-In":

    st.title("Patient Check-In")

    patient_id = st.text_input(
        "Enter Patient ID"
    )

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

elif menu == "Admin Panel":

    st.title("Admin Panel")

    name = st.text_input("Patient Name")
    phone = st.text_input("Phone Number")
    email = st.text_input("Email")

    sessions_total = st.number_input(
        "Total Sessions",
        min_value=1,
        step=1
    )

    if st.button("Add Patient"):

        patient_id = (
            name[:4].upper()
            + phone[-4:]
        )

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

        st.success(
            f"Patient added successfully. ID: {patient_id}"
        )

    patients_df = pd.read_sql(
        "SELECT * FROM patients",
        engine
    )

    st.dataframe(patients_df)

elif menu == "Attendance History":

    st.title("Attendance History")

    attendance_df = pd.read_sql(
        "SELECT * FROM attendance",
        engine
    )

    st.dataframe(attendance_df)