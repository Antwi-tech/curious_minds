from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from typing import Optional
from config import SessionLocal
from models import Company, AvailableTime, Booking, School, is_overlapping
from sqlalchemy.exc import IntegrityError

class CompanyDetails:
    def __init__(self):
        pass

    def get_session(self):
        return SessionLocal()

    # -------------------- Register Company --------------------
    def register_company(self, company_name, email, password, contact_person,
                         phone_number, description, region, company_address,
                         industry_type=None, website=None, is_verified=False, is_active=True):
        db = self.get_session()
        try:
            new_company = Company(
                company_name=company_name,
                email=email,
                contact_person=contact_person,
                region=region,
                industry_type=industry_type,
                company_address=company_address,
                phone_number=phone_number,
                description=description,
                website=website,
                is_verified=is_verified,
                is_active=is_active
            )
            new_company.set_password(password)
            db.add(new_company)
            db.commit()
            db.refresh(new_company)
            return new_company
        except IntegrityError:
            db.rollback()
            print("Error: Company with this email already exists.")
            return None
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Database error occurred: {e}")
            return None
        finally:
            db.close()

    # -------------------- Login Company --------------------
    def login_company(self, email: str, password: str) -> Optional[Company]:
        db = self.get_session()
        try:
            # expire_on_commit=False ensures we get fresh data
            company = db.query(Company).filter_by(email=email, is_active=True).first()
            if company and company.check_password(password):
                # Refresh to get latest is_verified status from DB
                db.refresh(company)
                return company
            return None
        except SQLAlchemyError as e:
            print(f"Database error during login: {e}")
            return None
        finally:
            db.close()

    # -------------------- Change Password --------------------
    def change_password(self, company_id: int, old_password: str, new_password: str) -> bool:
        db = self.get_session()
        try:
            company = db.query(Company).filter_by(company_id=company_id).first()
            if not company or not company.check_password(old_password):
                return False
            company.set_password(new_password)
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error changing password: {e}")
            return False
        finally:
            db.close()

    # -------------------- Get Profile --------------------
    def get_profile(self, company_id: int) -> Optional[Company]:
        db = self.get_session()
        try:
            return db.query(Company).filter_by(company_id=company_id).first()
        except SQLAlchemyError as e:
            print(f"Error fetching company profile: {e}")
            return None
        finally:
            db.close()

    # -------------------- Update Profile --------------------
    def update_profile(self, company_id: int, **kwargs) -> Optional[Company]:
        db = self.get_session()
        try:
            company = db.query(Company).filter_by(company_id=company_id).first()
            if not company:
                return None
            for key, value in kwargs.items():
                if hasattr(company, key) and value is not None:
                    setattr(company, key, value)
            db.commit()
            db.refresh(company)
            return company
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error updating company profile: {e}")
            return None
        finally:
            db.close()

    # -------------------- Role-Based Access Decorator --------------------
    @staticmethod
    def company_required(fn):
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if not claims or claims.get("role") != "company":
                return jsonify({"error": "Company access required"}), 403
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper
    
    
    # -------------------- Get Company Slots --------------------
    def get_slots(self, company_id: int):
        db = self.get_session()
        try:
            return db.query(AvailableTime).filter_by(company_id=company_id).all()
        except SQLAlchemyError as e:
            print(f"Error fetching slots: {e}")
            return []
        finally:
            db.close()

# -------------------- Create Slot --------------------
    def create_slot(self, company_id: int, start_date: str, end_date: str):
        db = self.get_session()
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)

            if is_overlapping(db, company_id, start, end):
                print("Overlapping slot exists")
                return None

            slot = AvailableTime(
                company_id=company_id,
                start_date=start,
                end_date=end
            )
            db.add(slot)
            db.commit()
            db.refresh(slot)
            return slot
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error creating slot: {e}")
            return None
        finally:
            db.close()

# -------------------- Delete Slot --------------------
    def delete_slot(self, company_id: int, schedule_id: int) -> bool:
        db = self.get_session()
        try:
            slot = db.query(AvailableTime).filter_by(
                schedule_id=schedule_id,
                company_id=company_id
            ).first()
            if not slot:
                return False
            db.delete(slot)
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error deleting slot: {e}")
            return False
        finally:
            db.close()

# -------------------- Get Company Bookings --------------------
    def get_bookings(self, company_id: int):
        db = self.get_session()
        try:
            bookings = db.query(Booking).join(AvailableTime).filter(
                AvailableTime.company_id == company_id
            ).all()

            # Serialize while session is still open
            result = []
            for b in bookings:
                result.append({
                    "booking_id": b.booking_id,
                    "schedule_id": b.schedule_id,
                    "school_id": b.school_id,
                    "status": b.status,
                    "created_at": b.created_at.isoformat(),
                    "start_date": b.available_time.start_date.isoformat(),
                    "end_date": b.available_time.end_date.isoformat(),
                    "school_name": b.school.school_name,
                    "school_email": b.school.email,
                    "school_phone": b.school.phone_number,
                })
            return result
        except SQLAlchemyError as e:
            print(f"Error fetching bookings: {e}")
            return []
        finally:
            db.close()
            
            
# -------------------- Update Booking Status --------------------
    def update_booking_status(self, company_id: int, booking_id: int, status: str) -> bool:
        db = self.get_session()
        try:
            booking = db.query(Booking).join(AvailableTime).filter(
                Booking.booking_id == booking_id,
                AvailableTime.company_id == company_id
            ).first()
            if not booking:
                return False
            booking.status = status
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error updating booking status: {e}")
            return False
        finally:
            db.close()