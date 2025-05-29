from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                         QLineEdit, QDateEdit, QTableWidget, QTableWidgetItem,
                         QHeaderView, QFormLayout, QMessageBox, QComboBox, QCheckBox)
from PyQt5.QtCore import Qt, QDate
import datetime


class ExpenseTab(QWidget):
    """Tab for managing expense records"""
    
    def __init__(self, budget_manager, user_id):
        super().__init__()
        self.budget_manager = budget_manager
        self.user_id = user_id
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout()
        
        # Add Expense Form
        form_layout = QFormLayout()
        
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Enter amount")
        form_layout.addRow("Amount ($):", self.amount_input)
        
        # APR fields
        apr_layout = QHBoxLayout()
        
        self.has_apr_checkbox = QCheckBox("Has APR/Interest")
        self.has_apr_checkbox.stateChanged.connect(self.toggle_apr_field)
        
        self.apr_input = QLineEdit()
        self.apr_input.setPlaceholderText("APR %")
        self.apr_input.setEnabled(False)
        
        apr_layout.addWidget(self.has_apr_checkbox)
        apr_layout.addWidget(self.apr_input)
        apr_layout.addStretch()
        
        form_layout.addRow("APR:", apr_layout)
        
        # Category dropdown
        self.category_combo = QComboBox()
        self.load_categories()
        form_layout.addRow("Category:", self.category_combo)
        
        # Add new category button
        new_category_button = QPushButton("New Category")
        new_category_button.clicked.connect(self.add_new_category)
        form_layout.addRow("", new_category_button)
        
        self.date_input = QDateEdit(calendarPopup=True)
        self.date_input.setDate(QDate.currentDate())
        form_layout.addRow("Date:", self.date_input)
        
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Enter description (optional)")
        form_layout.addRow("Description:", self.description_input)
        
        # Add button
        add_button = QPushButton("Add Expense")
        add_button.clicked.connect(self.add_expense)
        
        form_section = QVBoxLayout()
        form_section.addLayout(form_layout)
        form_section.addWidget(add_button)
        
        main_layout.addLayout(form_section)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        self.filter_category = QComboBox()
        self.filter_category.addItem("All Categories", None)
        for category in self.budget_manager.get_expense_categories():
            self.filter_category.addItem(category.name, category.id)
        
        self.filter_month = QComboBox()
        for i in range(1, 13):
            self.filter_month.addItem(datetime.date(2000, i, 1).strftime("%B"), i)
        self.filter_month.setCurrentIndex(datetime.date.today().month - 1)
        
        self.filter_year = QComboBox()
        current_year = datetime.date.today().year
        for year in range(current_year - 5, current_year + 1):
            self.filter_year.addItem(str(year), year)
        self.filter_year.setCurrentText(str(current_year))
        
        filter_button = QPushButton("Filter")
        filter_button.clicked.connect(self.refresh_data)
        
        filter_layout.addWidget(QLabel("Category:"))
        filter_layout.addWidget(self.filter_category)
        filter_layout.addWidget(QLabel("Month:"))
        filter_layout.addWidget(self.filter_month)
        filter_layout.addWidget(QLabel("Year:"))
        filter_layout.addWidget(self.filter_year)
        filter_layout.addWidget(filter_button)
        filter_layout.addStretch()
        
        main_layout.addLayout(filter_layout)
        
        # Expense table
        self.expense_table = QTableWidget(0, 7)  # rows, columns
        self.expense_table.setHorizontalHeaderLabels(["ID", "Date", "Category", "Amount", "Description", "APR (%)", "Interest/Mo"])
        self.expense_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.expense_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make table read-only
        
        main_layout.addWidget(self.expense_table)
        
        self.setLayout(main_layout)
        self.refresh_data()
    
    def load_categories(self):
        """Load expense categories into combobox"""
        self.category_combo.clear()
        
        # Create default categories if none exist
        categories = self.budget_manager.get_expense_categories()
        if not categories:
            default_categories = [
                ("Food & Dining", "Groceries, restaurants, and food delivery"),
                ("Housing", "Rent, mortgage, and home maintenance"),
                ("Transportation", "Car payments, gas, public transit"),
                ("Utilities", "Electricity, water, internet, phone"),
                ("Shopping", "Clothing, electronics, and other retail"),
                ("Entertainment", "Movies, games, and hobbies"),
                ("Health & Fitness", "Medical expenses and fitness"),
                ("Personal Care", "Haircuts, cosmetics, etc."),
                ("Education", "Tuition, books, courses"),
                ("Travel", "Vacations and business trips"),
                ("Debt Payments", "Credit card payments and loans"),
                ("Savings & Investments", "Contributions to savings accounts"),
                ("Gifts & Donations", "Presents and charitable donations"),
                ("Miscellaneous", "Other expenses that don't fit elsewhere")
            ]
            
            for name, desc in default_categories:
                self.budget_manager.create_category(name, desc, "expense")
            
            categories = self.budget_manager.get_expense_categories()
        
        # Add categories to combobox
        for category in categories:
            self.category_combo.addItem(category.name, category.id)
    
    def add_new_category(self):
        """Add a new expense category"""
        from PyQt5.QtWidgets import QDialog, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Category")
        
        layout = QVBoxLayout()
        
        form = QFormLayout()
        name_input = QLineEdit()
        description_input = QLineEdit()
        
        form.addRow("Category Name:", name_input)
        form.addRow("Description:", description_input)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            name = name_input.text().strip()
            description = description_input.text().strip()
            
            if name:
                category_id = self.budget_manager.create_category(name, description, "expense")
                self.load_categories()
                
                # Set the newly created category as selected
                index = self.category_combo.findData(category_id)
                if index >= 0:
                    self.category_combo.setCurrentIndex(index)
                
                # Refresh filter dropdown too
                self.filter_category.clear()
                self.filter_category.addItem("All Categories", None)
                for category in self.budget_manager.get_expense_categories():
                    self.filter_category.addItem(category.name, category.id)
            else:
                QMessageBox.warning(self, "Input Error", "Category name cannot be empty.")
    
    def toggle_apr_field(self, state):
        """Enable/disable APR input based on checkbox state"""
        self.apr_input.setEnabled(state == Qt.Checked)
        if state != Qt.Checked:
            self.apr_input.clear()
    
    def add_expense(self):
        """Add a new expense record"""
        try:
            # Get form values
            amount_text = self.amount_input.text()
            category_id = self.category_combo.currentData()
            date = self.date_input.date().toPyDate()
            description = self.description_input.text()
            
            # Get APR values
            has_apr = 1 if self.has_apr_checkbox.isChecked() else 0
            apr_text = self.apr_input.text() if has_apr else "0"
            
            # Validate input
            if not amount_text:
                QMessageBox.warning(self, "Input Error", "Amount is required.")
                return
            
            try:
                amount = float(amount_text)
                if amount <= 0:
                    raise ValueError("Amount must be positive")
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Amount must be a positive number.")
                return
                
            # Validate APR if applicable
            apr = 0.0
            if has_apr:
                try:
                    apr = float(apr_text)
                    if apr < 0:
                        raise ValueError("APR cannot be negative")
                except ValueError:
                    QMessageBox.warning(self, "Input Error", "APR must be a valid number.")
                    return
            
            # Add expense to database
            expense_id = self.budget_manager.add_expense(
                self.user_id, category_id, amount, description, date, has_apr, apr
            )
            
            if expense_id:
                # Clear form
                self.amount_input.clear()
                self.date_input.setDate(QDate.currentDate())
                self.description_input.clear()
                self.has_apr_checkbox.setChecked(False)
                self.apr_input.clear()
                
                # Refresh table
                self.refresh_data()
                
                QMessageBox.information(self, "Success", "Expense added successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to add expense.")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def refresh_data(self):
        """Refresh the expense table with latest data"""
        try:
            # Get filter values
            category_id = self.filter_category.currentData()
            month = self.filter_month.currentData()
            year = self.filter_year.currentData()
            
            # Calculate date range for the selected month
            import calendar
            start_date = datetime.date(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end_date = datetime.date(year, month, last_day)
            
            # Get expense data
            expenses = self.budget_manager.db.get_expenses_by_date_range(
                self.user_id, start_date, end_date
            )
            
            # Filter by category if selected
            if category_id is not None:
                expenses = [e for e in expenses if e.category_id == category_id]
            
            # Update table
            self.expense_table.setRowCount(0)
            
            session = self.budget_manager.db.get_session()
            total_amount = 0
            
            for expense in expenses:
                row_position = self.expense_table.rowCount()
                self.expense_table.insertRow(row_position)
                
                # Get category name
                category = session.query(expense.category).first()
                category_name = category.name if category else "Unknown"
                
                # Set cell values
                self.expense_table.setItem(row_position, 0, QTableWidgetItem(str(expense.id)))
                self.expense_table.setItem(row_position, 1, QTableWidgetItem(expense.date.strftime("%Y-%m-%d")))
                self.expense_table.setItem(row_position, 2, QTableWidgetItem(category_name))
                self.expense_table.setItem(row_position, 3, QTableWidgetItem(f"${expense.amount:.2f}"))
                self.expense_table.setItem(row_position, 4, QTableWidgetItem(expense.description or ""))
                
                # Handle APR and interest calculation
                if expense.has_apr:
                    self.expense_table.setItem(row_position, 5, QTableWidgetItem(f"{expense.apr:.2f}%"))
                    
                    # Calculate and display monthly interest
                    monthly_interest = self.budget_manager.calculate_monthly_interest(expense.amount, expense.apr)
                    interest_item = QTableWidgetItem(f"${monthly_interest:.2f}")
                    interest_item.setForeground(Qt.red)
                    self.expense_table.setItem(row_position, 6, interest_item)
                else:
                    self.expense_table.setItem(row_position, 5, QTableWidgetItem("-"))
                    self.expense_table.setItem(row_position, 6, QTableWidgetItem("-"))
                
                total_amount += expense.amount
            
            session.close()
            
            # Calculate total interest for all expenses with APR
            total_interest = 0.0
            for expense in expenses:
                if expense.has_apr:
                    total_interest += self.budget_manager.calculate_monthly_interest(expense.amount, expense.apr)
            
            # Add total row
            self.expense_table.setRowCount(self.expense_table.rowCount() + 1)
            last_row = self.expense_table.rowCount() - 1
            self.expense_table.setItem(last_row, 2, QTableWidgetItem("Total:"))
            total_item = QTableWidgetItem(f"${total_amount:.2f}")
            self.expense_table.setItem(last_row, 3, total_item)
            
            # Display total monthly interest
            if total_interest > 0:
                total_interest_item = QTableWidgetItem(f"${total_interest:.2f}")
                total_interest_item.setForeground(Qt.red)
                self.expense_table.setItem(last_row, 5, QTableWidgetItem("Total Interest:"))
                self.expense_table.setItem(last_row, 6, total_interest_item)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh data: {str(e)}")
