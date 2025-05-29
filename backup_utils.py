import os
import shutil
import datetime
import sqlite3
import logging

logger = logging.getLogger('budget_app.backup')

class BackupManager:
    """Utility class for database backups"""
    
    def __init__(self, db_path='budget.db', backup_dir='backups'):
        """Initialize the backup manager
        
        Args:
            db_path: Path to the database file
            backup_dir: Directory to store backups
        """
        self.db_path = db_path
        self.backup_dir = backup_dir
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
    
    def create_backup(self):
        """Create a backup of the database
        
        Returns:
            Path to the backup file if successful, None otherwise
        """
        try:
            # Create a backup filename with timestamp
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"budget_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Use SQLite's backup API for a consistent backup
            source = sqlite3.connect(self.db_path)
            dest = sqlite3.connect(backup_path)
            
            source.backup(dest)
            
            source.close()
            dest.close()
            
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            return None
    
    def restore_backup(self, backup_path):
        """Restore database from a backup
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if the backup file exists
            if not os.path.exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Create a temporary copy of the current database
            temp_path = f"{self.db_path}.temp"
            shutil.copy2(self.db_path, temp_path)
            
            try:
                # Close any open connections to the database
                source = sqlite3.connect(backup_path)
                dest = sqlite3.connect(self.db_path)
                
                source.backup(dest)
                
                source.close()
                dest.close()
                
                # Remove the temporary file
                os.remove(temp_path)
                
                logger.info(f"Database restored from backup: {backup_path}")
                return True
                
            except Exception as e:
                # Restore the original database from the temporary copy
                shutil.copy2(temp_path, self.db_path)
                os.remove(temp_path)
                
                logger.error(f"Error restoring backup: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error during backup restoration: {e}")
            return False
    
    def list_backups(self):
        """List all available backups
        
        Returns:
            List of backup files with timestamps
        """
        try:
            backups = []
            
            # List all backup files
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("budget_backup_") and filename.endswith(".db"):
                    backup_path = os.path.join(self.backup_dir, filename)
                    created_time = os.path.getctime(backup_path)
                    
                    backups.append({
                        'filename': filename,
                        'path': backup_path,
                        'created': datetime.datetime.fromtimestamp(created_time),
                        'size': os.path.getsize(backup_path)
                    })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created'], reverse=True)
            return backups
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []
    
    def clean_old_backups(self, max_backups=10):
        """Remove old backups, keeping only the most recent ones
        
        Args:
            max_backups: Maximum number of backups to keep
            
        Returns:
            Number of backups removed
        """
        try:
            backups = self.list_backups()
            
            # If we have more backups than the maximum, remove the oldest ones
            if len(backups) > max_backups:
                backups_to_remove = backups[max_backups:]
                removed_count = 0
                
                for backup in backups_to_remove:
                    try:
                        os.remove(backup['path'])
                        removed_count += 1
                        logger.info(f"Removed old backup: {backup['filename']}")
                    except Exception as e:
                        logger.error(f"Error removing backup {backup['filename']}: {e}")
                
                return removed_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Error cleaning old backups: {e}")
            return 0
