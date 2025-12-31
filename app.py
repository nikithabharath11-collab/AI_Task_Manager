from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2, os

app = Flask(__name__)
app.secret_key = "super_secure_key_123"

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL)

# ---------- ROUTES ---------- #

# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        roll = request.form["roll"]
        hashed = generate_password_hash(password)

        conn = get_db()
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username TEXT UNIQUE, password TEXT, roll TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS tasks (id SERIAL PRIMARY KEY, user_id INTEGER, name TEXT, deadline TEXT, priority TEXT)")
        conn.commit()

        try:
            cur.execute("INSERT INTO users (username, password, roll) VALUES (%s, %s, %s)", (username, hashed, roll))
            conn.commit()
        except:
            return render_template("register.html", error="❌ Username already exists!")

        cur.close()
        conn.close()
        return redirect("/")
    
    return render_template("register.html")


# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, password FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            session["username"] = username
            return redirect("/home")
        else:
            return render_template("login.html", error="❌ Invalid username or password")

    return render_template("login.html")


# HOME (USER DASHBOARD)
@app.route("/home")
def home():
    if "user_id" not in session:
        return redirect("/")
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, deadline, priority FROM tasks WHERE user_id=%s ORDER BY id DESC", (session["user_id"],))
    tasks = cur.fetchall()
    conn.close()

    return render_template("index.html", tasks=tasks, user=session["username"])


# ADD TASK
@app.route("/add", methods=["POST"])
def add():
    if "user_id" not in session:
        return redirect("/")

    name = request.form["name"]
    deadline = request.form["deadline"]
    priority = request.form["priority"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (user_id, name, deadline, priority) VALUES (%s, %s, %s, %s)",
                (session["user_id"], name, deadline, priority))
    conn.commit()
    conn.close()

    return redirect("/home")


# EDIT TASK
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if request.method == "POST":
        name = request.form["name"]
        deadline = request.form["deadline"]
        priority = request.form["priority"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE tasks SET name=%s, deadline=%s, priority=%s WHERE id=%s AND user_id=%s",
                    (name, deadline, priority, id, session["user_id"]))
        conn.commit()
        conn.close()
        return redirect("/home")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name, deadline, priority FROM tasks WHERE id=%s AND user_id=%s", (id, session["user_id"]))
    task = cur.fetchone()
    conn.close()

    return render_template("edit.html", task=task)


# DELETE TASK
@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=%s AND user_id=%s", (id, session["user_id"]))
    conn.commit()
    conn.close()

    return redirect("/home")


# FORGOT PASSWORD (Reset Page - Local Reset)
@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        username = request.form["username"]
        new_pass = generate_password_hash(request.form["password"])

        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password=%s WHERE username=%s", (new_pass, username))
        conn.commit()
        conn.close()

        return redirect("/")
    return render_template("forgot.html")


# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run()
