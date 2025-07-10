"""
Main window for the SAT Question Bank application.
Provides the main application window and navigation between modules.
"""
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QHBoxLayout, QWidget, 
    QLabel, QStatusBar, QMessageBox, QSplitter, QCheckBox, QPushButton,
    QLineEdit, QTextEdit, QGroupBox, QFormLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, QSettings, QPoint, QRect, QTimer
from PyQt6.QtGui import QIcon, QScreen, QColor, QKeySequence, QShortcut

from ..ui.animations import NotificationManager, AnimationSpeed

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
from sat_app.ui.theme_manager import ThemeManager
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
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        
        self.setWindowTitle("SAT Question Bank")
        
        # Apply the window size/position based on settings or use default
        self._apply_window_geometry()
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Set the size policy to allow the window to resize with the screen
        size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.central_widget.setSizePolicy(size_policy)
        
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
        
        # Initialize notification manager with status bar
        self.notification_manager = NotificationManager(self.status_bar)
        
        # Set up keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
        # Apply initial theme based on settings
        self._apply_current_theme()
        
        self.logger.info("Main window initialized")
    
    def _setup_ui(self):
        """Set up the UI components."""
        # Questions tab with integrated worksheet functionality
        self._setup_questions_tab()
        
        # Student Responses tab
        self._setup_student_responses_tab()
        
        # Analytics tab
        self._setup_analytics_tab()
        
        # Import/Export tab
        self._setup_import_export_tab()
        
        # Settings tab
        self._setup_settings_tab()
    
    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for the application."""
        # Ctrl+N: Add new question
        new_question_shortcut = QShortcut(QKeySequence.StandardKey.New, self)
        new_question_shortcut.activated.connect(self._new_question_shortcut)
        
        # Alternative Ctrl+N shortcut (explicit)
        new_question_alt_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_question_alt_shortcut.activated.connect(self._new_question_shortcut)
        
        self.logger.info("Keyboard shortcuts initialized")
    
    def _new_question_shortcut(self):
        """Handle Ctrl+N shortcut for creating a new question."""
        self._edit_question(-1)
        self.logger.debug("New question created via keyboard shortcut")
    
    def _setup_questions_tab(self):
        """Set up the Questions tab with browser, editor, and integrated worksheet functionality."""
        questions_tab = QWidget()
        questions_layout = QVBoxLayout(questions_tab)
        
        # Main splitter - Left side for questions, right side for editor/worksheet
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel for question browser
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar for worksheet actions
        worksheet_toolbar = QHBoxLayout()
        
        # Worksheet mode toggle
        self.worksheet_mode_toggle = QCheckBox("Worksheet Mode")
        self.worksheet_mode_toggle.toggled.connect(self._toggle_worksheet_mode)
        worksheet_toolbar.addWidget(self.worksheet_mode_toggle)
        
        # Selected questions counter
        self.worksheet_selected_count = QLabel("Selected: 0")
        self.worksheet_selected_count.setVisible(False)
        worksheet_toolbar.addWidget(self.worksheet_selected_count)
        
        worksheet_toolbar.addStretch(1)
        
        # Generate worksheet button
        self.generate_worksheet_btn = QPushButton("Generate Worksheet")
        self.generate_worksheet_btn.clicked.connect(self._generate_worksheet_from_selection)
        self.generate_worksheet_btn.setVisible(False)
        self.generate_worksheet_btn.setEnabled(False)
        worksheet_toolbar.addWidget(self.generate_worksheet_btn)
        
        left_layout.addLayout(worksheet_toolbar)
        
        # Question browser
        self.question_browser = QuestionBrowser(self.question_manager)
        self.question_browser.edit_question.connect(self._edit_question)
        self.question_browser.view_question.connect(self._view_question)
        self.question_browser.question_deleted.connect(self._question_deleted)
        self.question_browser.worksheet_selection_changed.connect(self._update_worksheet_selection)
        left_layout.addWidget(self.question_browser, 1)
        
        # Right panel with stacked layout for editor and worksheet settings
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Question editor
        self.question_editor = QuestionEditor(self.question_manager)
        self.question_editor.question_saved.connect(self._question_saved)
        self.right_layout.addWidget(self.question_editor)
        
        # Worksheet settings panel (initially hidden)
        self.worksheet_settings = QWidget()
        worksheet_settings_layout = QVBoxLayout(self.worksheet_settings)
        
        # Settings group
        settings_group = QGroupBox("Worksheet Settings")
        settings_form = QFormLayout()
        
        # Title
        self.worksheet_title = QLineEdit()
        settings_form.addRow("Title:", self.worksheet_title)
        
        # Description
        self.worksheet_description = QTextEdit()
        self.worksheet_description.setMaximumHeight(80)
        settings_form.addRow("Description:", self.worksheet_description)
        
        # Randomization options
        self.randomize_questions = QCheckBox("Randomize Question Order")
        self.randomize_questions.setChecked(True)
        settings_form.addRow("", self.randomize_questions)
        
        self.randomize_answers = QCheckBox("Randomize Answer Choices")
        self.randomize_answers.setChecked(True)
        settings_form.addRow("", self.randomize_answers)
        
        # Generate answer key
        self.include_answer_key = QCheckBox("Include Answer Key")
        self.include_answer_key.setChecked(True)
        settings_form.addRow("", self.include_answer_key)
        
        settings_group.setLayout(settings_form)
        worksheet_settings_layout.addWidget(settings_group)
        
        # Generate PDF button
        self.generate_pdf_btn = QPushButton("Generate Worksheet PDF")
        self.generate_pdf_btn.clicked.connect(self._generate_worksheet_pdf_from_settings)
        worksheet_settings_layout.addWidget(self.generate_pdf_btn)
        
        # Return to question editing button
        back_btn = QPushButton("← Return to Question Editing")
        back_btn.clicked.connect(self._return_to_question_editing)
        worksheet_settings_layout.addWidget(back_btn)
        
        # Spacer to push everything to the top
        worksheet_settings_layout.addStretch(1)
        
        # Hide the worksheet settings initially
        self.worksheet_settings.hide()
        self.right_layout.addWidget(self.worksheet_settings)
        
        # Add panels to main splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(self.right_panel)
        
        # Set minimum sizes to prevent components from disappearing
        left_panel.setMinimumWidth(300)
        self.right_panel.setMinimumWidth(400)
        
        # Set initial sizes for a balanced layout (40% left, 60% right)
        main_splitter.setSizes([400, 600])
        
        questions_layout.addWidget(main_splitter)
        
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
        # Use animated status message
        self.notification_manager.pulse_status_message(
            f"Question {question_id} saved successfully",
            pulse_count=2,
            pulse_duration=250
        )
        
        # Show a toast notification
        self.notification_manager.show_toast(
            f"Question {question_id} saved successfully", 
            self,
            duration=3000,
            position="bottom"
        )
        
        # Refresh the question list
        self.question_browser.refresh_questions()
    
    def _question_deleted(self, question_id: int):
        """
        Handle notification that a question was deleted.
        
        Args:
            question_id: ID of the deleted question
        """
        # Use animated status message
        self.notification_manager.pulse_status_message(
            f"Question {question_id} deleted successfully",
            pulse_count=2,
            pulse_duration=250
        )
        
        # Show a toast notification with different styling for deletion
        self.notification_manager.show_toast(
            f"Question {question_id} deleted", 
            self,
            duration=3000,
            position="bottom"
        )
    
    def _toggle_worksheet_mode(self, enabled: bool):
        """
        Toggle worksheet selection mode in the question browser.
        
        Args:
            enabled: Whether worksheet mode is enabled
        """
        # Update UI elements
        self.worksheet_selected_count.setVisible(enabled)
        self.generate_worksheet_btn.setVisible(enabled)
        
        # Enable worksheet selection in question browser
        self.question_browser.set_worksheet_selection_mode(enabled)
        
        # If disabling and there are selections, confirm with user
        if not enabled and self.question_browser.get_selected_for_worksheet():
            response = QMessageBox.question(
                self, 
                "Clear Selections?", 
                "Do you want to clear your worksheet selections?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if response == QMessageBox.StandardButton.Yes:
                self.question_browser.clear_worksheet_selections()
            
        # If switching to worksheet mode, make sure we're in question editing mode
        if enabled:
            self._return_to_question_editing()
    
    def _update_worksheet_selection(self):
        """Update the worksheet selection count display."""
        count = len(self.question_browser.get_selected_for_worksheet())
        self.worksheet_selected_count.setText(f"Selected: {count}")
        
        # Enable/disable the generate button
        self.generate_worksheet_btn.setEnabled(count > 0)
    
    def _generate_worksheet_from_selection(self):
        """
        Show worksheet settings for the selected questions.
        """
        selected_questions = self.question_browser.get_selected_for_worksheet()
        if not selected_questions:
            QMessageBox.warning(
                self, 
                "No Questions Selected", 
                "Please select at least one question for the worksheet."
            )
            return
        
        # Hide the question editor and show the worksheet settings
        self.question_editor.hide()
        self.worksheet_settings.show()
        
        # Update the settings with any default values
        self.worksheet_title.setText(f"Worksheet - {len(selected_questions)} Questions")
        
        # Clear description if it's default text
        if not self.worksheet_description.toPlainText() or self.worksheet_description.toPlainText().startswith("Worksheet with "):
            self.worksheet_description.setText(f"Worksheet with {len(selected_questions)} questions")
        
        self.logger.debug(f"Showing worksheet settings for {len(selected_questions)} questions")
    
    def _return_to_question_editing(self):
        """Return to normal question editing mode."""
        self.worksheet_settings.hide()
        self.question_editor.show()
    
    def _generate_worksheet_pdf_from_settings(self):
        """Generate worksheet PDF from the current settings."""
        selected_questions = self.question_browser.get_selected_for_worksheet()
        if not selected_questions:
            QMessageBox.warning(self, "Error", "No questions selected for worksheet")
            return
        
        try:
            # Get worksheet settings
            title = self.worksheet_title.text() or "Untitled Worksheet"
            description = self.worksheet_description.toPlainText()
            randomize_questions = self.randomize_questions.isChecked()
            randomize_answers = self.randomize_answers.isChecked()
            include_answer_key = self.include_answer_key.isChecked()
            
            # Use the worksheet generator to create the worksheet
            worksheet_data = self.worksheet_generator.generate_from_questions(
                title=title,
                description=description,
                questions=selected_questions,
                randomize_questions=randomize_questions,
                randomize_answers=randomize_answers
            )
            
            # Prepare the data for PDF generation
            pdf_data = self.worksheet_generator.prepare_for_pdf(
                worksheet_data,
                include_answer_key=include_answer_key
            )
            
            # Generate the PDF
            self._generate_worksheet_pdf(pdf_data)
            
        except Exception as e:
            self.logger.error(f"Error generating worksheet: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error generating worksheet: {str(e)}")
    
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
    
    def _apply_window_geometry(self):
        """
        Apply the appropriate window geometry based on settings and screen size.
        If remember_window_size is enabled and there are saved geometry settings, use those.
        Otherwise, calculate default size based on the current screen.
        """
        # Get UI settings
        ui_settings = self.settings_manager.get_ui_settings()
        remember_window_size = ui_settings.get("remember_window_size", False)
        
        # Create QSettings for storing window state
        settings = QSettings("SATApp", "QuestionBank")
        
        if remember_window_size:
            # Try to restore saved geometry if it exists
            geometry = settings.value("mainWindowGeometry")
            state = settings.value("mainWindowState")
            
            if geometry is not None:
                self.restoreGeometry(geometry)
                if state is not None:
                    self.restoreState(state)
                self.logger.info("Restored saved window geometry and state")
                return
        
        # No saved geometry or not using saved settings - calculate based on screen
        screen = self.screen()
        screen_geometry = screen.availableGeometry()
        
        # Set window size to 80% of available screen space
        width = int(screen_geometry.width() * 0.8)
        height = int(screen_geometry.height() * 0.8)
        
        # Center the window
        x = (screen_geometry.width() - width) // 2
        y = (screen_geometry.height() - height) // 2
        
        # Apply the calculated geometry
        self.setGeometry(x, y, width, height)
        self.logger.info(f"Set window size to {width}x{height} based on screen resolution")
        
    def _apply_current_theme(self):
        """
        Apply the current theme from settings to the application.
        """
        # Get UI settings
        ui_settings = self.settings_manager.get_ui_settings()
        theme_name = ui_settings.get("theme", "light")
        font_size = ui_settings.get("font_size", 12)
        
        # Apply the theme
        success = self.theme_manager.apply_theme(theme_name, font_size)
        if success:
            self.logger.info(f"Applied {theme_name} theme with font size {font_size}")
        else:
            self.logger.error(f"Failed to apply {theme_name} theme")
            # Fallback to light theme if theme application fails
            self.theme_manager.apply_theme("light", 12)
    
    def _settings_updated(self):
        """
        Handle notification that settings were updated.
        
        Updates UI components and status based on new settings.
        """
        self.status_bar.showMessage("Settings updated successfully")
        
        # Get current UI settings
        ui_settings = self.settings_manager.get_ui_settings()
        
        # Apply theme and font size changes
        self._apply_current_theme()
        
        # Apply window geometry changes if remember_window_size setting changed
        remember_window_size = ui_settings.get("remember_window_size", False)
        settings = QSettings("SATApp", "QuestionBank")
        
        # If remember_window_size was disabled, clear saved geometry
        if not remember_window_size:
            settings.remove("mainWindowGeometry")
            settings.remove("mainWindowState")
            self.logger.info("Cleared saved window geometry")
    
    def closeEvent(self, event):
        """
        Handle window close event.
        
        Saves window geometry if enabled, closes database connection and performs cleanup.
        
        Args:
            event: Close event
        """
        try:
            # Save window geometry if enabled
            ui_settings = self.settings_manager.get_ui_settings()
            remember_window_size = ui_settings.get("remember_window_size", False)
            
            if remember_window_size:
                settings = QSettings("SATApp", "QuestionBank")
                settings.setValue("mainWindowGeometry", self.saveGeometry())
                settings.setValue("mainWindowState", self.saveState())
                self.logger.info("Saved window geometry and state")
            
            # Close database connection
            if self.db_manager:
                self.db_manager.close()
            
            self.logger.info("Application closed")
            event.accept()
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}")
            event.accept()  # Accept anyway to allow closing