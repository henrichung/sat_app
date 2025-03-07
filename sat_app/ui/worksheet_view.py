"""
Worksheet view module for the SAT Question Bank application.
Provides functionality to select questions for worksheets and configure worksheet settings.
"""
import os
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QCheckBox,
    QGroupBox, QFormLayout, QMessageBox, QSplitter, QAbstractItemView,
    QScrollArea, QTextEdit, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap

from ..business.question_manager import QuestionManager
from ..business.worksheet_generator import WorksheetGenerator
from ..dal.models import Question, Worksheet
from ..utils.logger import get_logger
from .question_browser import QuestionBrowser


class WorksheetView(QWidget):
    """
    Worksheet view widget.
    
    Allows users to select questions for a worksheet, configure worksheet settings,
    and preview the worksheet before generating a PDF.
    """
    
    # Signal emitted when a worksheet is ready to be generated
    generate_worksheet = pyqtSignal(dict)
    
    # Signal emitted when the user wants to return to the questions tab
    return_to_questions = pyqtSignal()
    
    def __init__(self, question_manager: QuestionManager, worksheet_generator: WorksheetGenerator, parent=None):
        """
        Initialize the worksheet view.
        
        Args:
            question_manager: The manager for question operations
            worksheet_generator: The generator for worksheet operations
            parent: The parent widget
        """
        super().__init__(parent)
        
        self.logger = get_logger(__name__)
        self.question_manager = question_manager
        self.worksheet_generator = worksheet_generator
        self.selected_questions: List[Question] = []
        self.external_selection_active = False
        
        # Create main layout with splitter
        main_layout = QVBoxLayout(self)
        
        # Header section with navigation
        header_layout = QHBoxLayout()
        
        # Return to questions button
        self.return_button = QPushButton("← Return to Questions")
        self.return_button.clicked.connect(self._return_to_questions)
        header_layout.addWidget(self.return_button)
        
        header_layout.addStretch(1)
        
        # Selected questions count
        self.selected_count_label = QLabel("0 questions selected")
        header_layout.addWidget(self.selected_count_label)
        
        # Go back to question selection
        self.edit_selection_button = QPushButton("Edit Selection")
        self.edit_selection_button.clicked.connect(self._edit_selection)
        self.edit_selection_button.setVisible(False)
        header_layout.addWidget(self.edit_selection_button)
        
        main_layout.addLayout(header_layout)
        
        # Main content
        self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.content_splitter.setChildrenCollapsible(False)  # Prevent children from collapsing completely
        main_layout.addWidget(self.content_splitter, 1)  # Give it stretch
        
        # Right panel: Worksheet settings and preview
        right_panel = QWidget()
        right_panel.setMinimumWidth(350)  # Ensure settings panel is always usable
        right_layout = QVBoxLayout(right_panel)
        
        # Worksheet settings
        settings_group = QGroupBox("Worksheet Settings")
        settings_layout = QFormLayout()
        
        # Title
        self.worksheet_title = QLineEdit()
        settings_layout.addRow("Title:", self.worksheet_title)
        
        # Description
        self.worksheet_description = QTextEdit()
        self.worksheet_description.setMaximumHeight(80)
        settings_layout.addRow("Description:", self.worksheet_description)
        
        # Randomization options
        self.randomize_questions = QCheckBox("Randomize Question Order")
        self.randomize_questions.setChecked(True)
        settings_layout.addRow("", self.randomize_questions)
        
        self.randomize_answers = QCheckBox("Randomize Answer Choices")
        self.randomize_answers.setChecked(True)
        settings_layout.addRow("", self.randomize_answers)
        
        # Generate answer key
        self.include_answer_key = QCheckBox("Include Answer Key")
        self.include_answer_key.setChecked(True)
        settings_layout.addRow("", self.include_answer_key)
        
        settings_group.setLayout(settings_layout)
        right_layout.addWidget(settings_group)
        
        # Preview section
        preview_group = QGroupBox("Worksheet Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        
        self.preview_content = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_content)
        self.preview_label = QLabel("Select questions to preview worksheet")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_layout.addWidget(self.preview_label)
        
        self.preview_scroll.setWidget(self.preview_content)
        preview_layout.addWidget(self.preview_scroll, 1)
        
        preview_group.setLayout(preview_layout)
        right_layout.addWidget(preview_group, 1)
        
        # Generate PDF button
        self.generate_button = QPushButton("Generate Worksheet PDF")
        self.generate_button.clicked.connect(self._generate_worksheet)
        self.generate_button.setEnabled(False)
        right_layout.addWidget(self.generate_button)
        
        # Add the worksheet configuration panel to the splitter
        self.content_splitter.addWidget(right_panel)
        
        # Default to configuration-only view at startup
        self.logger.info("Worksheet view initialized")
        
    def _return_to_questions(self):
        """Signal to return to the questions tab."""
        self.return_to_questions.emit()
        
    def _edit_selection(self):
        """Switch to edit selection mode."""
        if not hasattr(self, 'question_browser'):
            # Create the question browser if it doesn't exist
            left_panel = QWidget()
            left_layout = QVBoxLayout(left_panel)
            
            self.question_browser = QuestionBrowser(
                question_manager=self.question_manager,
                parent=self,
                enable_worksheet_selection=True
            )
            
            # Connect signals
            self.question_browser.questions_selected_for_worksheet.connect(self._update_selected_questions)
            
            left_layout.addWidget(self.question_browser)
            self.content_splitter.insertWidget(0, left_panel)
            
            # Load existing questions
            if self.selected_questions:
                self.question_browser.load_questions_to_worksheet(self.selected_questions)
        
        # Show the question browser
        if self.content_splitter.widget(0).isHidden():
            self.content_splitter.widget(0).show()
            
        # Update sizes
        self.content_splitter.setSizes([400, 400])
        self.edit_selection_button.setVisible(False)
        
    def load_selected_questions(self, questions: List[Question]):
        """
        Load a selection of questions from the main question browser.
        
        Args:
            questions: List of Question objects to use for the worksheet
        """
        self.external_selection_active = True
        self.selected_questions = questions
        
        # Update the count label
        count = len(self.selected_questions)
        self.selected_count_label.setText(f"{count} questions selected")
        
        # Update the preview
        self._update_preview()
        
        # Hide the question browser if it exists
        if hasattr(self, 'question_browser'):
            self.content_splitter.widget(0).hide()
        
        # Enable the edit selection button
        self.edit_selection_button.setVisible(True)
        
        # Enable the generate button
        self.generate_button.setEnabled(count > 0)
        
        self.logger.debug(f"Loaded {count} questions from external selection")
    
    def _update_selected_questions(self, questions: List[Question]):
        """
        Update the selected questions list and preview.
        
        Args:
            questions: List of Question objects selected for the worksheet
        """
        self.selected_questions = questions
        self._update_preview()
        self.generate_button.setEnabled(len(self.selected_questions) > 0)
        
        # Update count label
        count = len(self.selected_questions)
        self.selected_count_label.setText(f"{count} questions selected")
        
        self.logger.debug(f"Updated selected questions: {count} questions selected")
    
    def _update_preview(self):
        """Update the worksheet preview."""
        # Clear existing preview
        for i in reversed(range(self.preview_layout.count())):
            widget = self.preview_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        
        if not self.selected_questions:
            # No questions selected
            self.preview_label = QLabel("Select questions to preview worksheet")
            self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.preview_layout.addWidget(self.preview_label)
            return
        
        try:
            # Create a worksheet object for preview
            worksheet = Worksheet(
                title=self.worksheet_title.text() or "Untitled Worksheet",
                description=self.worksheet_description.toPlainText(),
                question_ids=[q.question_id for q in self.selected_questions]
            )
            
            # Get randomization settings
            randomize_questions = self.randomize_questions.isChecked()
            randomize_answers = self.randomize_answers.isChecked()
            
            # Generate a preview version of the worksheet with current settings
            preview_data = worksheet
            questions_to_preview = self.selected_questions
            
            # If randomization is enabled, use the worksheet generator to create a preview
            if randomize_questions or randomize_answers:
                # Generate worksheet data with randomization
                worksheet_data = self.worksheet_generator.generate_worksheet(
                    worksheet,
                    randomize_questions=randomize_questions,
                    randomize_answers=randomize_answers
                )
                
                # Get the processed questions from the worksheet data
                questions_to_preview = worksheet_data['questions']
                
            # Add worksheet title
            title = worksheet.title
            title_label = QLabel(f"<h1>{title}</h1>")
            self.preview_layout.addWidget(title_label)
            
            # Add description if present
            if worksheet.description:
                desc_label = QLabel(worksheet.description)
                desc_label.setWordWrap(True)
                self.preview_layout.addWidget(desc_label)
            
            # Add horizontal line
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            self.preview_layout.addWidget(line)
            
            # Preview questions
            for i, question in enumerate(questions_to_preview):
                question_widget = QWidget()
                question_layout = QVBoxLayout(question_widget)
                
                # Question number and text
                question_header = QLabel(f"<b>Question {i+1}</b>")
                question_layout.addWidget(question_header)
                
                question_text = QLabel(question.question_text)
                question_text.setWordWrap(True)
                question_layout.addWidget(question_text)
                
                # Question image if available
                if question.question_image_path and os.path.exists(question.question_image_path):
                    image_label = QLabel()
                    pixmap = QPixmap(question.question_image_path)
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(400, 300, Qt.AspectRatioMode.KeepAspectRatio)
                        image_label.setPixmap(pixmap)
                        question_layout.addWidget(image_label)
                
                # Answer choices
                answers_layout = QVBoxLayout()
                
                # Helper function for answer options
                def add_answer_option(option, text, image_path):
                    option_layout = QHBoxLayout()
                    
                    option_label = QLabel(f"<b>{option}.</b>")
                    option_layout.addWidget(option_label)
                    
                    text_label = QLabel(text)
                    text_label.setWordWrap(True)
                    option_layout.addWidget(text_label, 1)
                    
                    option_widget = QWidget()
                    option_widget.setLayout(option_layout)
                    answers_layout.addWidget(option_widget)
                    
                    # Answer image if available
                    if image_path and os.path.exists(image_path):
                        image_label = QLabel()
                        pixmap = QPixmap(image_path)
                        if not pixmap.isNull():
                            pixmap = pixmap.scaled(300, 200, Qt.AspectRatioMode.KeepAspectRatio)
                            image_label.setPixmap(pixmap)
                            indented_layout = QHBoxLayout()
                            indented_layout.addSpacing(20)
                            indented_layout.addWidget(image_label)
                            
                            image_widget = QWidget()
                            image_widget.setLayout(indented_layout)
                            answers_layout.addWidget(image_widget)
                
                # Add each answer choice
                add_answer_option("A", question.answer_a, question.answer_image_a)
                add_answer_option("B", question.answer_b, question.answer_image_b)
                add_answer_option("C", question.answer_c, question.answer_image_c)
                add_answer_option("D", question.answer_d, question.answer_image_d)
                
                answers_widget = QWidget()
                answers_widget.setLayout(answers_layout)
                question_layout.addWidget(answers_widget)
                
                self.preview_layout.addWidget(question_widget)
                
                # Add separator between questions
                if i < len(questions_to_preview) - 1:
                    separator = QFrame()
                    separator.setFrameShape(QFrame.Shape.HLine)
                    separator.setFrameShadow(QFrame.Shadow.Sunken)
                    self.preview_layout.addWidget(separator)
            
            # Add spacer at the end
            self.preview_layout.addStretch()
            
            self.logger.debug("Updated worksheet preview with randomize_questions=" + 
                            f"{randomize_questions}, randomize_answers={randomize_answers}")
                            
        except Exception as e:
            self.logger.error(f"Error updating preview: {str(e)}")
            error_label = QLabel(f"Error updating preview: {str(e)}")
            error_label.setWordWrap(True)
            self.preview_layout.addWidget(error_label)
    
    def _generate_worksheet(self):
        """Generate the worksheet and emit the generate_worksheet signal."""
        if not self.selected_questions:
            QMessageBox.warning(self, "Warning", "No questions selected for worksheet")
            return
        
        try:
            # Get worksheet settings
            title = self.worksheet_title.text() or "Untitled Worksheet"
            description = self.worksheet_description.toPlainText()
            randomize_questions = self.randomize_questions.isChecked()
            randomize_answers = self.randomize_answers.isChecked()
            include_answer_key = self.include_answer_key.isChecked()
            
            # Use the worksheet generator to create the worksheet from the selected questions
            worksheet_data = self.worksheet_generator.generate_from_questions(
                title=title,
                description=description,
                questions=self.selected_questions,
                randomize_questions=randomize_questions,
                randomize_answers=randomize_answers
            )
            
            # Prepare the data for PDF generation
            pdf_data = self.worksheet_generator.prepare_for_pdf(
                worksheet_data,
                include_answer_key=include_answer_key
            )
            
            # Emit signal to generate worksheet PDF
            self.generate_worksheet.emit(pdf_data)
            
            self.logger.info(f"Generated worksheet with {len(self.selected_questions)} questions, "
                            f"randomize_questions={randomize_questions}, "
                            f"randomize_answers={randomize_answers}")
            QMessageBox.information(self, "Success", "Worksheet generated successfully")
            
        except Exception as e:
            self.logger.error(f"Error generating worksheet: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error generating worksheet: {str(e)}")