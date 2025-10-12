import joblib

CLASS_MAPPING = {
    0: "negative",
    1: "neutral",
    2: "positive",
}


def load_model(model_path: str):
    return joblib.load(model_path)


def predict(classification_model, sentence_model, text: str) -> str:
    embedding = sentence_model.encode([text])
    predicted_class_id = int(classification_model.predict(embedding)[0])
    prediction = CLASS_MAPPING[predicted_class_id]
    return prediction
