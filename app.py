from fastapi import FastAPI
import inference
from inference import load_model
from api.models.iris import PredictResponse, PredictRequest

app = FastAPI()

try:
    model = load_model("trained_model.joblib")
except FileNotFoundError:
    print("Please run 'python training.py' first to create the model file.")
    raise FileNotFoundError("filed does not exist")


@app.get("/")
def welcome_root():
    return {"message": "Welcome to the ML API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/predict")
def predict(request: PredictRequest) -> PredictResponse:
    input_data = [
        request.sepal_length,
        request.sepal_width,
        request.petal_length,
        request.petal_width,
    ]
    prediction = inference.predict(model, input_data)

    return PredictResponse(prediction=prediction)
