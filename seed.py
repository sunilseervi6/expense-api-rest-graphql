# seed.py
from datetime import date
from app.database import SessionLocal, engine, Base
from app.models import Category, Expense

def seed_data():
    # Ensure tables are created
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()

    try:
        # Prevent double-seeding if categories already exist
        if db.query(Category).first():
            print("Database already contains data. Skipping seed.")
            return

        print("Seeding database...")

        # 1. Add Categories
        food = Category(name="Food")
        transport = Category(name="Transport")
        rent = Category(name="Rent")
        fun = Category(name="Fun")

        db.add_all([food, transport, rent, fun])
        db.commit()  # Commit to generate category IDs

        # 2. Add Expenses (Spread across May 2026 and June 2026)
        expenses = [
            # --- MAY 2026 ---
            Expense(amount=1200.00, description="Monthly Rent", spent_on=date(2026, 5, 1), category=rent),
            Expense(amount=85.50, description="Grocery Shopping", spent_on=date(2026, 5, 3), category=food),
            Expense(amount=32.00, description="Gasoline", spent_on=date(2026, 5, 7), category=transport),
            Expense(amount=15.00, description="Movie Ticket", spent_on=date(2026, 5, 12), category=fun),
            Expense(amount=45.20, description="Dinner out", spent_on=date(2026, 5, 18), category=food),
            Expense(amount=22.50, description="Subway Pass", spent_on=date(2026, 5, 25), category=transport),

            # --- JUNE 2026 ---
            Expense(amount=1200.00, description="Monthly Rent", spent_on=date(2026, 6, 1), category=rent),
            Expense(amount=98.10, description="Weekly Groceries", spent_on=date(2026, 6, 4), category=food),
            Expense(amount=60.00, description="Concert Ticket", spent_on=date(2026, 6, 10), category=fun),
            Expense(amount=35.00, description="Gas Station", spent_on=date(2026, 6, 15), category=transport),
            Expense(amount=18.00, description="Coffee & Bakery", spent_on=date(2026, 6, 21), category=food),
            Expense(amount=40.00, description="Board Game Night", spent_on=date(2026, 6, 28), category=fun),
        ]

        db.add_all(expenses)
        db.commit()
        print("Successfully seeded 4 categories and 12 expenses!")

    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()