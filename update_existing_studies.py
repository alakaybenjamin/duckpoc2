"""
Update existing clinical studies with drug information and create data products
"""
import sys
import os
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
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

DATA_PRODUCT_TYPES = ["Dataset", "Algorithm", "Image Collection", "Clinical Notes", "Genomic Data"]
DATA_FORMATS = ["CSV", "JSON", "DICOM", "FHIR", "BIDS", "HDF5"]

def update_existing_studies(session):
    """Update existing clinical studies with drug information and create data products"""
    try:
        # Get all clinical studies
        studies = session.query(ClinicalStudy).all()
        logger.info(f"Found {len(studies)} clinical studies to update")
        
        # Update each study
        for study in studies:
            # Add drug information if not already present
            if not study.drug:
                study.drug = random.choice(DRUGS)
            
            # Check if study has data products
            existing_data_products = session.query(DataProduct).filter_by(study_id=study.id).count()
            
            # Add data products if needed (up to 2)
            num_to_add = min(2 - existing_data_products, 2)
            if num_to_add > 0:
                for i in range(num_to_add):
                    data_type = random.choice(DATA_PRODUCT_TYPES)
                    data_format = random.choice(DATA_FORMATS)
                    
                    data_product = DataProduct(
                        title=f"{data_type} for {study.title}",
                        description=f"This {data_type} contains {random.choice(['demographic', 'genomic', 'clinical', 'imaging'])} data from the study.",
                        study_id=study.id,
                        type=data_type,
                        format=data_format,
                        size=f"{random.randint(1, 500)} {random.choice(['MB', 'GB'])}",
                        access_level=random.choice(["Public", "Restricted", "Private"]),
                        created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60))
                    )
                    
                    session.add(data_product)
        
        # Commit changes
        session.commit()
        logger.info(f"Successfully updated {len(studies)} clinical studies")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating studies: {str(e)}")
        raise

def main():
    """Main function to run the update"""
    try:
        # Create connection
        logger.info(f"Connecting to database: {DATABASE_URL.split('://')[0]}://*****")
        engine = create_engine(DATABASE_URL)
        
        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Update existing studies
        update_existing_studies(session)
        
    except Exception as e:
        logger.error(f"Failed to update studies: {str(e)}")
        raise
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    main() 