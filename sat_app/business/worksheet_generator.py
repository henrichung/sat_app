"""
Worksheet generator module for the SAT Question Bank application.

This module is responsible for:
- Accepting a list of selected question IDs or filtering criteria
- Randomizing question order when requested
- Shuffling answer choices while maintaining the mapping to correct answers
- Preparing data for rendering in both preview and PDF generation
"""
import random
from typing import List, Dict, Any, Optional, Tuple
from copy import deepcopy
from datetime import datetime

from ..dal.repositories import QuestionRepository, WorksheetRepository
from ..dal.models import Question, Worksheet
from ..utils.logger import get_logger


class WorksheetGenerator:
    """
    Manages worksheet generation with randomization features.
    
    This class is responsible for assembling worksheets with selected questions,
    randomizing question order, and shuffling answer choices while preserving
    the mapping to the correct answers.
    """
    
    def __init__(self, question_repository: QuestionRepository, 
                 worksheet_repository: Optional[WorksheetRepository] = None):
        """
        Initialize the WorksheetGenerator.
        
        Args:
            question_repository: The repository for question operations
            worksheet_repository: The repository for worksheet operations
        """
        self.logger = get_logger(__name__)
        self.question_repository = question_repository
        self.worksheet_repository = worksheet_repository
    
    def generate_worksheet(self, worksheet: Worksheet, randomize_questions: bool = True,
                          randomize_answers: bool = True) -> Dict[str, Any]:
        """
        Generate a worksheet from the selected questions with randomization.
        
        Args:
            worksheet: Worksheet object containing question IDs and metadata
            randomize_questions: Whether to randomize the order of questions
            randomize_answers: Whether to randomize the order of answer choices
        
        Returns:
            A dictionary containing the worksheet data, including:
            - worksheet: The Worksheet object
            - questions: List of processed Question objects
            - answer_key: Answer key for the worksheet
        
        Raises:
            ValueError: If no questions are found for the provided IDs
        """
        try:
            # Get the questions for the selected IDs
            questions = self._get_questions_by_ids(worksheet.question_ids)
            
            if not questions:
                raise ValueError("No questions found for the provided IDs")
            
            # Randomize question order if requested
            if randomize_questions:
                self._randomize_question_order(questions)
            
            # Randomize answer choices if requested
            answer_key = None
            if randomize_answers:
                answer_key = self._randomize_answer_choices(questions)
            else:
                # If not randomizing answers, create a standard answer key
                answer_key = {str(q.question_id): q.correct_answer for q in questions}
            
            # Create worksheet data structure
            worksheet_data = {
                'worksheet': worksheet,
                'questions': questions,
                'answer_key': answer_key
            }
            
            self.logger.info(
                f"Generated worksheet with {len(questions)} questions, "
                f"randomize_questions={randomize_questions}, "
                f"randomize_answers={randomize_answers}"
            )
            
            return worksheet_data
            
        except Exception as e:
            self.logger.error(f"Error generating worksheet: {str(e)}")
            raise
    
    def generate_from_questions(self, title: str, description: str, questions: List[Question],
                              randomize_questions: bool = True,
                              randomize_answers: bool = True) -> Dict[str, Any]:
        """
        Generate a worksheet from a list of Question objects.
        
        Args:
            title: Worksheet title
            description: Worksheet description
            questions: List of Question objects to include in the worksheet
            randomize_questions: Whether to randomize the order of questions
            randomize_answers: Whether to randomize the order of answer choices
        
        Returns:
            A dictionary containing the worksheet data (same as generate_worksheet())
        
        Raises:
            ValueError: If no questions are provided
        """
        try:
            if not questions:
                raise ValueError("No questions provided for worksheet generation")
            
            # Create a worksheet with the selected question IDs
            worksheet = Worksheet(
                title=title,
                description=description,
                question_ids=[q.question_id for q in questions]
            )
            
            # Generate the worksheet with the selected questions
            return self.generate_worksheet(
                worksheet, 
                randomize_questions=randomize_questions,
                randomize_answers=randomize_answers
            )
            
        except Exception as e:
            self.logger.error(f"Error generating worksheet from questions: {str(e)}")
            raise
            
    def generate_from_filters(self, title: str, description: str, filters: Dict[str, Any], 
                             count: int = 10, randomize_questions: bool = True,
                             randomize_answers: bool = True) -> Dict[str, Any]:
        """
        Generate a worksheet by selecting questions based on filters.
        
        Args:
            title: Worksheet title
            description: Worksheet description
            filters: Dictionary of filter criteria for selecting questions
            count: Number of questions to include
            randomize_questions: Whether to randomize the order of questions
            randomize_answers: Whether to randomize the order of answer choices
        
        Returns:
            A dictionary containing the worksheet data (same as generate_worksheet())
        
        Raises:
            ValueError: If no questions match the provided filters or count is invalid
        """
        try:
            if count <= 0:
                raise ValueError("Question count must be greater than zero")
            
            # Get questions matching the filters
            questions = self.question_repository.filter_questions(filters)
            
            if not questions:
                raise ValueError(f"No questions found matching the provided filters: {filters}")
            
            # Randomize the selection if we have more questions than needed
            if len(questions) > count:
                questions = random.sample(questions, count)
                
            # Use the generate_from_questions method to create the worksheet
            return self.generate_from_questions(
                title=title,
                description=description,
                questions=questions,
                randomize_questions=randomize_questions,
                randomize_answers=randomize_answers
            )
            
        except Exception as e:
            self.logger.error(f"Error generating worksheet from filters: {str(e)}")
            raise
    
    def _get_questions_by_ids(self, question_ids: List[int]) -> List[Question]:
        """
        Get Question objects for the provided IDs.
        
        Args:
            question_ids: List of question IDs
        
        Returns:
            List of Question objects
        """
        questions = []
        
        for qid in question_ids:
            question = self.question_repository.get_question(qid)
            if question:
                questions.append(question)
            else:
                self.logger.warning(f"Question with ID {qid} not found")
        
        return questions
    
    def _randomize_question_order(self, questions: List[Question]) -> None:
        """
        Randomize the order of questions in place.
        
        Args:
            questions: List of Question objects to randomize
        """
        random.shuffle(questions)
        self.logger.debug("Randomized question order")
    
    def _randomize_answer_choices(self, questions: List[Question]) -> Dict[str, str]:
        """
        Randomize answer choices for each question while preserving the correct answer.
        
        Args:
            questions: List of Question objects to process
        
        Returns:
            Dictionary mapping question IDs to their new correct answer choices
        """
        answer_key = {}
        
        for question in questions:
            # Make a deep copy of the question to avoid modifying the original
            q = deepcopy(question)
            
            # Skip answer shuffling for free response questions
            if getattr(q, 'question_type', 'multiple_choice') == 'free_response':
                # For free response questions, just store the correct answer as-is
                answer_key[str(q.question_id)] = q.correct_answer
                continue
            
            # For multiple choice questions, validate correct_answer format
            if not q.correct_answer or q.correct_answer not in ['A', 'B', 'C', 'D']:
                # Skip shuffling if correct_answer is invalid
                answer_key[str(q.question_id)] = q.correct_answer
                continue
            
            # Extract answer choices and corresponding images
            choices = [
                ('A', q.answer_a, q.answer_image_a),
                ('B', q.answer_b, q.answer_image_b),
                ('C', q.answer_c, q.answer_image_c),
                ('D', q.answer_d, q.answer_image_d)
            ]
            
            # Remember which choice is correct
            correct_index = ord(q.correct_answer) - ord('A')
            correct_choice = choices[correct_index]
            
            # Shuffle all choices
            random.shuffle(choices)
            
            # Update the question with the shuffled choices
            q.answer_a, q.answer_image_a = choices[0][1], choices[0][2]
            q.answer_b, q.answer_image_b = choices[1][1], choices[1][2]
            q.answer_c, q.answer_image_c = choices[2][1], choices[2][2]
            q.answer_d, q.answer_image_d = choices[3][1], choices[3][2]
            
            # Find the new position of the correct answer
            for i, (letter, _, _) in enumerate(choices):
                if (letter, choices[i][1], choices[i][2]) == correct_choice:
                    q.correct_answer = chr(i + ord('A'))
                    break
            
            # Store the new correct answer in the answer key
            answer_key[str(q.question_id)] = q.correct_answer
            
            # Replace the original question with the shuffled version
            question.answer_a = q.answer_a
            question.answer_b = q.answer_b
            question.answer_c = q.answer_c
            question.answer_d = q.answer_d
            question.answer_image_a = q.answer_image_a
            question.answer_image_b = q.answer_image_b
            question.answer_image_c = q.answer_image_c
            question.answer_image_d = q.answer_image_d
            question.correct_answer = q.correct_answer
        
        self.logger.debug("Randomized answer choices and created answer key")
        return answer_key
    
    def prepare_for_preview(self, worksheet_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Prepare worksheet data for live preview display.
        
        Args:
            worksheet_data: Worksheet data as returned by generate_worksheet()
        
        Returns:
            List of formatted questions for display
        """
        preview_data = []
        questions = worksheet_data.get('questions', [])
        
        for i, question in enumerate(questions):
            preview_question = {
                'number': i + 1,
                'id': question.question_id,
                'text': question.question_text,
                'image_path': question.question_image_path,
                'question_type': getattr(question, 'question_type', 'multiple_choice'),
                'correct_answer': question.correct_answer
            }
            
            # Only include answer choices for multiple choice questions
            if getattr(question, 'question_type', 'multiple_choice') == 'multiple_choice':
                preview_question['answers'] = [
                    {'letter': 'A', 'text': question.answer_a, 'image_path': question.answer_image_a},
                    {'letter': 'B', 'text': question.answer_b, 'image_path': question.answer_image_b},
                    {'letter': 'C', 'text': question.answer_c, 'image_path': question.answer_image_c},
                    {'letter': 'D', 'text': question.answer_d, 'image_path': question.answer_image_d}
                ]
            else:
                # For free response questions, no predefined answers
                preview_question['answers'] = []
            
            preview_data.append(preview_question)
        
        return preview_data
    
    def save_worksheet(self, worksheet: Worksheet, pdf_path: Optional[str] = None) -> Optional[int]:
        """
        Save the worksheet to the database.
        
        Args:
            worksheet: The worksheet to save
            pdf_path: Path to the generated PDF file
        
        Returns:
            The ID of the saved worksheet, or None if an error occurred
        """
        if not self.worksheet_repository:
            self.logger.warning("Cannot save worksheet: worksheet_repository is not available")
            return None
            
        try:
            # Update the PDF path if provided
            if pdf_path:
                worksheet.pdf_path = pdf_path
                
            # Add the worksheet to the database
            worksheet_id = self.worksheet_repository.add_worksheet(worksheet)
            
            if worksheet_id:
                self.logger.info(f"Saved worksheet {worksheet_id} with {len(worksheet.question_ids)} questions")
                return worksheet_id
            else:
                self.logger.error("Failed to save worksheet")
                return None
                
        except Exception as e:
            self.logger.error(f"Error saving worksheet: {str(e)}")
            return None
    
    def prepare_for_pdf(self, worksheet_data: Dict[str, Any], include_answer_key: bool = True) -> Dict[str, Any]:
        """
        Prepare worksheet data for PDF generation.
        
        Args:
            worksheet_data: Worksheet data as returned by generate_worksheet()
            include_answer_key: Whether to include an answer key in the PDF
        
        Returns:
            Dictionary containing formatted data for PDF generation
        """
        worksheet = worksheet_data.get('worksheet')
        questions = worksheet_data.get('questions', [])
        answer_key = worksheet_data.get('answer_key', {})
        
        # Save the worksheet to the database
        if worksheet and self.worksheet_repository:
            worksheet_id = self.save_worksheet(worksheet)
            if worksheet_id and worksheet_id != worksheet.worksheet_id:
                worksheet.worksheet_id = worksheet_id
        
        pdf_data = {
            'title': worksheet.title,
            'description': worksheet.description,
            'worksheet_id': worksheet.worksheet_id,
            'questions': [],
            'include_answer_key': include_answer_key,
            'answer_key': answer_key
        }
        
        # Format questions for PDF rendering
        for i, question in enumerate(questions):
            pdf_question = {
                'number': i + 1,
                'id': question.question_id,
                'text': question.question_text,
                'image_path': question.question_image_path,
                'question_type': getattr(question, 'question_type', 'multiple_choice')
            }
            
            # Only include answer choices for multiple choice questions
            if getattr(question, 'question_type', 'multiple_choice') == 'multiple_choice':
                pdf_question['answers'] = [
                    {'letter': 'A', 'text': question.answer_a, 'image_path': question.answer_image_a},
                    {'letter': 'B', 'text': question.answer_b, 'image_path': question.answer_image_b},
                    {'letter': 'C', 'text': question.answer_c, 'image_path': question.answer_image_c},
                    {'letter': 'D', 'text': question.answer_d, 'image_path': question.answer_image_d}
                ]
            else:
                # For free response questions, no predefined answers but provide space for writing
                pdf_question['answers'] = []
                pdf_question['response_space'] = True  # Indicate that space should be provided for writing
            
            pdf_data['questions'].append(pdf_question)
        
        return pdf_data