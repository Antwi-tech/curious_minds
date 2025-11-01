from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from config import SessionLocal
from models import Admin, AvailableTime, Booking, Company, School
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import Optional


class AdminDetails:
    def __init__(self):
        self.db_session = SessionLocal()

    # Register/add an admin
    def add_admin(
        self,
        first_name: str,
        email: str,
        password: str,
        last_name: Optional[str] = None,
        middle_name: Optional[str] = None
    ) -> Optional[Admin]:
        try:
            admin = Admin(
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                email=email
            )
            admin.set_password(password)  # hash password

            self.db_session.add(admin)
            self.db_session.commit()
            self.db_session.refresh(admin)

            return admin
        except IntegrityError as e:
            self.db_session.rollback()
            print(f"IntegrityError: {e}")   # <-- log actual DB error
            return None
        except SQLAlchemyError as e:
            self.db_session.rollback()
            print(f"Database error occurred: {e}")
            return None
        
 # Admin login
    def admin_login(self, email: str, password: str) -> Optional[Admin]:
        try:
            admin = self.db_session.query(Admin).filter_by(email=email).first()
            if admin and admin.check_password(password):
                return admin
            return None
        except SQLAlchemyError as e:
            print(f"Database error during admin login: {e}")
            return None
        

    # Admin logout (handled on client)
    def admin_logout(self):
        # """
        # JWT logout is stateless — you can’t ‘log out’ on the backend directly,
        # but you can tell the client to discard the token or implement token blacklisting.
        # """
        try:
            self.db_session.close()
            return {"message": "Session closed successfully"}
        except Exception as e:
            print(f"Unable to log out: {e}")
            return {"error": "Logout failed"}

    # Role-based access decorator
    @staticmethod
    def admin_required(fn):
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()  # access additional_claims
            identity = get_jwt_identity()  # string admin id
            if not claims or claims.get("role") != "admin":
                return jsonify({"error": "Admin access required"}), 403
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper
    
    # Delete an admin
    def delete_admin(self, id: int) -> Optional[Admin]:
        try:
            admin = self.db_session.query(Admin).filter_by(id=id).first()
            if not admin:
                print("Admin not found")
                return None

            self.db_session.delete(admin)
            self.db_session.commit()
            return admin
        except SQLAlchemyError as e:
            self.db_session.rollback()
            print(f"Error deleting admin: {e}")
            return None

    # Get all admins (filter by name optionally)
    def get_all_admins(self, first_name: Optional[str] = None, last_name: Optional[str] = None):
        try:
            query = self.db_session.query(Admin)

            if first_name:
                query = query.filter(Admin.first_name.ilike(f"%{first_name}%"))

            if last_name:
                query = query.filter(Admin.last_name.ilike(f"%{last_name}%"))

            return query.all()

        except SQLAlchemyError as e:
            print(f"Error fetching admins: {e}")
            return []

    # Change password
    def change_password(self, id: int, old_password: str, new_password: str) -> bool:
        try:
            admin_user = self.db_session.query(Admin).filter_by(id=id).first()
            if not admin_user or not admin_user.check_password(old_password):
                return False

            admin_user.set_password(new_password)
            self.db_session.commit()
            return True
        except SQLAlchemyError as e:
            self.db_session.rollback()
            print(f"Error changing password: {e}")
            return False

        # ---------- SCHOOL MANAGEMENT ----------
    def verify_school(self, school_id: int) -> bool:
        try:
            school = self.db_session.query(School).filter_by(school_id=school_id).first()
            if not school:
                return False
            school.is_verified = True
            self.db_session.commit()
            return True
        except SQLAlchemyError as e:
            self.db_session.rollback()
            print(f"Error verifying school: {e}")
            return False

    def activate_school(self, school_id: int) -> bool:
        try:
            school = self.db_session.query(School).filter_by(school_id=school_id).first()
            if not school:
                return False
            school.is_active = True
            self.db_session.commit()
            return True
        except SQLAlchemyError as e:
            self.db_session.rollback()
            print(f"Error activating school: {e}")
            return False

    def deactivate_school(self, school_id: int) -> bool:
        try:
            school = self.db_session.query(School).filter_by(school_id=school_id).first()
            if not school:
                return False
            school.is_active = False
            self.db_session.commit()
            return True
        except SQLAlchemyError as e:
            self.db_session.rollback()
            print(f"Error deactivating school: {e}")
            return False


    # ---------- COMPANY MANAGEMENT ----------
    def verify_company(self, company_id: int) -> bool:
        try:
            company = self.db_session.query(Company).filter_by(company_id=company_id).first()
            if not company:
                return False
            company.is_verified = True
            self.db_session.commit()
            return True
        except SQLAlchemyError as e:
            self.db_session.rollback()
            print(f"Error verifying company: {e}")
            return False

    def activate_company(self, company_id: int) -> bool:
        try:
            company = self.db_session.query(Company).filter_by(company_id=company_id).first()
            if not company:
                return False
            company.is_active = True
            self.db_session.commit()
            return True
        except SQLAlchemyError as e:
            self.db_session.rollback()
            print(f"Error activating company: {e}")
            return False

    def deactivate_company(self, company_id: int) -> bool:
        try:
            company = self.db_session.query(Company).filter_by(company_id=company_id).first()
            if not company:
                return False
            company.is_active = False
            self.db_session.commit()
            return True
        except SQLAlchemyError as e:
            self.db_session.rollback()
            print(f"Error deactivating company: {e}")
            return False

    # -------------------- GET ALL BOOKINGS --------------------
    def get_all_bookings(self):
        try:
            bookings = self.db_session.query(Booking).all()
            return bookings
        except SQLAlchemyError as e:
            print(f"Error fetching bookings: {e}")
            return []

    # -------------------- GET AVAILABLE TIMES --------------------
    def get_available_times(self):
        try:
            available_times = self.db_session.query(AvailableTime).all()
            return available_times
        except SQLAlchemyError as e:
            print(f"Error fetching available times: {e}")
            return []

    # -------------------- CANCEL BOOKING --------------------
    def cancel_booking(self, booking_id: int) -> bool:
        try:
            booking = self.db_session.query(Booking).filter_by(id=booking_id).first()
            if not booking:
                return False

            # Instead of deleting, mark it as cancelled
            booking.status = "cancelled"
            self.db_session.commit()
            return True
        except SQLAlchemyError as e:
            self.db_session.rollback()
            print(f"Error cancelling booking: {e}")
            return False