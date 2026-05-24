from pydantic import BaseModel

class Investigation(BaseModel):
    root_cause: str
    confidence: float
    evidence: list[str]