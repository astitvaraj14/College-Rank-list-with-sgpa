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

@app.route("/leaderboard")
def leaderboard():
    data = list(students_col.find({}, {"_id":0}).sort("total_marks",-1))
    for i,s in enumerate(data):
        s["rank"] = i+1
    return jsonify(data)

@app.route("/submit_result", methods=["POST"])
def submit_result():
    data = request.json
    usn = data["usn"]

    students_col.update_one({"usn":usn},{"$set":data},upsert=True)

    my_total = data["total_marks"]

    uni_rank = students_col.count_documents({"total_marks":{"$gt":my_total}})+1
    coll_rank = students_col.count_documents({
        "total_marks":{"$gt":my_total},
        "usn":{"$regex": f'^{usn[:3]}'}
    })+1

    return jsonify({"status":"success","uni_rank":uni_rank,"coll_rank":coll_rank})

if __name__ == "__main__":
    app.run()
