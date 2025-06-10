from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                         QFrame, QSizePolicy, QScrollArea, QPushButton)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette
import datetime
import calendar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class DashboardTab(QWidget):
    """Dashboard tab showing summary of financial status"""
    
    def __init__(self, budget_manager, user_id):
        super().__init__()
        self.budget_manager = budget_manager
        self.user_id = user_id
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Store references to widgets we'll need to update
        self.widgets = {}
        
        # Create main layout
        main_layout = QVBoxLayout()
        
        # Dashboard title
        title_label = QLabel("Financial Dashboard")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Add scrollable area for dashboard widgets
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout = scroll_layout  # Store reference
        
        # Monthly summary section
        month_summary = self.create_month_summary_widget()
        scroll_layout.addWidget(month_summary)
        self.widgets['month_summary'] = month_summary
        
        # Budget status section
        budget_status = self.create_budget_status_widget()
        scroll_layout.addWidget(budget_status)
        self.widgets['budget_status'] = budget_status
        
        # Expense breakdown chart
        expense_chart = self.create_expense_chart_widget()
        scroll_layout.addWidget(expense_chart)
        self.widgets['expense_chart'] = expense_chart
        
        # Monthly trend chart
        trend_chart = self.create_trend_chart_widget()
        scroll_layout.addWidget(trend_chart)
        self.widgets['trend_chart'] = trend_chart
        
        # Add stretch to push everything to the top
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
        
    def create_month_summary_widget(self):
        """Create the monthly summary widget"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("This Month's Summary")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Get current month data
        today = datetime.date.today()
        month_start = datetime.date(today.year, today.month, 1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        month_end = datetime.date(today.year, today.month, last_day)
        
        income = self.budget_manager.get_total_income(self.user_id, month_start, month_end)
        expenses = self.budget_manager.get_total_expense(self.user_id, month_start, month_end)
        savings = income - expenses
        
        # Create summary boxes
        summary_layout = QHBoxLayout()
        
        # Income box
        income_box = self.create_summary_box("Income", f"${income:.2f}", "green")
        summary_layout.addWidget(income_box)
        
        # Expenses box
        expense_box = self.create_summary_box("Expenses", f"${expenses:.2f}", "red")
        summary_layout.addWidget(expense_box)
        
        # Savings box
        savings_color = "green" if savings >= 0 else "red"
        savings_box = self.create_summary_box("Savings", f"${savings:.2f}", savings_color)
        summary_layout.addWidget(savings_box)
        
        layout.addLayout(summary_layout)
        frame.setLayout(layout)
        return frame
    
    def create_summary_box(self, title, value, color):
        """Create a summary statistic box"""
        box = QFrame()
        box.setFrameShape(QFrame.StyledPanel)
        box.setFrameShadow(QFrame.Raised)
        box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setFont(QFont("Arial", 16, QFont.Bold))
        
        # Set text color
        if color == "green":
            value_label.setStyleSheet("color: green")
        elif color == "red":
            value_label.setStyleSheet("color: red")
        elif color == "blue":
            value_label.setStyleSheet("color: blue")
        
        layout.addWidget(value_label)
        box.setLayout(layout)
        return box
    
    def create_budget_status_widget(self):
        """Create the budget status widget"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Budget Status")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Get budget status
        today = datetime.date.today()
        budget_status = self.budget_manager.get_budget_status(self.user_id, today.month, today.year)
        
        if not budget_status:
            layout.addWidget(QLabel("No budget data available for this month."))
        else:
            for category, data in budget_status.items():
                # Category label
                cat_label = QLabel(f"{category}")
                cat_label.setFont(QFont("Arial", 11, QFont.Bold))
                layout.addWidget(cat_label)
                
                # Progress info
                info_layout = QHBoxLayout()
                info_layout.addWidget(QLabel(f"Budget: ${data['budget']:.2f}"))
                info_layout.addWidget(QLabel(f"Spent: ${data['spent']:.2f}"))
                info_layout.addWidget(QLabel(f"Remaining: ${data['remaining']:.2f}"))
                layout.addLayout(info_layout)
                
                # Add some spacing
                layout.addSpacing(10)
        
        frame.setLayout(layout)
        return frame
    
    def create_expense_chart_widget(self):
        """Create expense breakdown chart widget"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Expense Breakdown")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Create matplotlib figure
        figure = Figure(figsize=(6, 4), dpi=100)
        canvas = FigureCanvas(figure)
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Get expense data
        today = datetime.date.today()
        month_start = datetime.date(today.year, today.month, 1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        month_end = datetime.date(today.year, today.month, last_day)
        
        expenses_by_category = self.budget_manager.get_expenses_by_category_summary(
            self.user_id, month_start, month_end
        )
        
        if expenses_by_category:
            ax = figure.add_subplot(111)
            labels = list(expenses_by_category.keys())
            sizes = list(expenses_by_category.values())
            
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            
        else:
            ax = figure.add_subplot(111)
            ax.text(0.5, 0.5, "No expense data available", 
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax.transAxes)
            ax.axis('off')
        
        layout.addWidget(canvas)
        frame.setLayout(layout)
        return frame
    
    def create_trend_chart_widget(self):
        """Create monthly trend chart widget"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Monthly Financial Trends")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        try:
            # Get monthly summary data
            df = self.budget_manager.generate_monthly_summary(self.user_id, 6)  # Last 6 months
            
            # Create figure and axes
            figure = Figure(figsize=(8, 4), dpi=100)
            canvas = FigureCanvas(figure)
            canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            ax = figure.add_subplot(111)
            
            if df is not None and not df.empty and len(df) > 0:
                # Verify required columns exist
                required_cols = ['Period', 'Total Income', 'Total Expenses', 'Net Savings']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    # Missing columns, show error message in chart
                    ax.text(0.5, 0.5, f"Error: Missing columns in data: {', '.join(missing_cols)}",
                            horizontalalignment='center', verticalalignment='center',
                            transform=ax.transAxes)
                    ax.set_title('Data Format Error')
                else:
                    # Data is valid, create the chart
                    try:
                        months = df['Period']
                        income = df['Total Income']
                        expense = df['Total Expenses']
                        savings = df['Net Savings']
                        
                        # Create line chart
                        ax.plot(months, income, 'g-', label='Income')
                        ax.plot(months, expense, 'r-', label='Expense')
                        ax.plot(months, savings, 'b-', label='Savings')
                        
                        ax.set_xlabel('Month')
                        ax.set_ylabel('Amount')
                        ax.legend()
                        ax.set_title('Monthly Financial Trends')
                        
                    except Exception as e:
                        print(f"Error processing chart data: {e}")
                        ax.text(0.5, 0.5, f"Error processing data: {str(e)}",
                            horizontalalignment='center', verticalalignment='center',
                            transform=ax.transAxes)
                        ax.set_title('Data Processing Error')
            else:
                # Create an empty chart with informative message
                ax.text(0.5, 0.5, "No financial data available for monthly trends.",
                        horizontalalignment='center', verticalalignment='center',
                        transform=ax.transAxes)
                ax.set_title('No Data Available')
                
            # Add the canvas to the layout
            layout.addWidget(canvas)
            
        except Exception as e:
            # Handle any unexpected errors
            print(f"Unexpected error in trend chart creation: {e}")
            
            # Create a fallback message
            error_label = QLabel(f"Error loading trend chart: {str(e)}")
            error_label.setStyleSheet("color: red;")
            layout.addWidget(error_label)
        
        frame.setLayout(layout)
        return frame
    
    def refresh_data(self):
        """Refresh all data in the dashboard without rebuilding the entire UI"""
        try:
            print("Refreshing dashboard data...")
            
            # Check if we have our widget references
            if not hasattr(self, 'widgets') or not self.widgets:
                print("Widget references not found, rebuilding UI...")
                # If we don't have widget references, rebuild the UI completely
                layout = self.layout()
                if layout:
                    while layout.count():
                        child = layout.takeAt(0)
                        if child.widget():
                            child.widget().deleteLater()
                self.init_ui()
                return
                
            # Get current data
            today = datetime.date.today()
            month_start = datetime.date(today.year, today.month, 1)
            last_day = calendar.monthrange(today.year, today.month)[1]
            month_end = datetime.date(today.year, today.month, last_day)
            
            # Update monthly summary widget
            if 'month_summary' in self.widgets:
                # Remove old widget
                old_widget = self.widgets['month_summary']
                index = self.scroll_layout.indexOf(old_widget)
                if index >= 0:
                    self.scroll_layout.removeWidget(old_widget)
                    old_widget.deleteLater()
                
                # Create new widget with fresh data
                new_widget = self.create_month_summary_widget()
                self.scroll_layout.insertWidget(index, new_widget)
                self.widgets['month_summary'] = new_widget
            
            # Update budget status widget
            if 'budget_status' in self.widgets:
                # Remove old widget
                old_widget = self.widgets['budget_status']
                index = self.scroll_layout.indexOf(old_widget)
                if index >= 0:
                    self.scroll_layout.removeWidget(old_widget)
                    old_widget.deleteLater()
                
                # Create new widget with fresh data
                new_widget = self.create_budget_status_widget()
                self.scroll_layout.insertWidget(index, new_widget)
                self.widgets['budget_status'] = new_widget
            
            # Update expense chart widget
            if 'expense_chart' in self.widgets:
                # Remove old widget
                old_widget = self.widgets['expense_chart']
                index = self.scroll_layout.indexOf(old_widget)
                if index >= 0:
                    self.scroll_layout.removeWidget(old_widget)
                    old_widget.deleteLater()
                
                # Create new widget with fresh data
                new_widget = self.create_expense_chart_widget()
                self.scroll_layout.insertWidget(index, new_widget)
                self.widgets['expense_chart'] = new_widget
            
            # Update trend chart widget
            if 'trend_chart' in self.widgets:
                # Remove old widget
                old_widget = self.widgets['trend_chart']
                index = self.scroll_layout.indexOf(old_widget)
                if index >= 0:
                    self.scroll_layout.removeWidget(old_widget)
                    old_widget.deleteLater()
                
                # Create new widget with fresh data
                new_widget = self.create_trend_chart_widget()
                self.scroll_layout.insertWidget(index, new_widget)
                self.widgets['trend_chart'] = new_widget
                
            # Force layout update
            self.scroll_layout.update()
            
        except Exception as e:
            print(f"Error refreshing dashboard: {e}")
            # Create a simple error message if refresh fails
            layout = QVBoxLayout()
            error_label = QLabel(f"Error refreshing dashboard: {str(e)}")
            error_label.setStyleSheet("color: red;")
            layout.addWidget(error_label)
            
            # Add a refresh button
            refresh_btn = QPushButton("Refresh Dashboard")
            refresh_btn.clicked.connect(self.refresh_data)
            layout.addWidget(refresh_btn)
            
            # Replace current layout
            QWidget().setLayout(self.layout())
            self.setLayout(layout)
