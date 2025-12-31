from flask import Flask, render_template, request, redirect, session
import os, subprocess
import psycopg2
from psycopg2.extras import RealDictCursor

# ------------------ FLASK SETUP ------------------
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")

# ------------------ DB CONNECT FUNCTION ------------------
def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=RealDictCursor)

# ------------------ CREATE TABLES ON STARTUP ------------------
try:
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
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
    print("🟢 PostgreSQL Database Ready!")

except Exception as e:
    print("❌ Database Setup Error:", e)


# ------------------ JAVA PRIORITY CHECK ------------------
def run_java(deadline):
    try:
        output = subprocess.check_output(["java", "TaskHelper", deadline])
        return output.decode().strip()
    except:
        return "Low"


# ------------------ REGISTER ------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        con = get_db()
        cur = con.cursor()

        # Check user exists
        cur.execute("SELECT * FROM users WHERE username=%s", (user,))
        if cur.fetchone():
            con.close()
            return render_template("register.html", error="⚠ Username already exists!")

        # Add new user
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (user, pwd))
        con.commit()
        con.close()
        return redirect("/")

    return render_template("register.html")


# ------------------ LOGIN ------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        con = get_db()
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (user, pwd))
        account = cur.fetchone()
        con.close()

        if account:
            session["user"] = account["id"]       # store user id
            session["username"] = account["username"]
            return redirect("/home")
        else:
            return render_template("login.html", error="❌ Invalid username or password")

    return render_template("login.html")


# ------------------ HOME / TASKS ------------------
@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/")

    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM tasks WHERE user_id=%s ORDER BY id DESC", (session["user"],))
    tasks = cur.fetchall()
    con.close()

    return render_template("index.html", tasks=tasks, user=session.get("username"))


# ------------------ ADD TASK ------------------
@app.route("/add", methods=["POST"])
def add():
    if "user" not in session:
        return redirect("/")

    name = request.form["name"]
    deadline = request.form["deadline"]
    priority = run_java(deadline)

    con = get_db()
    cur = con.cursor()
    cur.execute("INSERT INTO tasks (user_id, name, deadline, priority) VALUES (%s, %s, %s, %s)",
                (session["user"], name, deadline, priority))
    con.commit()
    con.close()

    return redirect("/home")


# ------------------ EDIT TASK ------------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if "user" not in session:
        return redirect("/")

    con = get_db()
    cur = con.cursor()

    if request.method == "POST":
        name = request.form["name"]
        deadline = request.form["deadline"]
        priority = run_java(deadline)
        cur.execute("UPDATE tasks SET name=%s, deadline=%s, priority=%s WHERE id=%s AND user_id=%s",
                    (name, deadline, priority, id, session["user"]))
        con.commit()
        con.close()
        return redirect("/home")

    cur.execute("SELECT * FROM tasks WHERE id=%s AND user_id=%s", (id, session["user"]))
    task = cur.fetchone()
    con.close()

    return render_template("edit.html", task=task)


# ------------------ DELETE TASK ------------------
@app.route("/delete/<int:id>")
def delete(id):
    if "user" not in session:
        return redirect("/")

    con = get_db()
    cur = con.cursor()
    cur.execute("DELETE FROM tasks WHERE id=%s AND user_id=%s", (id, session["user"]))
    con.commit()
    con.close()

    return redirect("/home")


# ------------------ LOGOUT ------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ------------------ RENDER / PRODUCTION SERVER ------------------
if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
