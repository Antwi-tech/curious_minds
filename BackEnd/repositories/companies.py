from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from typing import Optional
from config import SessionLocal
from models import Company
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