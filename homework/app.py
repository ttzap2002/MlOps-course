from fastapi import FastAPI
from homework.inference import load_model
import homework.inference
from sentence_transformers import SentenceTransformer
from homework.api.models.transormers import PredictResponse, PredictRequest
from pathlib import Path

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent

try:
    model_path = BASE_DIR / "model" / "classifier.joblib"
    sentence_model_path = BASE_DIR / "model" / "sentence_transformer.model"

    model_classifier = load_model(model_path)
    sentence_model = SentenceTransformer(str(sentence_model_path))
except FileNotFoundError:
    raise FileNotFoundError("filed does not exist")


@app.get("/")
def welcome_root():
    return {"message": "Welcome to the ML API"}


@app.post("/predict")
def predict(request: PredictRequest) -> PredictResponse:
    prediction = homework.inference.predict(
        model_classifier, sentence_model, request.text
    )
    return PredictResponse(prediction=prediction)
