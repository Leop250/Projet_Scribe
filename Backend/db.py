from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import get_database_url

DATABASE_URL = get_database_url()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()
