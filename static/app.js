// --- STATE MANAGEMENT ---
let categoriesList = [];
let editingExpenseId = null;

// Initialize form defaults on load
window.addEventListener('DOMContentLoaded', () => {
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('spent-on').value = today;

  const currentYearMonth = today.substring(0, 7); // e.g. "2026-07"
  const monthPicker = document.getElementById('summary-month');
  monthPicker.value = currentYearMonth;

  // Setup Event Listeners
  document.getElementById('expense-form').addEventListener('submit', handleFormSubmit);
  document.getElementById('category-form').addEventListener('submit', handleCategorySubmit);
  monthPicker.addEventListener('change', loadSummary);

  // Initial Data Load
  loadCategories();
  loadExpenses();
  loadSummary();
});

// --- TOAST ALERTS ---
const showToast = (message, type = 'success') => {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  toast.innerHTML = `
    <span>${message}</span>
    <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
  `;

  container.appendChild(toast);
  
  // Auto-remove after 4 seconds
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
};

// --- GRAPHQL API: Fetch Categories ---
const loadCategories = async () => {
  const selectElement = document.getElementById('category');
  const manageList = document.getElementById('manage-categories-list');
  try {
    const query = `
      query {
        categories {
          id
          name
        }
      }
    `;
    const response = await fetch('/graphql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    
    if (!response.ok) {
      throw new Error('GraphQL request failed');
    }
    
    const result = await response.json();
    if (result.errors) {
      throw new Error(result.errors[0].message);
    }
    
    categoriesList = result.data.categories;
    
    // Populate Select Dropdown
    selectElement.innerHTML = '<option value="" disabled selected>Select category</option>';
    manageList.innerHTML = '';
    
    categoriesList.forEach(cat => {
      const opt = document.createElement('option');
      opt.value = cat.id;
      opt.textContent = cat.name;
      selectElement.appendChild(opt);
      
      // Populate manage chips list
      const chip = document.createElement('span');
      chip.className = 'badge';
      chip.style.display = 'inline-flex';
      chip.style.alignItems = 'center';
      chip.style.gap = '0.4rem';
      chip.style.padding = '0.35rem 0.75rem';
      chip.innerHTML = `
        ${cat.name}
        <button onclick="handleDeleteCategory(${cat.id}, '${cat.name.replace(/'/g, "\\'")}')" style="background: none; border: none; box-shadow: none; color: var(--danger-color); cursor: pointer; padding: 0; font-size: 0.95rem; font-weight: bold; line-height: 1; display: inline; vertical-align: middle;">&times;</button>
      `;
      manageList.appendChild(chip);
    });
  } catch (err) {
    console.error(err);
    showToast('Error loading categories: ' + err.message, 'error');
    selectElement.innerHTML = '<option value="" disabled>Error loading categories</option>';
    manageList.innerHTML = '<div class="empty-state" style="padding: 0.5rem 0;">Error loading categories</div>';
  }
};

// --- REST API: Fetch Expenses ---
const loadExpenses = async () => {
  const tbody = document.getElementById('expenses-table-body');
  try {
    const response = await fetch('/expenses/');
    if (!response.ok) {
      throw new Error('REST request failed');
    }
    
    const expenses = await response.json();
    
    if (expenses.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="empty-state">No expenses recorded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = '';
    expenses.forEach(exp => {
      const tr = document.createElement('tr');
      
      const dateStr = new Date(exp.spent_on).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        timeZone: 'UTC'
      });

      tr.innerHTML = `
        <td>${dateStr}</td>
        <td>${exp.description || '—'}</td>
        <td><span class="badge">${exp.category ? exp.category.name : 'Unknown'}</span></td>
        <td class="amount-col">$${parseFloat(exp.amount).toFixed(2)}</td>
        <td>
          <div style="display: flex; justify-content: center; gap: 0.5rem;">
            <button onclick="startEditExpense(${exp.id}, ${exp.amount}, '${(exp.description || '').replace(/'/g, "\\'")}', '${exp.spent_on}', ${exp.category_id})" class="action-btn-edit">Edit</button>
            <button onclick="handleDeleteExpense(${exp.id})" class="action-btn-delete">Delete</button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error(err);
    showToast('Error loading expenses: ' + err.message, 'error');
    tbody.innerHTML = `<tr><td colspan="5" class="empty-state text-danger">Failed to load expenses.</td></tr>`;
  }
};

// --- REST API: Fetch Monthly Summary ---
const loadSummary = async () => {
  const monthPicker = document.getElementById('summary-month');
  const selectedMonth = monthPicker.value;
  const totalDisplay = document.getElementById('total-spend-value');
  const listElement = document.getElementById('category-breakdown-list');
  
  if (!selectedMonth) return;

  try {
    const response = await fetch(`/summary?month=${selectedMonth}`);
    if (!response.ok) {
      throw new Error('Failed to fetch summary data');
    }
    
    const data = await response.json();
    
    // Update total
    totalDisplay.textContent = `$${parseFloat(data.total_spend).toFixed(2)}`;
    
    // Update Breakdown
    listElement.innerHTML = '';
    if (data.categories.length === 0) {
      listElement.innerHTML = `<div class="empty-state" style="padding: 1rem 0;">No spending details for this month.</div>`;
      return;
    }

    data.categories.forEach(cat => {
      const div = document.createElement('div');
      div.className = 'category-item';
      div.innerHTML = `
        <div class="category-info">
          <span class="category-name">${cat.category_name}</span>
          <div class="category-amounts">
            <span class="category-percentage">${cat.percentage.toFixed(1)}%</span>
            <span class="category-total">$${parseFloat(cat.total_amount).toFixed(2)}</span>
          </div>
        </div>
        <div class="progress-bg">
          <div class="progress-bar" style="width: ${cat.percentage}%"></div>
        </div>
      `;
      listElement.appendChild(div);
    });
  } catch (err) {
    console.error(err);
    showToast('Error loading monthly summary: ' + err.message, 'error');
    totalDisplay.textContent = '$0.00';
    listElement.innerHTML = `<div class="empty-state text-danger">Failed to load summary data.</div>`;
  }
};

// --- REST API: Submit Add/Edit Expense Form ---
const handleFormSubmit = async (e) => {
  e.preventDefault();
  
  const submitBtn = document.getElementById('submit-btn');
  const amountVal = parseFloat(document.getElementById('amount').value);
  const descVal = document.getElementById('description').value;
  const spentOnVal = document.getElementById('spent-on').value;
  const catVal = parseInt(document.getElementById('category').value);

  if (isNaN(amountVal) || amountVal <= 0) {
    showToast('Amount must be positive.', 'error');
    return;
  }
  if (!catVal) {
    showToast('Please select a valid category.', 'error');
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = 'Saving...';

  try {
    const url = editingExpenseId ? `/expenses/${editingExpenseId}` : '/expenses/';
    const method = editingExpenseId ? 'PUT' : 'POST';

    const response = await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        amount: amountVal,
        description: descVal,
        spent_on: spentOnVal,
        category_id: catVal
      })
    });

    if (!response.ok) {
      const errData = await response.json();
      const detailMsg = Array.isArray(errData.detail) 
        ? errData.detail.map(d => d.msg).join(', ') 
        : errData.detail;
      throw new Error(detailMsg || 'Failed to save expense');
    }

    showToast(editingExpenseId ? 'Expense updated!' : 'Expense recorded!');
    cancelEditExpense();
    
    await Promise.all([
      loadExpenses(),
      loadSummary()
    ]);
  } catch (err) {
    console.error(err);
    showToast('Error saving expense: ' + err.message, 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = editingExpenseId ? 'Update Expense' : 'Save Expense';
  }
};

// --- REST API: Submit Add Category Form ---
const handleCategorySubmit = async (e) => {
  e.preventDefault();
  
  const nameInput = document.getElementById('category-name');
  const nameVal = nameInput.value.trim();
  if (!nameVal) return;

  const submitBtn = document.getElementById('category-submit-btn');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Saving...';

  try {
    const response = await fetch('/categories/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: nameVal })
    });

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || 'Failed to create category');
    }

    showToast(`Category "${nameVal}" successfully created!`);
    nameInput.value = '';
    await loadCategories();
  } catch (err) {
    console.error(err);
    showToast('Error saving category: ' + err.message, 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Save Category';
  }
};

// --- EDIT STATE MANAGEMENT ---
const startEditExpense = (id, amount, description, spent_on, category_id) => {
  editingExpenseId = id;
  document.getElementById('amount').value = amount;
  document.getElementById('description').value = description;
  document.getElementById('spent-on').value = spent_on;
  document.getElementById('category').value = category_id;
  
  document.getElementById('expense-form-title').innerHTML = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline;vertical-align:middle;margin-right:0.25rem;">
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
    </svg>
    Edit Expense #${id}
  `;
  document.getElementById('submit-btn').textContent = 'Update Expense';
  document.getElementById('cancel-edit-btn').style.display = 'block';
  
  document.getElementById('expense-form').scrollIntoView({ behavior: 'smooth' });
};

const cancelEditExpense = () => {
  editingExpenseId = null;
  document.getElementById('amount').value = '';
  document.getElementById('description').value = '';
  document.getElementById('spent-on').value = new Date().toISOString().split('T')[0];
  document.getElementById('category').value = '';
  
  document.getElementById('expense-form-title').innerHTML = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline;vertical-align:middle;margin-right:0.25rem;">
      <path d="M12 20h9"></path>
      <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
    </svg>
    Add New Expense
  `;
  document.getElementById('submit-btn').textContent = 'Save Expense';
  document.getElementById('cancel-edit-btn').style.display = 'none';
};

// --- GRAPHQL API: Delete Expense ---
const handleDeleteExpense = async (id) => {
  if (!confirm('Are you sure you want to delete this expense?')) {
    return;
  }

  try {
    const query = `
      mutation DeleteExpense($id: Int!) {
        deleteExpense(id: $id)
      }
    `;
    const response = await fetch('/graphql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        variables: { id: parseInt(id) }
      })
    });

    if (!response.ok) {
      throw new Error('GraphQL request failed');
    }

    const result = await response.json();
    if (result.errors) {
      throw new Error(result.errors[0].message);
    }

    showToast('Expense successfully deleted!');
    
    if (editingExpenseId === id) {
      cancelEditExpense();
    }

    await Promise.all([
      loadExpenses(),
      loadSummary()
    ]);
  } catch (err) {
    console.error(err);
    showToast('Error deleting expense: ' + err.message, 'error');
  }
};

// --- REST API: Delete Category ---
const handleDeleteCategory = async (id, name) => {
  if (!confirm(`Are you sure you want to delete category "${name}"?`)) {
    return;
  }

  try {
    const response = await fetch(`/categories/${id}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || 'Failed to delete category');
    }

    showToast(`Category "${name}" successfully deleted!`);
    
    await Promise.all([
      loadCategories(),
      loadExpenses(),
      loadSummary()
    ]);
  } catch (err) {
    console.error(err);
    showToast(err.message, 'error');
  }
};
