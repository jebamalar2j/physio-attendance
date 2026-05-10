from sqlalchemy import create_engine
import pandas as pd

# Connect to database
engine = create_engine("sqlite:///clinic.db")

# Sample patients
patients = pd.DataFrame([
    {
        "patient_id": "P001",
        "name": "Ravi",
        "sessions_total": 20,
        "sessions_used": 0
    },
    {
        "patient_id": "P002",
        "name": "Priya",
        "sessions_total": 15,
        "sessions_used": 2
    }
])

# Add patients to database
patients.to_sql(
    "patients",
    engine,
    if_exists="append",
    index=False
)

print("Patients added successfully")