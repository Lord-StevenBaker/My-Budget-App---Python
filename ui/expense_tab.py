from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QLineEdit, QDateEdit, QTableWidget, QTableWidgetItem,
                             QHeaderView, QFormLayout, QComboBox, QMessageBox,
                             QCheckBox, QDoubleSpinBox, QProgressBar, QGroupBox,
                             QMenu, QDialog)
from PyQt5.QtCore import Qt, QDate, QTimer, QPoint
from PyQt5.QtGui import QFont
import datetime
import traceback
import logging

# Get logger
logger = logging.getLogger('budget_app.ui.expense')


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
            logger.info("No expense categories found, creating defaults")
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
        if categories:
            logger.info(f"Found {len(categories)} expense categories")
            for category in categories:
                self.category_combo.addItem(category.name, category.id)
        else:
            logger.warning("Still no expense categories available after attempting to create defaults")
            # Add a placeholder item to avoid empty dropdown
            self.category_combo.addItem("No categories available", -1)
    
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
    
    def __init__(self, budget_manager, user_id):
        super().__init__()
        self.budget_manager = budget_manager
        self.user_id = user_id
        
        # Initialize logging
        logger.info(f"Initializing Expense Tab for user {user_id}")
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        logger.debug("Setting up expense tab UI")
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
        
        # Progress bar for potentially lengthy operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Add button
        add_button = QPushButton("Add Expense")
        add_button.clicked.connect(self.add_expense)
        
        # Edit button for table selections
        edit_button = QPushButton("Edit Selected Expense")
        edit_button.clicked.connect(self.edit_selected_expense)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(add_button)
        button_layout.addWidget(edit_button)
        
        form_section = QVBoxLayout()
        form_section.addLayout(form_layout)
        form_section.addWidget(self.progress_bar)
        form_section.addLayout(button_layout)
        
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
        
        # Load initial data
        logger.debug("Loading initial expense data")
        self.refresh_data()
    
    def add_expense(self):
        """Add a new expense record"""
        logger.debug("Add expense button clicked")
        
        try:
            # Get form values
            amount_text = self.amount_input.text()
            category_id = self.category_combo.currentData()
            date = self.date_input.date().toPyDate()
            description = self.description_input.text()
            
            logger.debug(f"Expense form values: amount={amount_text}, category_id={category_id}, "
                        f"date={date}, description={description}")
            
            # Get APR values
            has_apr = 1 if self.has_apr_checkbox.isChecked() else 0
            apr_text = self.apr_input.text() if has_apr else "0"
            
            logger.debug(f"APR values: has_apr={has_apr}, apr_text={apr_text}")
            
            # Validate input
            if not amount_text:
                logger.warning("Expense amount is empty")
                QMessageBox.warning(self, "Input Error", "Amount is required.")
                return
            
            # Validate amount
            try:
                amount = float(amount_text)
                if amount <= 0:
                    logger.warning(f"Invalid expense amount: {amount}")
                    raise ValueError("Amount must be positive")
            except ValueError as e:
                logger.warning(f"Invalid expense amount format: {amount_text}. Error: {str(e)}")
                QMessageBox.warning(self, "Input Error", "Amount must be a positive number.")
                return
                
            # Validate APR if applicable
            apr = 0.0
            if has_apr:
                try:
                    apr = float(apr_text)
                    if apr < 0:
                        logger.warning(f"Negative APR value: {apr}")
                        raise ValueError("APR cannot be negative")
                except ValueError as e:
                    logger.warning(f"Invalid APR format: {apr_text}. Error: {str(e)}")
                    QMessageBox.warning(self, "Input Error", "APR must be a valid non-negative number.")
                    return
            
            # Show progress bar for database operation
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            # Use QTimer to allow UI to update before continuing with the database operation
            QTimer.singleShot(100, lambda: self._execute_add_expense(amount, category_id, description, date, has_apr, apr))
            
        except Exception as e:
            logger.error(f"Error preparing to add expense: {str(e)}")
            logger.debug(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"An error occurred while preparing to add expense: {str(e)}")
            self.progress_bar.setVisible(False)
    
    def _execute_add_expense(self, amount, category_id, description, date, has_apr, apr):
        """Execute the database operation to add an expense"""
        try:
            logger.info(f"Adding expense: amount={amount}, category_id={category_id}, "
                       f"date={date}, has_apr={has_apr}, apr={apr}")
            
            # Make sure description is properly passed (not None)
            description = description if description else ""
            logger.info(f"Adding expense with description: '{description}'")
            
            # Add expense to database
            expense_id = self.budget_manager.add_expense(
                self.user_id, category_id, amount, description, date, has_apr, apr
            )
            
            # Update progress
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            
            if expense_id:
                logger.info(f"Expense added successfully with ID: {expense_id}")
                
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
                logger.error("Failed to add expense, database returned no ID")
                QMessageBox.warning(self, "Error", "Failed to add expense. Please try again.")
        
        except Exception as e:
            logger.error(f"Error adding expense: {str(e)}")
            logger.debug(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"An error occurred while adding expense: {str(e)}")
        finally:
            # Always hide progress bar when done
            self.progress_bar.setVisible(False)
            
    def show_context_menu(self, position):
        """Show context menu for expense table"""
        menu = QMenu()
        edit_action = menu.addAction("Edit Expense")
        
        # Get global position for menu
        global_position = self.expense_table.mapToGlobal(position)
        
        # Show menu and get selected action
        action = menu.exec_(global_position)
        
        if action == edit_action:
            # Get selected row
            selected_rows = self.expense_table.selectionModel().selectedRows()
            if not selected_rows:
                return
                
            row = selected_rows[0].row()
            # Get expense ID from first column
            expense_id = int(self.expense_table.item(row, 0).text())
            
            # Open edit dialog
            self.edit_expense(expense_id)
    
    def edit_selected_expense(self):
        """Edit the currently selected expense in the table"""
        # Get current row
        current_row = self.expense_table.currentRow()
        
        # Make sure a row is selected
        if current_row < 0:
            QMessageBox.information(self, "No Selection", "Please select an expense to edit.")
            return
        
        # Get the expense ID from the first column
        id_item = self.expense_table.item(current_row, 0)
        if not id_item:
            QMessageBox.warning(self, "Error", "Cannot find expense ID in the selected row.")
            return
            
        try:
            expense_id = int(id_item.text())
            logger.debug(f"Editing expense with ID: {expense_id}")
            
            # Call the edit dialog
            self.edit_expense(expense_id)
        except (ValueError, Exception) as e:
            logger.error(f"Error getting expense ID: {str(e)}")
            QMessageBox.warning(self, "Error", f"Could not get expense ID: {str(e)}")
            return
    
    def edit_expense(self, expense_id):
        """Open dialog to edit an expense"""
        # Get expense data
        expense = self.budget_manager.db.get_expense(expense_id)
        if not expense:
            QMessageBox.warning(self, "Error", "Could not find expense data")
            return
            
        # Create edit dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Expense")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        
        # Amount input
        amount_input = QDoubleSpinBox()
        amount_input.setRange(0.01, 1000000)
        amount_input.setValue(expense.amount)
        amount_input.setPrefix("$ ")
        amount_input.setDecimals(2)
        layout.addRow("Amount:", amount_input)
        
        # Category dropdown
        category_combo = QComboBox()
        categories = self.budget_manager.get_expense_categories()
        for category in categories:
            category_combo.addItem(category.name, category.id)
            # Set current category
            if category.id == expense.category_id:
                category_combo.setCurrentText(category.name)
        layout.addRow("Category:", category_combo)
        
        # Description input
        description_input = QLineEdit()
        description_input.setText(expense.description or "")
        layout.addRow("Description:", description_input)
        
        # Date input
        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        date_input.setDate(QDate(expense.date.year, expense.date.month, expense.date.day))
        layout.addRow("Date:", date_input)
        
        # APR checkbox and input
        apr_checkbox = QCheckBox("This is a debt with APR")
        apr_checkbox.setChecked(expense.has_apr == 1)
        layout.addRow("", apr_checkbox)
        
        apr_input = QDoubleSpinBox()
        apr_input.setRange(0, 100)
        apr_input.setValue(expense.apr)
        apr_input.setSuffix("%")
        apr_input.setEnabled(expense.has_apr == 1)
        layout.addRow("APR (Annual Percentage Rate):", apr_input)
        
        # Connect APR checkbox to enable/disable APR input
        apr_checkbox.stateChanged.connect(lambda state: apr_input.setEnabled(state == Qt.Checked))
        
        # Add buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save Changes")
        cancel_button = QPushButton("Cancel")
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addRow("", button_layout)
        
        # Connect buttons
        save_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        # Show dialog and process result
        if dialog.exec_() == QDialog.Accepted:
            # Get values from form
            new_amount = amount_input.value()
            new_category_id = category_combo.currentData()
            new_description = description_input.text()
            new_date = date_input.date().toPyDate()
            new_has_apr = 1 if apr_checkbox.isChecked() else 0
            new_apr = apr_input.value() if apr_checkbox.isChecked() else 0.0
            
            # Update expense
            success = self.budget_manager.update_expense(
                expense_id, 
                new_amount, 
                new_category_id, 
                new_description, 
                new_date, 
                new_has_apr, 
                new_apr
            )
            
            if success:
                QMessageBox.information(self, "Success", "Expense updated successfully")
                self.refresh_data()  # Refresh the table
            else:
                QMessageBox.warning(self, "Error", "Failed to update expense")
    
    def refresh_data(self):
        """Refresh the expense table with latest data"""
        logger.debug("Refreshing expense data")
        
        # Show progress indicator
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, 100)
        
        try:
            # Clear existing data
            self.expense_table.setRowCount(0)
            self.progress_bar.setValue(10)
            
            # Get filter values
            category_id = self.filter_category.currentData()
            month = self.filter_month.currentData()
            year = self.filter_year.currentData()
            
            logger.debug(f"Filter values: category_id={category_id}, month={month}, year={year}")
            
            # Calculate date range for the selected month if applicable
            if month is not None and year is not None:
                import calendar
                start_date = datetime.date(year, month, 1)
                last_day = calendar.monthrange(year, month)[1]
                end_date = datetime.date(year, month, last_day)
                logger.debug(f"Date range: {start_date} to {end_date}")
            
            # Get expense data
            expenses = []
            
            try:
                if category_id is not None:
                    logger.debug(f"Fetching expenses by category: {category_id}")
                    expenses = self.budget_manager.get_expenses_by_category(self.user_id, category_id)
                elif month is not None and year is not None:
                    # Get expenses by date range
                    logger.debug(f"Fetching expenses by date range: {start_date} to {end_date}")
                    expenses = self.budget_manager.db.get_expenses_by_date_range(
                        self.user_id, start_date, end_date
                    )
                else:
                    # Get all expenses
                    logger.debug("Fetching all expenses")
                    expenses = self.budget_manager.get_all_expenses(self.user_id)
                
                logger.debug(f"Found {len(expenses)} expenses matching criteria")
                self.progress_bar.setValue(50)
                
            except Exception as e:
                logger.error(f"Error fetching expense data: {str(e)}")
                logger.debug(traceback.format_exc())
                QMessageBox.warning(self, "Data Error", f"Error fetching expense data: {str(e)}")
                expenses = []  # Ensure we have an empty list to work with
            
            # Populate table
            total_rows = len(expenses)
            total_amount = 0.0
            total_interest = 0.0
            
            session = None
            try:
                # Get session for category lookup
                session = self.budget_manager.db.get_session()
                
                for i, expense in enumerate(expenses):
                    try:
                        row_position = self.expense_table.rowCount()
                        self.expense_table.insertRow(row_position)
                        
                        # Calculate monthly interest if applicable
                        monthly_interest = 0.0
                        if expense.has_apr and expense.apr > 0:
                            monthly_interest = self.budget_manager.calculate_monthly_interest(expense.amount, expense.apr)
                            total_interest += monthly_interest
                            
                        # Format APR display
                        apr_display = f"{expense.apr:.2f}%" if expense.has_apr else "N/A"
                        
                        # Get category name
                        category_name = "Unknown"
                        try:
                            category = session.query(self.budget_manager.db.Category).filter(
                                self.budget_manager.db.Category.id == expense.category_id
                            ).first()
                            category_name = category.name if category else "Unknown"
                        except Exception as e:
                            logger.warning(f"Error looking up category for expense {expense.id}: {str(e)}")
                        
                        # Set table items
                        self.expense_table.setItem(row_position, 0, QTableWidgetItem(str(expense.id)))
                        self.expense_table.setItem(row_position, 1, QTableWidgetItem(expense.date.strftime("%Y-%m-%d")))
                        self.expense_table.setItem(row_position, 2, QTableWidgetItem(category_name))
                        self.expense_table.setItem(row_position, 3, QTableWidgetItem(f"${expense.amount:.2f}"))
                        
                        # Make sure description is always displayed, even if None or empty
                        description_text = expense.description if expense.description else ""
                        self.expense_table.setItem(row_position, 4, QTableWidgetItem(description_text))
                        logger.debug(f"Setting description for expense {expense.id}: '{description_text}'")
                        
                        # APR and interest
                        if expense.has_apr:
                            self.expense_table.setItem(row_position, 5, QTableWidgetItem(apr_display))
                            interest_item = QTableWidgetItem(f"${monthly_interest:.2f}/mo")
                            interest_item.setForeground(Qt.red)
                            self.expense_table.setItem(row_position, 6, interest_item)
                        else:
                            self.expense_table.setItem(row_position, 5, QTableWidgetItem("-"))
                            self.expense_table.setItem(row_position, 6, QTableWidgetItem("-"))
                        
                        # Update progress and total
                        total_amount += expense.amount
                        if total_rows > 0:
                            progress_value = 50 + int((i / total_rows) * 50)
                            self.progress_bar.setValue(progress_value)
                        
                    except Exception as e:
                        logger.error(f"Error processing expense {getattr(expense, 'id', 'unknown')}: {str(e)}")
                        logger.debug(traceback.format_exc())
                        # Continue with the next expense instead of failing completely
                
                # Add total row if we have expenses
                if total_rows > 0:
                    self.expense_table.setRowCount(self.expense_table.rowCount() + 1)
                    last_row = self.expense_table.rowCount() - 1
                    self.expense_table.setItem(last_row, 2, QTableWidgetItem("Total:"))
                    total_item = QTableWidgetItem(f"${total_amount:.2f}")
                    total_item.setFont(QFont("Arial", 10, QFont.Bold))
                    self.expense_table.setItem(last_row, 3, total_item)
                    
                    # Display total monthly interest
                    if total_interest > 0:
                        self.expense_table.setItem(last_row, 5, QTableWidgetItem("Total Interest:"))
                        total_interest_item = QTableWidgetItem(f"${total_interest:.2f}/mo")
                        total_interest_item.setForeground(Qt.red)
                        total_interest_item.setFont(QFont("Arial", 10, QFont.Bold))
                        self.expense_table.setItem(last_row, 6, total_interest_item)
                
                logger.debug(f"Expense table updated with {self.expense_table.rowCount()} rows")
                logger.info(f"Total expenses: ${total_amount:.2f}, Total monthly interest: ${total_interest:.2f}")
                
            except Exception as e:
                logger.error(f"Error populating expense table: {str(e)}")
                logger.debug(traceback.format_exc())
                QMessageBox.critical(self, "Error", f"Failed to refresh data: {str(e)}")
            finally:
                # Always close the session
                if session:
                    session.close()
        
        except Exception as e:
            logger.error(f"Error refreshing expense data: {str(e)}")
            logger.debug(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"An error occurred while refreshing expense data: {str(e)}")
        finally:
            # Always update progress and hide progress bar when done
            self.progress_bar.setValue(100)
            self.progress_bar.setVisible(False)
