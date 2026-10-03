from app.services.database import get_db_connection
from app.services.auth import hash_password

username = "admin"
password = "admin123"
role = "Admin"

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute(
    """
    INSERT INTO users (username, password_hash, role)
    VALUES (%s, %s, %s)
    ON CONFLICT (username) DO NOTHING
    """,
    (username, hash_password(password), role)
)

conn.commit()
cursor.close()
conn.close()

print("User created successfully")
