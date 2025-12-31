from flask import Flask, render_template, request, redirect, session
import psycopg2, os
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = "supersecurekey123"

# DATABASE CONNECTION
def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=RealDictCursor)

# ROUTES

@app.route("/")
def login_page():
    return render_template("login.html")

@app.route("/", methods=["POST"])
def login():
    user = request.form["username"]
    pwd = request.form["password"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=%s AND password=%s;", (user, pwd))
    account = cur.fetchone()
    conn.close()

    if account:
        session["user"] = account["id"]
        return redirect("/home")
    return render_template("login.html", error="❌ Invalid username or password")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]
        roll = request.form["rollno"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s;", (user,))
        exists = cur.fetchone()

        if exists:
            return render_template("register.html", error="⚠️ Username already taken!")

        cur.execute("INSERT INTO users(username,password,rollno) VALUES(%s,%s,%s);", (user,pwd,roll))
        conn.commit()
        conn.close()

        return redirect("/")
    
    return render_template("register.html")

@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/")
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE user_id=%s ORDER BY deadline ASC;", (session["user"],))
    tasks = cur.fetchall()
    conn.close()

    return render_template("index.html", tasks=tasks)

@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    deadline = request.form["deadline"]
    priority = request.form["priority"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks(user_id,name,deadline,priority) VALUES(%s,%s,%s,%s);",
                (session["user"], name, deadline, priority))
    conn.commit()
    conn.close()

    return redirect("/home")

@app.route("/edit/<id>", methods=["GET","POST"])
def edit(id):
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        deadline = request.form["deadline"]
        priority = request.form["priority"]
        cur.execute("UPDATE tasks SET name=%s, deadline=%s, priority=%s WHERE id=%s;",
                    (name, deadline, priority, id))
        conn.commit()
        conn.close()
        return redirect("/home")

    cur.execute("SELECT * FROM tasks WHERE id=%s;", (id,))
    task = cur.fetchone()
    conn.close()
    return render_template("edit.html", task=task)

@app.route("/delete/<id>")
def delete(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=%s;", (id,))
    conn.commit()
    conn.close()
    return redirect("/home")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
