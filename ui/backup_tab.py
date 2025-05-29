from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                          QPushButton, QListWidget, QListWidgetItem, QMessageBox,
                          QFileDialog, QFrame, QGroupBox, QSizePolicy)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont, QIcon

import os
import datetime
from backup_utils import BackupManager

class BackupTab(QWidget):
    """Tab for database backup and restoration"""
    
    def __init__(self, budget_manager, user_id):
        super().__init__()
        self.budget_manager = budget_manager
        self.user_id = user_id
        self.backup_manager = BackupManager()
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
            backup_path = self.backup_manager.create_backup()
            
            if backup_path:
                QMessageBox.information(self, "Backup Created", 
                                       f"Database backup created successfully.\n\nPath: {backup_path}")
                self.refresh_backup_list()
            else:
                QMessageBox.warning(self, "Backup Failed", 
                                   "Failed to create database backup. Please check the logs for details.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while creating backup: {str(e)}")
    
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
            import shutil
            shutil.copy2(backup_path, export_path)
            
            QMessageBox.information(self, "Backup Exported", 
                                   f"Database backup exported successfully to:\n{export_path}")
            
        except Exception as e:
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
            import shutil.copy2
            shutil.copy2(import_path, import_dest)
            
            QMessageBox.information(self, "Backup Imported", 
                                   "Database backup imported successfully.")
            
            self.refresh_backup_list()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during import: {str(e)}")
    
    def restore_backup(self, item):
        """Restore the database from the selected backup (triggered by double-click)"""
        self.restore_from_item(item)
    
    def restore_selected_backup(self):
        """Restore the database from the currently selected backup"""
        selected_items = self.backup_list.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a backup to restore.")
            return
        
        self.restore_from_item(selected_items[0])
    
    def restore_from_item(self, item):
        """Restore from the specified list item"""
        try:
            # Get the backup path from the item data
            backup_path = item.data(Qt.UserRole)
            
            if not backup_path:
                return
            
            # Confirm with the user
            reply = QMessageBox.question(
                self, "Confirm Restore", 
                "Restoring a backup will replace your current data. Are you sure you want to continue?",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Create a backup of the current database first
            current_backup_path = self.backup_manager.create_backup()
            
            if not current_backup_path:
                reply = QMessageBox.question(
                    self, "Backup Failed", 
                    "Failed to create a backup of your current data. Do you still want to proceed with the restore?",
                    QMessageBox.Yes | QMessageBox.No, 
                    QMessageBox.No
                )
                
                if reply != QMessageBox.Yes:
                    return
            
            # Restore the selected backup
            success = self.backup_manager.restore_backup(backup_path)
            
            if success:
                QMessageBox.information(self, "Restore Complete", 
                                      "Database has been restored successfully. Please restart the application for changes to take effect.")
            else:
                QMessageBox.warning(self, "Restore Failed", 
                                  "Failed to restore the database. Please check the logs for details.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during restoration: {str(e)}")
    
    def clean_backups(self):
        """Clean old backups, keeping only the most recent ones"""
        try:
            # Ask user for confirmation
            reply = QMessageBox.question(
                self, "Confirm Cleanup", 
                "This will remove all but the 10 most recent backups. Continue?",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Clean old backups
            removed_count = self.backup_manager.clean_old_backups()
            
            if removed_count > 0:
                QMessageBox.information(self, "Cleanup Complete", 
                                      f"Removed {removed_count} old backups.")
            else:
                QMessageBox.information(self, "No Cleanup Needed", 
                                      "No old backups were removed. You have 10 or fewer backups.")
                
            self.refresh_backup_list()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during cleanup: {str(e)}")
