from flask import Blueprint, jsonify, request
from repositories.admin import AdminDetails
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
    
admin_dp = Blueprint("admin", __name__)  
admin = AdminDetails()


# Register/ add a school
@admin_dp.route("/register", methods=['POST'])
def add_admin():
    data = request.get_json()
    required_fields = [
        "first_name", "last_name", "email", "password"
    ]
    
    # check for missing fields
    for field in required_fields:
        if field not in data:
            return jsonify({"error":f"Missing required field:{field}"}), 400
    
    try:
        admin_usr = admin.add_admin(
            first_name = data["first_name"],
            last_name = data["last_name"],
            middle_name = data["middle_name"],
            email = data["email"],
            password = data["password"]   
        )
        
        if admin_usr:
            return jsonify({
                "message": "Admin registered successfully",
                "admin user": {
                    "first_name": admin_usr.first_name,
                    "middle_name": admin_usr.middle_name,
                    "last_name": admin_usr.last_name,
                    "email": admin_usr.email,
                }
            }), 201
        else:
            return jsonify({"error": "Admin with this email already exists."}), 409

    except SQLAlchemyError as e:
        return jsonify({"error": f"Database error occurred: {e}"}), 500
 
# Admin login
@admin_dp.route("/login", methods=["POST"])
def login_admin():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    
    try:
        admin_user = admin.admin_login(email, password)
        if not admin_user:
            return jsonify({"error": "Invalid credentials"}), 401

        access_token = create_access_token(identity={"id": admin_user.id, "role": "admin"})
        refresh_token = create_refresh_token(identity={"id": admin_user.id, "role": "admin"})

        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "admin": {
                "id": admin_user.id,
                "first_name": admin_user.first_name,
                "last_name": admin_user.last_name,
                "email": admin_user.email
            }
        }), 200

    except SQLAlchemyError as e:
        return jsonify({"error": f"Database error occurred: {e}"}), 500
# from flask import Blueprint, request, jsonify
# from flask_jwt_extended import (
#     create_access_token,
#     create_refresh_token,
#     jwt_required,
#     get_jwt_identity,
# )
# from repositories.admin import AdminDetails

# admin_dp = Blueprint("admin", __name__)
# admin_repo = AdminDetails()


# # Register new admin
# @admin_dp.route("/register", methods=["POST"])
# def register_admin():
#     data = request.get_json() or {}
#     first_name = data.get("first_name")
#     email = data.get("email")
#     password = data.get("password")

#     if not first_name or not email or not password:
#         return jsonify({"error": "first_name, email, and password are required"}), 400

#     admin = admin_repo.register_admin(
#         first_name=first_name,
#         middle_name=data.get("middle_name"),
#         last_name=data.get("last_name"),
#         email=email,
#         password=password,
#     )

#     if isinstance(admin, str):  # we returned an error message string
#         return jsonify({"error": admin}), 400
#     elif not admin:
#         return jsonify({"error": "Unknown failure"}), 400

#     if not admin:
#         return jsonify({"error": "Failed to register admin. Check logs for details"}), 409

#     return jsonify({
#         "message": "Admin registered successfully",
#         "admin": {
#             "id": admin.id,
#             "first_name": admin.first_name,
#             "email": admin.email,
#             "is_active": admin.is_active,
#         },
#     }), 201


# # Login admin
# @admin_dp.route("/login", methods=["POST"])
# def login_admin():
#     data = request.get_json() or {}
#     email = data.get("email")
#     password = data.get("password")

#     if not email or not password:
#         return jsonify({"error": "email and password are required"}), 400

#     admin = admin_repo.login_admin(email, password)
#     if not admin:
#         return jsonify({"error": "Invalid credentials"}), 401

#     access_token = create_access_token(identity=admin.id, fresh=True)
#     refresh_token = create_refresh_token(identity=admin.id)

#     return jsonify({
#         "message": "Login successful",
#         "access_token": access_token,
#         "refresh_token": refresh_token,
#         "admin": {
#             "id": admin.id,
#             "first_name": admin.first_name,
#             "email": admin.email,
#         },
#     }), 200


# # Get all admins
# @admin_dp.route("/users", methods=["GET"])
# @jwt_required()  # protect with JWT
# def get_all_admins():
#     first_name = request.args.get("first_name")
#     admins = admin_repo.get_all_admin(first_name=first_name)

#     return jsonify({
#         "admins": [
#             {
#                 "id": usr.id,
#                 "first_name": usr.first_name,
#                 "email": usr.email,
#                 "is_active": usr.is_active,
#             }
#             for usr in admins
#         ],
#         "count": len(admins),
#     }), 200


# # Change password
# @admin_dp.route("/change-password", methods=["POST"])
# @jwt_required()
# def change_password():
#     data = request.get_json() or {}
#     old_password = data.get("old_password")
#     new_password = data.get("new_password")

#     if not old_password or not new_password:
#         return jsonify({"error": "old_password and new_password are required"}), 400

#     admin_id = get_jwt_identity()
#     success = admin_repo.change_password(admin_id, old_password, new_password)

#     if not success:
#         return jsonify({"error": "Password change failed"}), 400

#     return jsonify({"message": "Password updated successfully"}), 200


