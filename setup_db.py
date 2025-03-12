"""
Script to set up the initial database for local development.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_postgres():
    """Create PostgreSQL database if it doesn't exist."""
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    
    # Get database configuration from environment
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "troyprince01")
    POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "fraud_detection")
    
    # Connect to PostgreSQL server
    try:
        conn = psycopg2.connect(
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_SERVER,
            port=POSTGRES_PORT
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{POSTGRES_DB}'")
        exists = cursor.fetchone()
        
        if exists:
           print(f"Database {POSTGRES_DB} already exists.")
            
            
        cursor.close()
        conn.close()
        
        # Now connect to the database and create tables
        from app.db.database import engine
        from app.db.model import Base
        
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
        
        return True
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        return False

if __name__ == "__main__":
    print("Setting up fraud detection database...")
    if setup_postgres():
        print("Database setup complete!")
    else:
        print("Database setup failed.")
        sys.exit(1)