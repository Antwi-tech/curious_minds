from flask import jsonify
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
from config import SessionLocal
from models import Admin, AvailableTime, Booking, Company, School
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import Optional


class AdminDetails:
    def __init__(self):
        pass

    def get_session(self):
        return SessionLocal()

    def add_admin(self, first_name, email, password, last_name=None, middle_name=None):
        db = self.get_session()
        try:
            admin = Admin(first_name=first_name, middle_name=middle_name, last_name=last_name, email=email)
            admin.set_password(password)
            db.add(admin)
            db.commit()
            db.refresh(admin)
            return admin
        except IntegrityError as e:
            db.rollback()
            print(f"IntegrityError: {e}")
            return None
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Database error: {e}")
            return None
        finally:
            db.close()

    def admin_login(self, email, password):
        db = self.get_session()
        try:
            admin = db.query(Admin).filter_by(email=email).first()
            if admin and admin.check_password(password):
                return admin
            return None
        except SQLAlchemyError as e:
            print(f"Database error during login: {e}")
            return None
        finally:
            db.close()

    def admin_logout(self):
        return {"message": "Session closed successfully"}

    @staticmethod
    def admin_required(fn):
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if not claims or claims.get("role") != "admin":
                return jsonify({"error": "Admin access required"}), 403
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper

    def delete_admin(self, id):
        db = self.get_session()
        try:
            admin = db.query(Admin).filter_by(id=id).first()
            if not admin:
                return None
            db.delete(admin)
            db.commit()
            return admin
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error deleting admin: {e}")
            return None
        finally:
            db.close()

    def get_all_admins(self, first_name=None, last_name=None):
        db = self.get_session()
        try:
            query = db.query(Admin)
            if first_name:
                query = query.filter(Admin.first_name.ilike(f"%{first_name}%"))
            if last_name:
                query = query.filter(Admin.last_name.ilike(f"%{last_name}%"))
            return query.all()
        except SQLAlchemyError as e:
            print(f"Error fetching admins: {e}")
            return []
        finally:
            db.close()

    def change_password(self, id, old_password, new_password):
        db = self.get_session()
        try:
            admin_user = db.query(Admin).filter_by(id=id).first()
            if not admin_user or not admin_user.check_password(old_password):
                return False
            admin_user.set_password(new_password)
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error changing password: {e}")
            return False
        finally:
            db.close()

    # -------------------- SCHOOL MANAGEMENT --------------------
    def verify_school(self, school_id):
        db = self.get_session()
        try:
            school = db.query(School).filter_by(school_id=school_id).first()
            if not school:
                return False
            school.is_verified = True
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error verifying school: {e}")
            return False
        finally:
            db.close()

    def activate_school(self, school_id):
        db = self.get_session()
        try:
            school = db.query(School).filter_by(school_id=school_id).first()
            if not school:
                return False
            school.is_active = True
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error activating school: {e}")
            return False
        finally:
            db.close()

    def deactivate_school(self, school_id):
        db = self.get_session()
        try:
            school = db.query(School).filter_by(school_id=school_id).first()
            if not school:
                return False
            school.is_active = False
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error deactivating school: {e}")
            return False
        finally:
            db.close()

    def get_all_schools(self):
        db = self.get_session()
        try:
            return db.query(School).all()
        except SQLAlchemyError as e:
            print(f"Error fetching schools: {e}")
            return []
        finally:
            db.close()

    # -------------------- COMPANY MANAGEMENT --------------------
    def verify_company(self, company_id):
        db = self.get_session()
        try:
            company = db.query(Company).filter_by(company_id=company_id).first()
            if not company:
                return False
            company.is_verified = True
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error verifying company: {e}")
            return False
        finally:
            db.close()

    def activate_company(self, company_id):
        db = self.get_session()
        try:
            company = db.query(Company).filter_by(company_id=company_id).first()
            if not company:
                return False
            company.is_active = True
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error activating company: {e}")
            return False
        finally:
            db.close()

    def deactivate_company(self, company_id):
        db = self.get_session()
        try:
            company = db.query(Company).filter_by(company_id=company_id).first()
            if not company:
                return False
            company.is_active = False
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error deactivating company: {e}")
            return False
        finally:
            db.close()

    def get_all_companies(self):
        db = self.get_session()
        try:
            return db.query(Company).all()
        except SQLAlchemyError as e:
            print(f"Error fetching companies: {e}")
            return []
        finally:
            db.close()

    # -------------------- BOOKINGS --------------------
    def get_all_bookings(self):
        db = self.get_session()
        try:
            bookings = db.query(Booking).all()
            result = []
            for b in bookings:
                result.append({
                    "booking_id": b.booking_id,
                    "school_id": b.school_id,
                    "school_name": b.school.school_name,
                    "company_id": b.available_time.company_id,
                    "company_name": b.available_time.company.company_name,
                    "start_date": b.available_time.start_date.isoformat(),
                    "end_date": b.available_time.end_date.isoformat(),
                    "status": b.status,
                    "created_at": b.created_at.isoformat(),
                })
            return result
        except SQLAlchemyError as e:
            print(f"Error fetching bookings: {e}")
            return []
        finally:
            db.close()

    # -------------------- AVAILABLE TIMES --------------------
    def get_available_times(self):
        db = self.get_session()
        try:
            return db.query(AvailableTime).all()
        except SQLAlchemyError as e:
            print(f"Error fetching available times: {e}")
            return []
        finally:
            db.close()

    # -------------------- REFRESH TOKEN --------------------
    def refresh_admin_access_token(self):
        try:
            current_admin_id = get_jwt_identity()
            claims = get_jwt()
            if claims.get("role") != "admin":
                return None
            return create_access_token(
                identity=current_admin_id,
                additional_claims={"role": "admin"}
            )
        except Exception as e:
            print(f"Error refreshing admin token: {e}")
            return None
    
    
       