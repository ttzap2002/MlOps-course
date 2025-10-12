from fastapi import FastAPI
from homework.inference import load_model
import homework.inference as inference
from sentence_transformers import SentenceTransformer
from homework.api.models.transormers import PredictResponse, PredictRequest

app = FastAPI()

try:
    model_classifier = load_model("model/classifier.joblib")
    sentence_model = SentenceTransformer("model/sentence_transformer.model")
except FileNotFoundError:
    raise FileNotFoundError("filed does not exist")


@app.get("/")
def welcome_root():
    return {"message": "Welcome to the ML API"}


@app.post("/predict")
def predict(request: PredictRequest) -> PredictResponse:
    print(request.text == request.dict()["text"])
    prediction = inference.predict(model_classifier, sentence_model, request.text)
    return PredictResponse(prediction=prediction)
