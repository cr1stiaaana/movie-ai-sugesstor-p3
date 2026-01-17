"""
Database initialization script
Run this once to create all tables
"""

from app import app, db
from models import User, MovieRating, UserSimilarity
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize the database with all tables"""
    with app.app_context():
        try:
            logger.info("Dropping existing tables...")
            db.drop_all()
            logger.info("Existing tables dropped")
            
            logger.info("Creating database tables...")
            db.create_all()
            logger.info("Database tables created successfully!")
            
            # Verify tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f"Tables created: {tables}")
            
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise


if __name__ == '__main__':
    init_database()
