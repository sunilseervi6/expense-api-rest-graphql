import re
from datetime import date
from typing import List, Optional, Annotated
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy import func, select

from app.database import DbSession
from app.models import Expense, Category
from app import schemas

router = APIRouter(prefix="/expenses", tags=["Expenses"])
summary_router = APIRouter(tags=["Summary"])


# 1. READ ALL EXPENSES WITH COMBINABLE FILTERS
@router.get("/", response_model=List[schemas.ExpenseResponse], status_code=status.HTTP_200_OK)
def get_expenses(
    db: DbSession,
    category_id: Annotated[Optional[int], Query(description="Filter by Category ID", ge=1)] = None,
    from_date: Annotated[Optional[date], Query(description="Filter expenses spent on or after this date (YYYY-MM-DD)")] = None,
    to_date: Annotated[Optional[date], Query(description="Filter expenses spent on or before this date (YYYY-MM-DD)")] = None,
):
    """
    Example: GET /expenses?category_id=1&from_date=2026-03-01&to_date=2026-03-31
    """
    # Start building the base query
    stmt = select(Expense)

    # Dynamically append filter clauses if query parameters are provided
    if category_id is not None:
        stmt = stmt.where(Expense.category_id == category_id)

    if from_date is not None:
        stmt = stmt.where(Expense.spent_on >= from_date)

    if to_date is not None:
        stmt = stmt.where(Expense.spent_on <= to_date)

    # Order by spent_on descending for a clean ledger view
    stmt = stmt.order_by(Expense.spent_on.desc())

    result = db.execute(stmt)
    return result.scalars().all()
    

# 2. READ SINGLE EXPENSE BY ID
@router.get("/{expense_id}", response_model=schemas.ExpenseResponse, status_code=status.HTTP_200_OK)
def get_expense(
    expense_id: Annotated[int, Path(ge=1)],
    db: DbSession,
):
    stmt = select(Expense).where(Expense.id == expense_id)
    expense = db.execute(stmt).scalar_one_or_none()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with ID {expense_id} not found",
        )
    return expense


# 3. CREATE EXPENSE (Validates Category existence & Positive amount)
@router.post("/", response_model=schemas.ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense_in: schemas.ExpenseCreate,
    db: DbSession,
):
    # Verify foreign key reference: Target Category MUST exist in database
    cat_stmt = select(Category).where(Category.id == expense_in.category_id)
    category = db.execute(cat_stmt).scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with ID {expense_in.category_id} does not exist",
        )

    new_expense = Expense(
        amount=expense_in.amount,
        description=expense_in.description,
        spent_on=expense_in.spent_on,
        category_id=expense_in.category_id,
    )

    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense


# 4. UPDATE EXPENSE
@router.put("/{expense_id}", response_model=schemas.ExpenseResponse, status_code=status.HTTP_200_OK)
def update_expense(
    expense_id: Annotated[int, Path(ge=1)],
    expense_in: schemas.ExpenseUpdate,
    db: DbSession,
):
    stmt = select(Expense).where(Expense.id == expense_id)
    expense = db.execute(stmt).scalar_one_or_none()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with ID {expense_id} not found",
        )

    # If updating category_id, verify that the new category exists
    if expense_in.category_id is not None:
        cat_stmt = select(Category).where(Category.id == expense_in.category_id)
        category = db.execute(cat_stmt).scalar_one_or_none()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with ID {expense_in.category_id} does not exist",
            )
        expense.category_id = expense_in.category_id

    if expense_in.amount is not None:
        expense.amount = expense_in.amount
    if expense_in.description is not None:
        expense.description = expense_in.description
    if expense_in.spent_on is not None:
        expense.spent_on = expense_in.spent_on

    db.commit()
    db.refresh(expense)
    return expense


# 5. DELETE EXPENSE
@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: Annotated[int, Path(ge=1)],
    db: DbSession,
):
    stmt = select(Expense).where(Expense.id == expense_id)
    expense = db.execute(stmt).scalar_one_or_none()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with ID {expense_id} not found",
        )

    db.delete(expense)
    db.commit()
    return None



@summary_router.get("/summary", response_model=schemas.MonthlySummaryResponse)
def get_summary(
    db: DbSession,
    month: Annotated[Optional[str], Query(description="Month in YYYY-MM format")] = None
):
    if month is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month parameter is required. Format must be YYYY-MM."
        )
    if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", month):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid month format. Format must be YYYY-MM."
        )
    # Query aggregates cleanly inside SQLite
    stmt = (
        select(
            Category.name.label("category_name"),
            func.coalesce(func.sum(Expense.amount), 0.0).label("total_amount")
        )
        .join(Expense, Category.id == Expense.category_id)
        .where(func.strftime("%Y-%m", Expense.spent_on) == month)
        .group_by(Category.id, Category.name)
    )

    results = db.execute(stmt).all()
    grand_total = sum(r.total_amount for r in results)

    breakdown = []
    for r in results:
        pct = round((r.total_amount / grand_total) * 100, 2) if grand_total > 0 else 0.0
        breakdown.append(
            schemas.CategorySummary(
                category_name=r.category_name,
                total_amount=round(r.total_amount, 2),
                percentage=pct
            )
        )

    return schemas.MonthlySummaryResponse(
        month=month,
        total_spend=round(grand_total, 2),
        categories=breakdown
    )