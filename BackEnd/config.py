# config.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# ---- Database connection variables ----
database_host = os.getenv("DB_HOST", "localhost")
database_port = os.getenv("DB_PORT", "3306")
database_user = os.getenv("DB_USER", "root")
database_password = os.getenv("DB_PASSWORD", "")
database_name = os.getenv("DB_NAME", "curious_minds")

connection_string = (
    f"mysql+mysqlconnector://{database_user}:{database_password}"
    f"@{database_host}:{database_port}/{database_name}"
)

# Engine
engine = create_engine(
    connection_string,
    pool_pre_ping=True,
    pool_recycle=280,
    pool_size=5,
    max_overflow=10
)

# Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection established successfully.")
            print("Driver:", engine.dialect.name, engine.dialect.driver)
    except Exception as e:
        print("❌ Error connecting to database:", e)

# # config.py
# import os
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from dotenv import load_dotenv

# load_dotenv()  # Load environment variables

# # ---- Database connection string ----
# database_username = os.getenv("DATABASE_USERNAME")
# database_password = os.getenv("DATABASE_PASSWORD")
# database_name = os.getenv("DATABASE_NAME")

# connection_string = (
#     f"mysql+mysqlconnector://{database_username}:{database_password}@localhost/{database_name}"
# )

# # Engine 
# engine = engine = create_engine(
#     connection_string,
#     pool_pre_ping=True,
#     pool_recycle=280,        # recycle connections every 280 seconds
#     pool_size=5,             # keep 5 connections in the pool
#     max_overflow=10          # allow 10 extra connections if needed
# )
# # Session Factory
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # Dependency (per-request/session use)
# def get_db():
#     db = SessionLocal()   # <-- creates a new session for each reques
#     try:
#         yield db
#     finally:
#         db.close()

# if __name__ == "__main__":
#     from sqlalchemy import text

#     try:
#         with engine.connect() as conn:
#             result = conn.execute(text("SELECT 1"))
#             print("Database connection established successfully.")
#             print("Driver in use:", engine.dialect.name, engine.dialect.driver)
#     except Exception as e:
#         print("Error connecting to database:", e)


