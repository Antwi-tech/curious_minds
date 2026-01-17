from flask import Blueprint, jsonify, request
from repositories.admin import AdminDetails
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt, jwt_required, get_jwt_identity
    
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

        # Identity must be a string
        admin_id = str(admin_user.id)

        # Use additional_claims for role and other metadata
        additional_claims = {"role": "admin"}

        access_token = create_access_token(
            identity=admin_id,
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(
            identity=admin_id,
            additional_claims=additional_claims
        )

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

    # Delete an admin
@admin_dp.route("/admin/<int:id>", methods=["DELETE"])
@AdminDetails.admin_required
def delete_admin(id):
    deleted = admin.delete_admin(id)
    if not deleted:
        return jsonify({"error": "Admin not found"}), 404
    return jsonify({"message": f"Admin {deleted.email} deleted successfully"}), 200


# Get all admins
@admin_dp.route("/admins", methods=["GET"])
@AdminDetails.admin_required
def get_all_admins():
    first_name = request.args.get("first_name")
    last_name = request.args.get("last_name")

    admins = admin.get_all_admins(first_name=first_name, last_name=last_name)
    return jsonify({
        "count": len(admins),
        "admins": [
            {
                "id": a.id,
                "first_name": a.first_name,
                "last_name": a.last_name,
                "email": a.email,
            } for a in admins
        ]
    }), 200


# Change admin password
@admin_dp.route("/change_password/<int:id>", methods=["PATCH"])
@AdminDetails.admin_required
def change_admin_password(id):
    identity = get_jwt_identity()  # This will be the admin_id (string)
    claims = get_jwt()             # This gives you the extra claims (like role)

    if claims.get("role") != "admin" or str(identity) != str(id):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return jsonify({"error": "Old and new passwords are required"}), 400

    success = admin.change_password(id, old_password, new_password)
    if not success:
        return jsonify({"error": "Invalid old password"}), 400

    return jsonify({"message": "Password updated successfully"}), 200


# Private apis for admin to manage schools and companies
# ---------- SCHOOL MANAGEMENT ----------
@admin_dp.route("/schools/<int:school_id>/verify", methods=["PATCH"])
@AdminDetails.admin_required
def verify_school(school_id):
    identity = get_jwt_identity()
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    success = admin.verify_school(school_id)
    if not success:
        return jsonify({"error": "School not found or failed to verify"}), 400
    return jsonify({"message": f"School {school_id} verified successfully"}), 200


@admin_dp.route("/schools/<int:school_id>/activate", methods=["PATCH"])
@AdminDetails.admin_required
def activate_school(school_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    success = admin.activate_school(school_id)
    if not success:
        return jsonify({"error": "School not found or failed to activate"}), 400
    return jsonify({"message": f"School {school_id} activated successfully"}), 200


@admin_dp.route("/schools/<int:school_id>/deactivate", methods=["PATCH"])
@jwt_required()
def deactivate_school(school_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    success = admin.deactivate_school(school_id)
    if not success:
        return jsonify({"error": "School not found or failed to deactivate"}), 400
    return jsonify({"message": f"School {school_id} deactivated successfully"}), 200


# ---------- COMPANY MANAGEMENT ----------
@admin_dp.route("/company/<int:company_id>/verify", methods=["PATCH"])
@jwt_required()
def verify_company(company_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    success = admin.verify_company(company_id)
    if not success:
        return jsonify({"error": "Company not found or failed to verify"}), 400
    return jsonify({"message": f"Company {company_id} verified successfully"}), 200


@admin_dp.route("/admin/companies/<int:company_id>/activate", methods=["PATCH"])
@jwt_required()
def activate_company(company_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    success = admin.activate_company(company_id)
    if not success:
        return jsonify({"error": "Company not found or failed to activate"}), 400
    return jsonify({"message": f"Company {company_id} activated successfully"}), 200


@admin_dp.route("/admin/companies/<int:company_id>/deactivate", methods=["PATCH"])
@jwt_required()
def deactivate_company(company_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    success = admin.deactivate_company(company_id)
    if not success:
        return jsonify({"error": "Company not found or failed to deactivate"}), 400
    return jsonify({"message": f"Company {company_id} deactivated successfully"}), 200



# -------------------- GET ALL BOOKINGS --------------------
@admin_dp.route("/bookings", methods=["GET"])
@AdminDetails.admin_required
def get_all_bookings():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    bookings = admin.get_all_bookings()
    result = [
        {
            "id": b.id,
            "school_id": b.school_id,
            "company_id": b.company_id,
            "date": b.date.isoformat() if b.date else None,
            "status": b.status
        }
        for b in bookings
    ]
    return jsonify(result), 200


# -------------------- GET AVAILABLE TIMES --------------------
@admin_dp.route("/available_times", methods=["GET"])
@AdminDetails.admin_required
def get_available_times():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    times = admin.get_available_times()
    result = [
        {
            "id": t.id,
            "company_id": t.company_id,
            "start_time": t.start_time.isoformat(),
            "end_time": t.end_time.isoformat(),
            "is_booked": t.is_booked
        }
        for t in times
    ]
    return jsonify(result), 200


# -------------------- CANCEL BOOKING --------------------
@admin_dp.route("/bookings/<int:booking_id>/cancel", methods=["PATCH"])
@AdminDetails.admin_required
def cancel_booking(booking_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    success = admin.cancel_booking(booking_id)
    if not success:
        return jsonify({"error": "Booking not found or failed to cancel"}), 404

    return jsonify({"message": f"Booking {booking_id} successfully cancelled"}), 200


# # -------------------- REFRESH ACCESS TOKEN (ADMIN) --------------------
# @admin_dp.route("/token/refresh", methods=["POST"])
# @AdminDetails.admin_required
# def refresh_admin_access_token():
#     new_access_token = admin.refresh_admin_access_token()

#     if not new_access_token:
#         return jsonify({"error": "Invalid or unauthorized refresh token"}), 403

#     return jsonify({
#         "access_token": new_access_token,
#         "message": "New admin access token generated"
#     }), 200



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


