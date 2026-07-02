from pathlib import Path

import joblib
import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "Gender",
    "Married",
    "Dependents",
    "Education",
    "Self_Employed",
    "ApplicantIncome",
    "CoapplicantIncome",
    "LoanAmount",
    "Loan_Amount_Term",
    "Credit_History",
    "Property_Area",
]

CATEGORICAL_COLUMNS = [
    "Gender",
    "Married",
    "Dependents",
    "Education",
    "Self_Employed",
    "Property_Area",
]

NUMERIC_COLUMNS = [
    "ApplicantIncome",
    "CoapplicantIncome",
    "LoanAmount",
    "Loan_Amount_Term",
    "Credit_History",
]


class HeuristicLoanModel:
    def predict(self, frame):
        predictions = []
        for _, row in frame.iterrows():
            score = 0.0
            if row.get("Credit_History") == 1:
                score += 0.35
            if row.get("Education") == "Graduate":
                score += 0.15
            if row.get("Married") == "Yes":
                score += 0.12
            if row.get("Property_Area") == "Urban":
                score += 0.1
            income_ratio = float(row.get("ApplicantIncome", 0)) / max(1.0, float(row.get("LoanAmount", 0)))
            if income_ratio > 20:
                score += 0.12
            if float(row.get("ApplicantIncome", 0)) < 3000:
                score -= 0.15
            if float(row.get("LoanAmount", 0)) > 300:
                score -= 0.1
            predictions.append(1 if score >= 0.35 else 0)
        return np.array(predictions)

    def predict_proba(self, frame):
        predictions = self.predict(frame)
        output = []
        for pred in predictions:
            if pred == 1:
                output.append([0.2, 0.8])
            else:
                output.append([0.8, 0.2])
        return np.array(output)


def build_feature_frame(payload):
    data = {column: payload.get(column, "") for column in FEATURE_COLUMNS}
    for column in NUMERIC_COLUMNS:
        value = payload.get(column)
        if value in (None, ""):
            data[column] = 0
        else:
            data[column] = float(value)
    if "Credit_History" in payload and isinstance(payload["Credit_History"], str):
        data["Credit_History"] = float(payload["Credit_History"])
    frame = pd.DataFrame([data], columns=FEATURE_COLUMNS)
    return frame


def get_prediction_result(payload, model=None, model_path="model.pkl"):
    if model is None:
        model_path = Path(model_path)
        if not model_path.exists():
            model = HeuristicLoanModel()
        else:
            model = joblib.load(model_path)

    frame = build_feature_frame(payload)
    probability = float(model.predict_proba(frame)[0][1])
    decision = int(model.predict(frame)[0])
    approved = decision == 1

    if approved:
        label = "Approved"
        if probability >= 0.9:
            risk = "Low"
            recommendation = "Strong candidate. Proceed with standard review."
        elif probability >= 0.75:
            risk = "Medium"
            recommendation = "Good candidate. Review supporting documents carefully."
        else:
            risk = "Medium"
            recommendation = "Candidate appears eligible but needs additional verification."
    else:
        label = "Rejected"
        if probability <= 0.25:
            risk = "High"
            recommendation = "High-risk profile. Consider improving financial credentials before reapplying."
        elif probability <= 0.45:
            risk = "Medium"
            recommendation = "Borderline profile. Recommend reviewing application details and repayment capacity."
        else:
            risk = "Medium"
            recommendation = "Application is likely to be declined; improve financial stability and repayment evidence."

    return {
        "prediction": label,
        "confidence": round(probability, 4),
        "risk": risk,
        "recommendation": recommendation,
    }
