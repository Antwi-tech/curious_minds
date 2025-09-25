from config import session 
from models import School
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List, Optional, Dict, Any
from sqlalchemy import SessionLocal 

class school_details:
    def __init__(self,db_session: SessionLocal = session):
        self.db_session = db_session

# register / add a school
    def add_school(self, school_name: str, email: str, password: str) -> Optional[School]:
        try:
            new_school = School(school_name=school_name, email=email)
            new_school.set_password(password)
            self.db_session.add(new_school)
            self.db_session.commit()
            self.db_session.refresh(new_school)
            return new_school
        except IntegrityError:
            self.db_session.rollback()
            print("Error: School with this email already exists.")
            return None
        except SQLAlchemyError as e:
            self.db_session.rollback()
            print(f"Database error occurred: {e}")
            return None        

