from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                         QPushButton, QComboBox, QDateEdit, QTabWidget,
                         QTableWidget, QTableWidgetItem, QHeaderView, 
                         QGroupBox, QFormLayout, QMessageBox, QSplitter)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QPixmap
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import datetime
import pandas as pd


class ReportsTab(QWidget):
    """Tab for generating and viewing financial reports"""
    
    def __init__(self, budget_manager, user_id):
        super().__init__()
        self.budget_manager = budget_manager
        self.user_id = user_id
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout()
        
        # Create report controls
        controls_group = QGroupBox("Report Controls")
        controls_layout = QVBoxLayout()
        
        # Date range selection
        date_form = QFormLayout()
        
        # Report type selection
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItem("Expense Breakdown", "expense_breakdown")
        self.report_type_combo.addItem("Income Sources", "income_sources")
        self.report_type_combo.addItem("Monthly Summary", "monthly_summary")
        self.report_type_combo.addItem("Income vs Expenses", "income_vs_expenses")
        self.report_type_combo.addItem("Debt Overview", "debt_overview")
        self.report_type_combo.currentIndexChanged.connect(self.report_type_changed)
        date_form.addRow("Report Type:", self.report_type_combo)
        
        # Date range
        date_range_layout = QHBoxLayout()
        
        self.start_date = QDateEdit(calendarPopup=True)
        self.start_date.setDate(QDate.currentDate().addMonths(-3))
        
        self.end_date = QDateEdit(calendarPopup=True)
        self.end_date.setDate(QDate.currentDate())
        
        date_range_layout.addWidget(QLabel("From:"))
        date_range_layout.addWidget(self.start_date)
        date_range_layout.addWidget(QLabel("To:"))
        date_range_layout.addWidget(self.end_date)
        
        date_form.addRow("Date Range:", date_range_layout)
        
        # Time period selection for trend reports
        self.period_combo = QComboBox()
        self.period_combo.addItem("Last 3 Months", 3)
        self.period_combo.addItem("Last 6 Months", 6)
        self.period_combo.addItem("Last 12 Months", 12)
        date_form.addRow("Time Period:", self.period_combo)
        
        controls_layout.addLayout(date_form)
        
        # Generate report button
        generate_button = QPushButton("Generate Report")
        generate_button.clicked.connect(self.generate_report)
        controls_layout.addWidget(generate_button)
        
        controls_group.setLayout(controls_layout)
        main_layout.addWidget(controls_group)
        
        # Create a splitter for the report view
        splitter = QSplitter(Qt.Vertical)
        
        # Chart area
        self.chart_widget = QWidget()
        self.chart_layout = QVBoxLayout(self.chart_widget)
        self.chart_layout.addWidget(QLabel("Generate a report to see charts"))
        
        # Data table
        self.table_widget = QTableWidget()
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)  # Make table read-only
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        splitter.addWidget(self.chart_widget)
        splitter.addWidget(self.table_widget)
        splitter.setSizes([400, 300])  # Set initial sizes
        
        main_layout.addWidget(splitter, 1)  # 1 = stretch factor
        
        # Initialize UI state
        self.report_type_changed(0)
        
        self.setLayout(main_layout)
    
    def report_type_changed(self, index):
        """Handle report type change"""
        report_type = self.report_type_combo.currentData()
        
        # Show/hide appropriate controls
        if report_type in ["expense_breakdown", "income_sources", "debt_overview"]:
            self.start_date.setEnabled(True)
            self.end_date.setEnabled(True)
            self.period_combo.setEnabled(False)
        elif report_type in ["monthly_summary", "income_vs_expenses"]:
            self.start_date.setEnabled(False)
            self.end_date.setEnabled(False)
            self.period_combo.setEnabled(True)
    
    def generate_report(self):
        """Generate the selected report"""
        try:
            report_type = self.report_type_combo.currentData()
            
            # Clear previous report
            self._clear_chart()
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(0)
            
            if report_type == "expense_breakdown":
                self._generate_expense_breakdown()
            elif report_type == "income_sources":
                self._generate_income_sources()
            elif report_type == "monthly_summary":
                self._generate_monthly_summary()
            elif report_type == "income_vs_expenses":
                self._generate_income_vs_expenses()
            elif report_type == "debt_overview":
                self._generate_debt_overview()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")
    
    def _clear_chart(self):
        """Clear the chart area"""
        # Remove all widgets from chart layout
        while self.chart_layout.count():
            item = self.chart_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
    
    def _generate_expense_breakdown(self):
        """Generate expense breakdown report"""
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        
        # Get expense data
        expenses_by_category = self.budget_manager.get_expenses_by_category_summary(
            self.user_id, start_date, end_date
        )
        
        if not expenses_by_category:
            self.chart_layout.addWidget(QLabel("No expense data available for the selected period"))
            return
        
        # Create pie chart
        figure = Figure(figsize=(8, 6))
        canvas = FigureCanvas(figure)
        ax = figure.add_subplot(111)
        
        labels = list(expenses_by_category.keys())
        sizes = list(expenses_by_category.values())
        
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        ax.set_title('Expense Breakdown by Category')
        
        self.chart_layout.addWidget(canvas)
        
        # Create data table
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["Category", "Amount"])
        
        total = sum(sizes)
        
        for i, (category, amount) in enumerate(expenses_by_category.items()):
            self.table_widget.insertRow(i)
            self.table_widget.setItem(i, 0, QTableWidgetItem(category))
            self.table_widget.setItem(i, 1, QTableWidgetItem(f"${amount:.2f}"))
        
        # Add total row
        row = self.table_widget.rowCount()
        self.table_widget.insertRow(row)
        self.table_widget.setItem(row, 0, QTableWidgetItem("Total"))
        self.table_widget.setItem(row, 1, QTableWidgetItem(f"${total:.2f}"))
    
    def _generate_income_sources(self):
        """Generate income sources report"""
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        
        # Get income data
        df = self.budget_manager.generate_income_report(self.user_id, start_date, end_date)
        
        if df.empty:
            self.chart_layout.addWidget(QLabel("No income data available for the selected period"))
            return
        
        # Group by source
        income_by_source = df.groupby('source')['amount'].sum()
        
        # Create pie chart
        figure = Figure(figsize=(8, 6))
        canvas = FigureCanvas(figure)
        ax = figure.add_subplot(111)
        
        labels = income_by_source.index
        sizes = income_by_source.values
        
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        ax.set_title('Income by Source')
        
        self.chart_layout.addWidget(canvas)
        
        # Create data table
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["Source", "Amount"])
        
        total = income_by_source.sum()
        
        for i, (source, amount) in enumerate(income_by_source.items()):
            self.table_widget.insertRow(i)
            self.table_widget.setItem(i, 0, QTableWidgetItem(source))
            self.table_widget.setItem(i, 1, QTableWidgetItem(f"${amount:.2f}"))
        
        # Add total row
        row = self.table_widget.rowCount()
        self.table_widget.insertRow(row)
        self.table_widget.setItem(row, 0, QTableWidgetItem("Total"))
        self.table_widget.setItem(row, 1, QTableWidgetItem(f"${total:.2f}"))
    
    def _generate_monthly_summary(self):
        """Generate monthly summary report"""
        months = self.period_combo.currentData()
        df = self.budget_manager.generate_monthly_summary(self.user_id, months)
        
        if df.empty:
            self.chart_layout.addWidget(QLabel("No data available for the selected period"))
            return
        
        # Create bar chart
        figure = Figure(figsize=(10, 6))
        canvas = FigureCanvas(figure)
        ax = figure.add_subplot(111)
        
        x = range(len(df))
        width = 0.25
        
        # Plot bars
        income_bars = ax.bar([i - width for i in x], df['income'], width, label='Income')
        expense_bars = ax.bar(x, df['expense'], width, label='Expenses')
        savings_bars = ax.bar([i + width for i in x], df['savings'], width, label='Savings')
        
        # Add labels and legend
        ax.set_xlabel('Month')
        ax.set_ylabel('Amount')
        ax.set_title('Monthly Financial Summary')
        ax.set_xticks(x)
        ax.set_xticklabels(df['month'])
        ax.legend()
        
        # Color savings bars based on positive/negative
        for i, bar in enumerate(savings_bars):
            if df['savings'][i] < 0:
                bar.set_color('red')
            else:
                bar.set_color('green')
        
        figure.tight_layout()
        self.chart_layout.addWidget(canvas)
        
        # Create data table
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["Month", "Income", "Expenses", "Savings"])
        
        for i in range(len(df)):
            self.table_widget.insertRow(i)
            self.table_widget.setItem(i, 0, QTableWidgetItem(df['month'][i]))
            self.table_widget.setItem(i, 1, QTableWidgetItem(f"${df['income'][i]:.2f}"))
            self.table_widget.setItem(i, 2, QTableWidgetItem(f"${df['expense'][i]:.2f}"))
            
            savings_item = QTableWidgetItem(f"${df['savings'][i]:.2f}")
            if df['savings'][i] < 0:
                savings_item.setForeground(Qt.red)
            else:
                savings_item.setForeground(Qt.darkGreen)
                
            self.table_widget.setItem(i, 3, savings_item)
    
    def _generate_income_vs_expenses(self):
        """Generate income vs expenses trend report"""
        months = self.period_combo.currentData()
        df = self.budget_manager.generate_monthly_summary(self.user_id, months)
        
        if df.empty:
            self.chart_layout.addWidget(QLabel("No data available for the selected period"))
            return
        
        # Create line chart
        figure = Figure(figsize=(10, 6))
        canvas = FigureCanvas(figure)
        ax = figure.add_subplot(111)
        
        ax.plot(df['month'], df['income'], 'g-', marker='o', label='Income')
        ax.plot(df['month'], df['expense'], 'r-', marker='o', label='Expenses')
        ax.plot(df['month'], df['savings'], 'b--', marker='s', label='Savings')
        
        # Add labels and legend
        ax.set_xlabel('Month')
        ax.set_ylabel('Amount')
        ax.set_title('Income vs Expenses Trend')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        
        figure.tight_layout()
        self.chart_layout.addWidget(canvas)
        
        # Create data table - same as monthly summary
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["Month", "Income", "Expenses", "Savings"])
        
        total_income = 0
        total_expenses = 0
        total_savings = 0
        
        for i in range(len(df)):
            self.table_widget.insertRow(i)
            self.table_widget.setItem(i, 0, QTableWidgetItem(df['month'][i]))
            self.table_widget.setItem(i, 1, QTableWidgetItem(f"${df['income'][i]:.2f}"))
            self.table_widget.setItem(i, 2, QTableWidgetItem(f"${df['expense'][i]:.2f}"))
            
            savings_item = QTableWidgetItem(f"${df['savings'][i]:.2f}")
            if df['savings'][i] < 0:
                savings_item.setForeground(Qt.red)
            else:
                savings_item.setForeground(Qt.darkGreen)
                
            self.table_widget.setItem(i, 3, savings_item)
            
            total_income += df['income'][i]
            total_expenses += df['expense'][i]
            total_savings += df['savings'][i]
        
        # Add total row
        row = self.table_widget.rowCount()
        self.table_widget.insertRow(row)
        self.table_widget.setItem(row, 0, QTableWidgetItem("Total"))
        self.table_widget.setItem(row, 1, QTableWidgetItem(f"${total_income:.2f}"))
        self.table_widget.setItem(row, 2, QTableWidgetItem(f"${total_expenses:.2f}"))
        
        savings_item = QTableWidgetItem(f"${total_savings:.2f}")
        if total_savings < 0:
            savings_item.setForeground(Qt.red)
        else:
            savings_item.setForeground(Qt.darkGreen)
            
        self.table_widget.setItem(row, 3, savings_item)
        
    def _generate_debt_overview(self):
        """Generate a debt and interest overview report"""
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        
        # Get debt report data
        df = self.budget_manager.generate_debt_report(self.user_id, start_date, end_date)
        
        if df.empty or len(df) <= 1:  # Only the summary row, no actual data
            self.chart_layout.addWidget(QLabel("No debt expenses with APR found in the selected period"))
            return
        
        # Create stacked bar chart showing principal vs annual interest
        figure = Figure(figsize=(10, 6))
        canvas = FigureCanvas(figure)
        ax = figure.add_subplot(111)
        
        # Remove the summary row for the chart
        chart_df = df[df['id'] != 'TOTAL'].copy()
        
        # Prepare data for the chart
        categories = chart_df['description']
        principal = chart_df['amount']
        annual_interest = chart_df['annual_interest']
        
        # Create the stacked bar chart
        bar_width = 0.5
        bars1 = ax.bar(categories, principal, bar_width, label='Principal')
        bars2 = ax.bar(categories, annual_interest, bar_width, bottom=principal, label='Annual Interest', color='red')
        
        # Customize the chart
        ax.set_ylabel('Amount ($)')
        ax.set_title('Debt Principal vs Annual Interest')
        ax.legend()
        
        # Rotate x-axis labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        figure.tight_layout()
        
        self.chart_layout.addWidget(canvas)
        
        # Create data table
        self.table_widget.setColumnCount(7)
        self.table_widget.setHorizontalHeaderLabels([
            "Date", "Description", "Category", "Principal ($)", "APR (%)", 
            "Monthly Interest ($)", "Annual Interest ($)"
        ])
        
        # Populate the table
        for i in range(len(df)):
            self.table_widget.insertRow(i)
            
            # Different formatting for the summary row
            if df['id'][i] == 'TOTAL':
                # Summary row with totals
                self.table_widget.setItem(i, 0, QTableWidgetItem(""))
                
                total_item = QTableWidgetItem("TOTAL")
                total_item.setFont(QFont("Arial", 10, QFont.Bold))
                self.table_widget.setItem(i, 1, total_item)
                
                self.table_widget.setItem(i, 2, QTableWidgetItem(""))
                
                amount_item = QTableWidgetItem(f"${df['amount'][i]:.2f}")
                amount_item.setFont(QFont("Arial", 10, QFont.Bold))
                self.table_widget.setItem(i, 3, amount_item)
                
                self.table_widget.setItem(i, 4, QTableWidgetItem(""))
                
                monthly_item = QTableWidgetItem(f"${df['monthly_interest'][i]:.2f}")
                monthly_item.setFont(QFont("Arial", 10, QFont.Bold))
                monthly_item.setForeground(Qt.red)
                self.table_widget.setItem(i, 5, monthly_item)
                
                annual_item = QTableWidgetItem(f"${df['annual_interest'][i]:.2f}")
                annual_item.setFont(QFont("Arial", 10, QFont.Bold))
                annual_item.setForeground(Qt.red)
                self.table_widget.setItem(i, 6, annual_item)
            else:
                # Regular data row
                date_str = df['date'][i].strftime("%Y-%m-%d") if df['date'][i] else ""
                self.table_widget.setItem(i, 0, QTableWidgetItem(date_str))
                self.table_widget.setItem(i, 1, QTableWidgetItem(str(df['description'][i])))
                self.table_widget.setItem(i, 2, QTableWidgetItem(str(df['category'][i])))
                self.table_widget.setItem(i, 3, QTableWidgetItem(f"${df['amount'][i]:.2f}"))
                self.table_widget.setItem(i, 4, QTableWidgetItem(f"{df['apr'][i]:.2f}%"))
                
                monthly_item = QTableWidgetItem(f"${df['monthly_interest'][i]:.2f}")
                monthly_item.setForeground(Qt.red)
                self.table_widget.setItem(i, 5, monthly_item)
                
                annual_item = QTableWidgetItem(f"${df['annual_interest'][i]:.2f}")
                annual_item.setForeground(Qt.red)
                self.table_widget.setItem(i, 6, annual_item)
        
        # Add a section with financial insights
        insights_frame = QFrame()
        insights_layout = QVBoxLayout(insights_frame)
        
        # Get the summary row data
        summary = df[df['id'] == 'TOTAL'].iloc[0]
        total_principal = summary['amount']
        total_monthly_interest = summary['monthly_interest']
        total_annual_interest = summary['annual_interest']
        
        # Calculate some insights
        interest_to_principal_ratio = (total_annual_interest / total_principal * 100) if total_principal > 0 else 0
        
        insights_title = QLabel("Debt Insights")
        insights_title.setFont(QFont("Arial", 12, QFont.Bold))
        insights_layout.addWidget(insights_title)
        
        insights_layout.addWidget(QLabel(f"• Total debt principal: ${total_principal:.2f}"))
        insights_layout.addWidget(QLabel(f"• Total monthly interest: ${total_monthly_interest:.2f}"))
        insights_layout.addWidget(QLabel(f"• Total annual interest: ${total_annual_interest:.2f}"))
        insights_layout.addWidget(QLabel(f"• Interest to principal ratio: {interest_to_principal_ratio:.2f}%"))
        
        if interest_to_principal_ratio > 20:
            recommendation = QLabel("⚠️ High interest ratio detected! Consider prioritizing debt repayment.")
            recommendation.setStyleSheet("color: red;")
            insights_layout.addWidget(recommendation)
        
        self.chart_layout.addWidget(insights_frame)
    
    def refresh_data(self):
        """Refresh report data if needed"""
        # Nothing to refresh automatically
