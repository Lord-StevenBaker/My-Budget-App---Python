import os
import shutil
import datetime
import sqlite3
import logging
import traceback

# Configure logger with a NullHandler by default
logger = logging.getLogger('budget_app.backup')
logger.addHandler(logging.NullHandler())

class BackupManager:
    """Utility class for database backups"""
    
    def __init__(self, db_path='budget.db', backup_dir='backups'):
        """
        Initialize the backup manager
        
        Args:
            db_path: Path to the database file
            backup_dir: Directory to store backups
        """
        self.db_path = db_path
        self.backup_dir = backup_dir
        
        # Create backup directory if it doesn't exist
        try:
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
                logger.info(f"Created backup directory: {backup_dir}")
            
            # Validate database path exists
            if not os.path.exists(db_path) and db_path != ':memory:':
                logger.warning(f"Database file not found at initialization: {db_path}")
        except Exception as e:
            logger.error(f"Error during backup manager initialization: {str(e)}")
            logger.debug(traceback.format_exc())
    
    def create_backup(self):
        """
        Create a backup of the database
        
        Returns:
            Path to the backup file if successful, None otherwise
        """
        source = None
        dest = None
        try:
            # Validate database file exists
            if not os.path.exists(self.db_path) and self.db_path != ':memory:':
                logger.error(f"Database file not found: {self.db_path}")
                return None
                
            # Create a backup filename with timestamp
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"budget_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Ensure backup directory exists
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir)
                logger.info(f"Created backup directory: {self.backup_dir}")
            
            # Use SQLite's backup API for a consistent backup
            logger.debug(f"Opening source database: {self.db_path}")
            source = sqlite3.connect(self.db_path)
            
            logger.debug(f"Creating destination database: {backup_path}")
            dest = sqlite3.connect(backup_path)
            
            logger.debug("Starting database backup process")
            source.backup(dest)
            
            logger.info(f"Database backup successfully created: {backup_path}")
            return backup_path
            
        except sqlite3.Error as sql_e:
            logger.error(f"SQLite error during backup creation: {sql_e}")
            logger.debug(traceback.format_exc())
            return None
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            logger.debug(traceback.format_exc())
            return None
        finally:
            # Ensure connections are closed even if an exception occurs
            if source:
                source.close()
            if dest:
                dest.close()
    
    def restore_backup(self, backup_path):
        """
        Restore database from a backup
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            True if successful, False otherwise
        """
        source = None
        dest = None
        temp_path = None
        
        try:
            # Check if the backup file exists
            if not os.path.exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False
                
            # Validate backup file is a valid SQLite database
            try:
                test_conn = sqlite3.connect(backup_path)
                test_conn.cursor().execute("SELECT name FROM sqlite_master WHERE type='table';")
                test_conn.close()
            except sqlite3.Error as e:
                logger.error(f"Invalid backup file (not a valid SQLite database): {backup_path}. Error: {e}")
                return False
            
            # Create a temporary copy of the current database
            temp_path = f"{self.db_path}.temp"
            logger.debug(f"Creating temporary backup of current database at {temp_path}")
            
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, temp_path)
            else:
                logger.warning(f"Current database file does not exist: {self.db_path}")
                # Create an empty file as a placeholder
                with open(temp_path, 'wb') as f:
                    pass
            
            try:
                # Close any open connections to the database
                logger.debug(f"Opening source backup database: {backup_path}")
                source = sqlite3.connect(backup_path)
                
                logger.debug(f"Opening destination database: {self.db_path}")
                dest = sqlite3.connect(self.db_path)
                
                logger.debug("Starting database restore process")
                source.backup(dest)
                
                logger.info(f"Database successfully restored from backup: {backup_path}")
                return True
                
            except Exception as e:
                logger.error(f"Error during database restore: {e}")
                logger.debug(traceback.format_exc())
                
                # Restore the original database from the temporary copy
                logger.debug("Attempting to roll back to the original database state")
                if os.path.exists(temp_path):
                    shutil.copy2(temp_path, self.db_path)
                    logger.info("Successfully rolled back to the original database state")
                
                return False
                
        except Exception as e:
            logger.error(f"Error during backup restoration process: {e}")
            logger.debug(traceback.format_exc())
            return False
        finally:
            # Clean up resources
            if source:
                source.close()
            if dest:
                dest.close()
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    logger.debug(f"Removed temporary database file: {temp_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove temporary file {temp_path}: {e}")
    
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
