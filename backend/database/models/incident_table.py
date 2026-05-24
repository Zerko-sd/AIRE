from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Float, DateTime

Base = declarative_base()

class IncidentTable(Base):
    __tablename__ = 'incidents'

    id = Column(String, primary_key=True)
    title = Column(String)
    severity = Column(String)
    services = Column(String)
    metric = Column(String)
    value = Column(Float)
    created_at = Column(DateTime)

