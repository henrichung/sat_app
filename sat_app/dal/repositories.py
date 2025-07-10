"""
Repository classes for the SAT Question Bank application.
Implements CRUD operations for data models.
"""
import json
import logging
from typing import List, Optional, Dict, Any, Tuple

from .database_manager import DatabaseManager
from .models import Question, Worksheet, Score


class QuestionRepository:
    """
    Repository for Question model.
    
    Implements CRUD operations for the Question model.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the QuestionRepository.
        
        Args:
            db_manager: The database manager
        """
        self.logger = logging.getLogger(__name__)
        self.db_manager = db_manager
    
    def add_question(self, question: Question) -> Optional[int]:
        """
        Add a question to the database.
        
        Args:
            question: The Question to add
        
        Returns:
            The ID of the added question, or None if an error occurred
        """
        try:
            query = '''
            INSERT INTO questions (
                question_text, question_image_path,
                answer_a, answer_b, answer_c, answer_d,
                answer_image_a, answer_image_b, answer_image_c, answer_image_d,
                correct_answer, answer_explanation, subject_tags, difficulty_label
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            params = (
                question.question_text, question.question_image_path,
                question.answer_a, question.answer_b, question.answer_c, question.answer_d,
                question.answer_image_a, question.answer_image_b, question.answer_image_c, question.answer_image_d,
                question.correct_answer, question.answer_explanation, ','.join(question.subject_tags), question.difficulty_label
            )
            
            self.db_manager.execute_query(query, params)
            
            # Get the ID of the inserted question
            result = self.db_manager.execute_query("SELECT last_insert_rowid() as id")
            return result[0]['id'] if result else None
            
        except Exception as e:
            self.logger.error(f"Error adding question: {str(e)}")
            return None
    
    def get_question(self, question_id: int) -> Optional[Question]:
        """
        Get a question by ID.
        
        Args:
            question_id: The ID of the question to get
        
        Returns:
            The Question, or None if not found
        """
        try:
            query = "SELECT * FROM questions WHERE question_id = ?"
            result = self.db_manager.execute_query(query, (question_id,))
            
            if not result:
                return None
            
            return Question.from_dict(result[0])
            
        except Exception as e:
            self.logger.error(f"Error getting question: {str(e)}")
            return None
    
    def update_question(self, question: Question) -> bool:
        """
        Update a question.
        
        Args:
            question: The Question to update
        
        Returns:
            True if the update was successful, False otherwise
        """
        try:
            query = '''
            UPDATE questions SET
                question_text = ?, question_image_path = ?,
                answer_a = ?, answer_b = ?, answer_c = ?, answer_d = ?,
                answer_image_a = ?, answer_image_b = ?, answer_image_c = ?, answer_image_d = ?,
                correct_answer = ?, answer_explanation = ?, subject_tags = ?, difficulty_label = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE question_id = ?
            '''
            
            params = (
                question.question_text, question.question_image_path,
                question.answer_a, question.answer_b, question.answer_c, question.answer_d,
                question.answer_image_a, question.answer_image_b, question.answer_image_c, question.answer_image_d,
                question.correct_answer, question.answer_explanation, ','.join(question.subject_tags), question.difficulty_label,
                question.question_id
            )
            
            result = self.db_manager.execute_query(query, params)
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error updating question: {str(e)}")
            return False
    
    def delete_question(self, question_id: int) -> bool:
        """
        Delete a question.
        
        Args:
            question_id: The ID of the question to delete
        
        Returns:
            True if the deletion was successful, False otherwise
        """
        try:
            query = "DELETE FROM questions WHERE question_id = ?"
            result = self.db_manager.execute_query(query, (question_id,))
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error deleting question: {str(e)}")
            return False
    
    def get_all_questions(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Question]:
        """
        Get all questions with pagination support.
        
        Args:
            limit: Maximum number of questions to return
            offset: Number of questions to skip
        
        Returns:
            A list of Questions with pagination applied
        """
        try:
            query = "SELECT * FROM questions ORDER BY question_id"
            
            # Add pagination if specified
            if limit is not None:
                query += f" LIMIT {limit}"
                if offset is not None:
                    query += f" OFFSET {offset}"
            
            result = self.db_manager.execute_query(query)
            
            if not result:
                return []
            
            return [Question.from_dict(row) for row in result]
            
        except Exception as e:
            self.logger.error(f"Error getting all questions: {str(e)}")
            return []
    
    def count_all_questions(self) -> int:
        """
        Count all questions in the database.
        
        Returns:
            Total number of questions
        """
        try:
            query = "SELECT COUNT(*) as count FROM questions"
            result = self.db_manager.execute_query(query)
            
            if not result:
                return 0
                
            return result[0]['count']
            
        except Exception as e:
            self.logger.error(f"Error counting questions: {str(e)}")
            return 0
    
    def _build_filter_conditions(self, filters: Dict[str, Any]) -> Tuple[List[str], List]:
        """
        Helper method to build WHERE conditions from filters.
        
        Args:
            filters: Dictionary of filter criteria
        
        Returns:
            Tuple of (conditions list, parameters list)
        """
        conditions = []
        params = []
        
        # Build query conditions based on filters
        if 'text_search' in filters and filters['text_search']:
            conditions.append("question_text LIKE ?")
            params.append(f"%{filters['text_search']}%")
        
        if 'subject_tags' in filters and filters['subject_tags']:
            tags = filters['subject_tags']
            if isinstance(tags, list):
                for tag in tags:
                    conditions.append("subject_tags LIKE ?")
                    params.append(f"%{tag}%")
            else:
                conditions.append("subject_tags LIKE ?")
                params.append(f"%{tags}%")
        
        if 'difficulty' in filters and filters['difficulty']:
            conditions.append("difficulty_label = ?")
            params.append(filters['difficulty'])
            
        if 'exclude_ids' in filters and filters['exclude_ids']:
            if isinstance(filters['exclude_ids'], list) and filters['exclude_ids']:
                placeholders = ','.join(['?' for _ in filters['exclude_ids']])
                conditions.append(f"question_id NOT IN ({placeholders})")
                params.extend(filters['exclude_ids'])
        
        return conditions, params
    
    def filter_questions(self, filters: Dict[str, Any], limit: Optional[int] = None, offset: Optional[int] = None) -> List[Question]:
        """
        Filter questions based on criteria with pagination support.
        
        Args:
            filters: Dictionary of filter criteria
            limit: Maximum number of questions to return
            offset: Number of questions to skip
        
        Returns:
            A list of Questions matching the criteria with pagination applied
        """
        try:
            conditions, params = self._build_filter_conditions(filters)
            
            # Create the query string
            query = "SELECT * FROM questions"
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY question_id"
            
            # Add pagination if specified
            if limit is not None:
                query += f" LIMIT {limit}"
                if offset is not None:
                    query += f" OFFSET {offset}"
            
            # Execute the query
            result = self.db_manager.execute_query(query, tuple(params))
            
            if not result:
                return []
            
            return [Question.from_dict(row) for row in result]
            
        except Exception as e:
            self.logger.error(f"Error filtering questions: {str(e)}")
            return []
    
    def count_filtered_questions(self, filters: Dict[str, Any]) -> int:
        """
        Count questions matching the filter criteria.
        
        Args:
            filters: Dictionary of filter criteria
        
        Returns:
            Count of questions matching the criteria
        """
        try:
            conditions, params = self._build_filter_conditions(filters)
            
            # Create the count query
            query = "SELECT COUNT(*) as count FROM questions"
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            # Execute the query
            result = self.db_manager.execute_query(query, tuple(params))
            
            if not result:
                return 0
                
            return result[0]['count']
            
        except Exception as e:
            self.logger.error(f"Error counting filtered questions: {str(e)}")
            return 0


class WorksheetRepository:
    """
    Repository for Worksheet model.
    
    Implements CRUD operations for the Worksheet model.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the WorksheetRepository.
        
        Args:
            db_manager: The database manager
        """
        self.logger = logging.getLogger(__name__)
        self.db_manager = db_manager
    
    def add_worksheet(self, worksheet: Worksheet) -> Optional[int]:
        """
        Add a worksheet to the database.
        
        Args:
            worksheet: The Worksheet to add
        
        Returns:
            The ID of the added worksheet, or None if an error occurred
        """
        try:
            query = '''
            INSERT INTO worksheets (title, description, question_ids, pdf_path)
            VALUES (?, ?, ?, ?)
            '''
            
            params = (
                worksheet.title,
                worksheet.description,
                json.dumps(worksheet.question_ids),
                worksheet.pdf_path
            )
            
            self.db_manager.execute_query(query, params)
            
            # Get the ID of the inserted worksheet
            result = self.db_manager.execute_query("SELECT last_insert_rowid() as id")
            return result[0]['id'] if result else None
            
        except Exception as e:
            self.logger.error(f"Error adding worksheet: {str(e)}")
            return None
    
    def get_worksheet(self, worksheet_id: int) -> Optional[Worksheet]:
        """
        Get a worksheet by ID.
        
        Args:
            worksheet_id: The ID of the worksheet to get
        
        Returns:
            The Worksheet, or None if not found
        """
        try:
            query = "SELECT * FROM worksheets WHERE worksheet_id = ?"
            result = self.db_manager.execute_query(query, (worksheet_id,))
            
            if not result:
                return None
            
            return Worksheet.from_dict(result[0])
            
        except Exception as e:
            self.logger.error(f"Error getting worksheet: {str(e)}")
            return None
    
    def update_worksheet(self, worksheet: Worksheet) -> bool:
        """
        Update a worksheet.
        
        Args:
            worksheet: The Worksheet to update
        
        Returns:
            True if the update was successful, False otherwise
        """
        try:
            query = '''
            UPDATE worksheets SET
                title = ?, description = ?, question_ids = ?, pdf_path = ?
            WHERE worksheet_id = ?
            '''
            
            params = (
                worksheet.title,
                worksheet.description,
                json.dumps(worksheet.question_ids),
                worksheet.pdf_path,
                worksheet.worksheet_id
            )
            
            result = self.db_manager.execute_query(query, params)
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error updating worksheet: {str(e)}")
            return False
    
    def delete_worksheet(self, worksheet_id: int) -> bool:
        """
        Delete a worksheet.
        
        Args:
            worksheet_id: The ID of the worksheet to delete
        
        Returns:
            True if the deletion was successful, False otherwise
        """
        try:
            query = "DELETE FROM worksheets WHERE worksheet_id = ?"
            result = self.db_manager.execute_query(query, (worksheet_id,))
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error deleting worksheet: {str(e)}")
            return False
    
    def get_all_worksheets(self) -> List[Worksheet]:
        """
        Get all worksheets.
        
        Returns:
            A list of all Worksheets
        """
        try:
            query = "SELECT * FROM worksheets ORDER BY worksheet_id"
            result = self.db_manager.execute_query(query)
            
            if not result:
                return []
            
            return [Worksheet.from_dict(row) for row in result]
            
        except Exception as e:
            self.logger.error(f"Error getting all worksheets: {str(e)}")
            return []


class ScoreRepository:
    """
    Repository for Score model.
    
    Implements CRUD operations for the Score model.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the ScoreRepository.
        
        Args:
            db_manager: The database manager
        """
        self.logger = logging.getLogger(__name__)
        self.db_manager = db_manager
    
    def add_score(self, score: Score) -> Optional[int]:
        """
        Add a score to the database.
        
        Args:
            score: The Score to add
        
        Returns:
            The ID of the added score, or None if an error occurred
        """
        try:
            query = '''
            INSERT INTO scores (student_id, worksheet_id, question_id, correct)
            VALUES (?, ?, ?, ?)
            '''
            
            params = (
                score.student_id,
                score.worksheet_id,
                score.question_id,
                1 if score.correct else 0
            )
            
            self.db_manager.execute_query(query, params)
            
            # Get the ID of the inserted score
            result = self.db_manager.execute_query("SELECT last_insert_rowid() as id")
            return result[0]['id'] if result else None
            
        except Exception as e:
            self.logger.error(f"Error adding score: {str(e)}")
            return None
    
    def get_scores_by_student(self, student_id: str) -> List[Score]:
        """
        Get scores for a student.
        
        Args:
            student_id: The ID of the student
        
        Returns:
            A list of Scores for the student
        """
        try:
            query = "SELECT * FROM scores WHERE student_id = ? ORDER BY timestamp DESC"
            result = self.db_manager.execute_query(query, (student_id,))
            
            if not result:
                return []
            
            return [Score.from_dict(row) for row in result]
            
        except Exception as e:
            self.logger.error(f"Error getting scores by student: {str(e)}")
            return []
    
    def get_scores_by_worksheet(self, worksheet_id: int) -> List[Score]:
        """
        Get scores for a worksheet.
        
        Args:
            worksheet_id: The ID of the worksheet
        
        Returns:
            A list of Scores for the worksheet
        """
        try:
            query = "SELECT * FROM scores WHERE worksheet_id = ? ORDER BY student_id, question_id"
            result = self.db_manager.execute_query(query, (worksheet_id,))
            
            if not result:
                return []
            
            return [Score.from_dict(row) for row in result]
            
        except Exception as e:
            self.logger.error(f"Error getting scores by worksheet: {str(e)}")
            return []
    
    def get_student_question_score(self, student_id: str, question_id: int) -> Optional[Score]:
        """
        Get a student's score for a specific question.
        
        Args:
            student_id: The ID of the student
            question_id: The ID of the question
        
        Returns:
            The Score, or None if not found
        """
        try:
            query = "SELECT * FROM scores WHERE student_id = ? AND question_id = ? ORDER BY timestamp DESC LIMIT 1"
            result = self.db_manager.execute_query(query, (student_id, question_id))
            
            if not result:
                return None
            
            return Score.from_dict(result[0])
            
        except Exception as e:
            self.logger.error(f"Error getting student question score: {str(e)}")
            return None
    
    def get_student_worksheet_scores(self, student_id: str, worksheet_id: int) -> List[Score]:
        """
        Get a student's scores for a specific worksheet.
        
        Args:
            student_id: The ID of the student
            worksheet_id: The ID of the worksheet
        
        Returns:
            A list of Scores for the student and worksheet
        """
        try:
            query = "SELECT * FROM scores WHERE student_id = ? AND worksheet_id = ? ORDER BY question_id"
            result = self.db_manager.execute_query(query, (student_id, worksheet_id))
            
            if not result:
                return []
            
            return [Score.from_dict(row) for row in result]
            
        except Exception as e:
            self.logger.error(f"Error getting student worksheet scores: {str(e)}")
            return []