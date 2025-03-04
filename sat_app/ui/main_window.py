"""
Main window for the SAT Question Bank application.
Provides the main application window and navigation between modules.
"""
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget, 
    QLabel, QStatusBar, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

from sat_app.config.config_manager import ConfigManager
from sat_app.dal.database_manager import DatabaseManager
from sat_app.business.manager_factory import ManagerFactory
from sat_app.ui.question_editor import QuestionEditor
from sat_app.ui.question_browser import QuestionBrowser, QuestionDetailDialog
from sat_app.ui.worksheet_view import WorksheetView
from sat_app.ui.analytics_dashboard import AnalyticsDashboard
from sat_app.ui.import_export_view import ImportExportView
from sat_app.ui.settings_view import SettingsView
from sat_app.ui.student_response_view import StudentResponseView
from sat_app.dal.models import Question, Worksheet
from sat_app.rendering.pdf_generator import PDFGenerator


class MainWindow(QMainWindow):
    """
    Main application window.
    
    Manages the overall window layout and navigation between modules.
    Implements a tabbed interface for different application components.
    """
    
    def __init__(self, config: ConfigManager, db_manager: DatabaseManager, manager_factory: ManagerFactory):
        """
        Initialize the main window.
        
        Args:
            config: Application configuration manager
            db_manager: Database manager
            manager_factory: Factory for business layer managers
        """
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.db_manager = db_manager
        self.manager_factory = manager_factory
        
        # Initialize business layer managers
        self.question_manager = manager_factory.get_question_manager()
        self.worksheet_generator = manager_factory.get_worksheet_generator()
        self.scoring_service = manager_factory.get_scoring_service()
        self.import_export_manager = manager_factory.get_import_export_manager()
        self.settings_manager = manager_factory.get_settings_manager()
        
        # Initialize rendering components
        self.pdf_generator = PDFGenerator(config)
        
        # Connect PDF generator to worksheet generator for updating worksheet records
        self.pdf_generator.worksheet_generator = self.worksheet_generator
        
        self.setWindowTitle("SAT Question Bank")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tab widget for different modules
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Initialize UI components
        self._setup_ui()
        
        # Set up status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        self.logger.info("Main window initialized")
    
    def _setup_ui(self):
        """Set up the UI components."""
        # Questions tab
        self._setup_questions_tab()
        
        # Worksheets tab
        self._setup_worksheets_tab()
        
        # Student Responses tab
        self._setup_student_responses_tab()
        
        # Analytics tab
        self._setup_analytics_tab()
        
        # Import/Export tab
        self._setup_import_export_tab()
        
        # Settings tab
        self._setup_settings_tab()
    
    def _setup_questions_tab(self):
        """Set up the Questions tab with browser and editor."""
        questions_tab = QWidget()
        questions_layout = QVBoxLayout(questions_tab)
        
        # Create a splitter to allow resizing
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Question browser
        self.question_browser = QuestionBrowser(self.question_manager)
        self.question_browser.edit_question.connect(self._edit_question)
        self.question_browser.view_question.connect(self._view_question)
        self.question_browser.question_deleted.connect(self._question_deleted)
        splitter.addWidget(self.question_browser)
        
        # Question editor
        self.question_editor = QuestionEditor(self.question_manager)
        self.question_editor.question_saved.connect(self._question_saved)
        splitter.addWidget(self.question_editor)
        
        # Set initial sizes
        splitter.setSizes([600, 600])
        
        questions_layout.addWidget(splitter)
        
        self.tab_widget.addTab(questions_tab, "Questions")
    
    def _add_placeholder_tab(self, title: str, message: str):
        """
        Add a placeholder tab with a message.
        
        Args:
            title: Tab title
            message: Message to display in the tab
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        label = QLabel(f"{message}\n\nThis module is under construction.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        self.tab_widget.addTab(tab, title)
    
    def _edit_question(self, question_id: int):
        """
        Handle request to edit a question.
        
        Args:
            question_id: ID of the question to edit, or -1 for new question
        """
        if question_id > 0:
            self.question_editor.load_question(question_id)
            self.status_bar.showMessage(f"Editing question {question_id}")
        else:
            self.question_editor.clear_form()
            self.status_bar.showMessage("Creating new question")
        
        # Switch to Questions tab and focus the editor
        self.tab_widget.setCurrentIndex(0)
        self.question_editor.setFocus()
    
    def _view_question(self, question_id: int):
        """
        Handle request to view question details.
        
        Args:
            question_id: ID of the question to view
        """
        try:
            question = self.question_manager.get_question(question_id)
            if question:
                dialog = QuestionDetailDialog(question, self)
                dialog.exec()
            else:
                QMessageBox.warning(self, "Error", f"Question with ID {question_id} not found")
        except Exception as e:
            self.logger.error(f"Error viewing question: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error viewing question: {str(e)}")
    
    def _question_saved(self, question_id: int):
        """
        Handle notification that a question was saved.
        
        Args:
            question_id: ID of the saved question
        """
        self.status_bar.showMessage(f"Question {question_id} saved successfully")
        self.question_browser.refresh_questions()
    
    def _question_deleted(self, question_id: int):
        """
        Handle notification that a question was deleted.
        
        Args:
            question_id: ID of the deleted question
        """
        self.status_bar.showMessage(f"Question {question_id} deleted successfully")
    
    def _setup_worksheets_tab(self):
        """Set up the Worksheets tab with the worksheet view."""
        worksheets_tab = QWidget()
        worksheets_layout = QVBoxLayout(worksheets_tab)
        
        # Create the worksheet view
        self.worksheet_view = WorksheetView(self.question_manager, self.worksheet_generator)
        self.worksheet_view.generate_worksheet.connect(self._generate_worksheet_pdf)
        
        worksheets_layout.addWidget(self.worksheet_view)
        
        self.tab_widget.addTab(worksheets_tab, "Worksheets")
    
    def _setup_student_responses_tab(self):
        """Set up the Student Responses tab with the student response view."""
        responses_tab = QWidget()
        responses_layout = QVBoxLayout(responses_tab)
        
        # Create the student response view
        self.student_response_view = StudentResponseView(self.scoring_service)
        self.student_response_view.responses_saved.connect(self._responses_saved)
        
        responses_layout.addWidget(self.student_response_view)
        
        self.tab_widget.addTab(responses_tab, "Student Responses")
        
    def _setup_analytics_tab(self):
        """Set up the Analytics tab with the analytics dashboard."""
        analytics_tab = QWidget()
        analytics_layout = QVBoxLayout(analytics_tab)
        
        # Create the analytics dashboard
        self.analytics_dashboard = AnalyticsDashboard(self.scoring_service)
        analytics_layout.addWidget(self.analytics_dashboard)
        
        self.tab_widget.addTab(analytics_tab, "Analytics")
    
    def _setup_import_export_tab(self):
        """Set up the Import/Export tab with the import/export interface."""
        import_export_tab = QWidget()
        import_export_layout = QVBoxLayout(import_export_tab)
        
        # Create the import/export view
        self.import_export_view = ImportExportView(
            self.import_export_manager,
            self.question_manager
        )
        
        # Connect signals
        self.import_export_view.import_completed.connect(self._import_completed)
        self.import_export_view.export_completed.connect(self._export_completed)
        
        import_export_layout.addWidget(self.import_export_view)
        
        self.tab_widget.addTab(import_export_tab, "Import/Export")
        
        # Populate filter dropdowns with data from database
        self.import_export_view.populate_subject_tags()
        self.import_export_view.populate_difficulty_levels()
    
    def _generate_worksheet_pdf(self, worksheet_data: dict):
        """
        Handle request to generate a worksheet PDF.
        
        Args:
            worksheet_data: Data for generating the worksheet PDF
        """
        try:
            # Generate the PDF using the PDFGenerator
            pdf_path = self.pdf_generator.generate_pdf(worksheet_data)
            
            # Show success message with the path
            self.status_bar.showMessage(f"Worksheet PDF generated: {pdf_path}")
            self.logger.info(f"Generated worksheet PDF with {len(worksheet_data['questions'])} questions: {pdf_path}")
            
            # Show a success message box with the path
            QMessageBox.information(
                self,
                "Worksheet Generated",
                f"Worksheet has been generated successfully.\nSaved to: {pdf_path}"
            )
            
        except Exception as e:
            self.logger.error(f"Error generating worksheet PDF: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error generating worksheet PDF: {str(e)}")
    
    def _import_completed(self, success: bool, message: str, stats: dict):
        """
        Handle import completion notification.
        
        Args:
            success: Whether the import was successful
            message: Message from the import operation
            stats: Statistics about the import
        """
        if success:
            self.status_bar.showMessage(message)
            
            # Refresh question browser to show newly imported questions
            self.question_browser.refresh_questions()
        else:
            self.status_bar.showMessage(f"Import error: {message}")
    
    def _export_completed(self, success: bool, message: str):
        """
        Handle export completion notification.
        
        Args:
            success: Whether the export was successful
            message: Message from the export operation
        """
        if success:
            self.status_bar.showMessage(message)
        else:
            self.status_bar.showMessage(f"Export error: {message}")
            
    def _setup_settings_tab(self):
        """Set up the Settings tab with the settings view."""
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        
        # Create the settings view
        self.settings_view = SettingsView(self.settings_manager)
        
        # Connect signals
        self.settings_view.settings_updated.connect(self._settings_updated)
        
        settings_layout.addWidget(self.settings_view)
        
        self.tab_widget.addTab(settings_tab, "Settings")
    
    def _responses_saved(self, student_id: str, worksheet_id: int):
        """
        Handle notification that student responses were saved.
        
        Args:
            student_id: ID of the student
            worksheet_id: ID of the worksheet
        """
        self.status_bar.showMessage(f"Responses saved for student {student_id} on worksheet {worksheet_id}")
        
        # If analytics dashboard is initialized, refresh it
        if hasattr(self, 'analytics_dashboard'):
            self.analytics_dashboard.refresh_data()
    
    def _settings_updated(self):
        """
        Handle notification that settings were updated.
        
        Updates UI components and status based on new settings.
        """
        self.status_bar.showMessage("Settings updated successfully")
        
        # Get current UI settings
        ui_settings = self.settings_manager.get_ui_settings()
        
        # TODO: Apply theme and font size changes to the UI when implemented
        # This would involve updating the application style sheet based on themes
        # and updating font sizes for components
    
    def closeEvent(self, event):
        """
        Handle window close event.
        
        Closes database connection and performs cleanup.
        
        Args:
            event: Close event
        """
        try:
            # Close database connection
            if self.db_manager:
                self.db_manager.close()
            
            self.logger.info("Application closed")
            event.accept()
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}")
            event.accept()  # Accept anyway to allow closing