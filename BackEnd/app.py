from flask import Flask, jsonify , request
from routes.school_blueprint import school_dp
from repositories import schools


app = Flask(__name__)
app.register_blueprint(school_dp, url_prefix='/school')

school = schools.SchoolDetails()
@app.route("/")
def home():
    return "Welcome Curious Minds "
@app.route("/status")
def status():
    return jsonify({"status": "API is running"}), 200   


if __name__ == "__main__":
    app.run(debug=True, port=5000)