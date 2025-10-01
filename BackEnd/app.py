from datetime import timedelta
import os
from flask import Flask, jsonify , request
from routes.school_blueprint import school_dp
from repositories import schools
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv


load_dotenv()
app = Flask(__name__)

# JWT configuration
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
jwt = JWTManager(app)


app.register_blueprint(school_dp, url_prefix='/school')
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)  # short-lived access token
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)    # refresh token valid for 30 days

school = schools.SchoolDetails()
@app.route("/")
def home():
    return "Welcome Curious Minds "
@app.route("/status")
def status():
    return jsonify({"status": "API is running"}), 200   


if __name__ == "__main__":
    app.run(debug=True, port=5000)