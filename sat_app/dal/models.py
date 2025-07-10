"""
Data models for the SAT Question Bank application.
Defines the core data objects used in the application.
"""
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Question:
    """
    Represents an SAT question.
    
    Contains the question text, answer choices, correct answer,
    and associated metadata.
    """
    question_id: int = 0
    question_text: str = ""
    question_image_path: Optional[str] = None
    answer_a: str = ""
    answer_b: str = ""
    answer_c: str = ""
    answer_d: str = ""
    answer_image_a: Optional[str] = None
    answer_image_b: Optional[str] = None
    answer_image_c: Optional[str] = None
    answer_image_d: Optional[str] = None
    correct_answer: str = ""  # 'A', 'B', 'C', or 'D' for multiple choice, or expected answer for free response
    answer_explanation: str = ""
    question_type: str = "multiple_choice"  # 'multiple_choice' or 'free_response'
    subject_tags: List[str] = field(default_factory=list)
    difficulty_label: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Question':
        """
        Create a Question from a dictionary.
        
        Args:
            data: Dictionary containing question data
        
        Returns:
            A Question object
        """
        # Handle subject_tags which might be a comma-separated string
        subject_tags = data.get('subject_tags', [])
        if isinstance(subject_tags, str):
            subject_tags = [tag.strip() for tag in subject_tags.split(',') if tag.strip()]
        
        # Handle dates
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
        
        updated_at = data.get('updated_at')
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        elif updated_at is None:
            updated_at = datetime.now()
        
        return cls(
            question_id=data.get('question_id', 0),
            question_text=data.get('question_text', ''),
            question_image_path=data.get('question_image_path'),
            answer_a=data.get('answer_a', ''),
            answer_b=data.get('answer_b', ''),
            answer_c=data.get('answer_c', ''),
            answer_d=data.get('answer_d', ''),
            answer_image_a=data.get('answer_image_a'),
            answer_image_b=data.get('answer_image_b'),
            answer_image_c=data.get('answer_image_c'),
            answer_image_d=data.get('answer_image_d'),
            correct_answer=data.get('correct_answer', ''),
            answer_explanation=data.get('answer_explanation', ''),
            question_type=data.get('question_type', 'multiple_choice'),
            subject_tags=subject_tags,
            difficulty_label=data.get('difficulty_label', ''),
            created_at=created_at,
            updated_at=updated_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Question to a dictionary.
        
        Returns:
            A dictionary representation of the Question
        """
        return {
            'question_id': self.question_id,
            'question_text': self.question_text,
            'question_image_path': self.question_image_path,
            'answer_a': self.answer_a,
            'answer_b': self.answer_b,
            'answer_c': self.answer_c,
            'answer_d': self.answer_d,
            'answer_image_a': self.answer_image_a,
            'answer_image_b': self.answer_image_b,
            'answer_image_c': self.answer_image_c,
            'answer_image_d': self.answer_image_d,
            'correct_answer': self.correct_answer,
            'answer_explanation': self.answer_explanation,
            'question_type': self.question_type,
            'subject_tags': ','.join(self.subject_tags),
            'difficulty_label': self.difficulty_label,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class Worksheet:
    """
    Represents a worksheet.
    
    Contains the worksheet ID, title, description,
    list of question IDs, and path to the generated PDF.
    """
    worksheet_id: int = 0
    title: str = ""
    description: str = ""
    question_ids: List[int] = field(default_factory=list)
    pdf_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Worksheet':
        """
        Create a Worksheet from a dictionary.
        
        Args:
            data: Dictionary containing worksheet data
        
        Returns:
            A Worksheet object
        """
        # Handle question_ids which might be a JSON string or a comma-separated string
        question_ids = data.get('question_ids', [])
        if isinstance(question_ids, str):
            try:
                question_ids = json.loads(question_ids)
            except json.JSONDecodeError:
                question_ids = [int(id.strip()) for id in question_ids.split(',') if id.strip().isdigit()]
        
        # Handle date
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
        
        return cls(
            worksheet_id=data.get('worksheet_id', 0),
            title=data.get('title', ''),
            description=data.get('description', ''),
            question_ids=question_ids,
            pdf_path=data.get('pdf_path'),
            created_at=created_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Worksheet to a dictionary.
        
        Returns:
            A dictionary representation of the Worksheet
        """
        return {
            'worksheet_id': self.worksheet_id,
            'title': self.title,
            'description': self.description,
            'question_ids': json.dumps(self.question_ids),
            'pdf_path': self.pdf_path,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class Score:
    """
    Represents a student's score for a question.
    
    Contains the score ID, student ID, worksheet ID,
    question ID, whether the answer was correct, and timestamp.
    """
    score_id: int = 0
    student_id: str = ""
    worksheet_id: int = 0
    question_id: int = 0
    correct: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Score':
        """
        Create a Score from a dictionary.
        
        Args:
            data: Dictionary containing score data
        
        Returns:
            A Score object
        """
        # Handle date
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()
        
        return cls(
            score_id=data.get('score_id', 0),
            student_id=data.get('student_id', ''),
            worksheet_id=data.get('worksheet_id', 0),
            question_id=data.get('question_id', 0),
            correct=bool(data.get('correct', False)),
            timestamp=timestamp
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Score to a dictionary.
        
        Returns:
            A dictionary representation of the Score
        """
        return {
            'score_id': self.score_id,
            'student_id': self.student_id,
            'worksheet_id': self.worksheet_id,
            'question_id': self.question_id,
            'correct': 1 if self.correct else 0,  # SQLite doesn't have a boolean type
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class StudentResponse:
    """
    Represents a student's response to a question.
    
    Stores the actual answer given by the student, separate from scoring.
    This allows for both automatic scoring and manual review of free response answers.
    """
    response_id: int = 0
    student_id: str = ""
    worksheet_id: int = 0
    question_id: int = 0
    student_answer: str = ""  # The actual answer given by the student
    is_graded: bool = False  # Whether this response has been manually graded
    is_correct: Optional[bool] = None  # Manual grade (True/False/None for ungraded)
    graded_by: Optional[str] = None  # Who graded this response
    grading_notes: str = ""  # Optional notes from grader
    timestamp: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StudentResponse':
        """
        Create a StudentResponse from a dictionary.
        
        Args:
            data: Dictionary containing response data
        
        Returns:
            A StudentResponse object
        """
        # Handle date
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()
        
        # Handle is_correct which might be None, 0, 1, or boolean
        is_correct = data.get('is_correct')
        if is_correct is not None:
            if isinstance(is_correct, (int, str)):
                if str(is_correct) in ['0', 'False']:
                    is_correct = False
                elif str(is_correct) in ['1', 'True']:
                    is_correct = True
                else:
                    is_correct = None
        
        return cls(
            response_id=data.get('response_id', 0),
            student_id=data.get('student_id', ''),
            worksheet_id=data.get('worksheet_id', 0),
            question_id=data.get('question_id', 0),
            student_answer=data.get('student_answer', ''),
            is_graded=bool(data.get('is_graded', False)),
            is_correct=is_correct,
            graded_by=data.get('graded_by'),
            grading_notes=data.get('grading_notes', ''),
            timestamp=timestamp
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the StudentResponse to a dictionary.
        
        Returns:
            A dictionary representation of the StudentResponse
        """
        return {
            'response_id': self.response_id,
            'student_id': self.student_id,
            'worksheet_id': self.worksheet_id,
            'question_id': self.question_id,
            'student_answer': self.student_answer,
            'is_graded': 1 if self.is_graded else 0,
            'is_correct': None if self.is_correct is None else (1 if self.is_correct else 0),
            'graded_by': self.graded_by,
            'grading_notes': self.grading_notes,
            'timestamp': self.timestamp.isoformat()
        }