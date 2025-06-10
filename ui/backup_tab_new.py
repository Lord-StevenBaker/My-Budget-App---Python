from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                          QPushButton, QListWidget, QListWidgetItem, QMessageBox,
                          QFileDialog, QFrame, QGroupBox, QSizePolicy, QProgressBar)
from PyQt5.QtCore import Qt, QDateTime, QTimer
from PyQt5.QtGui import QFont, QIcon

import os
import datetime
import logging
import traceback
import shutil
from backup_utils import BackupManager

# Get logger
logger = logging.getLogger('budget_app.ui.backup')

class BackupTab(QWidget):
    """Tab for database backup and restoration"""
    
    def __init__(self, budget_manager, user_id):
        super().__init__()
        self.budget_manager = budget_manager
        self.user_id = user_id
        
        # Initialize backup manager with path to the database
        try:
            self.backup_manager = BackupManager()
            logger.info("Backup manager initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing backup manager: {e}")
            QMessageBox.critical(self, "Initialization Error", 
                               f"Failed to initialize backup system: {str(e)}")
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Database Backup & Restore")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Regularly backing up your data is important to prevent data loss. "
                          "Use the options below to create backups or restore from a previous backup.")
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)
        
        # Create two columns layout
        columns_layout = QHBoxLayout()
        
        # Left column - Backup operations
        backup_group = QGroupBox("Backup Operations")
        backup_layout = QVBoxLayout()
        
        # Progress bar for operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        backup_layout.addWidget(self.progress_bar)
        
        # Create backup button
        backup_btn = QPushButton("Create New Backup")
        backup_btn.setIcon(QIcon.fromTheme("document-save"))
        backup_btn.clicked.connect(self.create_backup)
        backup_layout.addWidget(backup_btn)
        
        # Export backup button
        export_btn = QPushButton("Export Backup to File")
        export_btn.setIcon(QIcon.fromTheme("document-save-as"))
        export_btn.clicked.connect(self.export_backup)
        backup_layout.addWidget(export_btn)
        
        # Import backup button
        import_btn = QPushButton("Import Backup from File")
        import_btn.setIcon(QIcon.fromTheme("document-open"))
        import_btn.clicked.connect(self.import_backup)
        backup_layout.addWidget(import_btn)
        
        # Clean old backups button
        clean_btn = QPushButton("Clean Old Backups")
        clean_btn.setIcon(QIcon.fromTheme("edit-clear"))
        clean_btn.clicked.connect(self.clean_backups)
        backup_layout.addWidget(clean_btn)
        
        backup_layout.addStretch()
        backup_group.setLayout(backup_layout)
        columns_layout.addWidget(backup_group)
        
        # Right column - Backup list and restore
        restore_group = QGroupBox("Available Backups")
        restore_layout = QVBoxLayout()
        
        # Backup list
        self.backup_list = QListWidget()
        self.backup_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.backup_list.itemDoubleClicked.connect(self.restore_backup)
        restore_layout.addWidget(self.backup_list)
        
        # Restore button
        restore_btn = QPushButton("Restore Selected Backup")
        restore_btn.setIcon(QIcon.fromTheme("edit-undo"))
        restore_btn.clicked.connect(self.restore_selected_backup)
        restore_layout.addWidget(restore_btn)
        
        # Refresh list button
        refresh_btn = QPushButton("Refresh List")
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_btn.clicked.connect(self.refresh_backup_list)
        restore_layout.addWidget(refresh_btn)
        
        restore_group.setLayout(restore_layout)
        columns_layout.addWidget(restore_group)
        
        main_layout.addLayout(columns_layout)
        
        # Add cautionary note
        note_frame = QFrame()
        note_frame.setFrameShape(QFrame.StyledPanel)
        note_frame.setFrameShadow(QFrame.Raised)
        note_layout = QVBoxLayout()
        
        note_label = QLabel("<b>Important Note:</b> Restoring a backup will replace your current data. "
                          "Consider creating a backup of your current data before restoring an older backup.")
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: red;")
        note_layout.addWidget(note_label)
        
        note_frame.setLayout(note_layout)
        main_layout.addWidget(note_frame)
        
        self.setLayout(main_layout)
        
        # Load backups
        self.refresh_backup_list()
    
    def refresh_backup_list(self):
        """Refresh the list of available backups"""
        self.backup_list.clear()
        
        backups = self.backup_manager.list_backups()
        
        if not backups:
            item = QListWidgetItem("No backups available")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.backup_list.addItem(item)
            return
        
        for backup in backups:
            # Format size
            size_kb = backup['size'] / 1024
            size_mb = size_kb / 1024
            
            if size_mb >= 1:
                size_str = f"{size_mb:.2f} MB"
            else:
                size_str = f"{size_kb:.2f} KB"
            
            # Format date/time
            date_str = backup['created'].strftime("%Y-%m-%d %H:%M:%S")
            
            # Create list item
            item_text = f"{date_str} ({size_str})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, backup['path'])
            
            self.backup_list.addItem(item)
    
    def create_backup(self):
        """Create a new backup of the database"""
        try:
            # Show progress indication
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            # Schedule the backup operation to run after the UI updates
            QTimer.singleShot(100, self._execute_backup)
            
        except Exception as e:
            logger.error(f"Error preparing backup: {e}")
            logger.debug(traceback.format_exc())
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"An error occurred while preparing backup: {str(e)}")
    
    def _execute_backup(self):
        """Execute the actual backup operation"""
        try:
            backup_path = self.backup_manager.create_backup()
            
            # Update progress
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            
            if backup_path:
                logger.info(f"Backup created successfully at: {backup_path}")
                QMessageBox.information(self, "Backup Created", 
                                      f"Database backup created successfully.\n\nPath: {backup_path}")
                self.refresh_backup_list()
            else:
                logger.warning("Backup creation failed")
                QMessageBox.warning(self, "Backup Failed", 
                                  "Failed to create database backup. Please check the logs for details.")
        except Exception as e:
            logger.error(f"Error during backup creation: {e}")
            logger.debug(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"An error occurred while creating backup: {str(e)}")
        finally:
            # Hide progress bar
            self.progress_bar.setVisible(False)
    
    def export_backup(self):
        """Export a backup to a user-specified location"""
        try:
            # Create a new backup first
            backup_path = self.backup_manager.create_backup()

            if not backup_path:
                QMessageBox.warning(self, "Backup Failed", 
                                   "Failed to create database backup for export.")
                return

            # Ask user for export location
            export_path, _ = QFileDialog.getSaveFileName(
                self, "Export Backup", "", "SQLite Database (*.db);;All Files (*)"
            )

            if not export_path:
                return

            # Copy the backup to the export location
            shutil.copy2(backup_path, export_path)

            QMessageBox.information(self, "Backup Exported", 
                                   f"Database backup exported successfully to:\n{export_path}")

        except Exception as e:
            logger.error(f"Error during export: {e}")
            logger.debug(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"An error occurred during export: {str(e)}")
    
    def import_backup(self):
        """Import a backup from a user-specified location"""
        try:
            # Ask user for import file
            import_path, _ = QFileDialog.getOpenFileName(
                self, "Import Backup", "", "SQLite Database (*.db);;All Files (*)"
            )
            
            if not import_path:
                return
            
            # Create backups directory if it doesn't exist
            if not os.path.exists(self.backup_manager.backup_dir):
                os.makedirs(self.backup_manager.backup_dir)
            
            # Create a filename for the imported backup
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            import_filename = f"budget_import_{timestamp}.db"
            import_dest = os.path.join(self.backup_manager.backup_dir, import_filename)
            
            # Copy the import file to the backups directory
            shutil.copy2(import_path, import_dest)
            
            QMessageBox.information(self, "Backup Imported", 
                                   "Database backup imported successfully.")
            
            self.refresh_backup_list()
            
        except Exception as e:
            logger.error(f"Error during import: {e}")
            logger.debug(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"An error occurred during import: {str(e)}")
    
    def restore_backup(self, item):
        """Restore a backup from the selected item (double-click)"""
        logger.debug("Double-click detected on backup item, initiating restore")
        self.restore_selected_backup()
    
    def restore_selected_backup(self):
        """Restore the currently selected backup"""
        try:
            selected_items = self.backup_list.selectedItems()

            if not selected_items:
                logger.debug("No backup selected for restore operation")
                QMessageBox.warning(self, "No Selection", 
                                   "Please select a backup to restore.")
                return

            selected_item = selected_items[0]
            backup_path = selected_item.data(Qt.UserRole)

            if not backup_path or not os.path.exists(backup_path):
                logger.error(f"Selected backup file does not exist: {backup_path}")
                QMessageBox.critical(self, "File Not Found", 
                                    "The selected backup file cannot be found. It may have been moved or deleted.")
                self.refresh_backup_list()  # Refresh list to remove invalid entries
                return

            # Confirm restoration
            item_text = selected_item.text()
            reply = QMessageBox.question(self, "Confirm Restore", 
                                     f"Are you sure you want to restore this backup?\n\n" +
                                     f"Backup: {item_text}\n\n" +
                                     "This will replace your current data with the selected backup.", 
                                     QMessageBox.Yes | QMessageBox.No, 
                                     QMessageBox.No)

            if reply != QMessageBox.Yes:
                logger.debug("User cancelled backup restoration")
                return

            # Show progress
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress

            # Schedule the restore operation
            logger.info(f"Initiating restore from backup: {backup_path}")
            QTimer.singleShot(100, lambda: self._execute_restore(backup_path))
                
        except Exception as e:
            logger.error(f"Error preparing for backup restore: {e}")
            logger.debug(traceback.format_exc())
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"An error occurred while preparing restore: {str(e)}")
    
    def _execute_restore(self, backup_path):
        """Execute the actual restore operation"""
        try:
            # Perform restoration
            success = self.backup_manager.restore_backup(backup_path)

            # Update progress
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)

            if success:
                logger.info(f"Successfully restored database from backup: {backup_path}")
                QMessageBox.information(self, "Restore Successful", 
                                      "Database has been successfully restored from the selected backup.\n\n" +
                                      "You may need to restart the application for all changes to take effect.")
            else:
                logger.error(f"Failed to restore database from backup: {backup_path}")
                QMessageBox.critical(self, "Restore Failed", 
                                   "Failed to restore from the selected backup. Please check the logs for details.")
        except Exception as e:
            logger.error(f"Error during backup restoration: {e}")
            logger.debug(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"An error occurred during restore: {str(e)}")
        finally:
            # Hide progress bar
            self.progress_bar.setVisible(False)
    
    def clean_backups(self):
        """Clean old backups, keeping only the most recent ones"""
        try:
            # Get current backup count
            backups = self.backup_manager.list_backups()

            if len(backups) <= 10:
                logger.info("No cleanup needed, fewer than 10 backups exist")
                QMessageBox.information(self, "No Cleanup Needed", 
                                      f"You currently have {len(backups)} backups, which is within the limit of 10.\n\n" +
                                      "No cleanup is necessary at this time.")
                return

            # Confirm cleanup
            reply = QMessageBox.question(self, "Confirm Cleanup", 
                                       f"Are you sure you want to clean old backups?\n\n" +
                                       f"You currently have {len(backups)} backups.\n" +
                                       "This will keep only the 10 most recent backups and delete the rest.", 
                                       QMessageBox.Yes | QMessageBox.No, 
                                       QMessageBox.No)

            if reply != QMessageBox.Yes:
                logger.debug("User cancelled backup cleanup")
                return

            # Show progress
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress

            # Schedule the cleanup operation
            logger.info("Initiating backup cleanup")
            QTimer.singleShot(100, self._execute_cleanup)

        except Exception as e:
            logger.error(f"Error preparing for backup cleanup: {e}")
            logger.debug(traceback.format_exc())
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"An error occurred while preparing cleanup: {str(e)}")
    
    def _execute_cleanup(self):
        """Execute the actual backup cleanup operation"""
        try:
            # Perform cleanup
            removed_count = self.backup_manager.clean_old_backups(max_backups=10)

            # Update progress
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)

            logger.info(f"Backup cleanup completed, removed {removed_count} old backups")
            QMessageBox.information(self, "Cleanup Complete", 
                                  f"Cleanup completed. {removed_count} old backups were removed.")

            # Refresh the list
            self.refresh_backup_list()

        except Exception as e:
            logger.error(f"Error during backup cleanup: {e}")
            logger.debug(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"An error occurred during cleanup: {str(e)}")
        finally:
            # Hide progress bar
            self.progress_bar.setVisible(False)
