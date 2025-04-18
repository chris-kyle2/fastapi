from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import os

load_dotenv()

# Use environment variables with your RDS values
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "91cqwerty12345")
DB_HOST = os.getenv("DB_HOST", "postgres.cep44usy2men.us-east-1.rds.amazonaws.com")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "postgres")  # Default database name in RDS is "postgres"

# Direct database URL string for RDS
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        # RDS specific settings
        connect_args={
            "connect_timeout": 15,  # 60 seconds connection timeout
            "sslmode": "prefer",   # Require SSL for RDS connection
            "keepalives": 1,        # Enable keepalive
            "keepalives_idle": 30,  # Idle time before sending keepalive
            "keepalives_interval": 10  # Interval between keepalives
        },
        pool_size=10,               # Maximum number of connections in the pool
        max_overflow=5,            # Maximum number of connections that can be created beyond pool_size
        pool_timeout=10,           # Timeout for getting a connection from the pool
        pool_recycle=1800,         # Recycle connections after 30 minutes
        pool_pre_ping=True,        # Pre-ping connections
        echo=True                  # Log all SQL queries (set to False in production)
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()

    # Add this function for FastAPI dependency injection
    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def test_connection():
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print("Database connection successful!")
                return True
        except Exception as e:
            print(f"Database connection failed: {str(e)}")
            return False

except Exception as e:
    print(f"Error initializing database connection: {str(e)}")

if __name__ == "__main__":
    test_connection()