"""
Analytics dashboard for the SAT Question Bank application.
Displays charts and tables for performance analytics.
"""
import logging
from typing import Dict, List, Any
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QTabWidget, QTableWidget, QTableWidgetItem, QSplitter,
    QPushButton, QLineEdit, QMessageBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QPalette, QFont

from sat_app.business.scorer import ScoringService


class MatplotlibCanvas(FigureCanvas):
    """
    Matplotlib canvas for displaying charts in PyQt6.
    """
    
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        """
        Initialize the canvas.
        
        Args:
            parent: Parent widget
            width: Width in inches
            height: Height in inches
            dpi: Dots per inch
        """
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        
        super(MatplotlibCanvas, self).__init__(self.fig)
        self.setParent(parent)
        
        # Make the figure fill the canvas
        self.fig.tight_layout()
    
    def clear(self):
        """Clear the canvas."""
        self.axes.clear()
        self.draw()


class PerformanceChart(QWidget):
    """
    Widget for displaying performance charts.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the performance chart.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Set up layout
        self.layout = QVBoxLayout(self)
        
        # Create matplotlib canvas
        self.canvas = MatplotlibCanvas(self, width=5, height=4)
        self.layout.addWidget(self.canvas)
    
    def plot_bar_chart(self, data: Dict[str, float], title: str, x_label: str, y_label: str, color: str = 'blue'):
        """
        Plot a bar chart.
        
        Args:
            data: Dictionary mapping categories to values
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            color: Bar color
        """
        # Clear previous plot
        self.canvas.axes.clear()
        
        # Sort data for better visualization
        sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
        categories = [x[0] for x in sorted_items]
        values = [x[1] for x in sorted_items]
        
        # Plot bar chart
        bars = self.canvas.axes.bar(categories, values, color=color)
        
        # Add labels and title
        self.canvas.axes.set_xlabel(x_label)
        self.canvas.axes.set_ylabel(y_label)
        self.canvas.axes.set_title(title)
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            self.canvas.axes.text(
                bar.get_x() + bar.get_width() / 2.,
                height,
                f'{height:.1f}%',
                ha='center', va='bottom', rotation=0, fontsize=9
            )
        
        # Rotate x-axis labels if there are many categories
        if len(categories) > 5:
            self.canvas.axes.set_xticklabels(categories, rotation=45, ha='right')
        
        self.canvas.fig.tight_layout()
        self.canvas.draw()
    
    def plot_line_chart(self, x_data: List[str], y_data: List[float], title: str, x_label: str, y_label: str, color: str = 'blue'):
        """
        Plot a line chart.
        
        Args:
            x_data: X-axis data points
            y_data: Y-axis data points
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            color: Line color
        """
        # Clear previous plot
        self.canvas.axes.clear()
        
        # Plot line chart
        self.canvas.axes.plot(x_data, y_data, marker='o', linestyle='-', color=color)
        
        # Add labels and title
        self.canvas.axes.set_xlabel(x_label)
        self.canvas.axes.set_ylabel(y_label)
        self.canvas.axes.set_title(title)
        
        # Set y-axis range from 0 to 100 for percentages
        if "%" in y_label:
            self.canvas.axes.set_ylim([0, 100])
        
        # Rotate x-axis labels if there are many data points
        if len(x_data) > 5:
            self.canvas.axes.set_xticklabels(x_data, rotation=45, ha='right')
        
        self.canvas.fig.tight_layout()
        self.canvas.draw()
    
    def plot_pie_chart(self, data: Dict[str, float], title: str):
        """
        Plot a pie chart.
        
        Args:
            data: Dictionary mapping categories to values
            title: Chart title
        """
        # Clear previous plot
        self.canvas.axes.clear()
        
        # Sort data for better visualization
        sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
        labels = [x[0] for x in sorted_items]
        values = [x[1] for x in sorted_items]
        
        # Plot pie chart
        self.canvas.axes.pie(
            values, 
            labels=labels,
            autopct='%1.1f%%',
            startangle=90,
            shadow=False
        )
        
        # Equal aspect ratio ensures that pie is drawn as a circle
        self.canvas.axes.axis('equal')
        
        # Add title
        self.canvas.axes.set_title(title)
        
        self.canvas.fig.tight_layout()
        self.canvas.draw()


class StudentSelector(QWidget):
    """
    Widget for selecting a student.
    """
    
    student_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """
        Initialize the student selector.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Set up layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Create student ID input
        self.student_label = QLabel("Student ID:")
        self.layout.addWidget(self.student_label)
        
        self.student_input = QLineEdit()
        self.student_input.setPlaceholderText("Enter student ID")
        self.layout.addWidget(self.student_input)
        
        # Create view button
        self.view_button = QPushButton("View Analytics")
        self.view_button.clicked.connect(self._on_view_button_clicked)
        self.layout.addWidget(self.view_button)
    
    def _on_view_button_clicked(self):
        """Handle view button click."""
        student_id = self.student_input.text().strip()
        if student_id:
            self.student_selected.emit(student_id)
        else:
            QMessageBox.warning(self, "Input Required", "Please enter a student ID")
    
    def get_student_id(self) -> str:
        """
        Get the selected student ID.
        
        Returns:
            The selected student ID
        """
        return self.student_input.text().strip()


class MasteryLevelWidget(QWidget):
    """
    Widget for displaying mastery levels.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the mastery level widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Set up layout
        self.layout = QVBoxLayout(self)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Subject", "Mastery Level", "Percentage", "Attempted", "Correct"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.layout.addWidget(self.table)
    
    def display_mastery_levels(self, mastery_data: Dict[str, Any]):
        """
        Display mastery levels in the table.
        
        Args:
            mastery_data: Dictionary of mastery levels by subject
        """
        self.table.clearContents()
        
        # Get mastery levels
        mastery_levels = mastery_data.get("mastery_levels", {})
        
        # Set table rows
        self.table.setRowCount(len(mastery_levels))
        
        # Fill table
        for row, (subject, data) in enumerate(mastery_levels.items()):
            # Subject
            subject_item = QTableWidgetItem(subject)
            self.table.setItem(row, 0, subject_item)
            
            # Mastery Level
            level_item = QTableWidgetItem(data.get("level", ""))
            level_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, level_item)
            
            # Set background color based on level
            level = data.get("level", "")
            if level == "Expert":
                level_item.setBackground(QColor(0, 200, 0, 100))  # Green
            elif level == "Proficient":
                level_item.setBackground(QColor(100, 200, 100, 100))  # Light green
            elif level == "Competent":
                level_item.setBackground(QColor(200, 200, 0, 100))  # Yellow
            elif level == "Developing":
                level_item.setBackground(QColor(255, 165, 0, 100))  # Orange
            elif level == "Needs Improvement":
                level_item.setBackground(QColor(255, 0, 0, 100))  # Red
            
            # Percentage
            percentage = data.get("percentage", 0)
            percentage_item = QTableWidgetItem(f"{percentage:.1f}%")
            percentage_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, percentage_item)
            
            # Attempted
            attempted = data.get("questions_attempted", 0)
            attempted_item = QTableWidgetItem(str(attempted))
            attempted_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, attempted_item)
            
            # Correct
            correct = data.get("questions_correct", 0)
            correct_item = QTableWidgetItem(str(correct))
            correct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, correct_item)
        
        # Resize columns to content
        self.table.resizeColumnsToContents()


class StudentPerformanceTab(QWidget):
    """
    Tab for displaying student performance analytics.
    """
    
    def __init__(self, scoring_service: ScoringService, parent=None):
        """
        Initialize the student performance tab.
        
        Args:
            scoring_service: Scoring service for analytics
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.scoring_service = scoring_service
        
        # Set up layout
        self.layout = QVBoxLayout(self)
        
        # Create student selector
        self.student_selector = StudentSelector()
        self.student_selector.student_selected.connect(self._load_student_analytics)
        self.layout.addWidget(self.student_selector)
        
        # Create a splitter for the main content
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setChildrenCollapsible(False)  # Prevent children from being collapsed completely
        self.layout.addWidget(self.splitter)
        
        # Create summary box
        self.summary_box = QGroupBox("Performance Summary")
        self.summary_box.setMinimumHeight(120)  # Ensure the summary is always visible
        self.summary_layout = QFormLayout(self.summary_box)
        
        self.total_questions_label = QLabel("0")
        self.total_correct_label = QLabel("0")
        self.percentage_correct_label = QLabel("0%")
        self.worksheets_completed_label = QLabel("0")
        
        self.summary_layout.addRow("Total Questions Attempted:", self.total_questions_label)
        self.summary_layout.addRow("Total Correct Answers:", self.total_correct_label)
        self.summary_layout.addRow("Overall Success Rate:", self.percentage_correct_label)
        self.summary_layout.addRow("Worksheets Completed:", self.worksheets_completed_label)
        
        self.splitter.addWidget(self.summary_box)
        
        # Create tabs for different charts
        self.charts_tabs = QTabWidget()
        self.splitter.addWidget(self.charts_tabs)
        
        # Create subject performance chart
        self.subject_chart_widget = QWidget()
        self.subject_chart_layout = QVBoxLayout(self.subject_chart_widget)
        self.subject_chart = PerformanceChart()
        self.subject_chart_layout.addWidget(self.subject_chart)
        self.charts_tabs.addTab(self.subject_chart_widget, "Performance by Subject")
        
        # Create difficulty performance chart
        self.difficulty_chart_widget = QWidget()
        self.difficulty_chart_layout = QVBoxLayout(self.difficulty_chart_widget)
        self.difficulty_chart = PerformanceChart()
        self.difficulty_chart_layout.addWidget(self.difficulty_chart)
        self.charts_tabs.addTab(self.difficulty_chart_widget, "Performance by Difficulty")
        
        # Create recent performance chart
        self.recent_chart_widget = QWidget()
        self.recent_chart_layout = QVBoxLayout(self.recent_chart_widget)
        self.recent_chart = PerformanceChart()
        self.recent_chart_layout.addWidget(self.recent_chart)
        self.charts_tabs.addTab(self.recent_chart_widget, "Recent Performance")
        
        # Create mastery levels tab
        self.mastery_widget = MasteryLevelWidget()
        self.charts_tabs.addTab(self.mastery_widget, "Mastery Levels")
        
        # Set initial splitter sizes
        self.splitter.setSizes([100, 500])
    
    def _load_student_analytics(self, student_id: str):
        """
        Load analytics for a student.
        
        Args:
            student_id: ID of the student
        """
        # Calculate student performance
        performance = self.scoring_service.calculate_student_performance(student_id)
        
        # Update summary
        self.total_questions_label.setText(str(performance.get("total_questions", 0)))
        self.total_correct_label.setText(str(performance.get("total_correct", 0)))
        self.percentage_correct_label.setText(f"{performance.get('percentage_correct', 0):.1f}%")
        self.worksheets_completed_label.setText(str(performance.get("worksheets_completed", 0)))
        
        # Update subject chart
        subject_performance = performance.get("subject_performance", {})
        subject_percentages = {subject: data.get("percentage", 0) for subject, data in subject_performance.items()}
        if subject_percentages:
            self.subject_chart.plot_bar_chart(
                subject_percentages,
                "Performance by Subject",
                "Subject",
                "Success Rate (%)",
                "blue"
            )
        
        # Update difficulty chart
        difficulty_performance = performance.get("difficulty_performance", {})
        difficulty_percentages = {difficulty: data.get("percentage", 0) for difficulty, data in difficulty_performance.items()}
        if difficulty_percentages:
            self.difficulty_chart.plot_bar_chart(
                difficulty_percentages,
                "Performance by Difficulty Level",
                "Difficulty Level",
                "Success Rate (%)",
                "green"
            )
        
        # Update recent performance chart
        recent_performance = performance.get("recent_performance", [])
        if recent_performance:
            dates = [entry.get("date", "") for entry in recent_performance]
            percentages = [entry.get("percentage", 0) for entry in recent_performance]
            self.recent_chart.plot_line_chart(
                dates,
                percentages,
                "Recent Performance Trend",
                "Date",
                "Success Rate (%)",
                "red"
            )
        
        # Get mastery levels
        mastery_data = self.scoring_service.get_mastery_levels(student_id)
        
        # Display mastery levels
        self.mastery_widget.display_mastery_levels(mastery_data)


class QuestionPerformanceTab(QWidget):
    """
    Tab for displaying question performance analytics.
    """
    
    def __init__(self, scoring_service: ScoringService, parent=None):
        """
        Initialize the question performance tab.
        
        Args:
            scoring_service: Scoring service for analytics
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.scoring_service = scoring_service
        
        # Set up layout
        self.layout = QVBoxLayout(self)
        
        # Create question selector
        selector_layout = QHBoxLayout()
        self.layout.addLayout(selector_layout)
        
        self.question_label = QLabel("Question ID:")
        selector_layout.addWidget(self.question_label)
        
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Enter question ID")
        selector_layout.addWidget(self.question_input)
        
        self.view_button = QPushButton("View Analytics")
        self.view_button.clicked.connect(self._load_question_analytics)
        selector_layout.addWidget(self.view_button)
        
        # Create group box for metrics
        self.metrics_box = QGroupBox("Question Performance Metrics")
        metrics_layout = QFormLayout(self.metrics_box)
        self.layout.addWidget(self.metrics_box)
        
        self.total_attempts_label = QLabel("0")
        self.correct_attempts_label = QLabel("0")
        self.success_rate_label = QLabel("0%")
        self.student_count_label = QLabel("0")
        
        metrics_layout.addRow("Total Attempts:", self.total_attempts_label)
        metrics_layout.addRow("Correct Attempts:", self.correct_attempts_label)
        metrics_layout.addRow("Success Rate:", self.success_rate_label)
        metrics_layout.addRow("Number of Students:", self.student_count_label)
    
    def _load_question_analytics(self):
        """Load analytics for a question."""
        question_id_text = self.question_input.text().strip()
        if not question_id_text.isdigit():
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid question ID (numeric)")
            return
        
        question_id = int(question_id_text)
        performance = self.scoring_service.calculate_question_performance(question_id)
        
        # Update metrics
        self.total_attempts_label.setText(str(performance.get("total_attempts", 0)))
        self.correct_attempts_label.setText(str(performance.get("correct_attempts", 0)))
        self.success_rate_label.setText(f"{performance.get('success_rate', 0):.1f}%")
        self.student_count_label.setText(str(performance.get("student_count", 0)))


class WorksheetPerformanceTab(QWidget):
    """
    Tab for displaying worksheet performance analytics.
    """
    
    def __init__(self, scoring_service: ScoringService, parent=None):
        """
        Initialize the worksheet performance tab.
        
        Args:
            scoring_service: Scoring service for analytics
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.scoring_service = scoring_service
        
        # Set up layout
        self.layout = QVBoxLayout(self)
        
        # Create worksheet selector
        selector_layout = QHBoxLayout()
        self.layout.addLayout(selector_layout)
        
        self.worksheet_label = QLabel("Worksheet ID:")
        selector_layout.addWidget(self.worksheet_label)
        
        self.worksheet_input = QLineEdit()
        self.worksheet_input.setPlaceholderText("Enter worksheet ID")
        selector_layout.addWidget(self.worksheet_input)
        
        self.view_button = QPushButton("View Analytics")
        self.view_button.clicked.connect(self._load_worksheet_analytics)
        selector_layout.addWidget(self.view_button)
        
        # Create group box for summary
        self.summary_box = QGroupBox("Worksheet Performance Summary")
        summary_layout = QFormLayout(self.summary_box)
        self.layout.addWidget(self.summary_box)
        
        self.total_attempts_label = QLabel("0")
        self.average_score_label = QLabel("0%")
        self.student_count_label = QLabel("0")
        
        summary_layout.addRow("Total Attempts:", self.total_attempts_label)
        summary_layout.addRow("Average Score:", self.average_score_label)
        summary_layout.addRow("Number of Students:", self.student_count_label)
        
        # Create table for student performances
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(4)
        self.students_table.setHorizontalHeaderLabels(["Student ID", "Questions", "Correct", "Score"])
        self.students_table.horizontalHeader().setStretchLastSection(True)
        self.layout.addWidget(self.students_table)
    
    def _load_worksheet_analytics(self):
        """Load analytics for a worksheet."""
        worksheet_id_text = self.worksheet_input.text().strip()
        if not worksheet_id_text.isdigit():
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid worksheet ID (numeric)")
            return
        
        worksheet_id = int(worksheet_id_text)
        performance = self.scoring_service.calculate_worksheet_performance(worksheet_id)
        
        # Update summary
        self.total_attempts_label.setText(str(performance.get("total_attempts", 0)))
        self.average_score_label.setText(f"{performance.get('average_score', 0):.1f}%")
        self.student_count_label.setText(str(performance.get("student_count", 0)))
        
        # Update table
        student_performances = performance.get("student_performances", [])
        self.students_table.setRowCount(len(student_performances))
        
        for row, student_perf in enumerate(student_performances):
            # Student ID
            student_id = student_perf.get("student_id", "")
            self.students_table.setItem(row, 0, QTableWidgetItem(student_id))
            
            # Questions
            questions = student_perf.get("total_questions", 0)
            questions_item = QTableWidgetItem(str(questions))
            questions_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.students_table.setItem(row, 1, questions_item)
            
            # Correct
            correct = student_perf.get("correct_answers", 0)
            correct_item = QTableWidgetItem(str(correct))
            correct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.students_table.setItem(row, 2, correct_item)
            
            # Score
            percentage = student_perf.get("percentage", 0)
            score_item = QTableWidgetItem(f"{percentage:.1f}%")
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.students_table.setItem(row, 3, score_item)
        
        # Resize columns to content
        self.students_table.resizeColumnsToContents()


class OverallAnalyticsTab(QWidget):
    """
    Tab for displaying overall analytics across all students.
    """
    
    def __init__(self, scoring_service: ScoringService, parent=None):
        """
        Initialize the overall analytics tab.
        
        Args:
            scoring_service: Scoring service for analytics
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.scoring_service = scoring_service
        
        # Set up layout
        self.layout = QVBoxLayout(self)
        
        # Create refresh button
        self.refresh_button = QPushButton("Refresh Analytics")
        self.refresh_button.clicked.connect(self._load_analytics)
        self.layout.addWidget(self.refresh_button)
        
        # Create summary box
        self.summary_box = QGroupBox("Overall Performance")
        summary_layout = QFormLayout(self.summary_box)
        self.layout.addWidget(self.summary_box)
        
        self.total_students_label = QLabel("0")
        self.total_questions_label = QLabel("0")
        self.average_score_label = QLabel("0%")
        
        summary_layout.addRow("Total Students:", self.total_students_label)
        summary_layout.addRow("Total Questions Answered:", self.total_questions_label)
        summary_layout.addRow("Average Score:", self.average_score_label)
        
        # Create tabs for different analytics
        self.analytics_tabs = QTabWidget()
        self.layout.addWidget(self.analytics_tabs)
        
        # Create difficult questions tab
        self.difficult_widget = QWidget()
        difficult_layout = QVBoxLayout(self.difficult_widget)
        self.difficult_table = QTableWidget()
        self.difficult_table.setColumnCount(2)
        self.difficult_table.setHorizontalHeaderLabels(["Question ID", "Success Rate"])
        self.difficult_table.horizontalHeader().setStretchLastSection(True)
        difficult_layout.addWidget(self.difficult_table)
        self.analytics_tabs.addTab(self.difficult_widget, "Most Difficult Questions")
        
        # Create easy questions tab
        self.easy_widget = QWidget()
        easy_layout = QVBoxLayout(self.easy_widget)
        self.easy_table = QTableWidget()
        self.easy_table.setColumnCount(2)
        self.easy_table.setHorizontalHeaderLabels(["Question ID", "Success Rate"])
        self.easy_table.horizontalHeader().setStretchLastSection(True)
        easy_layout.addWidget(self.easy_table)
        self.analytics_tabs.addTab(self.easy_widget, "Easiest Questions")
        
        # Load analytics
        self._load_analytics()
    
    def _load_analytics(self):
        """Load overall analytics."""
        analytics = self.scoring_service.get_comparative_analytics()
        
        # Update summary
        self.total_students_label.setText(str(analytics.get("total_students", 0)))
        self.total_questions_label.setText(str(analytics.get("total_questions_answered", 0)))
        self.average_score_label.setText(f"{analytics.get('average_score', 0):.1f}%")
        
        # Update difficult questions table
        difficult_questions = analytics.get("difficult_questions", [])
        self.difficult_table.setRowCount(len(difficult_questions))
        
        for row, question in enumerate(difficult_questions):
            # Question ID
            question_id = question.get("question_id", 0)
            id_item = QTableWidgetItem(str(question_id))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.difficult_table.setItem(row, 0, id_item)
            
            # Success Rate
            success_rate = question.get("success_rate", 0)
            rate_item = QTableWidgetItem(f"{success_rate:.1f}%")
            rate_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.difficult_table.setItem(row, 1, rate_item)
        
        # Update easy questions table
        easy_questions = analytics.get("easy_questions", [])
        self.easy_table.setRowCount(len(easy_questions))
        
        for row, question in enumerate(easy_questions):
            # Question ID
            question_id = question.get("question_id", 0)
            id_item = QTableWidgetItem(str(question_id))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.easy_table.setItem(row, 0, id_item)
            
            # Success Rate
            success_rate = question.get("success_rate", 0)
            rate_item = QTableWidgetItem(f"{success_rate:.1f}%")
            rate_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.easy_table.setItem(row, 1, rate_item)
        
        # Resize columns to content
        self.difficult_table.resizeColumnsToContents()
        self.easy_table.resizeColumnsToContents()


class AnalyticsDashboard(QWidget):
    """
    Dashboard for displaying performance analytics.
    
    Integrates with the scoring service to fetch performance data
    and displays it using charts and tables.
    """
    
    def __init__(self, scoring_service: ScoringService, parent=None):
        """
        Initialize the analytics dashboard.
        
        Args:
            scoring_service: Scoring service for analytics
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.scoring_service = scoring_service
        
        # Set up layout
        self.layout = QVBoxLayout(self)
        
        # Create title label
        self.title_label = QLabel("Performance Analytics Dashboard")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        self.title_label.setFont(title_font)
        self.layout.addWidget(self.title_label)
        
        # Create tabs for different analytics views
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Create student performance tab
        self.student_tab = StudentPerformanceTab(scoring_service)
        self.tabs.addTab(self.student_tab, "Student Performance")
        
        # Create question performance tab
        self.question_tab = QuestionPerformanceTab(scoring_service)
        self.tabs.addTab(self.question_tab, "Question Analytics")
        
        # Create worksheet performance tab
        self.worksheet_tab = WorksheetPerformanceTab(scoring_service)
        self.tabs.addTab(self.worksheet_tab, "Worksheet Analytics")
        
        # Create overall analytics tab
        self.overall_tab = OverallAnalyticsTab(scoring_service)
        self.tabs.addTab(self.overall_tab, "Overall Analytics")
    
    def refresh_data(self):
        """
        Refresh the analytics data.
        
        Called when data changes, such as when new student responses are saved.
        """
        # Refresh the overall analytics tab
        if hasattr(self, 'overall_tab'):
            self.overall_tab._load_analytics()
            
        # If a student is selected in the student performance tab, refresh that data too
        if hasattr(self, 'student_tab'):
            student_id = self.student_tab.student_selector.get_student_id()
            if student_id:
                self.student_tab._load_student_analytics(student_id)