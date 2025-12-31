from flask import Flask, render_template, request, redirect, session, send_file
import os, psycopg2, subprocess
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecret123")

# ---------------- DATABASE SETUP ---------------- #
def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=RealDictCursor)

conn = get_db()
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    roll TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS tasks(
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name TEXT NOT NULL,
    deadline TEXT NOT NULL,
    priority TEXT NOT NULL
);
""")

conn.commit()
cur.close()
conn.close()
print("🟢 Database Ready with PostgreSQL!")


# -------- JAVA PRIORITY CHECK (Optional) -------- #
def run_java(deadline):
    try:
        out = subprocess.check_output(["java", "TaskHelper", deadline])
        return out.decode().strip()
    except:
        return "Low"

# ---------------- REGISTER ---------------- #
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        roll = request.form["roll"]
        pwd = generate_password_hash(request.form["password"])

        db = get_db()
        cur = db.cursor()

        cur.execute("SELECT * FROM users WHERE username=%s OR roll=%s",(username, roll))
        if cur.fetchone():
            return render_template("register.html", error="⚠ Username or Roll No already taken")

        cur.execute("INSERT INTO users(username, roll, password) VALUES(%s,%s,%s)",
                    (username, roll, pwd))
        db.commit()
        cur.close(); db.close()
        return redirect("/")
    return render_template("register.html")

# ---------------- LOGIN ---------------- #
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        pwd = request.form["password"]

        db = get_db(); cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s",(username,))
        user = cur.fetchone()
        cur.close(); db.close()

        if user and check_password_hash(user["password"], pwd):
            session["user_id"] = user["id"]
            session["user_name"] = user["username"]
            return redirect("/home")
        return render_template("login.html", error="❌ Incorrect username or password")

    return render_template("login.html")

# ---------------- FORGOT PASSWORD ---------------- #
@app.route("/forgot", methods=["GET","POST"])
def forgot():
    if request.method == "POST":
        roll = request.form["roll"]
        newpwd = generate_password_hash(request.form["password"])

        db = get_db(); cur = db.cursor()
        cur.execute("UPDATE users SET password=%s WHERE roll=%s",(newpwd, roll))
        db.commit(); cur.close(); db.close()
        return redirect("/")
    return render_template("forgot.html")

# ---------------- HOME / TASK LIST ---------------- #
@app.route("/home")
def home():
    if "user_id" not in session:
        return redirect("/")

    db = get_db(); cur = db.cursor()
    cur.execute("SELECT * FROM tasks WHERE user_id=%s",(session["user_id"],))
    tasks = cur.fetchall()
    cur.close(); db.close()

    return render_template("index.html", user=session["user_name"], tasks=tasks)

# ---------------- ADD TASK ---------------- #
@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    deadline = request.form["deadline"]
    priority = run_java(deadline)

    db = get_db(); cur = db.cursor()
    cur.execute("INSERT INTO tasks(user_id, name, deadline, priority) VALUES(%s,%s,%s,%s)",
                (session["user_id"], name, deadline, priority))
    db.commit(); cur.close(); db.close()
    return redirect("/home")

# ---------------- PDF EXPORT ---------------- #
@app.route("/export")
def export_pdf():
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT name, deadline, priority FROM tasks WHERE user_id=%s",(session["user_id"],))
    data = cur.fetchall()
    cur.close(); db.close()

    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    table = Table([["Task", "Deadline", "Priority"]] + data)
    
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.black),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("BOX", (0,0), (-1,-1), 2, colors.darkblue),
        ("GRID", (0,0), (-1,-1), 1, colors.grey),
        ("FONT", (0,0), (-1,0), "Helvetica-Bold"),
    ]))

    pdf.build([table])
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="StudyManager_Report.pdf")

# ---------------- LOGOUT ---------------- #
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- RUN APP ---------------- #
if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
