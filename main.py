import sys
import traceback
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QCoreApplication, Qt
from ui.main_window import MainWindow
from budget_manager import BudgetManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("budget_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('budget_app')

# Add global exception handler
def exception_hook(exctype, value, tb):
    """Global exception handler for unhandled exceptions"""
    # Log the error
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    logger.error(f"Unhandled exception: {error_msg}")
    
    # Show error dialog if possible
    try:
        app = QCoreApplication.instance()
        if app:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText("An unexpected error occurred.")
            msg_box.setInformativeText(str(value))
            msg_box.setDetailedText(error_msg)
            msg_box.setWindowTitle("Application Error")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()
    except Exception as e:
        # If showing the error dialog fails, just log it
        logger.error(f"Failed to display error dialog: {e}")
    
    # Call the original exception handler
    sys.__excepthook__(exctype, value, tb)

def main():
    # Set the global exception hook
    sys.excepthook = exception_hook
    
    try:
        # Set application attributes
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setStyle('Fusion')  # Use Fusion style for consistent look
        
        # Initialize the application
        logger.info("Starting Budget App")
        app = QApplication(sys.argv)
        app.setApplicationName("Personal Budget Manager")
        
        # Initialize budget manager
        logger.info("Initializing budget manager")
        budget_manager = BudgetManager()
        
        # Create and show main window
        logger.info("Showing main window")
        window = MainWindow(budget_manager)
        window.show()
        
        # Start the application event loop
        return app.exec_()
    
    except Exception as e:
        # Log any exceptions during startup
        logger.error(f"Error during application startup: {e}")
        traceback.print_exc()
        
        # Show error dialog
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setText("Application Startup Error")
        error_dialog.setInformativeText(f"The application encountered an error during startup: {str(e)}")
        error_dialog.setDetailedText(traceback.format_exc())
        error_dialog.setWindowTitle("Startup Error")
        error_dialog.setStandardButtons(QMessageBox.Ok)
        error_dialog.exec_()
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
