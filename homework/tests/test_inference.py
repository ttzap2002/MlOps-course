from fastapi.testclient import TestClient
from homework.app import app
import pytest

client = TestClient(app)


def test_welcome_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the ML API"}


def test_empty_input():
    invalid_input = {"text": ""}
    response = client.post("/predict", json=invalid_input)
    assert response.status_code == 422


def test_valid_input():
    valid_input = {"text": "Valid input"}
    response = client.post("/predict", json=valid_input)
    assert response.status_code == 200


def test_json_output():
    valid_input = {"text": "Valid input"}
    response = client.post("/predict", json=valid_input)
    assert isinstance(response.json(), dict)


def test_sentences():
    positive_sentence = {"text": "That was really exciting"}
    response = client.post("/predict", json=positive_sentence)
    assert response.json() == {"prediction": "positive"}

    negative_sentence = {"text": "You are wrong"}
    response = client.post("/predict", json=negative_sentence)
    assert response.json() == {"prediction": "negative"}

    neutral_sentence = {"text": "This is a cat"}
    response = client.post("/predict", json=neutral_sentence)
    assert response.json() == {"prediction": "neutral"}


def test_invalidtype_check_json_response():
    invalid_value = {"text": 4.55}
    response = client.post("/predict", json=invalid_value)
    assert response.status_code == 422

    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)
    assert any(
        "Input should be a valid string" in err.get("msg", "") for err in data["detail"]
    )


def test_model_load_success():
    try:
        import homework.app

        assert homework.app.model_classifier is not None
        assert homework.app.sentence_model is not None

    except FileNotFoundError:
        pytest.fail("Initialization Error: No model files found in expected paths")
    except Exception as e:
        pytest.fail(f"Unexpected error while loading models: {e}")
