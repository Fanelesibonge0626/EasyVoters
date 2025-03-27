import sqlite3

# Connect to SQLite database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Create candidates table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        election_type TEXT NOT NULL,
        party TEXT NOT NULL,
        votes INTEGER DEFAULT 0
    )
''')

# Commit and close
conn.commit()
conn.close()

print("Database initialized successfully!")
