from flask import Flask, render_template, request, redirect, session, url_for
import psycopg2, os
from psycopg2.extras import RealDictCursor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "super_secure_secret"

def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require", cursor_factory=RealDictCursor)

# ---------- DATABASE SETUP ----------
con = get_db()
cur = con.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    roll TEXT,
    password TEXT NOT NULL
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS tasks(
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name TEXT NOT NULL,
    deadline DATE NOT NULL,
    priority TEXT NOT NULL
);
""")
con.commit(); cur.close(); con.close()

# ---------- ROUTES ----------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        db = get_db(); cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s",(user,))
        account = cur.fetchone()

        if account and check_password_hash(account["password"], pwd):
            session["user_id"] = account["id"]
            session["username"] = user
            return redirect("/home")

        return render_template("login.html", error="Invalid credentials ❌")

    return render_template("login.html")


@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        user = request.form["username"]
        roll = request.form["roll"]
        pwd = generate_password_hash(request.form["password"])

        db = get_db(); cur = db.cursor()
        try:
            cur.execute("INSERT INTO users(username,roll,password) VALUES(%s,%s,%s)",(user, roll, pwd))
            db.commit()
            return redirect("/")
        except:
            return render_template("register.html", error="Username already exists ⚠️")

    return render_template("register.html")


@app.route("/forgot", methods=["GET","POST"])
def forgot():
    if request.method == "POST":
        return "Password reset link (feature placeholder)."
    return render_template("forgot.html")


@app.route("/home", methods=["GET","POST"])
def home():
    if "user_id" not in session:
        return redirect("/")

    db = get_db(); cur = db.cursor()
    cur.execute("SELECT * FROM tasks WHERE user_id=%s",(session["user_id"],))
    tasks = cur.fetchall()
    return render_template("home.html", tasks=tasks, today=date.today())


@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    deadline = request.form["deadline"]
    priority = request.form["priority"]

    db = get_db(); cur = db.cursor()
    cur.execute("INSERT INTO tasks(user_id,name,deadline,priority) VALUES(%s,%s,%s,%s)",
                (session["user_id"], name, deadline, priority))
    db.commit()
    return redirect("/home")


@app.route("/delete/<int:id>")
def delete(id):
    db = get_db(); cur = db.cursor()
    cur.execute("DELETE FROM tasks WHERE id=%s AND user_id=%s",(id, session["user_id"]))
    db.commit()
    return redirect("/home")


@app.route("/edit/<int:id>", methods=["GET","POST"])
def edit(id):
    db = get_db(); cur = db.cursor()
    
    if request.method == "POST":
        cur.execute("UPDATE tasks SET name=%s, deadline=%s, priority=%s WHERE id=%s AND user_id=%s",
            (request.form["name"], request.form["deadline"],
            request.form["priority"], id, session["user_id"]))
        db.commit()
        return redirect("/home")

    cur.execute("SELECT * FROM tasks WHERE id=%s AND user_id=%s",(id, session["user_id"]))
    task = cur.fetchone()
    return render_template("edit.html", task=task)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run()
