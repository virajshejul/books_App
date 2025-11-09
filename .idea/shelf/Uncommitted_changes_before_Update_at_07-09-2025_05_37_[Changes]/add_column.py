import sqlite3

conn = sqlite3.connect('books.db')
c = conn.cursor()
c.execute("ALTER TABLE books ADD COLUMN added_by INTEGER")
conn.commit()
conn.close()