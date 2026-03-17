from flask import Flask, render_template, request
import joblib
import mysql.connector
import os
import matplotlib.pyplot as plt

# Template folder
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)

# Load ML model
model = joblib.load("model.pkl")

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="shikha",
    database="learning_path_db"
)
cursor = db.cursor()

@app.route("/", methods=["GET", "POST"])
def index():
    prediction = None
    recommendation = None
    graph_path = None  # initialize graph path

    if request.method == "POST":
        hours = int(request.form["hours"])
        scores = int(request.form["scores"])
        extra = request.form["extra"]  # 'Yes' or 'No'
        sleep = int(request.form["sleep"])
        papers = int(request.form["papers"])

        # --- Predict Performance Index ---
        extra_model = 1 if extra == "Yes" else 0
        pred = model.predict([[hours, scores, extra_model, sleep, papers]])
        prediction = round(pred[0], 2)

        # --- Save to Database ---
        cursor.execute("""
            INSERT INTO student_performance (
                hours_studied,
                previous_scores,
                extracurricular_activities,
                sleep_hours,
                sample_question_papers_practiced,
                performance_index
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (hours, scores, extra, sleep, papers, prediction))
        db.commit()

        # --- Generate Recommendations ---
        if prediction < 50:
            recommendation = ["Basic Math Quiz", "Simple Logic"]
        elif prediction < 80:
            recommendation = ["Aptitude Test", "Python Basics"]
        else:
            recommendation = ["DSA Advanced", "Machine Learning Basics"]

        # --- Plot Graph for Current Input Only ---
        hours_data = [hours]
        perf_data = [prediction]

        plt.figure(figsize=(6,4))
        plt.bar(hours_data, perf_data, color='skyblue')
        plt.title("Hours Studied vs Predicted Performance Index")
        plt.xlabel("Hours Studied")
        plt.ylabel("Performance Index")
        plt.ylim(0, 100)
        plt.grid(True, axis='y')

        # Save graph in static folder
        if not os.path.exists("static"):
            os.makedirs("static")
        graph_path = "static/performance_graph.png"
        plt.savefig(graph_path)
        plt.close()

    return render_template(
        "index.html",
        prediction=prediction,
        recommendation=recommendation,
        graph_path=graph_path
    )

if __name__ == "__main__":
    app.run(debug=True)