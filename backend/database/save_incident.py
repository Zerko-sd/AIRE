from sqlalchemy.orm import sessionmaker
from connection import engine

from models.incident_table import IncidentTable
import uuid

Session = sessionmaker(bind=engine)

def save_incident(incident_data):
    session = Session()

    row = IncidentTable(
        id = str(uuid.uuid4()),
        title=incident_data.title,
        severity=incident_data.severity,
        services=incident_data.services,
        metric=incident_data.metric,
        value=incident_data.value,
        created_at=incident_data.created_at
    )

    session.add(row)
    session.commit()
    session.close()