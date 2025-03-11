"""
Migration script to update the clinical studies and data products schemas
"""
import sys
import os
from sqlalchemy import create_engine, text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add root directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Database URL from environment or default
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/biomed_search")

def migrate_database():
    """Alter database schema to add new columns and relationships"""
    try:
        # Create connection
        logger.info(f"Connecting to database: {DATABASE_URL.split('://')[0]}://*****")
        engine = create_engine(DATABASE_URL)
        conn = engine.connect()
        
        # Start transaction
        trans = conn.begin()
        
        try:
            # 1. Add drug column to clinical_study table
            logger.info("Adding drug column to clinical_study table")
            conn.execute(text("ALTER TABLE clinical_study ADD COLUMN IF NOT EXISTS drug VARCHAR;"))
            
            # 2. Update data_products table with new columns
            logger.info("Adding new columns to data_products table")
            conn.execute(text("ALTER TABLE data_products ADD COLUMN IF NOT EXISTS size VARCHAR;"))
            conn.execute(text("ALTER TABLE data_products ADD COLUMN IF NOT EXISTS access_level VARCHAR DEFAULT 'Public';"))
            
            # 3. Commit transaction
            trans.commit()
            logger.info("Schema migration completed successfully")
            
        except Exception as e:
            # Rollback on error
            trans.rollback()
            logger.error(f"Error during migration: {str(e)}")
            raise
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise

if __name__ == "__main__":
    migrate_database() 