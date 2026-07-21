from typing import List
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func
from app.database import DbSession
from app.models import Category, Expense
from app import schemas

router = APIRouter(prefix="/categories", tags=["Categories"])


# 1. READ ALL CATEGORIES
@router.get("/", response_model=List[schemas.CategoryResponse], status_code=status.HTTP_200_OK)
def get_categories(db: DbSession):
    # 2.0 Style: select() -> db.execute() -> scalars().all()
    stmt = select(Category)
    result = db.execute(stmt)
    return result.scalars().all()


# 2. READ SINGLE CATEGORY BY ID
@router.get("/{category_id}", response_model=schemas.CategoryResponse, status_code=status.HTTP_200_OK)
def get_category(category_id: int, db: DbSession):
    stmt = select(Category).where(Category.id == category_id)
    category = db.execute(stmt).scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    return category


# 3. CREATE CATEGORY (201 Created / 409 Conflict)
@router.post("/", response_model=schemas.CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(category_in: schemas.CategoryCreate, db: DbSession):
    stmt = select(Category).where(Category.name == category_in.name)
    existing = db.execute(stmt).scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category '{category_in.name}' already exists"
        )
    
    new_category = Category(name=category_in.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


# 4. DELETE CATEGORY (204 No Content / 404 / 409)
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: DbSession):
    category = db.execute(select(Category).where(Category.id == category_id)).scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    
    # Count expenses in 2.0 style using func.count()
    count_stmt = select(func.count()).select_from(Expense).where(Expense.category_id == category_id)
    expense_count = db.execute(count_stmt).scalar()
    
    if expense_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete category '{category.name}'. It contains {expense_count} expenses."
        )

    db.delete(category)
    db.commit()
    return None