import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
