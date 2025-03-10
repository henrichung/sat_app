"""
Question editor module for the SAT Question Bank application.
Provides forms for adding and editing questions.
"""
import os
import re
import tempfile
from typing import Optional, Dict, Any, Callable, Tuple, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QComboBox,
    QPushButton, QFileDialog, QGridLayout, QMessageBox, QGroupBox, QRadioButton,
    QButtonGroup, QFormLayout, QScrollArea, QToolButton, QDialog, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QIcon, QImage, QTextCursor, QColor

from ..ui.animations import ValidationAnimator, ProgressAnimator, NotificationManager, AnimationSpeed

from ..business.question_manager import QuestionManager
from ..dal.models import Question
from ..utils.logger import get_logger

class QuestionEditor(QWidget):
    """
    Question editor widget.
    
    Provides forms for adding and editing questions, including text input,
    image selection, and answer option management.
    """
    
    # Signal emitted when a question is saved
    question_saved = pyqtSignal(int)
    
    def __init__(self, question_manager: QuestionManager, parent=None):
        """
        Initialize the question editor.
        
        Args:
            question_manager: The manager for question operations
            parent: The parent widget
        """
        super().__init__(parent)
        
        self.logger = get_logger(__name__)
        self.question_manager = question_manager
        self.current_question_id: Optional[int] = None
        self.question_image_path: Optional[str] = None
        self.answer_image_paths: Dict[str, Optional[str]] = {
            'A': None, 'B': None, 'C': None, 'D': None
        }
        
        # Initialize animation utilities
        self.validation_animator = ValidationAnimator()
        self.progress_animator = ProgressAnimator()
        self.notification_manager = NotificationManager()
        
        # State tracking
        self.is_saving = False
        self.button_original_state = None
        
        # Create layout
        main_layout = QVBoxLayout(self)
        
        # Create scroll area for the form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Question details group
        question_group = QGroupBox("Question Details")
        question_layout = QFormLayout()
        
        # Question text with LaTeX support
        question_text_layout = QVBoxLayout()
        
        self.question_text = QTextEdit()
        self.question_text.setPlaceholderText("Enter question text here... Use $...$ for LaTeX equations")
        self.question_text.setMinimumHeight(100)
        question_text_layout.addWidget(self.question_text)
        
        question_layout.addRow("Question Text:", question_text_layout)
        
        # Question image
        image_layout = QHBoxLayout()
        self.question_image_button = QPushButton("Select Image")
        self.question_image_button.clicked.connect(self._select_question_image)
        self.question_image_label = QLabel("No image selected")
        self.question_image_clear = QPushButton("Clear")
        self.question_image_clear.clicked.connect(self._clear_question_image)
        image_layout.addWidget(self.question_image_button)
        image_layout.addWidget(self.question_image_label, 1)
        image_layout.addWidget(self.question_image_clear)
        question_layout.addRow("Question Image:", image_layout)
        
        # Subject tags
        self.subject_tags = QLineEdit()
        self.subject_tags.setPlaceholderText("Enter comma-separated tags (e.g., Math,Algebra,Equations)")
        question_layout.addRow("Subject Tags:", self.subject_tags)
        
        # Difficulty
        self.difficulty = QComboBox()
        self.difficulty.addItems(["Easy", "Medium", "Hard", "Very Hard"])
        question_layout.addRow("Difficulty:", self.difficulty)
        
        question_group.setLayout(question_layout)
        scroll_layout.addWidget(question_group)
        
        # Answers group
        answers_group = QGroupBox("Answer Options")
        answers_layout = QGridLayout()
        
        # Correct answer radio buttons
        self.correct_answer_group = QButtonGroup(self)
        
        # Answer A
        self.correct_a = QRadioButton("A")
        self.correct_answer_group.addButton(self.correct_a, 0)
        answers_layout.addWidget(self.correct_a, 0, 0)
        
        answer_a_layout = QVBoxLayout()
        self.answer_a = QTextEdit()
        self.answer_a.setPlaceholderText("Enter answer option A... Use $...$ for LaTeX equations")
        self.answer_a.setMaximumHeight(80)
        answer_a_layout.addWidget(self.answer_a)
        
        answers_layout.addLayout(answer_a_layout, 0, 1)
        
        answer_a_image_layout = QHBoxLayout()
        self.answer_a_image_button = QPushButton("Select Image")
        self.answer_a_image_button.clicked.connect(lambda: self._select_answer_image('A'))
        self.answer_a_image_label = QLabel("No image")
        self.answer_a_image_clear = QPushButton("Clear")
        self.answer_a_image_clear.clicked.connect(lambda: self._clear_answer_image('A'))
        answer_a_image_layout.addWidget(self.answer_a_image_button)
        answer_a_image_layout.addWidget(self.answer_a_image_label, 1)
        answer_a_image_layout.addWidget(self.answer_a_image_clear)
        answers_layout.addLayout(answer_a_image_layout, 0, 2)
        
        # Answer B
        self.correct_b = QRadioButton("B")
        self.correct_answer_group.addButton(self.correct_b, 1)
        answers_layout.addWidget(self.correct_b, 1, 0)
        
        answer_b_layout = QVBoxLayout()
        self.answer_b = QTextEdit()
        self.answer_b.setPlaceholderText("Enter answer option B... Use $...$ for LaTeX equations")
        self.answer_b.setMaximumHeight(80)
        answer_b_layout.addWidget(self.answer_b)
        
        answers_layout.addLayout(answer_b_layout, 1, 1)
        
        answer_b_image_layout = QHBoxLayout()
        self.answer_b_image_button = QPushButton("Select Image")
        self.answer_b_image_button.clicked.connect(lambda: self._select_answer_image('B'))
        self.answer_b_image_label = QLabel("No image")
        self.answer_b_image_clear = QPushButton("Clear")
        self.answer_b_image_clear.clicked.connect(lambda: self._clear_answer_image('B'))
        answer_b_image_layout.addWidget(self.answer_b_image_button)
        answer_b_image_layout.addWidget(self.answer_b_image_label, 1)
        answer_b_image_layout.addWidget(self.answer_b_image_clear)
        answers_layout.addLayout(answer_b_image_layout, 1, 2)
        
        # Answer C
        self.correct_c = QRadioButton("C")
        self.correct_answer_group.addButton(self.correct_c, 2)
        answers_layout.addWidget(self.correct_c, 2, 0)
        
        answer_c_layout = QVBoxLayout()
        self.answer_c = QTextEdit()
        self.answer_c.setPlaceholderText("Enter answer option C... Use $...$ for LaTeX equations")
        self.answer_c.setMaximumHeight(80)
        answer_c_layout.addWidget(self.answer_c)
        
        answers_layout.addLayout(answer_c_layout, 2, 1)
        
        answer_c_image_layout = QHBoxLayout()
        self.answer_c_image_button = QPushButton("Select Image")
        self.answer_c_image_button.clicked.connect(lambda: self._select_answer_image('C'))
        self.answer_c_image_label = QLabel("No image")
        self.answer_c_image_clear = QPushButton("Clear")
        self.answer_c_image_clear.clicked.connect(lambda: self._clear_answer_image('C'))
        answer_c_image_layout.addWidget(self.answer_c_image_button)
        answer_c_image_layout.addWidget(self.answer_c_image_label, 1)
        answer_c_image_layout.addWidget(self.answer_c_image_clear)
        answers_layout.addLayout(answer_c_image_layout, 2, 2)
        
        # Answer D
        self.correct_d = QRadioButton("D")
        self.correct_answer_group.addButton(self.correct_d, 3)
        answers_layout.addWidget(self.correct_d, 3, 0)
        
        answer_d_layout = QVBoxLayout()
        self.answer_d = QTextEdit()
        self.answer_d.setPlaceholderText("Enter answer option D... Use $...$ for LaTeX equations")
        self.answer_d.setMaximumHeight(80)
        answer_d_layout.addWidget(self.answer_d)
        
        answers_layout.addLayout(answer_d_layout, 3, 1)
        
        answer_d_image_layout = QHBoxLayout()
        self.answer_d_image_button = QPushButton("Select Image")
        self.answer_d_image_button.clicked.connect(lambda: self._select_answer_image('D'))
        self.answer_d_image_label = QLabel("No image")
        self.answer_d_image_clear = QPushButton("Clear")
        self.answer_d_image_clear.clicked.connect(lambda: self._clear_answer_image('D'))
        answer_d_image_layout.addWidget(self.answer_d_image_button)
        answer_d_image_layout.addWidget(self.answer_d_image_label, 1)
        answer_d_image_layout.addWidget(self.answer_d_image_clear)
        answers_layout.addLayout(answer_d_image_layout, 3, 2)
        
        answers_group.setLayout(answers_layout)
        scroll_layout.addWidget(answers_group)
        
        # Explanation group
        explanation_group = QGroupBox("Explanation")
        explanation_layout = QVBoxLayout()
        
        self.explanation = QTextEdit()
        self.explanation.setPlaceholderText("Enter explanation for the correct answer... Use $...$ for LaTeX equations")
        self.explanation.setMinimumHeight(100)
        explanation_layout.addWidget(self.explanation)
        
        explanation_group.setLayout(explanation_layout)
        scroll_layout.addWidget(explanation_group)
        
        # Set the scroll content and add to main layout
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Clear Form")
        self.clear_button.clicked.connect(self.clear_form)
        button_layout.addWidget(self.clear_button)
        
        button_layout.addStretch()
        
        self.save_button = QPushButton("Save Question")
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self.save_question)
        button_layout.addWidget(self.save_button)
        
        main_layout.addLayout(button_layout)
        
        # Set default
        self.correct_a.setChecked(True)
        
        self.logger.info("Question editor initialized")
    
    def clear_form(self):
        """Clear all form fields and reset the editor."""
        self.current_question_id = None
        self.question_text.clear()
        self.question_image_path = None
        self.question_image_label.setText("No image selected")
        self.subject_tags.clear()
        self.difficulty.setCurrentIndex(0)
        self.answer_a.clear()
        self.answer_b.clear()
        self.answer_c.clear()
        self.answer_d.clear()
        self.explanation.clear()
        self.correct_a.setChecked(True)
        
        # Clear answer images
        for option in ['A', 'B', 'C', 'D']:
            self.answer_image_paths[option] = None
            getattr(self, f"answer_{option.lower()}_image_label").setText("No image")
        
        self.save_button.setText("Save Question")
        self.logger.debug("Form cleared")
    
    def load_question(self, question_id: int):
        """
        Load a question into the editor.
        
        Args:
            question_id: ID of the question to load
        """
        try:
            question = self.question_manager.get_question(question_id)
            if not question:
                QMessageBox.warning(self, "Error", f"Question with ID {question_id} not found")
                return
            
            self.current_question_id = question_id
            self.question_text.setText(question.question_text)
            self.question_image_path = question.question_image_path
            if question.question_image_path:
                self.question_image_label.setText(os.path.basename(question.question_image_path))
            else:
                self.question_image_label.setText("No image selected")
            
            self.subject_tags.setText(",".join(question.subject_tags))
            
            # Set difficulty
            difficulty_index = self.difficulty.findText(question.difficulty_label)
            if difficulty_index >= 0:
                self.difficulty.setCurrentIndex(difficulty_index)
            
            # Set answers
            self.answer_a.setText(question.answer_a)
            self.answer_b.setText(question.answer_b)
            self.answer_c.setText(question.answer_c)
            self.answer_d.setText(question.answer_d)
            
            # Set answer images
            self.answer_image_paths = {
                'A': question.answer_image_a,
                'B': question.answer_image_b,
                'C': question.answer_image_c,
                'D': question.answer_image_d
            }
            
            for option in ['A', 'B', 'C', 'D']:
                image_path = getattr(question, f"answer_image_{option.lower()}")
                if image_path:
                    getattr(self, f"answer_{option.lower()}_image_label").setText(os.path.basename(image_path))
                else:
                    getattr(self, f"answer_{option.lower()}_image_label").setText("No image")
            
            # Set correct answer
            if question.correct_answer == 'A':
                self.correct_a.setChecked(True)
            elif question.correct_answer == 'B':
                self.correct_b.setChecked(True)
            elif question.correct_answer == 'C':
                self.correct_c.setChecked(True)
            elif question.correct_answer == 'D':
                self.correct_d.setChecked(True)
            
            self.explanation.setText(question.answer_explanation)
            
            self.save_button.setText("Update Question")
            self.logger.info(f"Loaded question ID: {question_id}")
        
        except Exception as e:
            self.logger.error(f"Error loading question: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error loading question: {str(e)}")
    
    def save_question(self):
        """Save or update the current question with animation feedback."""
        # Prevent multiple save attempts
        if self.is_saving:
            return
            
        try:
            # Get the correct answer
            correct_answer = None
            if self.correct_a.isChecked():
                correct_answer = 'A'
            elif self.correct_b.isChecked():
                correct_answer = 'B'
            elif self.correct_c.isChecked():
                correct_answer = 'C'
            elif self.correct_d.isChecked():
                correct_answer = 'D'
            
            # Validate basic requirements with animated feedback
            if not self.question_text.toPlainText().strip():
                self.validation_animator.highlight_invalid_field(
                    self.question_text, 
                    "Question text is required", 
                    self
                )
                return
            
            # Validate answer options with animated feedback
            has_validation_error = False

            # Only validate question text, not answer text
            if not self.question_text.toPlainText().strip():
                self.validation_animator.highlight_invalid_field(
                    self.question_text, 
                    "Question text is required", 
                    self
                )
                return

            # Check that at least one answer option has either text or an image
            if (not any([
                self.answer_a.toPlainText().strip() or self.answer_image_paths['A'],
                self.answer_b.toPlainText().strip() or self.answer_image_paths['B'],
                self.answer_c.toPlainText().strip() or self.answer_image_paths['C'],
                self.answer_d.toPlainText().strip() or self.answer_image_paths['D'],
            ])):
                QMessageBox.warning(self, "Validation Error", "At least one answer option must have text or an image")
                return
            
            if has_validation_error:
                return
            
            if not correct_answer:
                # This shouldn't happen since radio buttons have default selection
                QMessageBox.warning(self, "Validation Error", "Please select the correct answer")
                return
            
            # Set button to loading state
            self.is_saving = True
            save_text = "Saving..." if self.current_question_id is None else "Updating..."
            self.button_original_state = self.progress_animator.create_button_loading_state(
                self.save_button, save_text
            )
            
            # Prepare question data
            question_data = {
                'question_text': self.question_text.toPlainText().strip(),
                'question_image_path': self.question_image_path,
                'answer_a': self.answer_a.toPlainText().strip(),
                'answer_b': self.answer_b.toPlainText().strip(),
                'answer_c': self.answer_c.toPlainText().strip(),
                'answer_d': self.answer_d.toPlainText().strip(),
                'answer_image_a': self.answer_image_paths['A'],
                'answer_image_b': self.answer_image_paths['B'],
                'answer_image_c': self.answer_image_paths['C'],
                'answer_image_d': self.answer_image_paths['D'],
                'correct_answer': correct_answer,
                'answer_explanation': self.explanation.toPlainText().strip(),
                'subject_tags': [tag.strip() for tag in self.subject_tags.text().split(',') if tag.strip()],
                'difficulty_label': self.difficulty.currentText()
            }
            
            # Use a timer to simulate processing time and show the animation
            # In real app this would be actual processing time, but we add 
            # a slight delay to ensure the animation is visible
            QTimer.singleShot(800, lambda: self._perform_save(question_data))
            
        except ValueError as ve:
            self.logger.error(f"Validation error: {str(ve)}")
            
            # Reset button state
            if self.button_original_state:
                self.progress_animator.restore_button_state(self.save_button, self.button_original_state)
                self.button_original_state = None
            self.is_saving = False
            
            QMessageBox.warning(self, "Validation Error", str(ve))
            
        except Exception as e:
            self.logger.error(f"Error saving question: {str(e)}")
            
            # Reset button state
            if self.button_original_state:
                self.progress_animator.restore_button_state(self.save_button, self.button_original_state)
                self.button_original_state = None
            self.is_saving = False
            
            QMessageBox.critical(self, "Error", f"Error saving question: {str(e)}")
    
    def _perform_save(self, question_data):
        """
        Perform the actual save operation after validation and animation.
        
        Args:
            question_data: The question data to save
        """
        try:
            # Save or update question
            if self.current_question_id is None:
                # Create new question
                question_id = self.question_manager.create_question(question_data)
                if question_id:
                    # Show success animation instead of message box
                    if self.parent():
                        self.notification_manager.show_toast(
                            f"Question created successfully (ID: {question_id})",
                            self.parent(),
                            duration=3000,
                            position="bottom"
                        )
                    
                    # Reset form with subtle animation
                    self.question_saved.emit(question_id)
                    
                    # Briefly highlight form before clearing
                    self._animate_save_success()
                    QTimer.singleShot(800, self.clear_form)
                else:
                    QMessageBox.critical(self, "Error", "Failed to create question")
            else:
                # Update existing question
                success = self.question_manager.update_question(self.current_question_id, question_data)
                if success:
                    # Show success animation instead of message box
                    if self.parent():
                        self.notification_manager.show_toast(
                            f"Question updated successfully",
                            self.parent(),
                            duration=3000,
                            position="bottom"
                        )
                    
                    # Reset form with subtle animation
                    self.question_saved.emit(self.current_question_id)
                    
                    # Briefly highlight form before clearing
                    self._animate_save_success()
                    QTimer.singleShot(800, self.clear_form)
                else:
                    QMessageBox.critical(self, "Error", "Failed to update question")
        
        except Exception as e:
            self.logger.error(f"Error in _perform_save: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error saving question: {str(e)}")
        finally:
            # Reset button state
            if self.button_original_state:
                self.progress_animator.restore_button_state(self.save_button, self.button_original_state)
                self.button_original_state = None
            self.is_saving = False
    
    def _animate_save_success(self):
        """Play a subtle success animation on the save button."""
        original_style = self.save_button.styleSheet()
        
        # Set success style
        self.save_button.setStyleSheet(original_style + """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: 1px solid #388E3C;
            }
        """)
        
        # Reset after animation duration
        QTimer.singleShot(800, lambda: self.save_button.setStyleSheet(original_style))
    
    def _select_question_image(self):
        """Open file dialog to select a question image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Question Image", "", "Image Files (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if file_path:
            self.question_image_path = file_path
            self.question_image_label.setText(os.path.basename(file_path))
            self.logger.debug(f"Selected question image: {file_path}")
    
    def _clear_question_image(self):
        """Clear the selected question image."""
        self.question_image_path = None
        self.question_image_label.setText("No image selected")
        self.logger.debug("Cleared question image")
    
    def _select_answer_image(self, option: str):
        """
        Open file dialog to select an answer option image.
        
        Args:
            option: The answer option ('A', 'B', 'C', or 'D')
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Select Image for Answer {option}", "", "Image Files (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if file_path:
            self.answer_image_paths[option] = file_path
            getattr(self, f"answer_{option.lower()}_image_label").setText(os.path.basename(file_path))
            self.logger.debug(f"Selected image for answer {option}: {file_path}")
    
    def _clear_answer_image(self, option: str):
        """
        Clear the selected answer option image.
        
        Args:
            option: The answer option ('A', 'B', 'C', or 'D')
        """
        self.answer_image_paths[option] = None
        getattr(self, f"answer_{option.lower()}_image_label").setText("No image")
        self.logger.debug(f"Cleared image for answer {option}")
