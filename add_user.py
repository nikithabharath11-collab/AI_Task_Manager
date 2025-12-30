import sqlite3

con = sqlite3.connect("database.db")
cur = con.cursor()
cur.execute("INSERT INTO users (username, password) VALUES (?,?)", ("admin","admin123"))
con.commit()
con.close()
print("User Created: username = admin, password = admin123")
