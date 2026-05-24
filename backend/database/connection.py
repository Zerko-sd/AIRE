from sqlalchemy import create_engine


DATABASE_URL = "postgresql://user:password@localhost:5432/aire"

engine = create_engine(DATABASE_URL)

