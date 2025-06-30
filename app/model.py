from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from .database import Base

class FraudTransaction(Base):
    __tablename__ = "fraud_transactions"

    id = Column(Integer, primary_key=True, index=True)
    trans_date_trans_time = Column(DateTime)
    cc_num = Column(String)
    merchant = Column(String)
    category = Column(String)
    amt = Column(Float)
    city = Column(String)
    state = Column(String)
    unix_time = Column(Float)
    merch_lat = Column(Float)
    merch_long = Column(Float)
    reason = Column(String)
    is_fraud = Column(Boolean)
    
