from sklearn.datasets import load_iris
from sklearn.neighbors import KNeighborsClassifier

import joblib


def load_data():
    iris_data = load_iris()
    return iris_data.data, iris_data.target, iris_data.target_names


def train_model(x, y) -> None:
    knn_model = KNeighborsClassifier(n_neighbors=3)
    knn_model.fit(x, y)

    return knn_model


def save_model(model, filename: str) -> None:
    joblib.dump(model, f"{filename}.joblib")


if __name__ == "__main__":
    X, y, target_names = load_data()
    model = {"model": train_model(X, y), "target_names": target_names}
    save_model(model, "trained_model")
