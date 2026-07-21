from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date

# --- CATEGORY SCHEMAS ---
class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None  # Optional field for updates

class CategoryResponse(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)



# Expense Schema
class ExpenseBase(BaseModel):
    # Field constraint enforces positive amount at the Pydantic/API level
    amount: float = Field(..., gt=0, description="Amount must be greater than zero")
    description: Optional[str] = None
    spent_on: date
    category_id: int

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None
    spent_on: Optional[date] = None
    category_id: Optional[int] = None

class ExpenseResponse(BaseModel):
    id: int
    amount: float
    description: Optional[str] = None
    spent_on: date
    category_id: int
    
    # NESTED OBJECT: Includes full category details (e.g. category.name) in the response
    category: CategoryResponse

    model_config = ConfigDict(from_attributes=True)


class CategorySummary(BaseModel):
    category_name: str
    total_amount: float
    percentage: float = Field(..., description="Percentage share of total monthly spend (0-100)")

class MonthlySummaryResponse(BaseModel):
    month: str
    total_spend: float
    categories: list[CategorySummary]
