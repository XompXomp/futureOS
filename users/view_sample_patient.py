import pickle
import pandas as pd

def view_sample_patient():
    """Load and display the sample patient record details"""
    
    # Load the sample patient record
    with open('sample_patient_record.pkl', 'rb') as f:
        sample_record = pickle.load(f)
    
    print("=" * 80)
    print("SAMPLE PATIENT RECORD DETAILS")
    print("=" * 80)
    
    # 1. Basic Patient Info
    print("\n1. BASIC PATIENT INFORMATION")
    print("-" * 40)
    patient = sample_record['patients'].iloc[0]
    print(f"Patient ID: {patient['patient_id']}")
    print(f"Name: {patient['name']}")
    print(f"Date of Birth: {patient['dob']}")
    print(f"Age: {patient['age']}")
    print(f"Gender: {patient['gender']}")
    
    # 2. Maternal Health Status
    print("\n2. MATERNAL HEALTH STATUS")
    print("-" * 40)
    maternal = sample_record['maternal_health'].iloc[0]
    print(f"Pregnant: {'YES' if maternal['is_pregnant'] else 'NO'}")
    if maternal['is_pregnant']:
        print(f"Pregnancy Test Date: {maternal['pregnancy_test_date']}")
        print(f"Delivery Type: {maternal['delivery_type'] or 'Not delivered yet'}")
    
    # 3. Diagnoses
    print("\n3. DIAGNOSES")
    print("-" * 40)
    diagnoses = sample_record['diagnoses']
    for _, diagnosis in diagnoses.iterrows():
        print(f"• {diagnosis['diagnosis_name']} (ICD: {diagnosis['icd_code']}) - Diagnosed: {diagnosis['diagnosed_date']}")
    
    # 4. Medications
    print("\n4. MEDICATIONS")
    print("-" * 40)
    medications = sample_record['medications']
    for _, med in medications.iterrows():
        print(f"• {med['medication_name']} - {med['dosage']} - {med['frequency']} - Last refill: {med['last_refill']}")
    
    # 5. Lab Results
    print("\n5. LAB RESULTS")
    print("-" * 40)
    labs = sample_record['lab_results']
    for _, lab in labs.iterrows():
        print(f"• {lab['test_name']}: {lab['result']} {lab['unit']} (Reference: {lab['reference_range']}) - Date: {lab['test_date']}")
    
    # 6. Appointments
    print("\n6. APPOINTMENTS")
    print("-" * 40)
    appointments = sample_record['appointments']
    for _, apt in appointments.iterrows():
        print(f"• {apt['appointment_date']}: {apt['appointment_type']} at {apt['location']}")
    
    # 7. Clinical Notes
    print("\n7. CLINICAL NOTES")
    print("-" * 40)
    notes = sample_record['clinical_notes']
    for _, note in notes.iterrows():
        print(f"Date: {note['note_date']}")
        print(f"Note: {note['note_text']}")
        print()
    
    # 8. Vitals
    print("\n8. VITAL SIGNS")
    print("-" * 40)
    vitals = sample_record['vitals']
    for _, vital in vitals.iterrows():
        print(f"Date: {vital['vital_date']}")
        print(f"  BP: {vital['bp_systolic']}/{vital['bp_diastolic']}")
        print(f"  Heart Rate: {vital['heart_rate']} bpm")
        print(f"  Temperature: {vital['temperature']}°F")
        print(f"  Height: {vital['height_cm']} cm")
        print(f"  Weight: {vital['weight_kg']} kg")
        print(f"  BMI: {vital['bmi']}")
        print(f"  Body Fat: {vital['body_fat_pct']}%")
        print()
    
    # 9. Allergies
    print("\n9. ALLERGIES")
    print("-" * 40)
    allergies = sample_record['allergies']
    for _, allergy in allergies.iterrows():
        print(f"• {allergy['allergen']} - Reaction: {allergy['reaction']}")
    
    # 10. Patient Tags
    print("\n10. PATIENT TAGS")
    print("-" * 40)
    tags = sample_record['patient_tags']
    for _, tag in tags.iterrows():
        print(f"• {tag['tag']}")
    
    # 11. Cluster Analysis
    print("\n11. EXPECTED CLUSTER ASSIGNMENTS")
    print("-" * 40)
    print("Based on this patient's data, they should be assigned to:")
    print("• Mental Health (Depression, Anxiety)")
    print("• Sleep Health (Insomnia, Sleep Apnea)")
    print("• Fitness Centric (Patellar Tendinopathy, Protein Supplements)")
    print("• Maternal Health (Pregnancy)")
    print("• Preventive Health (Regular checkups)")

if __name__ == "__main__":
    view_sample_patient() 