import io
import re
import os
from typing import Dict, Any
from pathlib import Path
# Text Extractors
from pdfminer.high_level import extract_text
import docx  # Requires: pip install python-docx
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from groq import Groq
from dotenv import load_dotenv
# Load environment variables — try multiple locations for robustness
def _load_env_key(key_name: str) -> str | None:
    """Read a key from .env file robustly — handles BOM, quotes, and Windows line endings."""
    search_paths = [
        Path(__file__).parent / "config.env",
        Path.cwd() / "config.env",
    ]
    for env_path in search_paths:
        if env_path.exists():
            with open(env_path, encoding="utf-8-sig") as f:  # utf-8-sig strips Windows BOM
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, _, v = line.partition("=")
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k == key_name and v:
                            os.environ[key_name] = v  # inject into env so os.getenv works too
                            return v
    # Final fallback: system environment variable
    return (os.environ.get(key_name) or "").strip() or None
# Match Streamlit pattern: try plain load_dotenv first, then manual parse as fallback
load_dotenv("config.env")
api_key = os.getenv("GROQ_API_KEY") or _load_env_key("GROQ_API_KEY")
ats_model = None
def get_model():
    global ats_model
    if ats_model is None:
        ats_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return ats_model
# ---------- Helper Functions ----------
def extract_file_text(file_bytes: bytes, filename: str) -> str:
    """Extracts text from PDF, DOCX, or TXT files provided as bytes."""
    ext = filename.lower().split('.')[-1]
    
    try:
        if ext == 'pdf':
            return extract_text(io.BytesIO(file_bytes))
            
        elif ext in ['docx', 'doc']:
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join([para.text for para in doc.paragraphs])
            
        elif ext == 'txt':
            return file_bytes.decode('utf-8', errors='ignore')
            
        else:
            raise ValueError(f"Unsupported file extension: .{ext}")
    except Exception as e:
        raise ValueError(f"Error extracting text from {ext.upper()}: {str(e)}")
def calculate_similarity_bert(text1: str, text2: str) -> float:
    """Calculates cosine similarity between two texts using SentenceTransformers."""
    model = get_model()
    bindings1 = model.encode([text1])
    bindings2 = model.encode([text2])
    similarity = cosine_similarity(bindings1, bindings2)[0][0]
    return float(similarity)
def get_report(resume: str, job_desc: str) -> str:
    """Generates an AI evaluation report using Groq."""
    if not api_key:
        return "⚠️ **AI Engine Offline (Missing GROQ_API_KEY)**\n\nThe AI Assessment module requires an active Groq Developer Key to run deep semantic analytics. Please set your `GROQ_API_KEY` environment variable in the root folder.\n\nThe native ATS Score above was calculated locally using SentenceTransformers and remains fully active!"
    client = Groq(api_key=api_key)
    prompt = f"""
    # Context:
    - You are an AI Resume Analyzer, you will be given Candidate's resume and Job Description of the role he is applying for.
    # Instruction:
    - Analyze candidate's resume based on the possible points that can be extracted from job description,and give your evaluation on each point with the criteria below:  
    - Consider all points like required skills, experience,etc that are needed for the job role.
    - Calculate the score to be given (out of 5) for every point based on evaluation at the beginning of each point with a detailed explanation.  
    - If the resume aligns with the job description point, mark it with ✅ and provide a detailed explanation.  
    - If the resume doesn't align with the job description point, mark it with ❌ and provide a reason for it.  
    - If a clear conclusion cannot be made, use a ⚠️ sign with a reason.  
    - The Final Heading should be "Suggestions to improve your resume:" and give where and what the candidate can improve to be selected for that job role.
    # Inputs:
    Candidate Resume: {resume}
    ---
    Job Description: {job_desc}
    # Output:
    - Each any every point should be given a score (example: 3/5 ). 
    - Mention the scores and  relevant emoji at the beginning of each point and then explain the reason.
    """
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0,
        top_p=1,
    )
    return chat_completion.choices[0].message.content
def extract_scores(text: str) -> list[float]:
    """Extracts numerical score matches (X/5) from the text."""
    pattern = r'(\d+(?:\.\d+)?)/5'
    matches = re.findall(pattern, text)
    scores = [float(match) for match in matches]
    return scores
# ---------- Main Analyzer Function ----------
def analyze_resume(resume_bytes: bytes, filename: str, job_desc: str) -> Dict[str, Any]:
    """
    Main function to analyze a resume against a job description.
    Expected to be called from a FastAPI backend route.
    
    Args:
        resume_bytes (bytes): The bytes content of the uploaded document.
        filename (str): Original filename to determine extension (.pdf, .docx, .txt).
        job_desc (str): The raw text of the job description.
        
    Returns:
        dict: containing the ATS score, AI evaluation score, and the full generation report.
    """
    # 1. Extract text from the file (handles routing for PDF, DOCX, TXT)
    resume_text = extract_file_text(resume_bytes, filename)
    
    # 2. Calculate ATS Score
    ats_score = calculate_similarity_bert(resume_text, job_desc)
    
    # 3. Generate Report
    report = get_report(resume_text, job_desc)
    
    # 4. Extract AI Scores and calculate average
    report_scores = extract_scores(report)
    if len(report_scores) > 0:
        avg_score = sum(report_scores) / (5 * len(report_scores))
    else:
        avg_score = 0.0
        
    return {
        "ats_score": round(ats_score, 4),
        "ai_score": round(avg_score, 4),
        "report": report
    }