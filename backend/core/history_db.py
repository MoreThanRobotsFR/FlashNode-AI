import sqlite3
import os
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class HistoryDB:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to data/history.db at the root of the project
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "history.db")
            
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS operations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        status TEXT NOT NULL,
                        action TEXT NOT NULL,
                        target TEXT,
                        details TEXT,
                        duration_s REAL
                    )
                ''')
                conn.commit()
                logger.info(f"History DB initialized at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")

    def log_operation(self, status: str, action: str, target: str = None, details: str = None, duration_s: float = None):
        """Logs a single operation into the history database."""
        timestamp = datetime.now().isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT INTO operations (timestamp, status, action, target, details, duration_s)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (timestamp, status, action, target, details, duration_s)
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to log operation: {e}")

    def get_history(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve recent operation history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    '''SELECT * FROM operations ORDER BY timestamp DESC LIMIT ? OFFSET ?''',
                    (limit, offset)
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get history: {e}")
            return []

# Singleton instance
history_db = HistoryDB()
