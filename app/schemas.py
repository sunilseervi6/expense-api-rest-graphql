from pydantic import BaseModel, ConfigDict
from typing import Optional

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