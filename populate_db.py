from datetime import datetime, timedelta
from database import init_db, get_db
from models.database_models import (
    ClinicalStudy, Indication, Procedure, DataProduct,
    User, Collection, CollectionItem, ScientificPaper, DataDomainMetadata
)
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def populate_sample_data():
    """Populate database with sample data for testing"""
    try:
        logger.info("Starting database population...")
        db = next(get_db())

        # Create sample OAuth users
        logger.info("Creating sample users...")
        sample_users = [
            User(
                email="test1@example.com",
                username="Test User 1",
                is_active=True,
                created_at=datetime.utcnow()
            ),
            User(
                email="test2@example.com",
                username="Test User 2",
                is_active=True,
                created_at=datetime.utcnow()
            )
        ]
        for user in sample_users:
            db.add(user)
        db.commit()

        # Sample data lists
        statuses = ['Recruiting', 'Active', 'Completed', 'Not yet recruiting']
        phases = ['Phase I', 'Phase II', 'Phase III', 'Phase IV']
        indication_categories = ['Cardiovascular', 'Neurological', 'Oncology', 'Respiratory']
        severities = ['Mild', 'Moderate', 'Severe']
        procedure_categories = ['Diagnostic', 'Therapeutic', 'Surgical', 'Monitoring']
        risk_levels = ['Low', 'Medium', 'High']

        # Create indications
        logger.info("Creating sample indications...")
        indications = []
        for category in indication_categories:
            for i in range(3):  # 3 indications per category
                indication = Indication(
                    title=f"{category} Condition {i+1}",
                    description=f"Sample {category.lower()} condition for testing",
                    category=category,
                    severity=random.choice(severities)
                )
                db.add(indication)
                indications.append(indication)

        # Create procedures
        logger.info("Creating sample procedures...")
        procedures = []
        for category in procedure_categories:
            for i in range(3):  # 3 procedures per category
                procedure = Procedure(
                    title=f"{category} Procedure {i+1}",
                    description=f"Sample {category.lower()} procedure for testing",
                    category=category,
                    risk_level=random.choice(risk_levels),
                    duration=random.randint(30, 240)  # 30 mins to 4 hours
                )
                db.add(procedure)
                procedures.append(procedure)

        # Generate clinical studies with data products
        logger.info("Creating sample clinical studies and data products...")
        for i in range(1, 31):  # Create 30 studies
            start_date = datetime.now() - timedelta(days=random.randint(0, 365))
            indication = random.choice(indications)
            procedure = random.choice(procedures)

            study = ClinicalStudy(
                title=f"Study {i}: {indication.category} Research using {procedure.category}",
                description=f"Investigation of {indication.title} using {procedure.title}",
                status=random.choice(statuses),
                phase=random.choice(phases),
                start_date=start_date,
                end_date=start_date + timedelta(days=random.randint(180, 730)),
                indication_category=indication.category,
                procedure_category=procedure.category,
                severity=indication.severity,
                risk_level=procedure.risk_level,
                duration=procedure.duration
            )
            db.add(study)
            db.flush()  # Flush to get the study ID

            # Create data products for each study
            for _ in range(random.randint(1, 3)):  # 1-3 data products per study
                data_product = DataProduct(
                    title=f"Data from {study.title}",
                    description=f"Research data for {study.title}",
                    study_id=study.id,
                    type=random.choice(['raw_data', 'processed_data', 'analysis_results']),
                    format=random.choice(['CSV', 'JSON', 'XML']),
                    created_at=datetime.utcnow()
                )
                db.add(data_product)

        # Create collections for sample users
        logger.info("Creating sample collections...")
        for user in sample_users:
            for i in range(1, 4):  # 3 collections per user
                collection = Collection(
                    title=f"Collection {i} - {user.username}",
                    description=f"Sample collection {i} for {user.username}",
                    user_id=user.id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(collection)
                db.flush()

        # Generate scientific papers
        logger.info("Creating sample scientific papers...")
        journals = ['Nature Medicine', 'The Lancet', 'Science', 'Cell', 'JAMA']
        keywords = ['genomics', 'proteomics', 'clinical trials', 'biomarkers']

        for i in range(20):  # Create 20 papers
            pub_date = datetime.now() - timedelta(days=random.randint(7, 730))
            paper = ScientificPaper(
                title=f"Research Paper {i+1}: Advances in {random.choice(indication_categories)}",
                abstract=f"A comprehensive study in {random.choice(keywords)}",
                authors=[f"Author {j+1}" for j in range(random.randint(1, 5))],
                publication_date=pub_date,
                journal=random.choice(journals),
                doi=f"10.1000/paper.{i+1}",
                keywords=random.sample(keywords, k=random.randint(2, 4)),
                citations_count=random.randint(0, 500),
                reference_list=[f"ref_{j}" for j in range(random.randint(5, 15))],
                created_at=datetime.utcnow()
            )
            db.add(paper)


        # Create data domain metadata
        logger.info("Creating sample data domain metadata...")
        domains = ['Clinical Trials', 'Patient Records', 'Genomic Data', 'Medical Imaging']
        for domain in domains:
            metadata = DataDomainMetadata(
                domain_name=domain,
                description=f"Metadata schema for {domain.lower()}",
                schema_definition={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"}
                    }
                },
                validation_rules={
                    "required": ["id", "name"],
                    "format_checks": ["timestamp"]
                },
                data_format=random.choice(['CSV', 'JSON', 'XML']),
                sample_data={
                    "id": "example_id",
                    "name": "example_name",
                    "timestamp": datetime.utcnow().isoformat()
                },
                owner=f"Department {random.randint(1, 5)}",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(metadata)

        # Commit all changes
        db.commit()
        logger.info("Sample data has been populated successfully!")

    except Exception as e:
        logger.error(f"Error populating database: {e}")
        raise

if __name__ == "__main__":
    try:
        init_db()
        populate_sample_data()
        print("\nDatabase population completed successfully!")
        print("\nYou can now run the application and start searching through the sample data.")
        print("Use 'python app.py' to start the server.")
    except Exception as e:
        print(f"\nError: Failed to populate database - {e}")