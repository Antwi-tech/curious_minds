from flask import Flask, jsonify , request
from BackEnd.repositories import schools
from repositories import *

app = Flask(__name__)
app.register_blueprint(schools.school_dp)

school = schools.SchoolDetails()
@app.route("/")
def home():
    return "Welcome"
@app.route("/status")
def status():
    return jsonify({"status": "API is running"}), 200   



if __name__ == "__main__":
    app.run(debug=True, port=5000) 
    