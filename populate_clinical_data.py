"""
Populate database with sample clinical studies and data products
"""
import sys
import os
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add root directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import models
from models.database_models import ClinicalStudy, DataProduct, Base

# Database URL from environment or default
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/biomed_search")

# Sample data
DRUGS = [
    "Remdesivir", "Dexamethasone", "Tocilizumab", "Baricitinib", "Molnupiravir",
    "Evusheld", "Paxlovid", "Keytruda", "Humira", "Eliquis", "Rituxan", 
    "Avastin", "Herceptin", "Revlimid", "Opdivo", "Eylea", "Stelara"
]

PHASES = ["Phase I", "Phase II", "Phase III", "Phase IV"]
STATUSES = ["Recruiting", "Active", "Completed", "Not yet recruiting"]
INDICATIONS = ["Oncology", "Cardiology", "Neurology", "Infectious Disease", "Immunology"]
DATA_PRODUCT_TYPES = ["Dataset", "Algorithm", "Image Collection", "Clinical Notes", "Genomic Data"]
DATA_FORMATS = ["CSV", "JSON", "DICOM", "FHIR", "BIDS", "HDF5"]
INSTITUTIONS = [
    "Mayo Clinic", "Johns Hopkins", "Cleveland Clinic", "Massachusetts General Hospital",
    "Stanford Health Care", "UCLA Medical Center", "UCSF Medical Center",
    "NYU Langone Health", "Mount Sinai Hospital", "Duke University Hospital"
]

def generate_sample_data(session):
    """Generate and save sample clinical studies with data products"""
    try:
        # First check if we already have data
        existing_count = session.query(ClinicalStudy).count()
        if existing_count > 0:
            logger.info(f"Database already contains {existing_count} clinical studies. Skipping sample data generation.")
            return
        
        # Generate 25 sample clinical studies
        logger.info("Generating sample clinical studies...")
        studies = []
        for i in range(1, 26):
            # Create a clinical study
            study = ClinicalStudy(
                title=f"Clinical Trial {i}: Evaluation of {random.choice(DRUGS)} for {random.choice(INDICATIONS)}",
                description=f"A {random.choice(PHASES)} study to evaluate the safety and efficacy of treatment protocols.",
                status=random.choice(STATUSES),
                phase=random.choice(PHASES),
                drug=random.choice(DRUGS),
                start_date=datetime.utcnow() - timedelta(days=random.randint(30, 365)),
                end_date=datetime.utcnow() + timedelta(days=random.randint(30, 730)) if random.random() > 0.3 else None,
                institution=random.choice(INSTITUTIONS),
                indication_category=random.choice(INDICATIONS),
                severity=random.choice(["Mild", "Moderate", "Severe"]),
                risk_level=random.choice(["Low", "Medium", "High"]),
                duration=random.randint(30, 1095),  # 1 month to 3 years in days
                participant_count=random.randint(50, 10000)
            )
            
            # Add 0 to 2 data products per study
            num_data_products = random.randint(0, 2)
            for j in range(num_data_products):
                data_type = random.choice(DATA_PRODUCT_TYPES)
                data_format = random.choice(DATA_FORMATS)
                
                data_product = DataProduct(
                    title=f"{data_type} for Study {i}",
                    description=f"This {data_type} contains {random.choice(['demographic', 'genomic', 'clinical', 'imaging'])} data from the study.",
                    type=data_type,
                    format=data_format,
                    size=f"{random.randint(1, 500)} {random.choice(['MB', 'GB'])}",
                    access_level=random.choice(["Public", "Restricted", "Private"]),
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60))
                )
                
                # Associate with the study
                study.data_products.append(data_product)
            
            studies.append(study)
        
        # Add all studies to the session
        session.add_all(studies)
        session.commit()
        
        logger.info(f"Successfully added {len(studies)} clinical studies with associated data products.")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error generating sample data: {str(e)}")
        raise

def main():
    """Main function to run the sample data population"""
    try:
        # Create connection
        logger.info(f"Connecting to database: {DATABASE_URL.split('://')[0]}://*****")
        engine = create_engine(DATABASE_URL)
        
        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Generate sample data
        generate_sample_data(session)
        
    except Exception as e:
        logger.error(f"Failed to populate sample data: {str(e)}")
        raise
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    main() 