import psycopg2
import os
import hashlib
def get_conn():
    return psycopg2.connect(
        os.getenv("DATABASE_URL"),
        sslmode="require"
    )
def init_db():
    """
    Initializes the PostgreSQL 'users' table if it doesn't already exist.
    Called from app.py on startup.
    """
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
def hash_password(password):
    """
    Deterministic SHA-256 hash for secure password storage.
    """
    return hashlib.sha256(password.encode()).hexdigest()
def create_user(username, email, password):
    """
    Inserts a new user into the PostgreSQL database.
    Returns True if successful, False if the username is taken.
    """
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username, email, hash_password(password))
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Signup Error: {str(e)}")
        return False
    finally:
        conn.close()
def verify_user(username, password):
    """
    Verifies a login attempt by comparing hashed passwords in PostgreSQL.
    """
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute(
            "SELECT password FROM users WHERE username = %s",
            (username,)
        )
        result = c.fetchone()
        return result and result[0] == hash_password(password)
    except Exception as e:
        print(f"Login Error: {str(e)}")
        return False
    finally:
        conn.close()
