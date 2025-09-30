from flask import Blueprint, jsonify, request
from repositories.schools import SchoolDetails
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
    
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
    
# search for school by school name
@school_dp.route("/search_school", methods=["GET"])
def get_school():
    try:
        search_term = request.args.get("q", "").strip()
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))

        if not search_term:
            return jsonify({"error": "Search query parameter 'q' is required"}), 400

        results, total = school.search_school(search_term, page, limit)

        if not results:
            return jsonify({"message": "No schools found"}), 404

        return jsonify({
            "schools": [
                {
                    "school_id": s.school_id,
                    "school_name": s.school_name,
                    "email": s.email,
                    "school_address": s.school_address,
                    "region": s.region,
                    "contact_person": s.contact_person,
                    "phone_number": s.phone_number,
                    "website": s.website,
                    "description": s.description,
                }
                for s in results
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total_results": total,
                "total_pages": (total + limit - 1) // limit
            },
            "message": "Schools found successfully"
        }), 200

    except ValueError:
        return jsonify({"error": "Invalid pagination parameters"}), 400
    except Exception as e:
        return jsonify({
            "error": "An unexpected error occurred",
            "details": str(e)
        }), 500


# delete school by id
@school_dp.route("/delete/<int:school_id>", methods=["DELETE"])
def delete_school(school_id):
    try:
        deleted = school.delete_school(school_id)

        if not deleted:
            return jsonify({"error": "School not found"}), 404

        return jsonify({
            "message": "School deleted successfully",
            "deleted_school": {
                "school_id": deleted.school_id,
                "school_name": deleted.school_name,
                "email": deleted.email
            }
        }), 200

    except Exception as e:
        return jsonify({
            "error": "An unexpected error occurred",
            "details": str(e)
        }), 500


# School Login
@school_dp.route("/school/login", methods=["POST"])
def login_school():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        school = school.login_school(email, password)
        if not school:
            return jsonify({"error": "Invalid credentials or inactive account"}), 401

        return jsonify({
            "message": "Login successful",
            "school": {
                "school_id": school.school_id,
                "school_name": school.school_name,
                "email": school.email,
                "region": school.region,
                "is_active": school.is_active
            }
        }), 200
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


# change password with athentication
@school_dp.route("/change_password/<int:school_id>", methods=["PATCH"])
@jwt_required()
def change_password(school_id):
    current_user_id = get_jwt_identity()

    if current_user_id != school_id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return jsonify({"error": "Both old and new passwords are required"}), 400

    success = school.change_password(school_id, old_password, new_password)
    if success:
        return jsonify({"message": "Password updated successfully"}), 200
    return jsonify({"error": "Failed to update password. Check old password."}), 400

# Get All Schools
@school_dp.route("/schools", methods=["GET"])
def get_all_schools():
    try:
        region = request.args.get("region")
        is_active = request.args.get("is_active")

        # Convert query param "is_active" to boolean if provided
        if is_active is not None:
            is_active = is_active.lower() in ["true", "1", "yes"]

        schools = school.get_all_schools(region=region, is_active=is_active)

        return jsonify({
            "count": len(schools),
            "schools": [
                {
                    "school_id": s.school_id,
                    "school_name": s.school_name,
                    "email": s.email,
                    "region": s.region,
                    "is_active": s.is_active,
                    "is_verified": s.is_verified
                } for s in schools
            ]
        }), 200

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500
