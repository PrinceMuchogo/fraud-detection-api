import pandas as pd
import joblib
from typing import Dict

# Load the trained model
model_path = "saved_model/fraud_detection_rf.pkl"
model = joblib.load(model_path)

# Store the expected features from the trained model
expected_features = model.feature_names_in_

def preprocess_input(data: Dict) -> pd.DataFrame:
    df = pd.DataFrame([data])
    # One-hot encode categorical columns
    df = pd.get_dummies(df)
    
    # Add missing columns as zeroes
    missing_cols = set(expected_features) - set(df.columns)
    for col in missing_cols:
        df[col] = 0

    # Ensure the columns are in the same order as during training
    df = df[expected_features]
    return df


def predict_fraud(data: Dict) -> str:
    df = preprocess_input(data)
    prediction = model.predict(df)
    return "Fraud" if prediction[0] == 1 else "Not Fraud"


def predict_bulk_fraud(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = pd.get_dummies(dataframe)

    # Add missing columns as zeroes
    missing_cols = set(expected_features) - set(dataframe.columns)
    for col in missing_cols:
        dataframe[col] = 0

    # Ensure the columns are in the same order as during training
    dataframe = dataframe[expected_features]

    predictions = model.predict(dataframe)
    dataframe['prediction'] = ["Fraud" if pred == 1 else "Not Fraud" for pred in predictions]
    frauds = dataframe[dataframe['prediction'] == "Fraud"]
    return frauds
