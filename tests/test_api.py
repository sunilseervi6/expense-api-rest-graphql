import pytest

def test_create_read_filter_expenses(client):
    # 1. Create a category
    resp = client.post("/categories/", json={"name": "Food"})
    assert resp.status_code == 201
    category = resp.json()
    category_id = category["id"]

    # 2. Create expenses
    resp1 = client.post("/expenses/", json={
        "amount": 10.5,
        "description": "Lunch",
        "spent_on": "2026-07-20",
        "category_id": category_id
    })
    assert resp1.status_code == 201
    
    resp2 = client.post("/expenses/", json={
        "amount": 25.0,
        "description": "Dinner",
        "spent_on": "2026-07-21",
        "category_id": category_id
    })
    assert resp2.status_code == 201

    # 3. Read expenses
    resp_list = client.get("/expenses/")
    assert resp_list.status_code == 200
    expenses = resp_list.json()
    assert len(expenses) == 2
    
    # 4. Filter expenses by date
    # filter from_date
    resp_filter1 = client.get("/expenses/", params={"from_date": "2026-07-21"})
    assert resp_filter1.status_code == 200
    filtered1 = resp_filter1.json()
    assert len(filtered1) == 1
    assert filtered1[0]["amount"] == 25.0

    # filter to_date
    resp_filter2 = client.get("/expenses/", params={"to_date": "2026-07-20"})
    assert resp_filter2.status_code == 200
    filtered2 = resp_filter2.json()
    assert len(filtered2) == 1
    assert filtered2[0]["amount"] == 10.5

    # filter by category_id
    resp_filter3 = client.get("/expenses/", params={"category_id": category_id})
    assert resp_filter3.status_code == 200
    assert len(resp_filter3.json()) == 2


def test_expense_validation_failure(client):
    # Create category first
    resp = client.post("/categories/", json={"name": "Food"})
    category_id = resp.json()["id"]

    # Create expense with negative amount (gt=0 triggers validation failure)
    resp_neg = client.post("/expenses/", json={
        "amount": -5.0,
        "description": "Negative expense",
        "spent_on": "2026-07-20",
        "category_id": category_id
    })
    assert resp_neg.status_code == 422


def test_expense_not_found(client):
    resp = client.get("/expenses/999")
    assert resp.status_code == 404


def test_duplicate_category_409(client):
    resp1 = client.post("/categories/", json={"name": "Utilities"})
    assert resp1.status_code == 201
    
    resp2 = client.post("/categories/", json={"name": "Utilities"})
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["detail"]


def test_summary_calculation(client):
    # Create categories
    cat_food = client.post("/categories/", json={"name": "Food"}).json()
    cat_util = client.post("/categories/", json={"name": "Utilities"}).json()

    # Expenses in 2026-07
    client.post("/expenses/", json={
        "amount": 50.0,
        "description": "Groceries",
        "spent_on": "2026-07-10",
        "category_id": cat_food["id"]
    })
    client.post("/expenses/", json={
        "amount": 150.0,
        "description": "Electricity",
        "spent_on": "2026-07-15",
        "category_id": cat_util["id"]
    })
    client.post("/expenses/", json={
        "amount": 50.0,
        "description": "Restaurant",
        "spent_on": "2026-07-20",
        "category_id": cat_food["id"]
    })

    # Expense in 2026-06 (out of month boundary)
    client.post("/expenses/", json={
        "amount": 100.0,
        "description": "Internet",
        "spent_on": "2026-06-15",
        "category_id": cat_util["id"]
    })

    # Call summary for 2026-07
    resp = client.get("/summary", params={"month": "2026-07"})
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["month"] == "2026-07"
    assert data["total_spend"] == 250.0
    
    categories = data["categories"]
    assert len(categories) == 2
    
    food_summary = next(c for c in categories if c["category_name"] == "Food")
    util_summary = next(c for c in categories if c["category_name"] == "Utilities")
    
    assert food_summary["total_amount"] == 100.0
    assert food_summary["percentage"] == 40.0
    
    assert util_summary["total_amount"] == 150.0
    assert util_summary["percentage"] == 60.0


def test_graphql_query_categories(client):
    # Setup some categories
    client.post("/categories/", json={"name": "Food"})
    client.post("/categories/", json={"name": "Travel"})

    query = """
    query {
      categories {
        id
        name
      }
    }
    """
    resp = client.post("/graphql", json={"query": query})
    assert resp.status_code == 200
    
    resp_json = resp.json()
    assert "data" in resp_json
    assert "errors" not in resp_json
    categories = resp_json["data"]["categories"]
    assert len(categories) == 2
    names = [c["name"] for c in categories]
    assert "Food" in names
    assert "Travel" in names


def test_graphql_add_expense_mutation(client):
    # Setup category
    cat_resp = client.post("/categories/", json={"name": "Shopping"})
    category_id = cat_resp.json()["id"]

    mutation = """
    mutation AddExpense($input: AddExpenseInput!) {
      addExpense(input: $input) {
        id
        amount
        description
        spentOn
        categoryId
      }
    }
    """
    variables = {
      "input": {
        "amount": 45.5,
        "description": "New Jeans",
        "spentOn": "2026-07-22",
        "categoryId": category_id
      }
    }
    
    resp = client.post("/graphql", json={"query": mutation, "variables": variables})
    assert resp.status_code == 200
    resp_json = resp.json()
    
    assert "data" in resp_json
    assert "errors" not in resp_json
    add_expense_data = resp_json["data"]["addExpense"]
    assert add_expense_data["amount"] == 45.5
    assert add_expense_data["description"] == "New Jeans"
    assert add_expense_data["spentOn"] == "2026-07-22"
    assert add_expense_data["categoryId"] == category_id
