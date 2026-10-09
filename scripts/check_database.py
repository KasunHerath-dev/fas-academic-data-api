import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

def check_database():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("Error: DATABASE_URL environment variable is not set.")
        sys.exit(1)
        
    try:
        engine = create_engine(db_url)
        with engine.connect() as connection:
            print("Successfully connected to the database.")
            sys.exit(0)
    except OperationalError as e:
        print("Failed to connect to the database. OperationalError occurred.")
        sys.exit(1)
    except Exception as e:
        print("An unexpected error occurred while connecting to the database.")
        sys.exit(1)

if __name__ == "__main__":
    check_database()
