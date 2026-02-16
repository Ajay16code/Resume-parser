"""Train and export a classifier using the sample dataset.

This script: 
- Loads `data/sample_dataset.csv` (expects columns: resume_text, job_description, label)
- Computes sentence embeddings using `SentenceTransformer('all-MiniLM-L6-v2')`
- Builds classifier features by concatenating resume and job embeddings
- Trains a `LogisticRegression` pipeline and saves to `models/resume_classifier.pkl`

Run:
    python train_model.py
"""
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sentence_transformers import SentenceTransformer
from ranking_engine import build_feature_vector

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "sample_dataset.csv"
MODEL_DIR = ROOT / "models"
MODEL_DIR.mkdir(exist_ok=True)
MODEL_PATH = MODEL_DIR / "resume_classifier.pkl"

print("Loading dataset:", DATA_PATH)
df = pd.read_csv(DATA_PATH)
if not {"resume_text", "job_description", "label"}.issubset(df.columns):
    raise SystemExit("Dataset must contain resume_text, job_description, label columns")

print("Loading embedding model (this may take a while)...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")

X = []
y = df["label"].astype(int).values
for idx, row in df.iterrows():
    resume_text = str(row["resume_text"])
    job_text = str(row["job_description"])
    # encode
    r_emb = embedder.encode(resume_text)
    j_emb = embedder.encode(job_text)
    feat = np.concatenate([r_emb, j_emb])
    X.append(feat)

X = np.vstack(X)
print("Feature shape:", X.shape)

pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", LogisticRegression(max_iter=2000))
])
print("Training classifier...")
pipeline.fit(X, y)

print("Saving model to:", MODEL_PATH)
joblib.dump(pipeline, MODEL_PATH)
print("Done.")
