from sqlite3 import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from typing import Optional
from config import SessionLocal
from models import Admin, AvailableTime, Booking, Company, School
import datetime

class CompanyDetails:
    def __init__(self):
        self.db_session = SessionLocal()  

    # -------------------- Register Company --------------------
    def register_company(
        self,  
        company_name: str, 
        email: str, 
        password: str, 
        contact_person: str,
        phone_number: str, 
        description: str, 
        region: str,
        company_address: str,
        industry_type: Optional[str] = None,   
        website: Optional[str] = None,
        is_verified: bool = False,
        is_active: bool = True 
    ) -> Optional[Company]:
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

            self.db_session.add(new_company)
            self.db_session.commit()
            self.db_session.refresh(new_company)
            return new_company
        
        except IntegrityError:
                self.db_session.rollback()
                print("Error: Company with this email already exists.")
                return None
            
        except SQLAlchemyError as e:
                self.db_session.rollback()
                print(f"Database error occurred: {e}")
                return None

    # -------------------- Login Company --------------------
    def login_company(self, email: str, password: str) -> Optional[Company]:
        try:
            company = self.db_session.query(Company).filter_by(email=email, is_active=True).first()
            if company and company.check_password(password):
                return company
            return None
        except SQLAlchemyError as e:
            print(f"Database error during login: {e}")
            return None

    # -------------------- Change Password --------------------
    def change_password(self, company_id: int, old_password: str, new_password: str) -> bool:
        try:
            company = self.db_session.query(Company).filter_by(company_id=company_id).first()
            if not company or not company.check_password(old_password):
                return False
            company.set_password(new_password)
            self.db_session.commit()
            return True
        except SQLAlchemyError as e:
            self.db_session.rollback()
            print(f"Error changing password: {e}")
            return False

    # -------------------- Get Profile --------------------
    def get_profile(self, company_id: int) -> Optional[Company]:
        try:
            return self.db_session.query(Company).filter_by(company_id=company_id).first()
        except SQLAlchemyError as e:
            print(f"Error fetching company profile: {e}")
            return None

    # -------------------- Update Profile --------------------
    def update_profile(self, company_id: int, **kwargs) -> Optional[Company]:
        try:
            company = self.db_session.query(Company).filter_by(company_id=company_id).first()
            if not company:
                return None
            for key, value in kwargs.items():
                if hasattr(company, key) and value is not None:
                    setattr(company, key, value)
            self.db_session.commit()
            self.db_session.refresh(company)
            return company
        except SQLAlchemyError as e:
            self.db_session.rollback()
            print(f"Error updating company profile: {e}")
            return None

    # -------------------- Role-Based Access Decorator --------------------
    @staticmethod
    def company_required(fn):
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if not claims or claims.get("role") != "company":
                return jsonify({"error": "Company access required"}), 403

            company_id = get_jwt_identity()  # string ID from token
            return fn(*args, company_id=int(company_id), **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper