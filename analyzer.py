import io
import re
import os
from typing import Dict, Any
from pathlib import Path

# Text Extractors
from pdfminer.high_level import extract_text
import docx  # Requires: pip install python-docx
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

# Global Groq Client Cache
groq_client = None

def get_groq_client():
    global groq_client
    if groq_client is None:
        groq_client = Groq(api_key=api_key, timeout=60)
    return groq_client

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

def extract_ats(text: str) -> float:
    """Extracts ATS_MATCH score from the Groq response."""
    match = re.search(r"ATS_MATCH:\s*(\d+)", text)
    if match:
        return float(match.group(1)) / 100
    return 0.0

def extract_scores(text: str) -> list[float]:
    """Extracts numerical score matches (X/5) from the text."""
    pattern = r'(\d+(?:\.\d+)?)/5'
    matches = re.findall(pattern, text)
    scores = [float(match) for match in matches]
    return scores

def get_report(resume: str, job_desc: str) -> str:
    """Generates an AI evaluation report using Groq."""
    if not api_key:
        return "⚠️ **AI Engine Offline (Missing GROQ_API_KEY)**\n\nThe AI Assessment module requires an active Groq Developer Key to run deep semantic analytics. Please set your `GROQ_API_KEY` environment variable in the root folder."
    
    client = get_groq_client()
    prompt = f"""
You are an expert-level AI Resume Evaluation Engine designed to perform deep semantic 
analysis across ALL professional domains including engineering, medicine, research, law, 
finance, design, fashion, academia, and emerging fields.

Your objective is to determine how well the candidate matches the job description using 
holistic reasoning, not just keyword overlap.

You must analyze dynamically — do NOT limit evaluation to fixed categories.

==================================================
PRIMARY OBJECTIVE
==================================================

Evaluate the resume against the job description using:

• semantic understanding
• transferable skills reasoning
• implied experience inference
• role seniority alignment
• domain expertise depth
• industry-specific expectations
• responsibility overlap
• measurable achievements
• skill maturity
• contextual relevance
• career progression consistency
• specialization relevance
• risk factors (missing critical requirements)
• overqualification detection
• adaptability potential

==================================================
ATS SCORE REQUIREMENT (CRITICAL)
==================================================

At the very top return:

ATS_MATCH: <0-100>

This must be computed using:

• semantic similarity
• requirement coverage
• experience relevance
• skill depth
• domain alignment
• transferable competencies
• seniority match
• missing critical requirements penalty

This should simulate a REAL ATS system.

==================================================
ANALYSIS FORMAT
==================================================

You must:

• Automatically determine evaluation dimensions
• Create as many sections as needed
• Score each section out of 5
• Provide deep reasoning

Use format:

<Dimension Name> — Score: X/5 [emoji]
Explanation...

Emoji Rules:
✅ Strong Match
⚠️ Partial Match
❌ Missing or Weak

==================================================
DEEP ANALYSIS REQUIREMENTS
==================================================

Your reasoning must:

• infer implied skills
• detect synonyms
• consider equivalent experience
• consider domain crossover skills
• evaluate leadership signals
• assess impact metrics
• identify missing requirements
• detect resume strengths not explicitly requested
• identify hidden gaps

==================================================
FINAL SECTION (MANDATORY)
==================================================

Suggestions to Improve Resume:

Provide:
• missing skills
• missing experience
• formatting improvements
• stronger keywords
• role-specific improvements
• measurable achievement suggestions

==================================================
INPUTS
==================================================

Candidate Resume:
{resume}

--------------------------------------

Job Description:
{job_desc}

==================================================
OUTPUT RULES
==================================================

• Start with ATS_MATCH
• Use dynamic evaluation sections
• Be highly analytical
• Be professional
• Avoid repetition
• Work for ANY profession
• Provide realistic ATS percentage
"""
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0,
        top_p=1,
    )
    return chat_completion.choices[0].message.content

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
    
    # 2. Generate Report (includes ATS_MATCH score from Groq)
    report = get_report(resume_text, job_desc)
    
    # 3. Extract ATS Score from Groq response
    ats_score = extract_ats(report)
    
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