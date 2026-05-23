from pydantic import BaseModel
from datetime import datetime

class Incident(BaseModel):

    title: str
    severity: str
    services: str
    metric: str
    value: float
    created_at: datetime