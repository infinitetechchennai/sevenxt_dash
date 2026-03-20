from sqlalchemy import create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL").replace("postgres://", "postgresql://")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def get_db_connection():
    return engine.raw_connection()