from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from repositories.companies import CompanyDetails
from sqlalchemy.exc import SQLAlchemyError
from datetime import timedelta

company_dp = Blueprint("company", __name__) #, url_prefix="/company") 
company = CompanyDetails()


# -------------------- Register Company --------------------
@company_dp.route("/register", methods=["POST"])
def register_company():
    data = request.get_json()
    required_fields = ["company_name", "email", "password", "contact_person","company_address","region", "phone_number", "description", "industry_type"]

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
            return jsonify({"error": "School with this email already exists."}), 409

    except SQLAlchemyError as e:
        return jsonify({"error": f"Database error occurred: {e}"}), 500
        

# -------------------- Login Company --------------------
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
        identity={"id": logged_in_company.company_id, "role": "company"},
        expires_delta=timedelta(hours=1)
    )
    refresh_token = create_refresh_token(
        identity={"id": logged_in_company.company_id, "role": "company"},
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


# -------------------- Refresh Token --------------------
@company_dp.route("/token/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_access_token():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity, expires_delta=timedelta(hours=1))
    return jsonify({"access_token": access_token}), 200

# -------------------- Change Password --------------------
@company_dp.route("/change_password/<int:company_id>", methods=["PATCH"])
@CompanyDetails.company_required
def change_password(company_id):
    current_user = get_jwt_identity()
    if current_user["id"] != company_id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    success = company.change_password(company_id, old_password, new_password)
    if not success:
        return jsonify({"error": "Password change failed"}), 400
    return jsonify({"message": "Password updated successfully"}), 200

# -------------------- Get Profile --------------------
# @company_dp.route("/profile", methods=["GET"])
# def get_profile():
#     identity = get_jwt_identity()
#     company = company.get_profile(identity["id"])
#     if not company:
#         return jsonify({"error": "Company not found"}), 404

#     return jsonify({
#         "company_id": company.company_id,
#         "company_name": company.company_name,
#         "email": company.email,
#         "contact_person": company.contact_person,
#         "phone_number": company.phone_number,
#         "description": company.description,
#         "website": company.website,
#         "is_verified": company.is_verified,
#         "is_active": company.is_active
#     }), 200




# # -------------------- Get All Companies --------------------
# @company_dp.route("/companies", methods=["GET"])            
# def get_all_companies():
#     try:
#         region = request.args.get("region")
#         is_active = request.args.get("is_active")

#         # Convert query param "is_active" to boolean if provided
#         if is_active is not None:
#             is_active = is_active.lower() in ["true", "1", "yes"]

#         companies = company.get_all_companies(region=region, is_active=is_active)

#         return jsonify({
#             "count": len(companies),
#             "companies": [
#                 {
#                     "company_id": c.company_id,
#                     "company_name": c.company_name,
#                     "email": c.email,
#                     "region": c.region,
#                     "industry_type": c.industry_type,
#                     "is_active": c.is_active,
#                     "is_verified": c.is_verified
#                 } for c in companies
#             ]
#         }), 200

#     except Exception as e:
#         return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500