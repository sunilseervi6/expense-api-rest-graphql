from fastapi import FastAPI, Depends
from strawberry.fastapi import GraphQLRouter

from app.database import engine, Base, get_db
from app import models  # Ensures models are registered before create_all
from app.category import router as category_router
from app.expense import router as expense_router, summary_router
from app.graphql.schema import schema  # Import your Strawberry schema


# Passes the database session into info.context["db"] for Strawberry resolvers
async def get_graphql_context(db=Depends(get_db)):
    return {"db": db}


def create_app() -> FastAPI:
    app = FastAPI(title="Expense Tracker")

    # Create SQLite tables on startup if they don't exist
    Base.metadata.create_all(bind=engine)

    # 1. Existing REST Routers
    app.include_router(category_router)
    app.include_router(expense_router)
    app.include_router(summary_router)

    # 2. Mount Strawberry GraphQL Router at /graphql
    graphql_app = GraphQLRouter(schema, context_getter=get_graphql_context)
    app.include_router(graphql_app, prefix="/graphql")

    return app