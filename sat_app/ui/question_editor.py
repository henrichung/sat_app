"""
Question editor module for the SAT Question Bank application.
Provides forms for adding and editing questions.
"""
import os
import re
import tempfile
from typing import Optional, Dict, Any, Callable, Tuple, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QComboBox,
    QPushButton, QFileDialog, QGridLayout, QMessageBox, QGroupBox, QRadioButton,
    QButtonGroup, QFormLayout, QScrollArea, QToolButton, QDialog, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QByteArray, QTimer
from PyQt5.QtGui import QPixmap, QIcon, QImage, QTextCursor

from ..business.question_manager import QuestionManager
from ..dal.models import Question
from ..utils.logger import get_logger
from ..rendering.pdf_generator import LatexEquationRenderer


class LatexPreviewWidget(QWidget):
    """
    Widget for previewing LaTeX equations.
    
    Provides a live preview of LaTeX equations entered in a text editor.
    """
    
    def __init__(self, parent=None):
        """Initialize the LaTeX preview widget."""
        super().__init__(parent)
        
        self.logger = get_logger(__name__)
        self.latex_renderer = LatexEquationRenderer()
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add preview label - reduced height and padding for more proportion
        self.preview_label = QLabel("LaTeX Preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet(
            "background-color: white; border: 1px solid #ccc; padding: 6px;"
        )
        # Reduced minimum height to better match text size
        self.preview_label.setMinimumHeight(40) 
        # Constrain maximum height to prevent oversized previews
        self.preview_label.setMaximumHeight(60)
        layout.addWidget(self.preview_label)
        
        # Add help button and text
        help_layout = QHBoxLayout()
        help_text = QLabel("Use $...$ for inline math. Example: $\\frac{x}{y}$ or $\\sqrt{x^2 + y^2}$")
        help_text.setStyleSheet("font-style: italic; color: #666; font-size: 9pt;")
        help_layout.addWidget(help_text)
        help_layout.addStretch()
        
        # Add refresh button
        self.refresh_button = QPushButton("Refresh Preview")
        self.refresh_button.clicked.connect(self.update_preview)
        self.refresh_button.setMaximumWidth(120) # Constrain button width
        help_layout.addWidget(self.refresh_button)
        
        layout.addLayout(help_layout)
        
        # Set up a timer for delayed preview updates
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_preview)
        
        # Current equation being previewed
        self.current_equation = ""
        
    def set_text_editor(self, editor: QTextEdit):
        """
        Connect to a text editor to enable live preview.
        
        Args:
            editor: The QTextEdit widget to connect to
        """
        self.text_editor = editor
        self.text_editor.textChanged.connect(self.schedule_update)
        
    def schedule_update(self):
        """Schedule a preview update with delay to avoid excessive rendering."""
        self.update_timer.start(500)  # 500ms delay
        
    def update_preview(self):
        """Update the LaTeX preview based on the current text."""
        try:
            # Extract the current equation under the cursor or the first one found
            cursor = self.text_editor.textCursor()
            position = cursor.position()
            text = self.text_editor.toPlainText()
            
            # Try to find the equation at or near the cursor position
            equation = self._extract_equation_at_position(text, position)
            
            if not equation or equation == self.current_equation:
                return
                
            self.current_equation = equation
            
            # Render the equation
            preview_data = self.latex_renderer.render_for_preview(equation)
            
            if preview_data:
                pixmap = QPixmap()
                pixmap.loadFromData(QByteArray(preview_data))
                if not pixmap.isNull():
                    # Scale the pixmap to a more appropriate size for UI display
                    # This ensures the preview is proportional to surrounding UI elements
                    scaled_pixmap = pixmap.scaled(
                        pixmap.width() * 0.8,  # Scale to 80% of original width
                        pixmap.height() * 0.8,  # Scale to 80% of original height
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.preview_label.setPixmap(scaled_pixmap)
                    self.preview_label.setAlignment(Qt.AlignCenter)
                    return
            
            # If we get here, something failed
            self.preview_label.setText(f"Preview: ${equation}$")
            
        except Exception as e:
            self.logger.error(f"Error updating LaTeX preview: {str(e)}")
            self.preview_label.setText("Error rendering LaTeX")
    
    def _extract_equation_at_position(self, text: str, position: int) -> Optional[str]:
        """
        Extract the LaTeX equation at or near the given position in the text.
        
        Args:
            text: The text containing LaTeX equations
            position: The cursor position
            
        Returns:
            The equation string, or None if no equation is found
        """
        # Find all equations in the text
        pattern = r'\$(.*?)\$'
        equations = [(match.start(), match.end(), match.group(1)) 
                     for match in re.finditer(pattern, text)]
        
        if not equations:
            return None
            
        # First, check if cursor is inside an equation
        for start, end, equation in equations:
            if start <= position <= end:
                return equation
                
        # If not, find the closest equation
        distances = [(abs(position - (start + end) // 2), equation) 
                     for start, end, equation in equations]
        distances.sort(key=lambda x: x[0])  # Sort by distance
        
        return distances[0][1] if distances else None


class LatexEquationDialog(QDialog):
    """
    Dialog for inserting and editing LaTeX equations.
    """
    
    def __init__(self, parent=None, initial_equation: str = ""):
        """
        Initialize the LaTeX equation dialog.
        
        Args:
            parent: The parent widget
            initial_equation: Initial equation to edit
        """
        super().__init__(parent)
        self.setWindowTitle("LaTeX Equation Editor")
        self.setMinimumSize(600, 400)
        
        # Create layout
        main_layout = QVBoxLayout(self)
        
        # Create splitter for editor and preview
        splitter = QSplitter(Qt.Vertical)
        
        # Add equation editor
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.addWidget(QLabel("Enter LaTeX Equation:"))
        
        self.equation_editor = QTextEdit()
        self.equation_editor.setPlainText(initial_equation)
        editor_layout.addWidget(self.equation_editor)
        
        # Add common equation buttons
        button_layout = QHBoxLayout()
        
        self._add_latex_button(button_layout, "Fraction", "\\frac{x}{y}")
        self._add_latex_button(button_layout, "Square Root", "\\sqrt{x}")
        self._add_latex_button(button_layout, "Exponent", "x^{n}")
        self._add_latex_button(button_layout, "Subscript", "x_{i}")
        self._add_latex_button(button_layout, "Sum", "\\sum_{i=1}^{n} x_i")
        self._add_latex_button(button_layout, "Integral", "\\int_{a}^{b} f(x) dx")
        
        editor_layout.addLayout(button_layout)
        
        # Create and connect preview widget
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.addWidget(QLabel("Preview:"))
        
        self.preview = LatexPreviewWidget()
        self.preview.set_text_editor(self.equation_editor)
        preview_layout.addWidget(self.preview)
        
        # Add widgets to splitter
        splitter.addWidget(editor_widget)
        splitter.addWidget(preview_widget)
        
        main_layout.addWidget(splitter)
        
        # Add dialog buttons
        button_box = QHBoxLayout()
        button_box.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_box.addWidget(self.cancel_button)
        
        self.ok_button = QPushButton("Insert Equation")
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.accept)
        button_box.addWidget(self.ok_button)
        
        main_layout.addLayout(button_box)
        
        # Initial preview
        self.preview.update_preview()
        
    def _add_latex_button(self, layout, label: str, latex: str):
        """Add a button for inserting a LaTeX template."""
        button = QPushButton(label)
        button.clicked.connect(lambda: self._insert_latex(latex))
        layout.addWidget(button)
        
    def _insert_latex(self, latex: str):
        """Insert LaTeX template at cursor position."""
        cursor = self.equation_editor.textCursor()
        cursor.insertText(latex)
        self.equation_editor.setFocus()
        
    def get_equation(self) -> str:
        """Get the entered equation."""
        return self.equation_editor.toPlainText().strip()


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
        
        # Create LaTeX renderer for equations
        self.latex_renderer = LatexEquationRenderer()
        
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
        
        # Add LaTeX toolbar
        latex_toolbar = QHBoxLayout()
        
        self.latex_equation_button = QPushButton("Insert Equation")
        self.latex_equation_button.clicked.connect(lambda: self._open_latex_dialog(self.question_text))
        latex_toolbar.addWidget(self.latex_equation_button)
        
        # Add LaTeX preview
        self.latex_preview = LatexPreviewWidget()
        self.latex_preview.set_text_editor(self.question_text)
        question_text_layout.addWidget(self.latex_preview)
        
        question_text_layout.addLayout(latex_toolbar)
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
        
        # Add LaTeX button for answer A
        self.latex_a_button = QPushButton("LaTeX")
        self.latex_a_button.setMaximumWidth(60)
        self.latex_a_button.clicked.connect(lambda: self._open_latex_dialog(self.answer_a))
        answer_a_layout.addWidget(self.latex_a_button, alignment=Qt.AlignRight)
        
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
        
        # Add LaTeX button for answer B
        self.latex_b_button = QPushButton("LaTeX")
        self.latex_b_button.setMaximumWidth(60)
        self.latex_b_button.clicked.connect(lambda: self._open_latex_dialog(self.answer_b))
        answer_b_layout.addWidget(self.latex_b_button, alignment=Qt.AlignRight)
        
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
        
        # Add LaTeX button for answer C
        self.latex_c_button = QPushButton("LaTeX")
        self.latex_c_button.setMaximumWidth(60)
        self.latex_c_button.clicked.connect(lambda: self._open_latex_dialog(self.answer_c))
        answer_c_layout.addWidget(self.latex_c_button, alignment=Qt.AlignRight)
        
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
        
        # Add LaTeX button for answer D
        self.latex_d_button = QPushButton("LaTeX")
        self.latex_d_button.setMaximumWidth(60)
        self.latex_d_button.clicked.connect(lambda: self._open_latex_dialog(self.answer_d))
        answer_d_layout.addWidget(self.latex_d_button, alignment=Qt.AlignRight)
        
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
        
        # Add LaTeX support for explanation
        explanation_latex_layout = QHBoxLayout()
        explanation_latex_layout.addStretch()
        
        self.explanation_latex_button = QPushButton("Insert LaTeX Equation")
        self.explanation_latex_button.clicked.connect(lambda: self._open_latex_dialog(self.explanation))
        explanation_latex_layout.addWidget(self.explanation_latex_button)
        
        # Add LaTeX preview for explanations
        explanation_preview_layout = QVBoxLayout()
        self.explanation_preview = LatexPreviewWidget()
        self.explanation_preview.set_text_editor(self.explanation)
        explanation_preview_layout.addWidget(self.explanation_preview)
        
        explanation_layout.addLayout(explanation_latex_layout)
        explanation_layout.addLayout(explanation_preview_layout)
        
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
        """Save or update the current question."""
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
            
            # Validate basic requirements
            if not self.question_text.toPlainText().strip():
                QMessageBox.warning(self, "Validation Error", "Question text is required")
                return
            
            if not self.answer_a.toPlainText().strip() or not self.answer_b.toPlainText().strip() \
               or not self.answer_c.toPlainText().strip() or not self.answer_d.toPlainText().strip():
                QMessageBox.warning(self, "Validation Error", "All answer options are required")
                return
            
            if not correct_answer:
                QMessageBox.warning(self, "Validation Error", "Please select the correct answer")
                return
            
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
            
            # Save or update question
            if self.current_question_id is None:
                # Create new question
                question_id = self.question_manager.create_question(question_data)
                if question_id:
                    QMessageBox.information(self, "Success", f"Question created with ID: {question_id}")
                    self.question_saved.emit(question_id)
                    self.clear_form()
                else:
                    QMessageBox.critical(self, "Error", "Failed to create question")
            else:
                # Update existing question
                success = self.question_manager.update_question(self.current_question_id, question_data)
                if success:
                    QMessageBox.information(self, "Success", f"Question updated successfully")
                    self.question_saved.emit(self.current_question_id)
                    self.clear_form()
                else:
                    QMessageBox.critical(self, "Error", "Failed to update question")
        
        except ValueError as ve:
            self.logger.error(f"Validation error: {str(ve)}")
            QMessageBox.warning(self, "Validation Error", str(ve))
        except Exception as e:
            self.logger.error(f"Error saving question: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error saving question: {str(e)}")
    
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
        
    def _open_latex_dialog(self, text_editor: QTextEdit):
        """
        Open the LaTeX equation editor dialog.
        
        Args:
            text_editor: The text editor to insert the equation into
        """
        # Get the current selection or equation at cursor position
        cursor = text_editor.textCursor()
        current_equation = ""
        
        if cursor.hasSelection():
            # Check if the selection is a LaTeX equation
            selection = cursor.selectedText()
            if selection.startswith("$") and selection.endswith("$"):
                current_equation = selection[1:-1]  # Remove the $ signs
            else:
                current_equation = selection
        else:
            # Try to find an equation at the cursor position
            text = text_editor.toPlainText()
            position = cursor.position()
            
            # Use a regex to find equations in the text
            pattern = r'\$(.*?)\$'
            for match in re.finditer(pattern, text):
                start, end = match.span()
                if start <= position <= end:
                    current_equation = match.group(1)
                    # Select the equation in the text editor
                    cursor.setPosition(start)
                    cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
                    text_editor.setTextCursor(cursor)
                    break
        
        # Open the LaTeX equation dialog
        dialog = LatexEquationDialog(self, current_equation)
        if dialog.exec():
            equation = dialog.get_equation()
            if equation:
                # Insert the equation with $ delimiters
                cursor = text_editor.textCursor()
                cursor.removeSelectedText()
                cursor.insertText(f"${equation}$")
                text_editor.setFocus()