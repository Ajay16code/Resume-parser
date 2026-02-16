"""Quick setup script to create a dummy classifier for testing."""
from pathlib import Path
import joblib
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import numpy as np

# Create models directory if it doesn't exist
models_dir = Path(__file__).resolve().parents[1] / "models"
models_dir.mkdir(exist_ok=True)

# Create a simple pipeline classifier
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('classifier', LogisticRegression(random_state=42, max_iter=1000))
])

# Train on dummy data
X_dummy = np.random.randn(100, 512)  # Dummy feature vectors
y_dummy = np.random.randint(0, 2, 100)  # Binary classification
pipeline.fit(X_dummy, y_dummy)

# Save the model
model_path = models_dir / "resume_classifier.pkl"
joblib.dump(pipeline, model_path)

print(f"ℹ️ Dummy classifier created at: {model_path}")
print("✅ Model setup complete! You can now run the backend.")
