import sqlite3

# Make sure you connect to the exact same file you're checking in DB Browser
conn = sqlite3.connect("brand_insights.db")  # <-- check spelling here
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    website TEXT NOT NULL
)
""")

# Insert test row
cursor.execute("INSERT INTO brands (name, website) VALUES (?, ?)", 
               ("Test Brand", "https://testbrand.com"))

# Commit changes
conn.commit()

# Fetch all rows to verify
cursor.execute("SELECT * FROM brands")
rows = cursor.fetchall()
print("Data in brands table:")
for row in rows:
    print(row)

conn.close()
