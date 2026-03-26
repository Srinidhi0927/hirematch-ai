from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from pydantic import BaseModel
import sqlite3
import hashlib
from analyzer import analyze_resume # Importing the backend module we created earlier

# -------- INIT APP --------
app = FastAPI()

# -------- CORS (VERY IMPORTANT) --------
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, # Fixed illegal overlap natively
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "users.db"


# -------- DATABASE --------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username, email, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?, ?, ?)",
                  (username, email, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verify_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == hash_password(password)


# -------- REQUEST MODELS --------
class LoginRequest(BaseModel):
    username: str
    password: str


class SignupRequest(BaseModel):
    username: str
    email: str
    password: str


# -------- ROUTES --------
@app.post("/login")
def login(data: LoginRequest):
    if verify_user(data.username, data.password):
        return {"status": "success"}
    return {"status": "error", "message": "Invalid credentials"}


@app.post("/signup")
def signup(data: SignupRequest):
    if create_user(data.username, data.email, data.password):
        return {"status": "success"}
    return {"status": "error", "message": "User already exists"}


# -------- ANALYZER ROUTE --------
@app.post("/analyze")
async def analyze_endpoint(
    resume: UploadFile = File(...),
    job_desc: str = Form(...)
):
    """
    Endpoint to receive a resume PDF file and a job description string,
    then run them through the AI Resume Analyzer backend pipeline.
    """
    if not resume.filename.endswith((".pdf", ".txt", ".docx")):
        raise HTTPException(status_code=400, detail="Invalid file format. Only PDF, TXT, and DOCX are supported.")
        
    try:
        # Read the file contents as bytes
        resume_bytes = await resume.read()
        
        # Pass exactly the parameters our analyzer.py core logic expects, including the filename mapping
        result = analyze_resume(resume_bytes, resume.filename, job_desc)
        
        return {
            "status": "success",
            "data": result
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Return generic processing error alongside what failed
        raise HTTPException(status_code=500, detail=f"Server Analysis Error: {str(e)}")

# -------- START SERVER NATIVELY --------
if __name__ == "__main__":
    import uvicorn
    # Allows you to just click the "Play" button in VSCode to start the FastAPI server!
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)