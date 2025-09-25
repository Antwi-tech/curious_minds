from config import session
from models import School
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import Optional


class SchoolDetails:
    def __init__(self, db_session=session):
        self.db_session = db_session

    # register / add a school
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
        website: Optional[str] = None,   # optional
        is_verified: bool = False        # default
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
                is_verified=is_verified
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
