from flask import Flask, render_template, request, redirect, session
import sqlite3, subprocess

app = Flask(__name__)
app.secret_key = "supersecretkey123"

def run_java(deadline):
    try:
        output = subprocess.check_output(["java", "TaskHelper", deadline])
        return output.decode().strip()
    except:
        return "Low"

# LOGIN
# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        # Connect to DB safely
        try:
            con = sqlite3.connect("database.db")
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pwd))
            data = cur.fetchone()
            con.close()
        except:
            return "Error connecting to database. Make sure database.db is uploaded!"

        if data:
            session["user"] = user
            return redirect("/home")   # 👈 This is where successful login goes
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


# HOME PAGE
# HOME PAGE
@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/")

    try:
        con = sqlite3.connect("database.db")
        cur = con.cursor()
        cur.execute("SELECT * FROM tasks")
        tasks = cur.fetchall()
        con.close()
    except:
        return "Error loading tasks. Make sure 'tasks' table exists in database.db!"

    return render_template("index.html", tasks=tasks, user=session["user"])

# ADD TASK
@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    deadline = request.form["deadline"]
    priority = run_java(deadline)

    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("INSERT INTO tasks (name, deadline, priority) VALUES (?, ?, ?)", (name, deadline, priority))
    con.commit()
    con.close()
    return redirect("/home")

# EDIT TASK
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    con = sqlite3.connect("database.db")
    cur = con.cursor()

    if request.method == "POST":
        name = request.form["name"]
        deadline = request.form["deadline"]
        priority = run_java(deadline)
        cur.execute("UPDATE tasks SET name=?, deadline=?, priority=? WHERE id=?", (name, deadline, priority, id))
        con.commit()
        con.close()
        return redirect("/home")

    cur.execute("SELECT * FROM tasks WHERE id=?", (id,))
    task = cur.fetchone()
    con.close()
    return render_template("edit.html", task=task)

# DELETE
@app.route("/delete/<int:id>")
def delete(id):
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("DELETE FROM tasks WHERE id=?", (id,))
    con.commit()
    con.close()
    return redirect("/home")

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)





