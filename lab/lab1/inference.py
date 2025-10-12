import joblib
import numpy as np


def load_model(filename: str):
    return joblib.load(filename)


def predict(model, input_data: list) -> str:
    target_names = model["target_names"]
    prediction_model = model["model"]

    prediction = prediction_model.predict(np.array(input_data).reshape(1, -1))
    prediction_index = prediction[0]

    return target_names[prediction_index]
