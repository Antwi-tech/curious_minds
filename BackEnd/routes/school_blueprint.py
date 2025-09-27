from flask import Blueprint, jsonify, request
from repositories.schools import SchoolDetails
from sqlalchemy.exc import SQLAlchemyError

school_dp = Blueprint("school", __name__)  
school = SchoolDetails()

# Register / add a school
@school_dp.route("/register", methods=['POST'])   
def register_school():
    data = request.get_json()
    required_fields = [
        "school_name", "email", "password", "school_address",
        "region", "contact_person", "phone_number", "description"
    ]

    # Check for missing fields
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    try:
        new_school = school.add_school(
            school_name=data["school_name"],
            email=data["email"],
            password=data["password"],
            school_address=data["school_address"],
            region=data["region"],
            contact_person=data["contact_person"],
            phone_number=data["phone_number"],
            description=data["description"],
            website=data.get("website"),
           
        )

        if new_school:
            return jsonify({
                "message": "School registered successfully",
                "school": {
                    "school_id": new_school.school_id,
                    "school_name": new_school.school_name,
                    "email": new_school.email,
                    "school_address": new_school.school_address,
                    "region": new_school.region,
                    "contact_person": new_school.contact_person,
                    "phone_number": new_school.phone_number,
                    "website": new_school.website,
                    "description": new_school.description,
                    "is_verified": new_school.is_verified,   # default False
                    "is_active": new_school.is_active       # default True
                }
            }), 201
        else:
            return jsonify({"error": "School with this email already exists."}), 409

    except SQLAlchemyError as e:
        return jsonify({"error": f"Database error occurred: {e}"}), 500
