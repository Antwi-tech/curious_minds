# Second file to create is a connection to the database by use of SQLAlchemy
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv() # Load environment variables from env file

database_username = os.getenv('DATABASE_USERNAME')
database_name = os.getenv("DATABASE_NAME")
database_password = os.getenv("DATABASE_PASSWORD")

connection_string = f'mysql+mysqlconnector://{database_username}:{database_password}@localhost/{database_name}'

engine = create_engine(connection_string) 

try:
    connection = engine.connect()
    print("Database connection extablished successfully.")
    connection.close()
except Exception as e:
    print(f"Error connecting to database: {e}")
    
DBsession = sessionmaker(bind=engine) # Create a configured "Session" class
session = DBsession() 

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) 
# def get_db():
#     db = SessionLocal() 
#     try:
#         yield db
#     finally:
#         db.close()