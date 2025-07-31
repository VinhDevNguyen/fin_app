from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class TransactionEntry(BaseModel):
    transaction_date: datetime
    transaction_detail: str
    amount: str
    currency: str
    category: Literal[
        "Income",
        "Housing",
        "Transportation",
        "Food & Dining",
        "Personal Care & Health",
        "Entertainment & Lifestyle",
        "Education & Development",
        "Debt & Loans",
        "Children/Dependents",
        "Miscellaneous/Other",
    ]
    service_subscription: Optional[str] = Field(
        default=None, description="Services like Netflix, Spotify, ..."
    )
    receiver_name: Optional[str]


class TransactionHistory(BaseModel):
    transactions: list[TransactionEntry]
