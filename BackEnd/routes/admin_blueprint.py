from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from repositories.admin import AdminDetails

admin_dp = Blueprint("admin", __name__)
admin_usr = AdminDetails()

# Register new admin (optional - maybe only super admin can use this)
@admin_dp.route("/register", methods=["POST"])
def register_admin():
    data = request.get_json()
    first_name = data.get("first_name")
    email = data.get("email")
    password = data.get("password")

    if not first_name or not email or not password:
        return jsonify({"error": "First name, email, and password are required"}), 400

    admin = admin_usr.register_admin(
        first_name=first_name,
        middle_name=data.get("middle_name"),
        last_name=data.get("last_name"),
        email=email,
        password=password
    )

    if not admin:
        return jsonify({"error": "Admin with this email already exists"}), 409

    return jsonify({"message": "Admin registered successfully"}), 201


# Login admin
@admin_dp.route("/login", methods=["POST"])
def login_admin():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    admin = admin_usr.login_admin(email, password)
    if not admin:
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=admin.id, fresh=True)
    refresh_token = create_refresh_token(identity=admin.id)

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "admin": {
            "id": admin.id,
            "first_name": admin.first_name,
            "email": admin.email
        }
    }), 200


# Get all admin
@admin_dp.route("/users", methods=["GET"])
def get_all_admin():
    try:
        first_name = request.args.get("first_name")
        admins = admin_usr.get_all_admin(first_name=first_name)

        return jsonify({
            "admins": [
                {
                    "id": usr.id,
                    "first_name": usr.first_name,
                    "email": usr.email,
                } for usr in admins
            ],
            "count": len(admins)
        }), 200

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500
