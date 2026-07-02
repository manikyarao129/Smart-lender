# Smart Lender

Smart Lender is a full-stack Flask application that predicts loan eligibility with an AI model and provides a polished banking-style experience.

## Features
- Responsive Bootstrap-based UI
- Loan prediction form and result page
- REST API endpoint for programmatic prediction
- User registration/login and dashboard
- SQLite-backed prediction history export
- Model training and pickling workflow

## Setup
1. Create a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Train the model: `python train_model.py`
4. Start the app: `python app.py`

## API Example
POST /api/predict with JSON payload:

```json
{
  "Gender": "Male",
  "Married": "Yes",
  "Dependents": "1",
  "Education": "Graduate",
  "Self_Employed": "No",
  "ApplicantIncome": 6000,
  "CoapplicantIncome": 2000,
  "LoanAmount": 150,
  "Loan_Amount_Term": 360,
  "Credit_History": 1,
  "Property_Area": "Urban"
}
```

## Deployment
The app is ready for deployment on Render, Railway, IBM Cloud, or Docker with environment variables such as `PORT`, `SECRET_KEY`, and `DATABASE_URL`.
