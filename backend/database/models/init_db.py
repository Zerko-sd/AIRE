from database.connection import engine
from database.models.incident_table import Base

Base.metadata.create_all(bind=engine)

print("Database Initialized successfully.")