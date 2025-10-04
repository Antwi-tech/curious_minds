from config import SessionLocal
from models import Admin
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
       

    
# class AdminDetails:
#     # Register admin
#     def register_admin(
#         self,
#         first_name: str,
#         email: str,
#         password: str,
#         middle_name: Optional[str] = None,
#         last_name: Optional[str] = None,
#     ) -> Optional[Admin]:
#         try:
#             with SessionLocal() as session:
#                 new_admin = Admin(
#                     first_name=first_name,
#                     middle_name=middle_name,
#                     last_name=last_name,
#                     email=email,
#                 )
#                 new_admin.set_password(password)  # from PasswordMixin

#                 session.add(new_admin)
#                 session.commit()
#                 session.refresh(new_admin)
#                 return new_admin

#         except IntegrityError as e:
#             print(f"[IntegrityError] {e.orig}")  # full MySQL error in console
#             return f"IntegrityError: {e.orig}"   # log actual DB error
            
#         except SQLAlchemyError as e:
#             print(f"[SQLAlchemyError] {e}")
#             return None

#     # Login admin
#     def login_admin(self, email: str, password: str) -> Optional[Admin]:
#         try:
#             with SessionLocal() as session:
#                 admin = session.query(Admin).filter_by(email=email).first()
#                 if admin and admin.check_password(password):
#                     return admin
#                 return None
#         except SQLAlchemyError as e:
#             print(f"[LoginError] {e}")
#             return None

#     # Change password
#     def change_password(self, admin_id: int, old_password: str, new_password: str) -> bool:
#         try:
#             with SessionLocal() as session:
#                 admin = session.query(Admin).filter_by(id=admin_id).first()
#                 if not admin or not admin.check_password(old_password):
#                     return False
#                 admin.set_password(new_password)
#                 session.commit()
#                 return True
#         except SQLAlchemyError as e:
#             print(f"[ChangePasswordError] {e}")
#             return False

#     # Get all admins (optionally filter by first_name)
#     def get_all_admin(self, first_name: Optional[str] = None) -> List[Admin]:
#         try:
#             with SessionLocal() as session:
#                 query = session.query(Admin)
#                 if first_name:
#                     query = query.filter(Admin.first_name.ilike(f"%{first_name}%"))
#                 return query.all()
#         except SQLAlchemyError as e:
#             print(f"[GetAllAdminsError] {e}")
#             return []


