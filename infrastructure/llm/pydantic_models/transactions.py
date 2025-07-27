from typing import Dict, Any, Optional, Union, Literal, List
from pydantic import BaseModel, Field
from datetime import datetime

class TransactionEntry(BaseModel):
    transaction_date: datetime
    transaction_detail: str
    amount: str
    currency: str
    category: Literal["Income", "Housing", "Transportation", "Food & Dining", "Personal Care & Health", "Entertainment & Lifestyle", "Education & Development", "Debt & Loans", "Children/Dependents", "Miscellaneous/Other"]
    service_subscription: Optional[str] = Field(default = None, description = "Services like Netflix, Spotify, ...")
    receiver_name: Optional[str]

class TransactionHistory(BaseModel):
    transactions: List[TransactionEntry]