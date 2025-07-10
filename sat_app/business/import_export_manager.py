"""
Module for handling import and export of questions.

This module contains the ImportExportManager class that manages the import and export
of questions in JSON format.
"""

import json
import os
import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import logging
import shutil
from fuzzywuzzy import fuzz

from sat_app.dal.models import Question
from sat_app.dal.repositories import QuestionRepository
from sat_app.utils.logger import get_logger

logger = get_logger(__name__)


class ImportExportManager:
    """
    Manages the import and export of questions in JSON format.
    
    This class provides functionality to:
    - Import questions from a JSON file
    - Export questions to a JSON file
    - Validate imported JSON against a schema
    - Handle associated images during import/export
    """
    
    SCHEMA_FIELDS = {
        'required': [
            'question_text',
        ],
        'optional': [
            'answer_a', 'answer_b', 'answer_c', 'answer_d', 'correct_answer',
            'question_image_path', 'answer_image_a', 'answer_image_b',
            'answer_image_c', 'answer_image_d', 'answer_explanation',
            'subject_tags', 'difficulty_label', 'question_type'
        ]
    }
    
    def __init__(self, question_repository: QuestionRepository, 
                 image_base_path: str) -> None:
        """
        Initialize the ImportExportManager.
        
        Args:
            question_repository: Repository for question operations
            image_base_path: Base path where question images are stored
        """
        self.question_repository = question_repository
        self.image_base_path = image_base_path
        self.logger = logger
    
    def export_questions(self, question_ids: List[int], 
                          export_path: str,
                          include_images: bool = True) -> Tuple[bool, str]:
        """
        Export questions to a JSON file.
        
        Args:
            question_ids: List of question IDs to export
            export_path: Path to the export file
            include_images: Whether to include images in the export
            
        Returns:
            (success, message): Tuple indicating success and a message
        """
        try:
            # Get all questions to be exported
            questions = []
            for qid in question_ids:
                question = self.question_repository.get_question(qid)
                if question:
                    questions.append(question)
                else:
                    self.logger.warning(f"Question with ID {qid} not found, skipping.")
            
            # Create dictionary with questions and metadata
            export_data = {
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "count": len(questions),
                    "version": "1.0"
                },
                "questions": [q.to_dict() for q in questions]
            }
            
            # Create a directory for images if needed
            if include_images and any(self._has_images(q) for q in questions):
                export_dir = os.path.dirname(export_path)
                images_dir = os.path.join(export_dir, 'images')
                os.makedirs(images_dir, exist_ok=True)
                
                # Copy images and update paths in the export data
                for i, question_dict in enumerate(export_data["questions"]):
                    question = questions[i]
                    self._process_images_for_export(question_dict, question, images_dir)
            
            # Write to JSON file
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return True, f"Successfully exported {len(questions)} questions to {export_path}"
        
        except Exception as e:
            error_msg = f"Error during export: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def import_questions(self, import_path: str, 
                         import_images: bool = True) -> Tuple[bool, str, Dict[str, int]]:
        """
        Import questions from a JSON file.
        
        Args:
            import_path: Path to the import file
            import_images: Whether to import related images
            
        Returns:
            (success, message, stats): Tuple with success flag, message, and import statistics
        """
        stats = {
            "total": 0,
            "imported": 0,
            "skipped": 0,
            "duplicates": 0,
            "errors": 0
        }
        
        try:
            # Read and parse JSON file
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if not isinstance(import_data, dict) or "questions" not in import_data:
                return False, "Invalid import format: missing 'questions' array", stats
            
            question_dicts = import_data.get("questions", [])
            stats["total"] = len(question_dicts)
            
            # Process each question
            for q_dict in question_dicts:
                try:
                    # Validate schema
                    validation_result, validation_msg = self._validate_question_schema(q_dict)
                    if not validation_result:
                        self.logger.warning(f"Skipping invalid question: {validation_msg}")
                        stats["skipped"] += 1
                        continue
                    
                    # Check for duplicates using fuzzy matching
                    if self._is_duplicate_question(q_dict):
                        self.logger.info(f"Skipping duplicate question: {q_dict.get('question_text', '')[:50]}...")
                        stats["duplicates"] += 1
                        continue
                    
                    # Process images if needed
                    if import_images:
                        self._process_images_for_import(q_dict, import_path)
                    
                    # Create and add question
                    question = Question.from_dict(q_dict)
                    self.question_repository.add_question(question)
                    stats["imported"] += 1
                    
                except Exception as e:
                    self.logger.error(f"Error importing question: {str(e)}", exc_info=True)
                    stats["errors"] += 1
            
            success_msg = (f"Import complete: {stats['imported']} imported, "
                          f"{stats['skipped']} skipped, {stats['duplicates']} duplicates, "
                          f"{stats['errors']} errors")
            return True, success_msg, stats
            
        except Exception as e:
            error_msg = f"Error during import: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg, stats
    
    def _has_images(self, question: Question) -> bool:
        """Check if a question has any associated images."""
        return any([
            question.question_image_path,
            question.answer_image_a,
            question.answer_image_b,
            question.answer_image_c,
            question.answer_image_d
        ])
    
    def _process_images_for_export(self, question_dict: Dict[str, Any], 
                                 question: Question, images_dir: str) -> None:
        """
        Process and copy images for export.
        
        Args:
            question_dict: Question dictionary for export
            question: Original Question object
            images_dir: Directory to save exported images
        """
        image_fields = [
            "question_image_path", "answer_image_a", "answer_image_b",
            "answer_image_c", "answer_image_d"
        ]
        
        for field in image_fields:
            image_path = getattr(question, field, None)
            if not image_path:
                continue
                
            # Create a unique filename for the exported image
            original_name = os.path.basename(image_path)
            unique_name = f"{uuid.uuid4().hex}_{original_name}"
            export_image_path = os.path.join(images_dir, unique_name)
            
            # Copy the image file
            try:
                full_original_path = os.path.join(self.image_base_path, image_path)
                shutil.copy2(full_original_path, export_image_path)
                
                # Update the path in the export dict to be relative to the export file
                question_dict[field] = os.path.join('images', unique_name)
            except Exception as e:
                self.logger.error(f"Error copying image {image_path}: {str(e)}")
                # Keep the original path if copy fails
    
    def _process_images_for_import(self, question_dict: Dict[str, Any], 
                                 import_path: str) -> None:
        """
        Process images during import.
        
        Args:
            question_dict: Question dictionary being imported
            import_path: Path to the import file
        """
        image_fields = [
            "question_image_path", "answer_image_a", "answer_image_b",
            "answer_image_c", "answer_image_d"
        ]
        
        import_dir = os.path.dirname(import_path)
        
        for field in image_fields:
            image_path = question_dict.get(field)
            if not image_path:
                continue
                
            # Resolve the path relative to the import file
            full_import_path = os.path.join(import_dir, image_path)
            
            if not os.path.exists(full_import_path):
                self.logger.warning(f"Image not found: {full_import_path}")
                question_dict[field] = None
                continue
                
            # Create a destination path within our image structure
            image_type = "questions" if field == "question_image_path" else "answers"
            filename = os.path.basename(image_path)
            unique_name = f"{uuid.uuid4().hex}_{filename}"
            dest_rel_path = os.path.join(image_type, unique_name)
            dest_abs_path = os.path.join(self.image_base_path, dest_rel_path)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(dest_abs_path), exist_ok=True)
            
            # Copy the image
            try:
                shutil.copy2(full_import_path, dest_abs_path)
                # Update path to be relative to image base directory
                question_dict[field] = dest_rel_path
            except Exception as e:
                self.logger.error(f"Error importing image {image_path}: {str(e)}")
                question_dict[field] = None
    
    def _validate_question_schema(self, question_dict: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate a question dictionary against the schema.
        
        Args:
            question_dict: Question dictionary to validate
            
        Returns:
            (valid, message): Whether the question is valid and a message
        """
        # Check required fields
        for field in self.SCHEMA_FIELDS['required']:
            if field not in question_dict or question_dict[field] is None:
                return False, f"Missing required field: {field}"
        
        # Convert complex answer data structures to strings if needed
        self._normalize_answer_fields(question_dict)
        
        # Auto-detect question type if not explicitly set
        question_type = question_dict.get('question_type')
        correct_answer = question_dict.get('correct_answer')
        
        # If question_type is not set, try to infer it from the data
        if question_type is None:
            # Check if we have multiple choice answers (A, B, C, D)
            has_multiple_choice_answers = any([
                question_dict.get('answer_a'),
                question_dict.get('answer_b'),
                question_dict.get('answer_c'),
                question_dict.get('answer_d')
            ])
            
            # If correct_answer is A, B, C, or D, it's likely multiple choice
            if correct_answer and correct_answer in ['A', 'B', 'C', 'D']:
                question_type = 'multiple_choice'
            # If we have multiple choice answers, assume multiple choice
            elif has_multiple_choice_answers:
                question_type = 'multiple_choice'
            # If correct_answer is not A-D format and no multiple choice answers, assume free response
            else:
                question_type = 'free_response'
                
            # Update the question dict with the inferred type
            question_dict['question_type'] = question_type
            self.logger.info(f"Auto-detected question_type as '{question_type}' for question: {question_dict.get('question_text', '')[:50]}...")
        
        # Validate question_type
        if question_type not in ['multiple_choice', 'free_response']:
            return False, f"Invalid question_type: {question_type}. Must be 'multiple_choice' or 'free_response'."
        
        # Validate correct_answer based on question type
        if question_type == 'multiple_choice':
            # For multiple choice, correct_answer must be A, B, C, or D (if provided and not empty)
            if correct_answer is not None and correct_answer.strip() != '' and correct_answer not in ['A', 'B', 'C', 'D']:
                # If we have a non-A-D answer but it's marked as multiple choice, suggest it might be free response
                self.logger.warning(f"Question marked as multiple_choice but correct_answer is '{correct_answer}'. Consider changing question_type to 'free_response'.")
                return False, f"Invalid correct_answer for multiple_choice: {correct_answer}. Must be one of A, B, C, D. If this is a free response question, set question_type to 'free_response'."
            elif correct_answer is not None and correct_answer.strip() == '':
                # Handle empty correct_answer - this is valid for import, can be set later
                self.logger.info(f"Multiple choice question has empty correct_answer - this can be set later during editing.")
        # For free_response, correct_answer can be any string or empty/null
        
        # All fields should be in either required or optional
        all_allowed_fields = (
            self.SCHEMA_FIELDS['required'] + 
            self.SCHEMA_FIELDS['optional'] + 
            ['question_id', 'created_at', 'updated_at']  # System fields
        )
        
        for field in question_dict:
            if field not in all_allowed_fields:
                return False, f"Unknown field: {field}"
        
        return True, "Valid"
    
    def _normalize_answer_fields(self, question_dict: Dict[str, Any]) -> None:
        """
        Normalize complex answer data structures to strings for database storage.
        
        Args:
            question_dict: Question dictionary to normalize
        """
        answer_fields = ['answer_a', 'answer_b', 'answer_c', 'answer_d']
        
        for field in answer_fields:
            answer_value = question_dict.get(field)
            if answer_value is None:
                continue
                
            # If the answer is a complex data structure (dict, list), convert to string
            if isinstance(answer_value, (dict, list)):
                try:
                    # For table data, create a readable string representation
                    if isinstance(answer_value, dict):
                        # Handle table-like data structures
                        if 'x' in answer_value and 'h(x)' in answer_value:
                            x_values = answer_value.get('x', [])
                            h_values = answer_value.get('h(x)', [])
                            if len(x_values) == len(h_values):
                                # Create a table-like string representation
                                rows = []
                                for x, h in zip(x_values, h_values):
                                    rows.append(f"x={x}, h(x)={h}")
                                question_dict[field] = "; ".join(rows)
                            else:
                                # Fallback to string representation
                                question_dict[field] = str(answer_value)
                        else:
                            # General dictionary handling
                            question_dict[field] = str(answer_value)
                    else:
                        # Handle lists and other structures
                        question_dict[field] = str(answer_value)
                        
                    self.logger.info(f"Converted complex {field} data to string: {question_dict[field][:50]}...")
                    
                except Exception as e:
                    self.logger.error(f"Error converting {field} data to string: {str(e)}")
                    question_dict[field] = "[Complex data - conversion failed]"
            
            # Ensure the field is a string
            elif not isinstance(answer_value, str):
                question_dict[field] = str(answer_value)
        
        # For free response questions, ensure answer fields are set to empty strings if None
        question_type = question_dict.get('question_type', 'multiple_choice')
        if question_type == 'free_response':
            for field in answer_fields:
                if question_dict.get(field) is None:
                    question_dict[field] = ""
    
    def export_all_questions(self, export_path: str, 
                             include_images: bool = True) -> Tuple[bool, str]:
        """
        Export all questions to a JSON file.
        
        Args:
            export_path: Path to the export file
            include_images: Whether to include images in the export
            
        Returns:
            (success, message): Tuple indicating success and a message
        """
        questions = self.question_repository.get_all_questions()
        question_ids = [q.question_id for q in questions]
        return self.export_questions(question_ids, export_path, include_images)
    
    def export_filtered_questions(self, filters: Dict[str, Any], 
                                  export_path: str,
                                  include_images: bool = True) -> Tuple[bool, str]:
        """
        Export questions that match the given filters.
        
        Args:
            filters: Dictionary of filters to apply
            export_path: Path to the export file
            include_images: Whether to include images in the export
            
        Returns:
            (success, message): Tuple indicating success and a message
        """
        questions = self.question_repository.filter_questions(filters)
        question_ids = [q.question_id for q in questions]
        return self.export_questions(question_ids, export_path, include_images)
    
    def _normalize_text_for_comparison(self, text: str) -> str:
        """
        Normalize text for fuzzy comparison by removing LaTeX formatting and image annotations.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text for comparison
        """
        if not text:
            return ""
        
        # Handle non-string inputs (like dictionaries or other objects)
        if not isinstance(text, str):
            # Try to convert to string representation
            try:
                text = str(text)
            except Exception:
                return ""
        
        # Convert to lowercase
        normalized = text.lower()
        
        # Remove common LaTeX delimiters and commands but keep the content
        normalized = re.sub(r'\$([^$]+)\$', r'\1', normalized)  # Remove $ delimiters
        normalized = re.sub(r'\\[a-zA-Z]+ ?', '', normalized)   # Remove LaTeX commands like \sqrt, \frac
        normalized = re.sub(r'[{}]', '', normalized)            # Remove braces
        
        # Remove common image annotation patterns
        normalized = re.sub(r'\(see (figure|image|table|diagram)[^)]*\)', '', normalized)
        normalized = re.sub(r'\(figure \d+[^)]*\)', '', normalized)
        normalized = re.sub(r'\(image [^)]*\)', '', normalized)
        normalized = re.sub(r'as shown in the (figure|image|table|diagram)', '', normalized)
        
        # Clean up whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized.strip()
    
    def _get_question_signature(self, question_dict: Dict[str, Any]) -> str:
        """
        Create a signature string for a question combining normalized text and answers.
        
        Args:
            question_dict: Question dictionary
            
        Returns:
            Normalized signature string for comparison
        """
        # Normalize question text
        question_text = self._normalize_text_for_comparison(
            question_dict.get('question_text', '')
        )
        
        # Normalize and combine answer choices (if they exist)
        answers = []
        for choice in ['answer_a', 'answer_b', 'answer_c', 'answer_d']:
            answer_text = question_dict.get(choice, '')
            if answer_text:  # Only include non-empty answers
                normalized_answer = self._normalize_text_for_comparison(answer_text)
                answers.append(normalized_answer)
        
        # Create combined signature
        if answers:
            # For multiple choice questions
            return f"{question_text} ||| {' | '.join(sorted(answers))}"
        else:
            # For open response questions
            return question_text
    
    def _is_duplicate_question(self, question_dict: Dict[str, Any], 
                              similarity_threshold: int = 95) -> bool:
        """
        Check if a question is a duplicate using fuzzy matching.
        
        Args:
            question_dict: Question dictionary to check
            similarity_threshold: Minimum similarity score (0-100) to consider as duplicate
            
        Returns:
            True if question is likely a duplicate, False otherwise
        """
        try:
            # Get all existing questions from database
            existing_questions = self.question_repository.get_all_questions()
            
            if not existing_questions:
                return False
            
            # Create signature for the new question
            new_signature = self._get_question_signature(question_dict)
            
            if not new_signature.strip():
                return False
            
            # Compare with existing questions
            for existing_question in existing_questions:
                existing_dict = existing_question.to_dict()
                existing_signature = self._get_question_signature(existing_dict)
                
                if not existing_signature.strip():
                    continue
                
                # Calculate similarity using token set ratio (handles word order differences)
                similarity = fuzz.token_set_ratio(new_signature, existing_signature)
                
                if similarity >= similarity_threshold:
                    self.logger.debug(
                        f"Found duplicate with {similarity}% similarity: "
                        f"'{new_signature[:50]}...' vs '{existing_signature[:50]}...'"
                    )
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error during duplicate checking: {str(e)}", exc_info=True)
            # If there's an error, don't block the import - just log and continue
            return False