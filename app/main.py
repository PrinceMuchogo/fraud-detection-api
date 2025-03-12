from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import pandas as pd
from .detector import predict_fraud, predict_bulk_fraud
from .validate import validate_card

app = FastAPI()

# Single Transaction Prediction
class Transaction(BaseModel):
    trans_date_trans_time: str  # Add transaction date and time
    cc_num: str                 # Card number
    merchant: str               # Merchant
    category: str               # Transaction category
    amt: float                  # Amount
    first: str                  # First name
    last: str                   # Last name
    gender: str                 # Gender
    street: str                 # Street address
    city: str                   # City
    state: str                  # State
    zip: str                    # Zip code
    lat: float                  # Latitude
    long: float                 # Longitude
    city_pop: int               # City population
    job: str                    # Job
    dob: str                    # Date of birth
    trans_num: str              # Transaction number
    unix_time: float            # Unix time
    merch_lat: float            # Merchant latitude
    merch_long: float           # Merchant longitude
    exp_month: int              # Expiration month (required for card validation)
    exp_year: int               # Expiration year (required for card validation)
    cvv: str                    # CVV (required for card validation)
    is_fraud: Optional[bool] = None  # Optional fraud flag            # Fraud flag (for model prediction purposes)

@app.post("/predict/")
async def predict(transaction: Transaction):
    data = transaction.dict()

    # Validate the credit/debit card
    is_valid = validate_card(data["cc_num"], data["exp_month"], data["exp_year"], data["cvv"])
    if not is_valid:
        return {"prediction": "Fraud", "reason": "Invalid credit/debit card details"}

    # Predict fraud if card is valid
    prediction = predict_fraud(data)
    return {"prediction": prediction}

# Bulk Transaction Prediction
@app.post("/predict-bulk/")
async def predict_bulk(file: UploadFile = File(...)):
    try:
        dataframe = pd.read_csv(file.file)

        # Validate credit card details in the bulk data
        invalid_cards = []
        for index, row in dataframe.iterrows():
            is_valid = validate_card(
                str(row["cc_num"]), int(row["exp_month"]), int(row["exp_year"]), str(row["cvv"])
            )
            if not is_valid:
                invalid_cards.append(index)

        # Remove rows with invalid cards before predicting
        valid_data = dataframe.drop(invalid_cards)

        # Prevent passing an empty DataFrame to the model
        if valid_data.empty:
            return {
                "error": "No valid transactions found. All cards are invalid.",
                "invalid_cards": invalid_cards
            }

        # Make predictions on the valid data
        frauds = predict_bulk_fraud(valid_data)

        # Convert flagged frauds to a dictionary for the response
        frauds_dict = frauds.to_dict(orient="records")
        return {
            "fraudulent_transactions": frauds_dict,
            "invalid_cards": invalid_cards
        }

    except Exception as e:
        return {"error": str(e)}
