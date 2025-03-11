from datetime import datetime, timedelta

now = datetime.utcnow()

clinical_studies = [
    {
        "id": 1,
        "title": "Effects of Vitamin D on COVID-19 Outcomes",
        "description": "Randomized controlled trial studying vitamin D supplementation in COVID-19 patients",
        "status": "Active",
        "phase": "Phase III",
        "start_date": now - timedelta(days=180),
        "end_date": now + timedelta(days=180),
        "institution": "University Medical Center",
        "participant_count": 500
    },
    {
        "id": 2,
        "title": "Novel Cancer Immunotherapy Approach",
        "description": "Phase II trial of combination immunotherapy in advanced melanoma",
        "status": "Recruiting",
        "phase": "Phase II",
        "start_date": now - timedelta(days=90),
        "end_date": now + timedelta(days=275),
        "institution": "Cancer Research Institute",
        "participant_count": 200
    },
    {
        "id": 3,
        "title": "Alzheimer's Early Detection Biomarkers",
        "description": "Longitudinal study of blood-based biomarkers for Alzheimer's detection",
        "status": "Active",
        "phase": "Phase I",
        "start_date": now - timedelta(days=365),
        "end_date": now + timedelta(days=365),
        "institution": "Neurology Research Center",
        "participant_count": 150
    }
]

indications = [
    {
        "id": 1,
        "name": "Type 2 Diabetes",
        "category": "Endocrine",
        "severity": "Moderate",
        "description": "Chronic metabolic disorder characterized by high blood sugar"
    },
    {
        "id": 2,
        "name": "Hypertension",
        "category": "Cardiovascular",
        "severity": "Moderate",
        "description": "Chronic condition of elevated blood pressure"
    },
    {
        "id": 3,
        "name": "Major Depressive Disorder",
        "category": "Psychiatric",
        "severity": "Severe",
        "description": "Mental health disorder characterized by persistent feelings of sadness"
    },
    {
        "id": 4,
        "name": "Rheumatoid Arthritis",
        "category": "Autoimmune",
        "severity": "Moderate",
        "description": "Chronic inflammatory disorder affecting joints"
    }
]

procedures = [
    {
        "id": 1,
        "name": "Coronary Angioplasty",
        "category": "Surgical",
        "risk_level": "High",
        "duration": 120,
        "description": "Procedure to open blocked coronary arteries"
    },
    {
        "id": 2,
        "name": "Total Hip Replacement",
        "category": "Surgical",
        "risk_level": "High",
        "duration": 180,
        "description": "Surgical replacement of hip joint"
    },
    {
        "id": 3,
        "name": "Laparoscopic Cholecystectomy",
        "category": "Surgical",
        "risk_level": "Medium",
        "duration": 60,
        "description": "Minimally invasive gallbladder removal"
    },
    {
        "id": 4,
        "name": "Colonoscopy",
        "category": "Diagnostic",
        "risk_level": "Low",
        "duration": 45,
        "description": "Examination of the large intestine"
    }
]