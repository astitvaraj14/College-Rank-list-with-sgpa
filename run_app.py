import os
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient

app = Flask(__name__)

MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["university_db"]
students_col = db["students"]

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/leaderboard')
def leaderboard():
    if students_col is None:
        connect_db()

    students = list(students_col.find({}, {'_id': 0}))
    students.sort(key=lambda x: x.get('total_marks', 0), reverse=True)

    for i, s in enumerate(students):
        s['rank'] = i + 1

    return jsonify({
        "status": "success",
        "data": students
    })




if __name__ == "__main__":
    app.run()
