from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
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
            identity = get_jwt_identity()
            if not identity or identity.get("role") != "admin":
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
