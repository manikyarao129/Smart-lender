import os
import random
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier

try:
    from xgboost import XGBClassifier
except ImportError:  # pragma: no cover
    XGBClassifier = GradientBoostingClassifier

from predict import FEATURE_COLUMNS, CATEGORICAL_COLUMNS, NUMERIC_COLUMNS

ROOT = Path(__file__).resolve().parent
DATASET_PATH = ROOT / "dataset" / "loan_dataset.csv"
MODEL_PATH = ROOT / "model.pkl"
XGBOOST_MODEL_PATH = ROOT / "models" / "xgboost_model.pkl"


def create_dataset(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    random.seed(42)
    rows = []
    for index in range(500):
        gender = random.choice(["Male", "Female"])
        married = random.choice(["Yes", "No"])
        dependents = random.choice(["0", "1", "2", "3+"])
        education = random.choice(["Graduate", "Not Graduate"])
        self_employed = random.choice(["Yes", "No"])
        applicant_income = random.randint(1000, 18000)
        coapplicant_income = random.randint(0, 6000)
        loan_amount = random.randint(80, 500)
        loan_term = random.choice([120, 180, 240, 360])
        credit_history = random.choice([0, 1])
        property_area = random.choice(["Urban", "Semiurban", "Rural"])

        score = 0.0
        score += 0.05 if gender == "Male" else 0.0
        score += 0.08 if married == "Yes" else 0.0
        score += 0.04 if dependents in ["0", "1"] else 0.0
        score += 0.06 if education == "Graduate" else 0.0
        score += 0.05 if self_employed == "No" else 0.0
        score += 0.001 if applicant_income < 10000 else 0.0
        score += 0.001 if coapplicant_income > 1000 else 0.0
        score += 0.001 if loan_amount < 250 else 0.0
        score += 0.002 if loan_term >= 360 else 0.0
        score += 0.10 if credit_history == 1 else 0.0
        score += 0.04 if property_area == "Urban" else 0.0

        loan_status = 1 if random.random() < min(0.92, max(0.18, score)) else 0
        rows.append(
            {
                "Gender": gender,
                "Married": married,
                "Dependents": dependents,
                "Education": education,
                "Self_Employed": self_employed,
                "ApplicantIncome": applicant_income,
                "CoapplicantIncome": coapplicant_income,
                "LoanAmount": loan_amount,
                "Loan_Amount_Term": loan_term,
                "Credit_History": credit_history,
                "Property_Area": property_area,
                "Loan_Status": loan_status,
            }
        )

    pd.DataFrame(rows).to_csv(path, index=False)


def load_dataset(path: Path):
    if not path.exists():
        create_dataset(path)
    data = pd.read_csv(path)
    data["Loan_Status"] = data["Loan_Status"].astype(int)
    return data


def build_pipeline(model):
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), NUMERIC_COLUMNS),
            ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), CATEGORICAL_COLUMNS),
        ]
    )
    return Pipeline([("preprocessor", preprocessor), ("classifier", model)])


def evaluate_model(model, X_train, X_test, y_train, y_test):
    pipeline = build_pipeline(model)
    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "precision": round(float(precision_score(y_test, predictions, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, predictions, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, predictions, zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
    }
    return pipeline, metrics


def train_and_save():
    data = load_dataset(DATASET_PATH)
    X = data[FEATURE_COLUMNS]
    y = data["Loan_Status"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    models = {
        "Decision Tree": DecisionTreeClassifier(max_depth=4, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=120, random_state=42),
        "KNN": KNeighborsClassifier(n_neighbors=5),
        "XGBoost": XGBClassifier(n_estimators=120, max_depth=3, learning_rate=0.1, random_state=42),
    }

    results = {}
    best_pipeline = None
    best_metrics = None
    for name, model in models.items():
        pipeline, metrics = evaluate_model(model, X_train, X_test, y_train, y_test)
        results[name] = metrics
        if best_metrics is None or metrics["f1"] > best_metrics["f1"]:
            best_metrics = metrics
            best_pipeline = pipeline

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    XGBOOST_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_pipeline, MODEL_PATH)
    joblib.dump(best_pipeline, XGBOOST_MODEL_PATH)
    return results, best_metrics


if __name__ == "__main__":
    results, best_metrics = train_and_save()
    print("Training complete.")
    print("Best metrics:", best_metrics)
    print("All results:")
    for name, metrics in results.items():
        print(name, metrics)
