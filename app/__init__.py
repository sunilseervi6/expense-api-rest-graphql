from fastapi import FastAPI
from app.database import engine, Base
from app import models  # Ensures models are registered before create_all
# from app.routes import router

def create_app() -> FastAPI:
    app = FastAPI(title="Expense Tracker")

    # Create SQLite tables on startup if they don't exist
    Base.metadata.create_all(bind=engine)

    # app.include_router(router)
    return app