"""
Question manager module for the SAT Question Bank application.
Orchestrates the creation, update, and deletion of questions.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..dal.repositories import QuestionRepository
from ..dal.models import Question
from ..utils.logger import get_logger


class QuestionManager:
    """
    Manager for Question operations.
    
    Orchestrates the creation, update, and deletion of questions,
    performs business validation, and interacts with the repository.
    """
    
    def __init__(self, question_repository: QuestionRepository):
        """
        Initialize the QuestionManager.
        
        Args:
            question_repository: The repository for question operations
        """
        self.logger = get_logger(__name__)
        self.question_repository = question_repository
    
    def create_question(self, question_data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new question.
        
        Args:
            question_data: Dictionary containing question data
        
        Returns:
            The ID of the created question, or None if validation failed or an error occurred
        
        Raises:
            ValueError: If the question data is invalid
        """
        try:
            # Validate required fields
            self._validate_question_data(question_data)
            
            # Create Question instance
            question = Question.from_dict(question_data)
            
            # Set created and updated timestamps
            question.created_at = datetime.now()
            question.updated_at = datetime.now()
            
            # Add to repository
            question_id = self.question_repository.add_question(question)
            
            if question_id:
                self.logger.info(f"Created question with ID: {question_id}")
                return question_id
            else:
                self.logger.error("Failed to create question")
                return None
                
        except ValueError as ve:
            self.logger.error(f"Validation error creating question: {str(ve)}")
            raise
        except Exception as e:
            self.logger.error(f"Error creating question: {str(e)}")
            return None
    
    def update_question(self, question_id: int, question_data: Dict[str, Any]) -> bool:
        """
        Update an existing question.
        
        Args:
            question_id: The ID of the question to update
            question_data: Dictionary containing question data
        
        Returns:
            True if the update was successful, False otherwise
        
        Raises:
            ValueError: If the question data is invalid
            KeyError: If the question does not exist
        """
        try:
            # Check if question exists
            existing_question = self.question_repository.get_question(question_id)
            if not existing_question:
                error_msg = f"Question with ID {question_id} does not exist"
                self.logger.error(error_msg)
                raise KeyError(error_msg)
            
            # Validate required fields
            self._validate_question_data(question_data)
            
            # Create updated Question instance
            updated_question = Question.from_dict(question_data)
            updated_question.question_id = question_id
            
            # Keep original creation timestamp
            updated_question.created_at = existing_question.created_at
            
            # Update timestamp
            updated_question.updated_at = datetime.now()
            
            # Update in repository
            success = self.question_repository.update_question(updated_question)
            
            if success:
                self.logger.info(f"Updated question with ID: {question_id}")
                return True
            else:
                self.logger.error(f"Failed to update question with ID: {question_id}")
                return False
                
        except ValueError as ve:
            self.logger.error(f"Validation error updating question: {str(ve)}")
            raise
        except KeyError as ke:
            self.logger.error(f"Question not found: {str(ke)}")
            raise
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
        
        Raises:
            KeyError: If the question does not exist
        """
        try:
            # Check if question exists
            existing_question = self.question_repository.get_question(question_id)
            if not existing_question:
                error_msg = f"Question with ID {question_id} does not exist"
                self.logger.error(error_msg)
                raise KeyError(error_msg)
            
            # Delete from repository
            success = self.question_repository.delete_question(question_id)
            
            if success:
                self.logger.info(f"Deleted question with ID: {question_id}")
                return True
            else:
                self.logger.error(f"Failed to delete question with ID: {question_id}")
                return False
                
        except KeyError as ke:
            self.logger.error(f"Question not found: {str(ke)}")
            raise
        except Exception as e:
            self.logger.error(f"Error deleting question: {str(e)}")
            return False
    
    def get_question(self, question_id: int) -> Optional[Question]:
        """
        Get a question by ID.
        
        Args:
            question_id: The ID of the question to get
        
        Returns:
            The Question, or None if not found
        """
        try:
            return self.question_repository.get_question(question_id)
        except Exception as e:
            self.logger.error(f"Error getting question: {str(e)}")
            return None
    
    def get_all_questions(self, limit=None, offset=None) -> List[Question]:
        """
        Get all questions with pagination support.
        
        Args:
            limit: Maximum number of questions to return (for pagination)
            offset: Number of questions to skip (for pagination)
        
        Returns:
            A list of Questions, potentially limited by pagination parameters
        """
        return self.question_repository.get_all_questions(limit=limit, offset=offset)
    
    def filter_questions(self, filters: Dict[str, Any], limit=None, offset=None) -> List[Question]:
        """
        Filter questions based on criteria with pagination support.
        
        Args:
            filters: Dictionary of filter criteria, which may include:
                - text_search: Text to search for in question text
                - subject_tags: List or string of subject tags to filter by
                - difficulty: Difficulty level to filter by
                - exclude_ids: List of question IDs to exclude
            limit: Maximum number of questions to return (for pagination)
            offset: Number of questions to skip (for pagination)
        
        Returns:
            A list of Questions matching the criteria
        """
        return self.question_repository.filter_questions(filters, limit=limit, offset=offset)
    
    def count_all_questions(self) -> int:
        """
        Count all questions without fetching them.
        
        Returns:
            The total number of questions in the database
        """
        try:
            return self.question_repository.count_all_questions()
        except Exception as e:
            self.logger.error(f"Error counting questions: {str(e)}")
            return 0
    
    def count_filtered_questions(self, filters: Dict[str, Any]) -> int:
        """
        Count questions matching the filters without fetching them.
        
        Args:
            filters: Dictionary of filter criteria
            
        Returns:
            The number of questions matching the filter criteria
        """
        try:
            return self.question_repository.count_filtered_questions(filters)
        except Exception as e:
            self.logger.error(f"Error counting filtered questions: {str(e)}")
            return 0
    
    def get_questions_by_tag(self, tag: str) -> List[Question]:
        """
        Get questions by subject tag.
        
        Args:
            tag: The subject tag to filter by
        
        Returns:
            A list of Questions with the given tag
        """
        filters = {'subject_tags': tag}
        return self.filter_questions(filters)
    
    def get_questions_by_difficulty(self, difficulty: str) -> List[Question]:
        """
        Get questions by difficulty level.
        
        Args:
            difficulty: The difficulty level to filter by
        
        Returns:
            A list of Questions with the given difficulty
        """
        filters = {'difficulty': difficulty}
        return self.filter_questions(filters)
    
    def _validate_question_data(self, question_data: Dict[str, Any]) -> None:
        """
        Validate question data.
        
        Args:
            question_data: The question data to validate
        
        Raises:
            ValueError: If the question data is invalid
        """
        # Check required fields
        required_fields = ['question_text', 'answer_a', 'answer_b', 'answer_c', 'answer_d', 'correct_answer']
        for field in required_fields:
            if field not in question_data or not question_data[field]:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate correct answer
        valid_answers = ['A', 'B', 'C', 'D']
        if question_data['correct_answer'] not in valid_answers:
            raise ValueError(f"Invalid correct_answer. Must be one of {valid_answers}")
    
    def get_student_list(self) -> List[str]:
        """
        Get a list of all student IDs who have recorded answers.
        
        Returns:
            A list of student IDs
        """
        try:
            # Try to access the database manager directly
            if hasattr(self.question_repository, 'db_manager'):
                db_manager = self.question_repository.db_manager
                query = "SELECT DISTINCT student_id FROM scores ORDER BY student_id"
                result = db_manager.execute_query(query)
                
                if not result:
                    return []
                
                return [row['student_id'] for row in result]
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting student list: {str(e)}")
            return []
    
    def get_student_answered_questions(self, student_id: str) -> Dict[int, Any]:
        """
        Get a dictionary of questions answered by a student and the worksheets they appeared in.
        
        Args:
            student_id: The ID of the student
        
        Returns:
            A dictionary mapping question IDs to [worksheet_id, worksheet_title] lists
        """
        try:
            # Check if we can access the database manager
            if not hasattr(self.question_repository, 'db_manager'):
                return {}
                
            db_manager = self.question_repository.db_manager
            
            # Query the database for all questions this student has answered
            query = """
            SELECT s.question_id, s.worksheet_id, w.title 
            FROM scores s 
            LEFT JOIN worksheets w ON s.worksheet_id = w.worksheet_id
            WHERE s.student_id = ? 
            GROUP BY s.question_id
            """
            
            result = db_manager.execute_query(query, (student_id,))
            
            # Build the answered questions dictionary
            student_answered_questions = {}
            
            if result:
                for row in result:
                    question_id = row['question_id']
                    worksheet_id = row['worksheet_id']
                    worksheet_title = row.get('title', f"Worksheet #{worksheet_id}")
                    
                    # Store the worksheet information with the question
                    student_answered_questions[question_id] = [worksheet_id, worksheet_title]
            
            return student_answered_questions
            
        except Exception as e:
            self.logger.error(f"Error getting student answered questions: {str(e)}")
            return {}