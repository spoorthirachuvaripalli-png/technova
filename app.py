from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
import random

app = Flask(__name__)
app.secret_key = "hackathon_secret"

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["adaptive_assesment"]
questions_collection = db["questions"]

# ----------------------------
# Route 1: Home Page
# ----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        session["score"] = 0
        session["difficulty"] = 2   # Start with Medium
        session["question_count"] = 0
        session["responses"] = []
        return redirect("/quiz")
    return render_template("index.html")


# ----------------------------
# Route 2: Quiz Page
# ----------------------------
@app.route("/quiz", methods=["GET", "POST"])
def quiz():

    if "question_count" not in session:
        return redirect("/")

    if request.method == "POST":
        selected_option = request.form.get("option")
        correct_answer = session["current_answer"]
        current_topic = session["current_topic"]

        session["question_count"] += 1

        # Adaptive Logic
        if selected_option == correct_answer:
            session["score"] += 1
            session["difficulty"] = min(3, session["difficulty"] + 1)
            result = "correct"
        else:
            session["difficulty"] = max(1, session["difficulty"] - 1)
            result = "wrong"

        session["responses"].append({
            "topic": current_topic,
            "result": result
        })

        if session["question_count"] >= 5:
            return redirect("/result")

    # Get new question
    difficulty = session["difficulty"]
    questions = list(questions_collection.find({"difficulty": difficulty}))
    question = random.choice(questions)

    session["current_answer"] = question["answer"]
    session["current_topic"] = question["topic"]

    return render_template("quiz.html", question=question)


# ----------------------------
# Route 3: Result Page
# ----------------------------
@app.route("/result")
def result():

    responses = session["responses"]
    topic_performance = {}

    for r in responses:
        topic = r["topic"]
        if topic not in topic_performance:
            topic_performance[topic] = {"correct": 0, "total": 0}
        topic_performance[topic]["total"] += 1
        if r["result"] == "correct":
            topic_performance[topic]["correct"] += 1

    mastery = {}
    for topic, data in topic_performance.items():
        percentage = (data["correct"] / data["total"]) * 100
        if percentage >= 80:
            level = "Master"
        elif percentage >= 60:
            level = "Intermediate"
        else:
            level = "Beginner"
        mastery[topic] = level

    return render_template("result.html",
                           score=session["score"],
                           mastery=mastery)


if __name__ == "__main__":
    app.run(debug=True)