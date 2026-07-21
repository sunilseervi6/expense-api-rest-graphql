from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./app.db"

# connect_args={"check_same_thread": False} is required specifically for SQLite in multi-threaded frameworks
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency injected into routes to handle DB session lifecycle automatically
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()