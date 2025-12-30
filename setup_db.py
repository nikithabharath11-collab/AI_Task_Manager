import sqlite3

con = sqlite3.connect("database.db")
cur = con.cursor()

# Create Users Table
cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT);")

# Insert default login user
cur.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ("admin", "admin"))

# Create Tasks Table
cur.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    deadline TEXT NOT NULL,
    priority TEXT NOT NULL
);
""")

con.commit()
con.close()
print("✔ Database Ready | Login: admin / admin")
