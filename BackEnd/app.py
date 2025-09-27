from flask import Flask, jsonify , request
from BackEnd.repositories import schools
from repositories import *

app = Flask(__name__)
app.register_blueprint(schools.school_dp, url_prefix="/schools")

school = schools.SchoolDetails()
@app.route("/")
def home():
    return "Welcome to the School Management API"
@app.route("/status")
def status():
    return jsonify({"status": "API is running"}), 200   
