from models import Admin
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import Optional, List
from config import SessionLocal

class AdminDetails:
    def __init__(self):
        self.db_session = SessionLocal()  

    # Register admin
    def register_admin(self, first_name: str, email: str, password: str, 
                       middle_name: Optional[str] = None, last_name: Optional[str] = None) -> Optional[Admin]:
        try:
            new_admin = Admin(
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                email=email
            )
            new_admin.set_password(password)  # hash password
            
            self.db_session.add(new_admin)
            self.db_session.commit()
            self.db_session.refresh(new_admin) 
            return new_admin

        except IntegrityError as e:
            self.db_session.rollback()
            print(f"Integrity error: {e.orig}")
            return None
        
        except SQLAlchemyError as e:
            self.db_session.rollback()
            print(f"Database error: {e}")
            return None 

    # Login admin
    def get_all_admin(self, first_name: Optional[str] = None) -> List[Admin]:
        try:
            query = self.db_session.query(Admin)
            if first_name:
                query = query.filter(Admin.first_name.ilike(f"%{first_name}%"))
            return query.all()
        except SQLAlchemyError as e:
            print(f"Error fetching admins: {e}")
            return []


    # Change password
    def change_password(self, admin_id: int, old_password: str, new_password: str) -> bool:
        try:
            admin = self.db_session.query(Admin).filter_by(id=admin_id).first()
            if not admin or not admin.check_password(old_password):
                return False

            admin.set_password(new_password)
            self.db_session.commit()
            return True
        except SQLAlchemyError as e:
            self.db_session.rollback()
            print(f"Error changing admin password: {e}")
            return False

    # Get all admins (with optional filter by first_name)
    def get_all_admin(self, first_name: Optional[str] = None) -> List[Admin]:
        try:
            query = self.db_session.query(Admin).all()

            if first_name:
                query = query.filter(Admin.first_name.ilike(f"%{first_name}%"))  

            return query.all()
        except SQLAlchemyError as e:
            print(f"Error fetching admins: {e}")
            return []
