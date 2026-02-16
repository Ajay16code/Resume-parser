from __future__ import annotations

import fitz
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from model_loader import load_classifier
from ranking_engine import build_feature_vector, cosine_similarity_score
from skill_extractor import extract_skills, infer_title, summarize_text
from resume_parser import parse_resume_text, ats_check
from pdf_report_generator import DatasetAnalysisReportGenerator

app = FastAPI(title="AI Candidate Intelligence Engine", version="1.0.0")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict:
    """Health check endpoint"""
    return {"status": "ok"}


@app.on_event("startup")
def startup_event() -> None:
    logger.info("Loading embedding model...")
    app.state.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    logger.info("Loading classifier...")
    app.state.classifier = load_classifier()
    logger.info("Startup complete!")


def _extract_pdf_text(file_bytes: bytes) -> str:
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            return "\n".join(page.get_text("text") for page in doc).strip()
    except Exception as exc:  # pragma: no cover - parser edge-cases
        raise HTTPException(status_code=400, detail="Invalid PDF file.") from exc


def _predict(resume_text: str, job_description: str) -> dict:
    model = app.state.embedding_model
    classifier = app.state.classifier

    resume_embedding = model.encode(resume_text)
    job_embedding = model.encode(job_description)

    features = build_feature_vector(
        np.array(resume_embedding), np.array(job_embedding)
    )

    prediction = int(classifier.predict(features)[0])

    if hasattr(classifier, "predict_proba"):
        confidence = float(classifier.predict_proba(features)[0][prediction])
    else:
        confidence = 0.0

    similarity = cosine_similarity_score(
        np.array(resume_embedding), np.array(job_embedding)
    )

    return {
        "prediction": "Fit" if prediction == 1 else "Not Fit",
        "confidence_score": confidence,
        "similarity_score": similarity,
        "resume_skills": extract_skills(resume_text),
        "job_skills": extract_skills(job_description),
        "profile_title": infer_title(resume_text) or infer_title(job_description),
        "resume_summary": summarize_text(resume_text, max_chars=400),
    }


@app.post("/analyze")
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
) -> dict:
    if resume.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Upload a PDF file.")

    resume_text = _extract_pdf_text(await resume.read())
    if not resume_text:
        raise HTTPException(status_code=400, detail="No extractable text found in PDF.")

    return _predict(resume_text=resume_text, job_description=job_description)


@app.post("/parse_resume")
async def parse_resume_endpoint(resume: UploadFile = File(...), job_description: str = Form("")) -> dict:
    """Parse uploaded PDF and return structured resume fields for review dashboard."""
    if resume.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Upload a PDF file.")

    text = _extract_pdf_text(await resume.read())
    if not text:
        raise HTTPException(status_code=400, detail="No extractable text found in PDF.")

    parsed = parse_resume_text(text)
    # enrich with inferred title and skills
    parsed["inferred_title"] = infer_title(text) or parsed.get("title")
    parsed["skills"] = extract_skills(text)
    # run ATS-style checks (optional job description helps compute overlap)
    parsed["ats"] = ats_check(text, job_description)
    return parsed


class TextAnalyzeRequest(BaseModel):
    resume_text: str
    job_description: str


@app.post("/analyze_text")
async def analyze_text(req: TextAnalyzeRequest) -> dict:
    """Lightweight NLP fallback endpoint that accepts raw text (no PDF upload).

    Useful for testing and for environments where PDF parsing or the classifier
    may not be available. Returns the same structure as `/analyze`.
    """
    if not req.resume_text.strip() or not req.job_description.strip():
        raise HTTPException(status_code=400, detail="Both resume_text and job_description are required.")

    return _predict(resume_text=req.resume_text, job_description=req.job_description)


@app.get("/download_dataset_report")
def download_dataset_report():
    """
    Download dataset analysis report as PDF
    
    Returns:
        PDF file with detailed analysis of sample_dataset.csv
    """
    try:
        # Get absolute path to CSV file relative to project root
        backend_dir = Path(__file__).parent
        csv_path = backend_dir.parent / "data" / "sample_dataset.csv"
        
        if not csv_path.exists():
            raise FileNotFoundError(f"Dataset file not found at {csv_path}")
        
        generator = DatasetAnalysisReportGenerator(str(csv_path))
        pdf_bytes = generator.generate_pdf()
        
        # Return as downloadable file
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=dataset_analysis_report.pdf"}
        )
    except Exception as exc:
        logger.error(f"Error generating report: {str(exc)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating PDF report: {str(exc)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
