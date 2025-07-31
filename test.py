import sqlite3
conn = sqlite3.connect('backend/smartfile_ai.db')
conn.execute("PRAGMA foreign_keys = ON")
print(conn.execute("SELECT * FROM folders").fetchall())
print(conn.execute("SELECT * FROM files").fetchall())
print(conn.execute("SELECT * FROM document_chunks").fetchall())