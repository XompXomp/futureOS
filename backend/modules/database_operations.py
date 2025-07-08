# SQL database operations 

import sqlite3
from typing import List, Dict, Any, Optional
from utils.logging_config import logger

class DatabaseOperations:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()

    def init_database(self) -> None:
        """Initialize the database with sample tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create patients table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    age INTEGER,
                    email TEXT,
                    phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                # Create appointments table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER,
                    appointment_date TEXT,
                    doctor_name TEXT,
                    status TEXT DEFAULT 'scheduled',
                    FOREIGN KEY (patient_id) REFERENCES patients (id)
                )
                ''')
                
                # Create medical_records table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS medical_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER,
                    diagnosis TEXT,
                    treatment TEXT,
                    date_recorded TEXT,
                    FOREIGN KEY (patient_id) REFERENCES patients (id)
                )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")

    def execute_query(self, query: str, params: tuple = ()) -> Optional[List[Dict[str, Any]]]:
        """Execute a SELECT query and return results."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # This allows dict-like access
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                result = [dict(row) for row in rows]
                logger.info(f"Query executed successfully, returned {len(result)} rows")
                return result
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return None

    def execute_non_query(self, query: str, params: tuple = ()) -> bool:
        """Execute INSERT, UPDATE, or DELETE query."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                logger.info(f"Non-query executed successfully, affected {cursor.rowcount} rows")
                return True
        except Exception as e:
            logger.error(f"Error executing non-query: {str(e)}")
            return False

    def get_table_schema(self, table_name: str) -> Optional[List[Dict[str, Any]]]:
        """Get the schema of a table."""
        try:
            query = f"PRAGMA table_info({table_name})"
            return self.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting table schema: {str(e)}")
            return None

    def get_all_tables(self) -> Optional[List[str]]:
        """Get all table names in the database."""
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table'"
            result = self.execute_query(query)
            if result:
                return [row['name'] for row in result]
            return []
        except Exception as e:
            logger.error(f"Error getting table names: {str(e)}")
            return None

    def natural_language_to_sql(self, nl_query: str) -> Optional[str]:
        """Convert natural language query to SQL (basic implementation)."""
        # This is a simplified version - in production, you'd use a more sophisticated NL2SQL model
        nl_query = nl_query.lower()
        
        # Simple pattern matching for common queries
        if 'patients' in nl_query or 'patient' in nl_query:
            if 'all' in nl_query or 'list' in nl_query:
                return "SELECT * FROM patients"
            elif 'count' in nl_query or 'how many' in nl_query:
                return "SELECT COUNT(*) as count FROM patients"
        
        elif 'appointments' in nl_query or 'appointment' in nl_query:
            if 'all' in nl_query or 'list' in nl_query:
                return "SELECT * FROM appointments"
            elif 'today' in nl_query:
                return "SELECT * FROM appointments WHERE appointment_date = date('now')"
        
        logger.warning(f"Could not convert natural language query to SQL: {nl_query}")
        return None