import datetime
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)

    # Relationship to access expenses from a category instance
    expenses = relationship("Expense", back_populates="category", cascade="all, delete-orphan")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    spent_on = Column(Date, nullable=False, default=datetime.date.today)
    
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)

    # Relationship back to Category
    category = relationship("Category", back_populates="expenses")

    # Table argument ensuring amount > 0
    __table_args__ = (
        CheckConstraint('amount > 0', name='check_positive_amount'),
    )