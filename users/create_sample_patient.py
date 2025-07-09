import pandas as pd
import pickle
from datetime import datetime, timedelta
import random

def create_sample_patient():
    """Create a comprehensive sample patient record with data from all tables"""
    
    # Sample patient ID
    patient_id = "SAMPLE001"
    
    # 1. PATIENTS TABLE
    patients_data = pd.DataFrame({
        'patient_id': [patient_id],
        'name': ['Sarah Johnson'],
        'dob': ['1990-05-15'],
        'age': [34],
        'gender': ['Female']
    })
    
    # 2. APPOINTMENTS TABLE
    appointments_data = pd.DataFrame({
        'appointment_id': [1, 2, 3, 4, 5],
        'patient_id': [patient_id] * 5,
        'appointment_date': [
            '2025-01-15',
            '2025-02-20',
            '2025-03-10',
            '2025-04-05',
            '2025-05-12'
        ],
        'appointment_type': [
            'Annual Physical',
            'Sleep Study Consultation',
            'Mental Health Follow-up',
            'Prenatal Visit',
            'Fitness Assessment'
        ],
        'location': [
            'Main Medical Center',
            'Sleep Clinic',
            'Mental Health Clinic',
            'Obstetrics Department',
            'Sports Medicine Center'
        ]
    })
    
    # 3. CLINICAL NOTES TABLE
    clinical_notes_data = pd.DataFrame({
        'note_id': [1, 2, 3, 4, 5],
        'patient_id': [patient_id] * 5,
        'note_date': [
            '2025-01-15',
            '2025-02-20',
            '2025-03-10',
            '2025-04-05',
            '2025-05-12'
        ],
        'note_text': [
            '34 y.o. female presenting for annual physical. Patient reports increased stress levels and difficulty sleeping. Blood pressure elevated at 140/90. Recommending stress management techniques and sleep hygiene education.',
            'Patient reports persistent insomnia and daytime fatigue. Sleep study ordered to rule out sleep apnea. Patient also mentions feeling anxious and overwhelmed at work.',
            'Follow-up for anxiety and depression symptoms. Patient reports improvement with current medication but still experiencing sleep disturbances. Discussed cognitive behavioral therapy options.',
            'Pregnancy confirmed. Patient is 8 weeks pregnant. All prenatal labs normal. Discussed prenatal care plan and nutrition recommendations. Patient excited but anxious about pregnancy.',
            'Fitness assessment completed. Patient interested in improving athletic performance. History of minor knee injury from running. Recommending strength training and proper recovery protocols.'
        ]
    })
    
    # 4. DIAGNOSES TABLE
    diagnoses_data = pd.DataFrame({
        'diagnosis_id': [1, 2, 3, 4, 5, 6],
        'patient_id': [patient_id] * 6,
        'diagnosis_name': [
            'Depression',
            'Anxiety Disorder',
            'Insomnia',
            'Obstructive Sleep Apnea',
            'Patellar Tendinopathy',
            'Pregnancy'
        ],
        'icd_code': [
            'F32.1',
            'F41.1',
            'G47.00',
            'G47.33',
            'M76.50',
            'Z32.1'
        ],
        'diagnosed_date': [
            '2024-11-15',
            '2024-11-15',
            '2025-02-20',
            '2025-03-10',
            '2024-08-10',
            '2025-04-05'
        ]
    })
    
    # 5. LAB RESULTS TABLE
    lab_results_data = pd.DataFrame({
        'lab_id': [1, 2, 3, 4, 5, 6, 7, 8],
        'patient_id': [patient_id] * 8,
        'test_name': [
            'Complete Blood Count',
            'Comprehensive Metabolic Panel',
            'Thyroid Stimulating Hormone',
            'Vitamin D',
            'Pregnancy Test',
            'Hemoglobin A1C',
            'Lipid Panel',
            'Sleep Study'
        ],
        'test_date': [
            '2025-01-15',
            '2025-01-15',
            '2025-01-15',
            '2025-01-15',
            '2025-04-05',
            '2025-01-15',
            '2025-01-15',
            '2025-03-10'
        ],
        'result': [
            'Normal',
            'Normal',
            '2.1',
            '25',
            'Positive',
            '5.2',
            'Normal',
            'Mild OSA'
        ],
        'unit': [
            'N/A',
            'N/A',
            'mIU/L',
            'ng/mL',
            'Positive/Negative',
            '%',
            'N/A',
            'AHI: 12'
        ],
        'reference_range': [
            'Normal range',
            'Normal range',
            '0.4-4.0',
            '30-100',
            'Negative',
            '<5.7',
            'Normal range',
            '<5'
        ]
    })
    
    # 6. MATERNAL HEALTH TABLE
    maternal_health_data = pd.DataFrame({
        'maternal_id': [1],
        'patient_id': [patient_id],
        'is_pregnant': [True],
        'pregnancy_test_date': ['2025-04-05'],
        'delivery_type': [None]  # Not delivered yet
    })
    
    # 7. MEDICATIONS TABLE
    medications_data = pd.DataFrame({
        'medication_id': [1, 2, 3, 4, 5],
        'patient_id': [patient_id] * 5,
        'medication_name': [
            'Sertraline',
            'Melatonin',
            'Prenatal Vitamins',
            'Protein Supplement',
            'CPAP Therapy'
        ],
        'dosage': [
            '50mg',
            '5mg',
            '1 tablet',
            '30g',
            'n/a'
        ],
        'frequency': [
            'Daily',
            'As needed',
            'Daily',
            'Post-workout',
            'Nightly'
        ],
        'last_refill': [
            '2025-05-01',
            '2025-04-15',
            '2025-04-05',
            '2025-05-10',
            '2025-03-15'
        ]
    })
    
    # 8. PATIENT TAGS TABLE
    patient_tags_data = pd.DataFrame({
        'tag_id': [1, 2, 3, 4, 5, 6, 7],
        'patient_id': [patient_id] * 7,
        'tag': [
            'mental_health',
            'sleep_disorder',
            'pregnancy',
            'fitness_oriented',
            'preventive_care',
            'stress_management',
            'performance_optimization'
        ]
    })
    
    # 9. VITALS TABLE
    vitals_data = pd.DataFrame({
        'vital_id': [1, 2, 3],
        'patient_id': [patient_id] * 3,
        'vital_date': [
            '2025-01-15',
            '2025-03-10',
            '2025-05-12'
        ],
        'bp_systolic': [140, 135, 130],
        'bp_diastolic': [90, 85, 82],
        'heart_rate': [72, 68, 65],
        'temperature': [98.6, 98.4, 98.2],
        'height_cm': [165, 165, 165],  # Height remains constant
        'weight_kg': [62, 63, 64],  # Slight weight gain due to pregnancy
        'bmi': [22.8, 23.1, 23.5],
        'body_fat_pct': [18.5, 19.0, 19.5]
    })
    
    # 10. ALLERGIES TABLE
    allergies_data = pd.DataFrame({
        'allergy_id': [1, 2],
        'patient_id': [patient_id] * 2,
        'allergen': [
            'Penicillin',
            'Shellfish'
        ],
        'reaction': [
            'Rash',
            'Swelling'
        ]
    })
    
    # Create a comprehensive patient record dictionary
    sample_patient_record = {
        'patients': patients_data,
        'appointments': appointments_data,
        'clinical_notes': clinical_notes_data,
        'diagnoses': diagnoses_data,
        'lab_results': lab_results_data,
        'maternal_health': maternal_health_data,
        'medications': medications_data,
        'patient_tags': patient_tags_data,
        'vitals': vitals_data,
        'allergies': allergies_data
    }
    
    return sample_patient_record

def save_sample_patient():
    """Save the sample patient record to a pickle file"""
    sample_record = create_sample_patient()
    
    # Save as a single pickle file containing all data
    with open('sample_patient_record.pkl', 'wb') as f:
        pickle.dump(sample_record, f)
    
    print("Sample patient record created successfully!")
    print("File saved as: sample_patient_record.pkl")
    print("\nPatient Summary:")
    print("Name: Sarah Johnson")
    print("Age: 34")
    print("Gender: Female")
    print("Status: Pregnant (8 weeks)")
    print("\nKey Conditions:")
    print("- Depression and Anxiety")
    print("- Insomnia and Sleep Apnea")
    print("- Patellar Tendinopathy (sports injury)")
    print("- Pregnancy")
    print("\nThis patient should trigger multiple clusters:")
    print("- Mental Health (depression, anxiety)")
    print("- Sleep Health (insomnia, sleep apnea)")
    print("- Fitness Centric (sports injury, protein supplements)")
    print("- Maternal Health (pregnancy)")
    print("- Preventive Health (regular checkups)")

if __name__ == "__main__":
    save_sample_patient() 