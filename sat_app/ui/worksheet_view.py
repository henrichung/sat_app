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


class WorksheetView(QWidget):
    """
    Worksheet view widget.
    
    Allows users to select questions for a worksheet, configure worksheet settings,
    and preview the worksheet before generating a PDF.
    """
    
    # Signal emitted when a worksheet is ready to be generated
    generate_worksheet = pyqtSignal(dict)
    
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
        
        # Create main layout with splitter
        main_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel: Question selection
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Question selection group
        selection_group = QGroupBox("Question Selection")
        selection_layout = QVBoxLayout()
        
        # Selection methods tabs (manual, filter, etc.)
        self.selection_tabs = QGroupBox("Selection Method")
        selection_tabs_layout = QVBoxLayout()
        
        # Manual selection
        self.manual_selection_radio = QCheckBox("Manual Selection")
        self.manual_selection_radio.setChecked(True)
        self.manual_selection_radio.toggled.connect(self._update_selection_method)
        selection_tabs_layout.addWidget(self.manual_selection_radio)
        
        # Filter-based selection
        self.filter_selection_radio = QCheckBox("Filter-Based Selection")
        self.filter_selection_radio.toggled.connect(self._update_selection_method)
        selection_tabs_layout.addWidget(self.filter_selection_radio)
        
        self.selection_tabs.setLayout(selection_tabs_layout)
        selection_layout.addWidget(self.selection_tabs)
        
        # Filter controls (initially hidden)
        self.filter_controls = QWidget()
        filter_layout = QFormLayout(self.filter_controls)
        
        # Subject tags filter
        self.tags_filter = QLineEdit()
        self.tags_filter.setPlaceholderText("Enter tags (comma-separated)")
        filter_layout.addRow("Subject Tags:", self.tags_filter)
        
        # Difficulty filter
        self.difficulty_filter = QComboBox()
        self.difficulty_filter.addItems(["All", "Easy", "Medium", "Hard", "Very Hard"])
        filter_layout.addRow("Difficulty:", self.difficulty_filter)
        
        # Question count
        self.question_count = QSpinBox()
        self.question_count.setRange(1, 100)
        self.question_count.setValue(10)
        filter_layout.addRow("Number of Questions:", self.question_count)
        
        # Apply filter button
        self.apply_filter_button = QPushButton("Apply Filters")
        self.apply_filter_button.clicked.connect(self._apply_filters)
        filter_layout.addRow("", self.apply_filter_button)
        
        self.filter_controls.setVisible(False)
        selection_layout.addWidget(self.filter_controls)
        
        # Question browser (for manual selection)
        self.question_browser = QTableWidget(0, 5)
        self.question_browser.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.question_browser.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.question_browser.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.question_browser.setHorizontalHeaderLabels(["ID", "Question", "Tags", "Difficulty", "Add"])
        
        # Set column widths
        self.question_browser.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        self.question_browser.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Question
        self.question_browser.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Tags
        self.question_browser.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Difficulty
        self.question_browser.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Add
        
        selection_layout.addWidget(self.question_browser, 1)
        
        # Selected questions group
        selected_group = QGroupBox("Selected Questions")
        selected_layout = QVBoxLayout()
        
        self.selected_table = QTableWidget(0, 4)
        self.selected_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.selected_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.selected_table.setHorizontalHeaderLabels(["ID", "Question", "Tags", "Remove"])
        
        # Set column widths
        self.selected_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        self.selected_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Question
        self.selected_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Tags
        self.selected_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Remove
        
        selected_layout.addWidget(self.selected_table)
        selected_group.setLayout(selected_layout)
        
        selection_layout.addWidget(selected_group)
        selection_group.setLayout(selection_layout)
        left_layout.addWidget(selection_group)
        
        # Right panel: Worksheet settings and preview
        right_panel = QWidget()
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
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 400])  # Initial sizes
        
        # Load questions for manual selection
        self._load_questions()
        
        self.logger.info("Worksheet view initialized")
    
    def _update_selection_method(self, checked):
        """Update the question selection method based on radio button selection."""
        if self.manual_selection_radio.isChecked():
            self.filter_controls.setVisible(False)
            self.question_browser.setVisible(True)
        elif self.filter_selection_radio.isChecked():
            self.filter_controls.setVisible(True)
            self.question_browser.setVisible(False)
    
    def _load_questions(self):
        """Load questions for manual selection."""
        try:
            questions = self.question_manager.get_all_questions()
            
            # Clear existing rows
            self.question_browser.setRowCount(0)
            
            # Add questions
            for row, question in enumerate(questions):
                self.question_browser.insertRow(row)
                
                # ID
                id_item = QTableWidgetItem(str(question.question_id))
                self.question_browser.setItem(row, 0, id_item)
                
                # Question text (truncated if needed)
                question_text = question.question_text
                if len(question_text) > 100:
                    question_text = question_text[:97] + "..."
                text_item = QTableWidgetItem(question_text)
                self.question_browser.setItem(row, 1, text_item)
                
                # Tags
                tags_str = ", ".join(question.subject_tags) if question.subject_tags else ""
                tags_item = QTableWidgetItem(tags_str)
                self.question_browser.setItem(row, 2, tags_item)
                
                # Difficulty
                difficulty_item = QTableWidgetItem(question.difficulty_label)
                self.question_browser.setItem(row, 3, difficulty_item)
                
                # Add button
                add_widget = QWidget()
                add_layout = QHBoxLayout(add_widget)
                add_layout.setContentsMargins(2, 2, 2, 2)
                
                add_button = QPushButton("Add")
                add_button.setProperty("question_id", question.question_id)
                add_button.clicked.connect(lambda checked, q=question: self._add_question_to_selection(q))
                add_layout.addWidget(add_button)
                
                self.question_browser.setCellWidget(row, 4, add_widget)
            
            self.logger.debug(f"Loaded {len(questions)} questions for selection")
            
        except Exception as e:
            self.logger.error(f"Error loading questions: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error loading questions: {str(e)}")
    
    def _apply_filters(self):
        """Apply filters and select questions automatically."""
        try:
            # Build filter criteria
            filters = {}
            
            # Tag filter
            tag_filter = self.tags_filter.text().strip()
            if tag_filter:
                filters['subject_tags'] = tag_filter
            
            # Difficulty filter
            difficulty = self.difficulty_filter.currentText()
            if difficulty != "All":
                filters['difficulty'] = difficulty
            
            # Get number of questions to select
            count = self.question_count.value()
            
            # Use the worksheet generator to get filtered and randomized questions
            try:
                # Get filtered questions from question manager
                questions = self.question_manager.filter_questions(filters)
                
                if not questions:
                    QMessageBox.warning(self, "Warning", 
                                        f"No questions found matching the selected filters.")
                    return
                
                # Randomize selection if we have more questions than requested
                if len(questions) > count:
                    import random
                    selected_questions = random.sample(questions, count)
                else:
                    selected_questions = questions
                
                # Clear existing selection and add new questions
                self.selected_questions.clear()
                for question in selected_questions:
                    self._add_question_to_selection(question)
                
                self.logger.debug(f"Applied filters: selected {len(selected_questions)} questions")
                
            except ValueError as ve:
                self.logger.error(f"Error in filter selection: {str(ve)}")
                QMessageBox.warning(self, "Warning", str(ve))
                
        except Exception as e:
            self.logger.error(f"Error applying filters: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error applying filters: {str(e)}")
    
    def _add_question_to_selection(self, question: Question):
        """
        Add a question to the selected questions list.
        
        Args:
            question: The question to add
        """
        # Check if question is already selected
        for q in self.selected_questions:
            if q.question_id == question.question_id:
                return
        
        # Add to selected questions list
        self.selected_questions.append(question)
        
        # Add to selected table
        row = self.selected_table.rowCount()
        self.selected_table.insertRow(row)
        
        # ID
        id_item = QTableWidgetItem(str(question.question_id))
        self.selected_table.setItem(row, 0, id_item)
        
        # Question text (truncated if needed)
        question_text = question.question_text
        if len(question_text) > 100:
            question_text = question_text[:97] + "..."
        text_item = QTableWidgetItem(question_text)
        self.selected_table.setItem(row, 1, text_item)
        
        # Tags
        tags_str = ", ".join(question.subject_tags) if question.subject_tags else ""
        tags_item = QTableWidgetItem(tags_str)
        self.selected_table.setItem(row, 2, tags_item)
        
        # Remove button
        remove_widget = QWidget()
        remove_layout = QHBoxLayout(remove_widget)
        remove_layout.setContentsMargins(2, 2, 2, 2)
        
        remove_button = QPushButton("Remove")
        remove_button.setProperty("question_id", question.question_id)
        remove_button.clicked.connect(lambda checked, qid=question.question_id: self._remove_question_from_selection(qid))
        remove_layout.addWidget(remove_button)
        
        self.selected_table.setCellWidget(row, 3, remove_widget)
        
        # Update preview and enable generate button if needed
        self._update_preview()
        self.generate_button.setEnabled(len(self.selected_questions) > 0)
        
        self.logger.debug(f"Added question {question.question_id} to selection")
    
    def _remove_question_from_selection(self, question_id: int):
        """
        Remove a question from the selected questions list.
        
        Args:
            question_id: ID of the question to remove
        """
        # Remove from selected questions list
        self.selected_questions = [q for q in self.selected_questions if q.question_id != question_id]
        
        # Remove from selected table
        for row in range(self.selected_table.rowCount()):
            if self.selected_table.item(row, 0).text() == str(question_id):
                self.selected_table.removeRow(row)
                break
        
        # Update preview and disable generate button if needed
        self._update_preview()
        self.generate_button.setEnabled(len(self.selected_questions) > 0)
        
        self.logger.debug(f"Removed question {question_id} from selection")
    
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
            # Create worksheet object
            worksheet = Worksheet(
                title=self.worksheet_title.text() or "Untitled Worksheet",
                description=self.worksheet_description.toPlainText(),
                question_ids=[q.question_id for q in self.selected_questions]
            )
            
            # Generate worksheet with options
            randomize_questions = self.randomize_questions.isChecked()
            randomize_answers = self.randomize_answers.isChecked()
            include_answer_key = self.include_answer_key.isChecked()
            
            # Use the worksheet generator to create the worksheet
            worksheet_data = self.worksheet_generator.generate_worksheet(
                worksheet,
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