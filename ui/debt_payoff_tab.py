from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                         QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
                         QTableWidget, QTableWidgetItem, QHeaderView, 
                         QGroupBox, QFormLayout, QMessageBox, QSplitter,
                         QRadioButton, QButtonGroup, QScrollArea, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
import datetime
from debt_payoff_calculator import DebtPayoffCalculator


class DebtPayoffTab(QWidget):
    """Tab for debt payoff calculator and strategy analysis"""
    
    def __init__(self, budget_manager, user_id):
        super().__init__()
        self.budget_manager = budget_manager
        self.user_id = user_id
        self.debt_calculator = DebtPayoffCalculator(budget_manager)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout()
        
        # Create title
        title_label = QLabel("Debt Payoff Calculator")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Create control panel
        controls_group = QGroupBox("Payoff Strategy Controls")
        controls_layout = QFormLayout()
        
        # Strategy selection
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItem("Highest Interest First (Avalanche)", "highest_interest")
        self.strategy_combo.addItem("Lowest Balance First (Snowball)", "lowest_balance")
        self.strategy_combo.addItem("Debt Avalanche", "avalanche")
        self.strategy_combo.addItem("Debt Snowball", "snowball")
        controls_layout.addRow("Payoff Strategy:", self.strategy_combo)
        
        # Additional payment input
        self.extra_payment_input = QDoubleSpinBox()
        self.extra_payment_input.setRange(0, 10000)
        self.extra_payment_input.setValue(100)
        self.extra_payment_input.setPrefix("$ ")
        self.extra_payment_input.setSingleStep(25)
        controls_layout.addRow("Additional Monthly Payment:", self.extra_payment_input)
        
        # Calculate button
        calculate_button = QPushButton("Calculate Payoff Plan")
        calculate_button.clicked.connect(self.calculate_payoff_plan)
        
        # Compare strategies button
        compare_button = QPushButton("Compare All Strategies")
        compare_button.clicked.connect(self.compare_strategies)
        
        # Add buttons to a horizontal layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(calculate_button)
        buttons_layout.addWidget(compare_button)
        
        controls_layout.addRow("", buttons_layout)
        controls_group.setLayout(controls_layout)
        main_layout.addWidget(controls_group)
        
        # Create splitter for chart and results
        splitter = QSplitter(Qt.Vertical)
        
        # Chart area
        self.chart_widget = QWidget()
        self.chart_layout = QVBoxLayout(self.chart_widget)
        self.default_label = QLabel("Select a strategy and calculate to see the payoff projection")
        self.default_label.setAlignment(Qt.AlignCenter)
        self.chart_layout.addWidget(self.default_label)
        
        # Results area with scroll
        results_scroll = QScrollArea()
        results_scroll.setWidgetResizable(True)
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        results_scroll.setWidget(self.results_widget)
        
        # Add to splitter
        splitter.addWidget(self.chart_widget)
        splitter.addWidget(results_scroll)
        splitter.setSizes([400, 400])
        
        main_layout.addWidget(splitter, 1)  # 1 = stretch factor
        self.setLayout(main_layout)
    
    def calculate_payoff_plan(self):
        """Calculate and display the debt payoff plan"""
        try:
            # Get user inputs
            strategy = self.strategy_combo.currentData()
            extra_payment = self.extra_payment_input.value()
            
            # Clear previous results
            self._clear_results()
            
            # Calculate payoff plan
            results_df, summary, debts = self.debt_calculator.calculate_payoff_plan(
                self.user_id, extra_payment, strategy
            )
            
            if results_df.empty or not summary:
                self.results_layout.addWidget(QLabel("No debt expenses found. Add expenses with APR to use this calculator."))
                return
            
            # Create payoff chart
            self._create_payoff_chart(strategy, extra_payment)
            
            # Create summary section
            summary_group = QGroupBox("Payoff Summary")
            summary_layout = QFormLayout()
            
            summary_layout.addRow("Total Debt Amount:", 
                                 QLabel(f"${summary['original_balance']:.2f}"))
            summary_layout.addRow("Monthly Payment:", 
                                 QLabel(f"${summary['monthly_payment']:.2f}"))
            summary_layout.addRow("Time to Debt Freedom:", 
                                 QLabel(f"{summary['total_months']} months ({summary['total_months']/12:.1f} years)"))
            summary_layout.addRow("Total Interest Paid:", 
                                 QLabel(f"${summary['total_interest_paid']:.2f}"))
            summary_layout.addRow("Total Amount Paid:", 
                                 QLabel(f"${summary['total_amount_paid']:.2f}"))
            
            summary_group.setLayout(summary_layout)
            self.results_layout.addWidget(summary_group)
            
            # Create debt payoff order table
            self._create_debt_table(debts)
            
            # Create payment schedule table (show first 12 months)
            self._create_payment_schedule(results_df[:12])
            
            # Add improvement suggestions
            self._add_improvement_suggestions(summary, extra_payment)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to calculate payoff plan: {str(e)}")
    
    def compare_strategies(self):
        """Compare different debt payoff strategies"""
        try:
            # Get additional payment amount
            extra_payment = self.extra_payment_input.value()
            
            # Clear previous results
            self._clear_results()
            
            # Get comparison results
            strategy_results = self.debt_calculator.compare_strategies(self.user_id, extra_payment)
            
            if not strategy_results:
                self.results_layout.addWidget(QLabel("No debt expenses found. Add expenses with APR to use this calculator."))
                return
            
            # Create comparison chart
            chart_buf = self.debt_calculator.create_comparison_chart(self.user_id, extra_payment)
            if chart_buf:
                self._clear_chart()
                from PyQt5.QtGui import QPixmap
                pixmap = QPixmap()
                pixmap.loadFromData(chart_buf.read())
                chart_label = QLabel()
                chart_label.setPixmap(pixmap)
                chart_label.setAlignment(Qt.AlignCenter)
                self.chart_layout.addWidget(chart_label)
            
            # Create comparison table
            comparison_group = QGroupBox("Strategy Comparison")
            comparison_layout = QVBoxLayout()
            
            table = QTableWidget(len(strategy_results), 3)
            table.setHorizontalHeaderLabels(["Strategy", "Time to Payoff", "Total Interest"])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            
            for i, (strategy, data) in enumerate(strategy_results.items()):
                table.setItem(i, 0, QTableWidgetItem(strategy))
                table.setItem(i, 1, QTableWidgetItem(f"{data['months']} months"))
                table.setItem(i, 2, QTableWidgetItem(f"${data['interest']:.2f}"))
            
            comparison_layout.addWidget(table)
            comparison_group.setLayout(comparison_layout)
            self.results_layout.addWidget(comparison_group)
            
            # Add recommendations
            self._add_strategy_recommendation(strategy_results)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to compare strategies: {str(e)}")
    
    def _clear_chart(self):
        """Clear the chart area"""
        while self.chart_layout.count():
            item = self.chart_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
    
    def _clear_results(self):
        """Clear the results area"""
        self._clear_chart()
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
    
    def _create_payoff_chart(self, strategy, extra_payment):
        """Create and display the payoff chart"""
        chart_buf = self.debt_calculator.create_payoff_chart(self.user_id, extra_payment, strategy)
        if chart_buf:
            self._clear_chart()
            from PyQt5.QtGui import QPixmap
            pixmap = QPixmap()
            pixmap.loadFromData(chart_buf.read())
            chart_label = QLabel()
            chart_label.setPixmap(pixmap)
            chart_label.setAlignment(Qt.AlignCenter)
            self.chart_layout.addWidget(chart_label)
    
    def _create_debt_table(self, debts):
        """Create a table showing debt payoff order"""
        if not debts:
            return
            
        debt_group = QGroupBox("Debt Payoff Order")
        debt_layout = QVBoxLayout()
        
        table = QTableWidget(len(debts), 6)
        table.setHorizontalHeaderLabels([
            "Description", "Category", "Balance", "APR", 
            "Minimum Payment", "Payoff Month"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        for i, debt in enumerate(debts):
            table.setItem(i, 0, QTableWidgetItem(debt['description']))
            table.setItem(i, 1, QTableWidgetItem(debt['category']))
            table.setItem(i, 2, QTableWidgetItem(f"${debt['balance']:.2f}"))
            table.setItem(i, 3, QTableWidgetItem(f"{debt['apr']:.2f}%"))
            table.setItem(i, 4, QTableWidgetItem(f"${debt['min_payment']:.2f}"))
            table.setItem(i, 5, QTableWidgetItem(f"{debt.get('payoff_month', '-')}"))
        
        debt_layout.addWidget(table)
        debt_group.setLayout(debt_layout)
        self.results_layout.addWidget(debt_group)
    
    def _create_payment_schedule(self, results_df):
        """Create a table showing payment schedule for first months"""
        if results_df.empty:
            return
            
        schedule_group = QGroupBox("Payment Schedule (First Year)")
        schedule_layout = QVBoxLayout()
        
        table = QTableWidget(len(results_df), 5)
        table.setHorizontalHeaderLabels([
            "Month", "Payment", "Interest", "Remaining Balance", "Progress"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        for i, (_, row) in enumerate(results_df.iterrows()):
            table.setItem(i, 0, QTableWidgetItem(f"{int(row['month'])}"))
            table.setItem(i, 1, QTableWidgetItem(f"${row['payment']:.2f}"))
            table.setItem(i, 2, QTableWidgetItem(f"${row['interest']:.2f}"))
            table.setItem(i, 3, QTableWidgetItem(f"${row['remaining_balance']:.2f}"))
            table.setItem(i, 4, QTableWidgetItem(f"{row['percent_paid']:.1f}%"))
        
        schedule_layout.addWidget(table)
        schedule_group.setLayout(schedule_layout)
        self.results_layout.addWidget(schedule_group)
    
    def _add_improvement_suggestions(self, summary, extra_payment):
        """Add suggestions for improving payoff time"""
        if not summary:
            return
            
        suggestions_group = QGroupBox("Improvement Suggestions")
        suggestions_layout = QVBoxLayout()
        
        # Calculate effect of additional payments
        additional_payments = [
            extra_payment + 50,
            extra_payment + 100,
            extra_payment + 200
        ]
        
        suggestions_layout.addWidget(QLabel("See how increasing your monthly payment affects your payoff time:"))
        
        table = QTableWidget(len(additional_payments), 3)
        table.setHorizontalHeaderLabels([
            "Monthly Payment", "Payoff Time", "Interest Saved"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        base_interest = summary['total_interest_paid']
        base_months = summary['total_months']
        
        for i, payment in enumerate(additional_payments):
            # Calculate new payoff with increased payment
            results_df, new_summary, _ = self.debt_calculator.calculate_payoff_plan(
                self.user_id, payment, self.strategy_combo.currentData()
            )
            
            if not new_summary:
                continue
                
            months_saved = base_months - new_summary['total_months']
            interest_saved = base_interest - new_summary['total_interest_paid']
            
            table.setItem(i, 0, QTableWidgetItem(f"${payment + summary['monthly_payment'] - extra_payment:.2f}"))
            table.setItem(i, 1, QTableWidgetItem(f"{new_summary['total_months']} months (save {months_saved} months)"))
            table.setItem(i, 2, QTableWidgetItem(f"${interest_saved:.2f}"))
        
        suggestions_layout.addWidget(table)
        suggestions_group.setLayout(suggestions_layout)
        self.results_layout.addWidget(suggestions_group)
    
    def _add_strategy_recommendation(self, strategy_results):
        """Add strategy recommendation based on comparison"""
        if not strategy_results:
            return
            
        # Find fastest strategy and lowest interest strategy
        fastest = min(strategy_results.items(), key=lambda x: x[1]['months'])
        cheapest = min(strategy_results.items(), key=lambda x: x[1]['interest'])
        
        rec_group = QGroupBox("Strategy Recommendation")
        rec_layout = QVBoxLayout()
        
        if fastest[0] == cheapest[0]:
            rec_layout.addWidget(QLabel(f"<b>{fastest[0]}</b> is the best strategy for your situation!"))
            rec_layout.addWidget(QLabel(f"It provides the fastest payoff time AND lowest interest cost."))
        else:
            rec_layout.addWidget(QLabel("<b>Strategy Trade-offs:</b>"))
            rec_layout.addWidget(QLabel(f"• <b>{fastest[0]}</b> gives you the fastest payoff ({fastest[1]['months']} months)"))
            rec_layout.addWidget(QLabel(f"• <b>{cheapest[0]}</b> costs the least in interest (${cheapest[1]['interest']:.2f})"))
            
            # Calculate the difference
            time_diff = strategy_results[cheapest[0]]['months'] - strategy_results[fastest[0]]['months']
            interest_diff = strategy_results[fastest[0]]['interest'] - strategy_results[cheapest[0]]['interest']
            
            if time_diff <= 2 and interest_diff > 50:
                rec_layout.addWidget(QLabel(f"<b>Recommendation:</b> Choose <b>{cheapest[0]}</b> to save ${interest_diff:.2f} with only {time_diff} extra months."))
            else:
                rec_layout.addWidget(QLabel(f"<b>Recommendation:</b> Choose <b>{fastest[0]}</b> for fastest debt freedom."))
        
        rec_group.setLayout(rec_layout)
        self.results_layout.addWidget(rec_group)
    
    def refresh_data(self):
        """Refresh data when tab is selected"""
        # No automatic refresh needed for this tab
