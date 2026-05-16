from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from repositories.companies import CompanyDetails
from sqlalchemy.exc import SQLAlchemyError
from datetime import timedelta

company_dp = Blueprint("company", __name__)
company = CompanyDetails()


# Regiater a Company 

@company_dp.route("/register", methods=["POST"])
def register_company():
    data = request.get_json()
    required_fields = ["company_name", "email", "password", "contact_person", "company_address", "region", "phone_number", "description", "industry_type"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        new_company = company.register_company(
            company_name=data["company_name"],
            email=data["email"],
            password=data["password"],
            company_address=data["company_address"],
            region=data["region"],
            contact_person=data["contact_person"],
            phone_number=data["phone_number"],
            description=data["description"],
            industry_type=data["industry_type"],
            website=data.get("website"),
        )
        if new_company:
            return jsonify({
                "message": "Company registered successfully",
                "company": {
                    "company_id": new_company.company_id,
                    "company_name": new_company.company_name,
                    "email": new_company.email,
                    "industry_type": new_company.industry_type,
                    "is_verified": new_company.is_verified,
                    "is_active": new_company.is_active
                }
            }), 201
        else:
            return jsonify({"error": "Company with this email already exists."}), 409

    except SQLAlchemyError as e:
        return jsonify({"error": f"Database error occurred: {e}"}), 500


# Compnay Login
@company_dp.route("/login", methods=["POST"])
def login_company():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    logged_in_company = company.login_company(email, password)
    if not logged_in_company:
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(
        identity=str(logged_in_company.company_id),
        additional_claims={"role": "company"},
        expires_delta=timedelta(hours=1)
    )
    refresh_token = create_refresh_token(
        identity=str(logged_in_company.company_id),
        additional_claims={"role": "company"},
        expires_delta=timedelta(days=30)
    )

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "company": {
            "company_id": logged_in_company.company_id,
            "company_name": logged_in_company.company_name,
            "email": logged_in_company.email,
            "is_verified": logged_in_company.is_verified
        }
    }), 200


# Refresh Token  - Not sure if it is being used in the frontend but it is here if needed
@company_dp.route("/token/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_access_token():
    identity = get_jwt_identity()
    access_token = create_access_token(
        identity=identity,
        additional_claims={"role": "company"},
        expires_delta=timedelta(hours=1)
    )
    return jsonify({"access_token": access_token}), 200


# Change Password 
@company_dp.route("/change_password/<int:company_id>", methods=["PATCH"])
@CompanyDetails.company_required
def change_password(company_id):
    current_user_id = int(get_jwt_identity())  
    if current_user_id != company_id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return jsonify({"error": "Old and new passwords are required"}), 400

    success = company.change_password(company_id, old_password, new_password)
    if not success:
        return jsonify({"error": "Password change failed"}), 400
    return jsonify({"message": "Password updated successfully"}), 200


#  Get Company Profile 
@company_dp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    company_id = int(get_jwt_identity())  
    company_data = company.get_profile(company_id)
    if not company_data:
        return jsonify({"error": "Company not found"}), 404
    return jsonify({
        "company_id": company_data.company_id,
        "company_name": company_data.company_name,
        "email": company_data.email,
        "industry_type": company_data.industry_type,
        "company_address": company_data.company_address,
        "region": company_data.region,
        "contact_person": company_data.contact_person,
        "phone_number": company_data.phone_number,
        "website": company_data.website,
        "description": company_data.description,
        "is_verified": company_data.is_verified,
        "is_active": company_data.is_active
    }), 200


#  Get Company Slots 
@company_dp.route("/slots", methods=["GET"])
@jwt_required()
def get_company_slots():
    company_id = int(get_jwt_identity()) 
    slots = company.get_slots(company_id)
    return jsonify({
        "count": len(slots),
        "slots": [
            {
                "schedule_id": s.schedule_id,
                "company_id": s.company_id,
                "start_date": s.start_date.isoformat(),
                "end_date": s.end_date.isoformat(),
                "created_at": s.created_at.isoformat()
            } for s in slots
        ]
    }), 200


#  Create company Slot 
@company_dp.route("/slots", methods=["POST"])
@jwt_required()
def create_slot():
    company_id = int(get_jwt_identity())  
    data = request.get_json()

    start_date = data.get("start_date")
    end_date = data.get("end_date")

    if not start_date or not end_date:
        return jsonify({"error": "start_date and end_date are required"}), 400

    slot = company.create_slot(company_id, start_date, end_date)
    if not slot:
        return jsonify({"error": "Failed to create slot or overlapping slot exists"}), 400

    return jsonify({
        "message": "Slot created successfully",
        "slot": {
            "schedule_id": slot.schedule_id,
            "company_id": slot.company_id,
            "start_date": slot.start_date.isoformat(),
            "end_date": slot.end_date.isoformat()
        }
    }), 201


#  Delete Slot
@company_dp.route("/slots/<int:schedule_id>", methods=["DELETE"])
def delete_slot(schedule_id):
    company_id = int(get_jwt_identity())  
    success = company.delete_slot(company_id, schedule_id)
    if not success:
        return jsonify({"error": "Slot not found or unauthorized"}), 404
    return jsonify({"message": "Slot deleted successfully"}), 200

# -------------------- Update Company Profile --------------------
@company_dp.route("/profile", methods=["PATCH"])
@jwt_required()
def update_profile():
    company_id = int(get_jwt_identity())
    data = request.get_json()

    updatable_fields = [
        "company_name", "email", "industry_type", "company_address",
        "region", "contact_person", "phone_number", "website", "description"
    ]

    updates = {k: data[k] for k in updatable_fields if k in data}

    updated = company.update_profile(company_id, **updates)
    if not updated:
        return jsonify({"error": "Company not found"}), 404

    return jsonify({
        "message": "Profile updated successfully",
        "company": {
            "company_id": updated.company_id,
            "company_name": updated.company_name,
            "email": updated.email,
            "industry_type": updated.industry_type,
            "company_address": updated.company_address,
            "region": updated.region,
            "contact_person": updated.contact_person,
            "phone_number": updated.phone_number,
            "website": updated.website,
            "description": updated.description,
        }
    }), 200

# Get Company Bookings 
@company_dp.route("/bookings", methods=["GET"])
@jwt_required()
def get_company_bookings():
    company_id = int(get_jwt_identity())
    bookings = company.get_bookings(company_id)
    return jsonify({
        "count": len(bookings),
        "bookings": bookings  # already serialized as dicts
    }), 200


# -------------------- Approve Booking --------------------
@company_dp.route("/bookings/<int:booking_id>/approve", methods=["PATCH"])
@jwt_required()
def approve_booking(booking_id):
    company_id = int(get_jwt_identity()) 
    success = company.update_booking_status(company_id, booking_id, "confirmed")
    if not success:
        return jsonify({"error": "Booking not found or unauthorized"}), 404
    return jsonify({"message": "Booking confirmed successfully"}), 200


# -------------------- Reject Booking --------------------
@company_dp.route("/bookings/<int:booking_id>/reject", methods=["PATCH"])
@jwt_required()
def reject_booking(booking_id):
    company_id = int(get_jwt_identity()) 
    success = company.update_booking_status(company_id, booking_id, "cancelled")
    if not success:
        return jsonify({"error": "Booking not found or unauthorized"}), 404
    return jsonify({"message": "Booking rejected successfully"}), 200