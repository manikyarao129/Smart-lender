import os
import sqlite3
from datetime import datetime
from io import BytesIO
from pathlib import Path

import joblib
from flask import Flask, flash, jsonify, make_response, redirect, render_template, request, session, url_for
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from werkzeug.security import check_password_hash, generate_password_hash

from predict import get_prediction_result

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "smart-lender-secret")
app.config["DATABASE"] = os.getenv("DATABASE_URL", "database.db")
app.config["MODEL_PATH"] = os.getenv("MODEL_PATH", "model.pkl")

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / app.config["DATABASE"] if not os.path.isabs(app.config["DATABASE"]) else Path(app.config["DATABASE"])
MODEL_PATH = BASE_DIR / app.config["MODEL_PATH"] if not os.path.isabs(app.config["MODEL_PATH"]) else Path(app.config["MODEL_PATH"])


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            prediction TEXT NOT NULL,
            confidence REAL NOT NULL,
            risk TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()

    admin = conn.execute("SELECT id FROM users WHERE username = ?", ("admin",)).fetchone()
    if not admin:
        conn.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
            ("admin", generate_password_hash("admin"), 1),
        )
        conn.commit()
    conn.close()


init_db()


def load_model():
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)


@app.context_processor
def inject_user():
    return {"logged_in": "user" in session, "username": session.get("user"), "is_admin": session.get("is_admin", 0)}


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Please provide both username and password.", "danger")
            return redirect(url_for("register"))
        conn = get_db()
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            flash("That username is already taken.", "warning")
            conn.close()
            return redirect(url_for("register"))
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        conn.commit()
        conn.close()
        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user"] = username
            session["is_admin"] = user["is_admin"]
            flash("You are now logged in.", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "danger")
        return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("is_admin", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


@app.route("/predict", methods=["GET", "POST"])
def predict():
    if request.method == "POST":
        data = {key: request.form.get(key, "") for key in [
            "Gender", "Married", "Dependents", "Education", "Self_Employed",
            "ApplicantIncome", "CoapplicantIncome", "LoanAmount", "Loan_Amount_Term",
            "Credit_History", "Property_Area"
        ]}
        if any(value in (None, "") for value in data.values()):
            flash("Please complete all required fields before submitting the form.", "danger")
            return render_template("predict.html", form_data=data)
        try:
            model = load_model()
            result = get_prediction_result(data, model=model)
            if "user" in session:
                conn = get_db()
                conn.execute(
                    "INSERT INTO predictions (username, prediction, confidence, risk, recommendation, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (session["user"], result["prediction"], result["confidence"], result["risk"], result["recommendation"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                )
                conn.commit()
                conn.close()
            return render_template("result.html", result=result, form_data=data)
        except Exception as exc:
            flash(f"Prediction error: {exc}", "danger")
            return render_template("predict.html", form_data=data)
    return render_template("predict.html", form_data={})


@app.route("/result")
def result():
    return redirect(url_for("predict"))


@app.route("/api/predict", methods=["POST"])
def api_predict():
    payload = request.get_json(silent=True) or {}
    model = load_model()
    result = get_prediction_result(payload, model=model)
    return jsonify(result)


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("Please log in to view the dashboard.", "warning")
        return redirect(url_for("login"))

    conn = get_db()
    predictions = conn.execute(
        "SELECT * FROM predictions WHERE username = ? ORDER BY id DESC LIMIT 10",
        (session["user"],),
    ).fetchall()
    total_predictions = conn.execute("SELECT COUNT(*) as count FROM predictions WHERE username = ?", (session["user"],)).fetchone()["count"]
    approved = conn.execute("SELECT COUNT(*) as count FROM predictions WHERE username = ? AND prediction = 'Approved'", (session["user"],)).fetchone()["count"]
    rejected = conn.execute("SELECT COUNT(*) as count FROM predictions WHERE username = ? AND prediction = 'Rejected'", (session["user"],)).fetchone()["count"]
    approval_rate = round((approved / total_predictions) * 100, 1) if total_predictions else 0.0
    conn.close()
    return render_template(
        "dashboard.html",
        predictions=predictions,
        total_predictions=total_predictions,
        approved=approved,
        rejected=rejected,
        approval_rate=approval_rate,
        model_accuracy=0.92,
    )


@app.route("/admin")
def admin_dashboard():
    if "user" not in session or not session.get("is_admin"):
        flash("Admin access is required.", "warning")
        return redirect(url_for("home"))
    conn = get_db()
    all_predictions = conn.execute("SELECT * FROM predictions ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    return render_template("admin.html", predictions=all_predictions)


@app.route("/download/csv")
def download_csv():
    if "user" not in session:
        flash("Please log in to download your history.", "warning")
        return redirect(url_for("login"))
    conn = get_db()
    rows = conn.execute("SELECT * FROM predictions WHERE username = ? ORDER BY id DESC", (session["user"],)).fetchall()
    conn.close()
    output = []
    output.append("id,username,prediction,confidence,risk,recommendation,created_at")
    for row in rows:
        output.append(
            f"{row['id']},{row['username']},{row['prediction']},{row['confidence']},{row['risk']},{row['recommendation']},{row['created_at']}"
        )
    response = make_response("\n".join(output))
    response.headers["Content-Disposition"] = "attachment; filename=smart_lender_history.csv"
    response.headers["Content-Type"] = "text/csv"
    return response


@app.route("/download/pdf")
def download_pdf():
    if "user" not in session:
        flash("Please log in to download a report.", "warning")
        return redirect(url_for("login"))
    conn = get_db()
    rows = conn.execute("SELECT * FROM predictions WHERE username = ? ORDER BY id DESC", (session["user"],)).fetchall()
    conn.close()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph("Smart Lender Prediction Report", styles["Title"]), Spacer(1, 12)]
    story.append(Paragraph(f"Prepared for: {session['user']}", styles["Heading2"]))
    story.append(Spacer(1, 12))
    for row in rows:
        story.append(Paragraph(f"- {row['created_at']} | {row['prediction']} | Confidence: {row['confidence']} | Risk: {row['risk']}", styles["BodyText"]))
        story.append(Spacer(1, 6))
    doc.build(story)
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=smart_lender_report.pdf"
    response.headers["Content-Type"] = "application/pdf"
    return response


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
