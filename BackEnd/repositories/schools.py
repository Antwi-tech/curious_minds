from config import SessionLocal
from models import School
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import Optional
from sqlalchemy import or_


class SchoolDetails:
    def __init__(self):
        self.db_session = SessionLocal()  
        
    # register / add a school / add school feature 
    def add_school(
        self,
        school_name: str,
        email: str,
        password: str,
        school_address: str,
        region: str,
        contact_person: str,
        phone_number: str,
        description: str,
        website: Optional[str] = None,
        is_verified: bool = False,
        is_active: bool = True 
    ) -> Optional[School]:
        try:
            new_school = School(
                school_name=school_name,
                email=email,
                school_address=school_address,
                region=region,
                contact_person=contact_person,
                phone_number=phone_number,
                website=website,
                description=description,
                is_verified=is_verified,
                is_active=is_active    
            )
            new_school.set_password(password)  # hash password

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
    
   
# search for a school
    def search_school(self, search_term: str, page: int = 1, limit: int = 10):
        try:
            query = self.db_session.query(School).filter(
                or_(
                    School.school_name.ilike(f"%{search_term}%"),
                    School.region.ilike(f"%{search_term}%"),
                    School.contact_person.ilike(f"%{search_term}%"),
                    School.email.ilike(f"%{search_term}%")
                )
            )

            total = query.count()  # total number of matches

            results = (
                query.offset((page - 1) * limit)
                .limit(limit)
                .all()
            )

            return results, total
        except Exception as e:
            print(f"Error occurred while retrieving schools: {e}")
            return [], 0


# delete a school
    def delete_school(self, school_id: int):
            try:
                
                school = self.db_session.query(School).filter_by(school_id=school_id).first()
                if not school:
                    return None

                self.db_session.delete(school)
                self.db_session.commit()
                return school
            except SQLAlchemyError as e:
                self.db_session.rollback()
                print(f"Error deleting school: {e}")
                return None