import datetime
from typing import List, Optional
import strawberry
from strawberry.types import Info
from sqlalchemy import select

from app.database import DbSession
from app.models import Category as CategoryModel, Expense as ExpenseModel


# --- GRAPHQL TYPES ---

@strawberry.type
class CategoryType:
    id: int
    name: str

    # Resolver for nested expenses belonging to this category
    @strawberry.field
    def expenses(self, info: Info) -> List["ExpenseType"]:
        db: DbSession = info.context["db"]
        stmt = select(ExpenseModel).where(ExpenseModel.category_id == self.id)
        return db.execute(stmt).scalars().all()


@strawberry.type
class ExpenseType:
    id: int
    amount: float
    description: Optional[str]
    spent_on: datetime.date
    category_id: int

    # Resolver for nested category object
    @strawberry.field
    def category(self, info: Info) -> CategoryType:
        db: DbSession = info.context["db"]
        stmt = select(CategoryModel).where(CategoryModel.id == self.category_id)
        return db.execute(stmt).scalar_one()


# --- STRAWBERRY INPUT TYPE FOR MUTATION ---

@strawberry.input
class AddExpenseInput:
    amount: float
    description: Optional[str] = None
    spent_on: datetime.date
    category_id: int


# --- QUERIES ---

@strawberry.type
class Query:
    @strawberry.field
    def expenses(
        self,
        info: Info,
        category_id: Optional[int] = None,
        from_date: Optional[datetime.date] = None,
        to_date: Optional[datetime.date] = None,
    ) -> List[ExpenseType]:
        db: DbSession = info.context["db"]
        stmt = select(ExpenseModel)

        if category_id is not None:
            stmt = stmt.where(ExpenseModel.category_id == category_id)
        if from_date is not None:
            stmt = stmt.where(ExpenseModel.spent_on >= from_date)
        if to_date is not None:
            stmt = stmt.where(ExpenseModel.spent_on <= to_date)

        return db.execute(stmt.order_by(ExpenseModel.spent_on.desc())).scalars().all()

    @strawberry.field
    def categories(self, info: Info) -> List[CategoryType]:
        db: DbSession = info.context["db"]
        return db.execute(select(CategoryModel)).scalars().all()


# --- MUTATIONS ---

@strawberry.type
class Mutation:
    @strawberry.mutation
    def add_expense(self, info: Info, input: AddExpenseInput) -> ExpenseType:
        db: DbSession = info.context["db"]

        # Validate amount
        if input.amount <= 0:
            raise Exception("Amount must be greater than zero.")

        # Validate category existence
        cat_stmt = select(CategoryModel).where(CategoryModel.id == input.category_id)
        category = db.execute(cat_stmt).scalar_one_or_none()
        if not category:
            raise Exception(f"Category with ID {input.category_id} does not exist.")

        new_expense = ExpenseModel(
            amount=input.amount,
            description=input.description,
            spent_on=input.spent_on,
            category_id=input.category_id,
        )
        db.add(new_expense)
        db.commit()
        db.refresh(new_expense)
        return new_expense

    @strawberry.mutation
    def delete_expense(self, info: Info, id: int) -> bool:
        db: DbSession = info.context["db"]

        stmt = select(ExpenseModel).where(ExpenseModel.id == id)
        expense = db.execute(stmt).scalar_one_or_none()

        if not expense:
            # Surfaces cleanly in GraphQL errors array without server crash
            raise Exception(f"Expense with ID {id} not found.")

        db.delete(expense)
        db.commit()
        return True


# Build Schema
schema = strawberry.Schema(query=Query, mutation=Mutation)