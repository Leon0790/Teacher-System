from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = "secret"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)

# ---------- MODELS ---------- #

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(100))
    text = db.Column(db.String(500))

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500))

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student = db.Column(db.String(100))
    subject = db.Column(db.String(50))
    marks = db.Column(db.Integer)

# ---------- AUTH ---------- #

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["email"] = user.email
            session["is_admin"] = user.is_admin
            return redirect("/dashboard")

    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect("/")

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- DASHBOARD ---------- #

@app.route("/dashboard")
def dashboard():
    if "email" not in session:
        return redirect("/")
    return render_template("dashboard.html", user=session["email"])

# ---------- CHAT ---------- #

@app.route("/chat", methods=["GET","POST"])
def chat():
    if "email" not in session:
        return redirect("/")

    if request.method == "POST":
        msg = request.form["message"]
        db.session.add(Message(user=session["email"], text=msg))
        db.session.commit()

    messages = Message.query.all()
    return render_template("chat.html", messages=messages)

# ---------- PERFORMANCE ---------- #

@app.route("/performance", methods=["GET","POST"])
def performance():
    if request.method == "POST":
        db.session.add(Score(
            student=request.form["student"],
            subject=request.form["subject"],
            marks=int(request.form["marks"])
        ))
        db.session.commit()

    scores = Score.query.all()
    return render_template("performance.html", scores=scores)

@app.route("/chart-data")
def chart_data():
    scores = Score.query.all()
    data = {}
    for s in scores:
        data[s.student] = data.get(s.student, 0) + s.marks

    return {"labels": list(data.keys()), "values": list(data.values())}

# ---------- REPORT ---------- #

@app.route("/report", methods=["GET","POST"])
def report():
    if request.method == "POST":
        db.session.add(Report(text=request.form["report"]))
        db.session.commit()
    return render_template("report.html")

# ---------- ADMIN ---------- #

@app.route("/admin")
def admin():
    if not session.get("is_admin"):
        return "Access denied"

    return render_template(
        "admin.html",
        scores=Score.query.all(),
        messages=Message.query.all(),
        reports=Report.query.all()
    )

# ---------- RUN ---------- #

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(email="admin@gmail.com").first():
            admin = User(
                email="admin@gmail.com",
                password=generate_password_hash("admin123"),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()

    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)
