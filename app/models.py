import datetime
from typing import List, Optional
from sqlalchemy import String, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)

    # Relationship to access expenses from a category instance
    expenses: Mapped[List["Expense"]] = relationship("Expense", back_populates="category")


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    amount: Mapped[float] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column(default=None)
    spent_on: Mapped[datetime.date] = mapped_column(default=datetime.date.today)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)

    # Relationship back to Category
    category: Mapped["Category"] = relationship("Category", back_populates="expenses")

    # Table argument ensuring amount > 0
    __table_args__ = (
        CheckConstraint('amount > 0', name='check_positive_amount'),
    )