from localinfo import set_patient_record, get_patient_record, add_or_update_care_ai_treatment, get_care_ai_treatment, get_all_care_ai_treatments
from datetime import datetime

user_id = 42

# Sample EMR (could be much more complex in reality)
patient_record = {
    "name": "Jane Doe",
    "dob": "1990-01-01",
    "gender": "F",
    "diagnoses": ["Hypertension", "Asthma"],
    "medications": ["Lisinopril", "Albuterol"],
    "allergies": ["Penicillin"]
}

print("Setting patient record...")
set_patient_record(user_id, patient_record)

print("Getting patient record:")
record = get_patient_record(user_id)
print(record)

# Add/update CareAITreatments for today
now_date = datetime.utcnow().date().isoformat()
print(f"\nAdding CareAITreatments for {now_date}...")
add_or_update_care_ai_treatment(
    user_id=user_id,
    date=now_date,
    sleep_quality=8,  # integer out of 10
    medication_adherence="missed evening dose",
    sleep_hours=7.5
)

print(f"Getting CareAITreatments for {now_date}:")
treatment = get_care_ai_treatment(user_id, now_date)
print(treatment)

print("\nAll CareAITreatments for user:")
all_treatments = get_all_care_ai_treatments(user_id)
for t in all_treatments:
    print(t) 