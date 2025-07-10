"""
Database manager for the SAT Question Bank application.
Manages connections to the SQLite database and database initialization.
"""
import os
import sqlite3
import logging
from typing import Optional, List, Dict, Any, Tuple


class DatabaseManager:
    """
    Manages database connections and operations.
    
    Handles connection to the SQLite database, initializes the database schema,
    and provides utility methods for common database operations.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize the DatabaseManager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
    
    def initialize(self) -> bool:
        """
        Initialize the database.
        
        Creates the database file if it doesn't exist and
        initializes the database schema.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Create data directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Connect to the database
            self.conn = self._get_connection()
            
            # Create tables
            self._create_tables()
            
            self.logger.info(f"Database initialized successfully at {self.db_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {str(e)}")
            return False
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection.
        
        Returns:
            A SQLite connection object
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # This allows accessing columns by name
        return conn
    
    def _create_tables(self) -> None:
        """
        Create database tables if they don't exist.
        """
        cursor = self.conn.cursor()
        
        # Create Questions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL,
            question_image_path TEXT,
            answer_a TEXT,
            answer_b TEXT,
            answer_c TEXT,
            answer_d TEXT,
            answer_image_a TEXT,
            answer_image_b TEXT,
            answer_image_c TEXT,
            answer_image_d TEXT,
            correct_answer TEXT,
            answer_explanation TEXT,
            question_type TEXT DEFAULT 'multiple_choice',
            subject_tags TEXT,
            difficulty_label TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Add question_type column if it doesn't exist (migration for existing databases)
        try:
            cursor.execute("ALTER TABLE questions ADD COLUMN question_type TEXT DEFAULT 'multiple_choice'")
            self.conn.commit()
        except sqlite3.OperationalError:
            # Column already exists
            pass
        
        # Migration: Remove NOT NULL constraints from answer columns for free response support
        self._migrate_answer_columns(cursor)
        
        # Update correct_answer column to allow TEXT instead of CHAR(1) for free response
        # Note: SQLite doesn't have a direct way to modify column types, but since CHAR(1) 
        # is just a hint in SQLite and stored as TEXT anyway, no migration is needed
        
        # Create Worksheets table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS worksheets (
            worksheet_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            question_ids TEXT NOT NULL,
            pdf_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create Scores table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            score_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            worksheet_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            correct BOOLEAN NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worksheet_id) REFERENCES worksheets (worksheet_id),
            FOREIGN KEY (question_id) REFERENCES questions (question_id)
        )
        ''')
        
        # Create Student Responses table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_responses (
            response_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            worksheet_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            student_answer TEXT NOT NULL,
            is_graded BOOLEAN DEFAULT 0,
            is_correct BOOLEAN,
            graded_by TEXT,
            grading_notes TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worksheet_id) REFERENCES worksheets (worksheet_id),
            FOREIGN KEY (question_id) REFERENCES questions (question_id)
        )
        ''')
        
        self.conn.commit()
    
    def _migrate_answer_columns(self, cursor) -> None:
        """
        Migrate existing tables to remove NOT NULL constraints from answer columns.
        This allows free response questions that don't have answer_a-d values.
        """
        try:
            # Check if the questions table exists and has the old schema
            cursor.execute("PRAGMA table_info(questions)")
            columns = cursor.fetchall()
            
            # Check if answer_a has NOT NULL constraint
            answer_a_info = next((col for col in columns if col[1] == 'answer_a'), None)
            if answer_a_info and answer_a_info[3]:  # notnull column is index 3
                self.logger.info("Migrating questions table to support free response questions...")
                
                # Backup existing data
                cursor.execute("SELECT * FROM questions")
                existing_questions = cursor.fetchall()
                
                # Drop the old table
                cursor.execute("DROP TABLE questions")
                
                # Create the new table with updated schema
                cursor.execute('''
                CREATE TABLE questions (
                    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_text TEXT NOT NULL,
                    question_image_path TEXT,
                    answer_a TEXT,
                    answer_b TEXT,
                    answer_c TEXT,
                    answer_d TEXT,
                    answer_image_a TEXT,
                    answer_image_b TEXT,
                    answer_image_c TEXT,
                    answer_image_d TEXT,
                    correct_answer TEXT,
                    answer_explanation TEXT,
                    question_type TEXT DEFAULT 'multiple_choice',
                    subject_tags TEXT,
                    difficulty_label TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                # Restore existing data
                for question in existing_questions:
                    # Convert Row object to dictionary for easier handling
                    question_dict = dict(question)
                    # Remove the primary key so it gets auto-generated
                    question_dict.pop('question_id', None)
                    
                    # Build insert query dynamically based on available columns
                    columns_list = list(question_dict.keys())
                    placeholders = ', '.join(['?' for _ in columns_list])
                    columns_str = ', '.join(columns_list)
                    values = [question_dict[col] for col in columns_list]
                    
                    insert_query = f"INSERT INTO questions ({columns_str}) VALUES ({placeholders})"
                    cursor.execute(insert_query, values)
                
                self.conn.commit()
                self.logger.info(f"Successfully migrated {len(existing_questions)} questions to new schema")
                
        except Exception as e:
            self.logger.error(f"Error during answer columns migration: {str(e)}")
            # Don't raise the error as this might break database initialization
    
    def execute_query(self, query: str, params: Tuple = ()) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a SQL query.
        
        Args:
            query: The SQL query to execute
            params: Parameters for the SQL query
        
        Returns:
            A list of rows as dictionaries, or None if an error occurred
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            
            if query.strip().upper().startswith(("SELECT", "PRAGMA")):
                # For SELECT queries, return the results
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                # For INSERT, UPDATE, DELETE queries, commit and return empty list
                self.conn.commit()
                return []
        except Exception as e:
            self.logger.error(f"Query execution error: {str(e)}")
            self.logger.error(f"Query: {query}, Params: {params}")
            self.conn.rollback()
            return None
    
    def close(self) -> None:
        """
        Close the database connection.
        """
        if self.conn:
            self.conn.close()
            self.conn = None