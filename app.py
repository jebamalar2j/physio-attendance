import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

st.set_page_config(
    page_title="Sheela Physiocare",
    layout="centered"
)

st.title("Sheela Physiocare")

st.subheader("Physio Attendance System")

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
        timestamp TEXT
    )
    """)

role = st.sidebar.radio(
    "Select Role",
    ["Patient", "Admin"]
)

if role == "Patient":

    st.header("Patient Check-In")

    patient_id = st.text_input(
        "Enter Patient ID"
    )

    if st.button("Check In"):

        patients_df = pd.read_sql(
            "SELECT * FROM patients",
            engine
        )

        patient = patients_df[
            patients_df["patient_id"] == patient_id
        ]

        if patient.empty:

            st.error("Patient not found")

        else:

            sessions_total = patient.iloc[0]["sessions_total"]
            sessions_used = patient.iloc[0]["sessions_used"]

            if sessions_used >= sessions_total:

                st.error("No sessions remaining")

            else:

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

                    st.warning(
                        "Already checked in today"
                    )

                else:

                    new_row = pd.DataFrame([{
                        "patient_id": patient_id,
                        "timestamp": datetime.now().isoformat()
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

                    remaining = (
                        sessions_total
                        - new_sessions_used
                    )

                    st.success(
                        "Attendance marked"
                    )

                    st.success(
                        f"Sessions remaining: {remaining}"
                    )

else:

    password = st.sidebar.text_input(
        "Admin Password",
        type="password"
    )

    if password == "physio123":

        menu = st.selectbox(
            "Menu",
            [
                "Add Patient",
                "Attendance History"
            ]
        )

        if menu == "Add Patient":

            st.header("Add Patient")

            name = st.text_input(
                "Patient Name"
            )

            phone = st.text_input(
                "Phone Number"
            )

            email = st.text_input(
                "Email"
            )

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
                    f"Patient added. ID: {patient_id}"
                )

            patients_df = pd.read_sql(
                "SELECT * FROM patients",
                engine
            )

            st.dataframe(patients_df)

        else:

            st.header("Attendance History")

            attendance_df = pd.read_sql(
                "SELECT * FROM attendance",
                engine
            )

            st.dataframe(attendance_df)

    else:

        st.warning(
            "Enter admin password"
        )