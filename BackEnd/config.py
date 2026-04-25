# config.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

# ---- Database connection string ----
database_username = os.getenv("DATABASE_USERNAME")
database_password = os.getenv("DATABASE_PASSWORD")
database_name = os.getenv("DATABASE_NAME")

connection_string = (
    f"mysql+mysqlconnector://{database_username}:{database_password}@localhost/{database_name}"
)

# Engine 
engine = engine = create_engine(
    connection_string,
    pool_pre_ping=True,
    pool_recycle=280,        # recycle connections every 280 seconds
    pool_size=5,             # keep 5 connections in the pool
    max_overflow=10          # allow 10 extra connections if needed
)
# Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency (per-request/session use)
def get_db():
    db = SessionLocal()   # <-- creates a new session for each reques
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    from sqlalchemy import text

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Database connection established successfully.")
            print("Driver in use:", engine.dialect.name, engine.dialect.driver)
    except Exception as e:
        print("Error connecting to database:", e)
