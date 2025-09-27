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
