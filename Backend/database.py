from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Load environment variables from .env file directly
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# PostgreSQL must be used for this project
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL must be defined in .env and point to PostgreSQL")
if not database_url.startswith("postgresql://"):
    raise RuntimeError("DATABASE_URL must use the postgresql:// scheme")

print(f"🔧 Using Database: {database_url}")
print("✅ Database Connected")

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()