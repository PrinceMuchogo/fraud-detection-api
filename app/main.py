from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import pandas as pd
from .detector import predict_fraud, predict_bulk_fraud
from .validate import validate_card

from sqlalchemy.orm import Session
from fastapi import Depends
from .model import FraudTransaction
from .database import get_db
from datetime import datetime
from app.database import init_db
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event for startup and shutdown tasks."""
    init_db()  # Create tables if they don't exist
    yield  # Continue running the app

app = FastAPI(lifespan=lifespan)

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
    is_fraud: Optional[bool] = None  # Optional fraud flag

@app.get("/")
def home():
    return {"message": "Fraud Detection API is running!"}

@app.post("/predict/")
async def predict(transaction: Transaction, db: Session = Depends(get_db)):
    data = transaction.dict()

    # Validate the credit/debit card
    is_valid = validate_card(data["cc_num"], data["exp_month"], data["exp_year"], data["cvv"])
    if not is_valid:
        fraud_entry = FraudTransaction(
            trans_date_trans_time=datetime.strptime(data["trans_date_trans_time"], "%Y-%m-%d %H:%M:%S"),
            cc_num=data["cc_num"],
            merchant=data["merchant"],
            category=data["category"],
            amt=data["amt"],
            city=data["city"],
            state=data["state"],
            unix_time=data["unix_time"],
            merch_lat=data["merch_lat"],
            merch_long=data["merch_long"],
            reason="Invalid credit/debit card details",
            is_fraud=True
        )
        db.add(fraud_entry)
        db.flush()  # Ensure SQLAlchemy processes the insert
        db.commit()
        db.refresh(fraud_entry)
        return {"prediction": "Fraud", "reason": "Invalid credit/debit card details"}

    prediction = predict_fraud(data)

    if prediction == "Fraud":
        fraud_entry = FraudTransaction(
            trans_date_trans_time=datetime.strptime(data["trans_date_trans_time"], "%Y-%m-%d %H:%M:%S"),
            cc_num=data["cc_num"],
            merchant=data["merchant"],
            category=data["category"],
            amt=data["amt"],
            city=data["city"],
            state=data["state"],
            unix_time=data["unix_time"],
            merch_lat=data["merch_lat"],
            merch_long=data["merch_long"],
            reason="Invalid credit/debit card details",
            is_fraud=True
        )
        db.add(fraud_entry)
        db.flush()  # Ensure SQLAlchemy processes the insert
        db.commit()
        db.refresh(fraud_entry)
        print(f"Saved Transaction: {fraud_entry.id}")

    fraud = FraudTransaction(
            trans_date_trans_time=datetime.strptime(data["trans_date_trans_time"], "%Y-%m-%d %H:%M:%S"),
            cc_num=data["cc_num"],
            merchant=data["merchant"],
            category=data["category"],
            amt=data["amt"],
            city=data["city"],
            state=data["state"],
            unix_time=data["unix_time"],
            merch_lat=data["merch_lat"],
            merch_long=data["merch_long"],
            reason="Valid credit/debit card details",
            is_fraud=False
        )
    db.add(fraud)
    db.flush()  # Ensure SQLAlchemy processes the insert
    db.commit()
    db.refresh(fraud)

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
    

@app.get("/test-db/")
def test_db(db: Session = Depends(get_db)):
    test_entry = FraudTransaction(
        trans_date_trans_time=datetime.utcnow(),
        cc_num="1234567890123456",
        merchant="Test Merchant",
        category="Test",
        amt=100.0,
        city="Test City",
        state="TS",
        unix_time=1234567890,
        merch_lat=0.0,
        merch_long=0.0,
        reason="Test Insert",
        is_fraud=False
    )
    db.add(test_entry)
    db.commit()
    db.refresh(test_entry)
    return {"success": True, "id": test_entry.id}


# Make sure the app uses the correct port
if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.getenv("PORT", 8000))  # Use Railway's assigned port or default to 8000
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
