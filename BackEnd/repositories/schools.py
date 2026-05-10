from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt
from typing import Optional
from config import SessionLocal
from models import School
from sqlalchemy import or_


class SchoolDetails:
    def __init__(self):
        pass

    def get_session(self):
        return SessionLocal()

    # -------------------- Register School --------------------
    def add_school(self, school_name, email, password, school_address, region,
               contact_person, phone_number, description, website=None,
               is_verified=False, is_active=True):
        db = self.get_session()
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
            new_school.set_password(password)
            db.add(new_school)
            db.commit()
            db.refresh(new_school)
            return new_school
        except IntegrityError:
            db.rollback()
            print("Error: School with this email already exists.")
            return None
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Database error occurred: {e}")
            return None
        finally:
            db.close()

    # -------------------- Search School --------------------
    def search_school(self, search_term: str, page: int = 1, limit: int = 10):
        db = self.get_session()
        try:
            query = db.query(School).filter(
                or_(
                    School.school_name.ilike(f"%{search_term}%"),
                    School.region.ilike(f"%{search_term}%"),
                    School.contact_person.ilike(f"%{search_term}%"),
                    School.email.ilike(f"%{search_term}%")
                )
            )
            total = query.count()
            results = query.offset((page - 1) * limit).limit(limit).all()
            return results, total
        except Exception as e:
            print(f"Error occurred while retrieving schools: {e}")
            return [], 0
        finally:
            db.close()

    # -------------------- Delete School --------------------
    def delete_school(self, school_id: int):
        db = self.get_session()
        try:
            school = db.query(School).filter_by(school_id=school_id).first()
            if not school:
                return None
            db.delete(school)
            db.commit()
            return school
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error deleting school: {e}")
            return None
        finally:
            db.close()

    # -------------------- Get All Schools --------------------
    def get_all_schools(self, region=None, is_active=None):
        db = self.get_session()
        try:
            query = db.query(School)
            if region:
                query = query.filter(School.region.ilike(f"%{region}%"))
            if is_active is not None:
                query = query.filter_by(is_active=is_active)
            return query.all()
        except SQLAlchemyError as e:
            print(f"Error fetching schools: {e}")
            return []
        finally:
            db.close()

    # -------------------- Login School --------------------
    def login_school(self, email: str, password: str) -> Optional[School]:
        db = self.get_session()
        try:
            school = db.query(School).filter_by(email=email, is_active=True).first()
            if school and school.check_password(password):
                db.refresh(school)
                return school
            return None
        except SQLAlchemyError as e:
            print(f"Database error during login: {e}")
            return None
        finally:
            db.close()

    # -------------------- Change Password --------------------
    def change_password(self, school_id: int, old_password: str, new_password: str) -> bool:
        db = self.get_session()
        try:
            school = db.query(School).filter_by(school_id=school_id).first()
            if not school or not school.check_password(old_password):
                return False
            school.set_password(new_password)
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error changing password: {e}")
            return False
        finally:
            db.close()

    # -------------------- Get School By ID --------------------
    def get_school_by_id(self, school_id: int) -> Optional[School]:
        db = self.get_session()
        try:
            return db.query(School).filter_by(school_id=school_id).first()
        except SQLAlchemyError as e:
            print(f"Error fetching school: {e}")
            return None
        finally:
            db.close()

    # -------------------- Role-Based Access Decorator --------------------
    @staticmethod
    def school_required(fn):
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if not claims or claims.get("role") != "school":
                return jsonify({"error": "School access required"}), 403
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper

        # -------------------- Get All Available Slots --------------------
    def get_all_available_slots(self):
        db = self.get_session()
        try:
            from models import AvailableTime, Company
            slots = db.query(AvailableTime).join(Company).filter(
                Company.is_active == True,
                Company.is_verified == True
            ).all()

            # Extract data while session is still open
            result = []
            for s in slots:
                result.append({
                    "schedule_id": s.schedule_id,
                    "company_id": s.company_id,
                    "company_name": s.company.company_name,
                    "industry_type": s.company.industry_type,
                    "company_address": s.company.company_address,
                    "region": s.company.region,
                    "start_date": s.start_date.isoformat(),
                    "end_date": s.end_date.isoformat(),
                })
            return result
        except SQLAlchemyError as e:
            print(f"Error fetching slots: {e}")
            return []
        finally:
            db.close()
    
    # -------------------- Book a Slot --------------------
    def book_slot(self, school_id: int, schedule_id: int):
        db = self.get_session()
        try:
            from models import Booking
            booking = Booking(
                schedule_id=schedule_id,
                school_id=school_id,
                status="pending"
            )
            db.add(booking)
            db.commit()
            db.refresh(booking)
            return booking
        except Exception as e:
            db.rollback()
            print(f"Error booking slot: {e}")
            return None
        finally:
            db.close()

    # -------------------- Get School Bookings --------------------
    def get_bookings(self, school_id: int):
        db = self.get_session()
        try:
            from models import Booking
            bookings = db.query(Booking).filter_by(school_id=school_id).all()

            result = []
            for b in bookings:
                result.append({
                    "booking_id": b.booking_id,
                    "schedule_id": b.schedule_id,
                    "status": b.status,
                    "created_at": b.created_at.isoformat(),
                    "start_date": b.available_time.start_date.isoformat(),
                    "end_date": b.available_time.end_date.isoformat(),
                    "company_name": b.available_time.company.company_name,
                    "company_address": b.available_time.company.company_address,
                    "industry_type": b.available_time.company.industry_type,
                })
            return result
        except Exception as e:
            import traceback
            traceback.print_exc()  # 👈 this prints the FULL error
            print(f"Error fetching bookings: {e}")
            return []
        finally:
            db.close()

    # -------------------- Cancel Booking --------------------
    def cancel_booking(self, school_id: int, booking_id: int) -> bool:
        db = self.get_session()
        try:
            from models import Booking
            booking = db.query(Booking).filter_by(
                booking_id=booking_id,
                school_id=school_id
            ).first()
            if not booking:
                return False
            booking.status = "cancelled"
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error cancelling booking: {e}")
            return False
        finally:
            db.close()    
    

# from config import SessionLocal
# from models import School
# from sqlalchemy.exc import SQLAlchemyError, IntegrityError
# from typing import Optional
# from sqlalchemy import or_


# class SchoolDetails:
#     def __init__(self):
#         self.db_session = SessionLocal()  
        
#     # register / add a school / add school feature 
#     def add_school(
#         self,
#         school_name: str,
#         email: str,
#         password: str,
#         school_address: str,
#         region: str,
#         contact_person: str,
#         phone_number: str,
#         description: str,
#         website: Optional[str] = None,
#         is_verified: bool = False,
#         is_active: bool = True 
#     ) -> Optional[School]:
#         try:
#             new_school = School(
#                 school_name=school_name,
#                 email=email,
#                 school_address=school_address,
#                 region=region,
#                 contact_person=contact_person,
#                 phone_number=phone_number,
#                 website=website,
#                 description=description,
#                 is_verified=is_verified,
#                 is_active=is_active    
#             )
#             new_school.set_password(password)  # hash password

#             self.db_session.add(new_school)
#             self.db_session.commit()
#             self.db_session.refresh(new_school)

#             return new_school

#         except IntegrityError:
#             self.db_session.rollback()
#             print("Error: School with this email already exists.")
#             return None
#         except SQLAlchemyError as e:
#             self.db_session.rollback()
#             print(f"Database error occurred: {e}")
#             return None
    
   
# # search for a school
#     def search_school(self, search_term: str, page: int = 1, limit: int = 10):
#         try:
#             query = self.db_session.query(School).filter(
#                 or_(
#                     School.school_name.ilike(f"%{search_term}%"),
#                     School.region.ilike(f"%{search_term}%"),
#                     School.contact_person.ilike(f"%{search_term}%"),
#                     School.email.ilike(f"%{search_term}%")
#                 )
#             )

#             total = query.count()  # total number of matches

#             results = (
#                 query.offset((page - 1) * limit)
#                 .limit(limit)
#                 .all()
#             )

#             return results, total
#         except Exception as e:
#             print(f"Error occurred while retrieving schools: {e}")
#             return [], 0


# # delete a school
#     def delete_school(self, school_id: int):
#             try:
                
#                 school = self.db_session.query(School).filter_by(school_id=school_id).first()
#                 if not school:
#                     return None

#                 self.db_session.delete(school)
#                 self.db_session.commit()
#                 return school
#             except SQLAlchemyError as e:
#                 self.db_session.rollback()
#                 print(f"Error deleting school: {e}")
#                 return None


# #  Get all schools (with optional filters)
#     def get_all_schools(self, region: Optional[str] = None, is_active: Optional[bool] = None):
#         try:
#             query = self.db_session.query(School)

#             if region:
#                 query = query.filter(School.region.ilike(f"%{region}%"))

#             if is_active is not None:
#                 query = query.filter_by(is_active=is_active)

#             return query.all()
#         except SQLAlchemyError as e:
#             print(f"Error fetching schools: {e}")
#             return []
        
#     # Login school
#     def login_school(self, email: str, password: str) -> Optional[School]:
#         try:
#             school = self.db_session.query(School).filter_by(email=email, is_active=True).first()
#             if school and school.check_password(password):
#                 return school
#             return None
#         except SQLAlchemyError as e:
#             print(f"Database error during login: {e}")
#             return None

    
#     # Change password
#     def change_password(self, school_id: int, old_password: str, new_password: str) -> bool:
#         try:
#             school = self.db_session.query(School).filter_by(school_id=school_id).first()
#             if not school or not school.check_password(old_password):
#                 return False

#             school.set_password(new_password)
#             self.db_session.commit()
#             return True
#         except SQLAlchemyError as e:
#             self.db_session.rollback()
#             print(f"Error changing password: {e}")
#             return False        
    
