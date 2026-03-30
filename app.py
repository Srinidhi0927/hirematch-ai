from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from pydantic import BaseModel
from analyzer import analyze_resume # Importing the backend module
from auth import init_db, create_user, verify_user # Moved database logic to auth.py
# -------- INIT APP --------
app = FastAPI()
# -------- CORS (VERY IMPORTANT) --------
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"],
)
# -------- DATABASE STARTUP --------
@app.on_event("startup")
def startup():
    """
    Called on FastAPI startup to ensure the users table is correctly initialized
    in whichever database auth.py is configured to use (PostgreSQL/SQLite).
    """
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print("Database init failed:", str(e))
    init_db()
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
    """
    Passes authentication logic to auth.py verify_user utility.
    """
    if verify_user(data.username, data.password):
        return {"status": "success"}
    return {"status": "error", "message": "Invalid credentials"}
@app.post("/signup")
def signup(data: SignupRequest):
    """
    Passes user creation logic to auth.py create_user utility.
    """
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
    Endpoint to receive a resume PDF/DOCX file and a job description string,
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
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)