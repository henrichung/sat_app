## Code Style Guidelines
- **Imports**: Group standard library, third-party, and local imports
- **Python version**: 3.9+
- **UI Framework**: PyQt6
- **Database**: SQLite
- **Naming**: Snake_case for functions/variables, PascalCase for classes
- **Type hints**: Required for all function parameters and return values
- **Documentation**: Docstrings for all classes and non-trivial functions
- **Error handling**: Use try/except with specific exceptions, log errors
- **Testing**: Write unit tests for all business logic and DAL components
- **Line length**: Max 100 characters

## 1. System Overview

**Objective:**  
Develop a high-performance, desktop-based Windows application that lets educators manage a SQL-backed SAT question bank, generate dynamic worksheets (with randomized question and answer order, inline images, and LaTeX-rendered equations), and capture detailed scoring analytics for individual students.

**Core Features:**  
- **Question Management:** CRUD operations for SAT questions, including optional images and metadata.
- **Bulk Import:** Support for JSON import of questions (with a schema provided later).
- **Worksheet Generation:** Dynamic selection of questions, randomization, LaTeX equation rendering, inline image embedding in PDF outputs, and live preview.
- **Scoring & Analytics:** Record students' responses, compute right/wrong answers, and generate performance reports.

## 2. Detailed Module and Class Responsibilities

### 2.1. **Configuration Module (`config/`)**

- **`config_manager.py`**
  - Loads settings from a configuration file (e.g., JSON/INI).
  - Provides global access to configuration settings (database path, image directories, etc.).
  - Validates paths and configuration options at startup.

### 2.2. **Data Access Layer (`dal/`)**

- **`database_manager.py`**
  - Manages connections to the SQLite database.
  - Provides helper functions for transactions and query execution.
  - Implements connection pooling if necessary for performance.

- **`models.py`**
  - Contains classes representing the core data objects:
    - **`Question`** with properties: question text, optional image paths, answer choices (A-D), answer images, explanation, subject tags, difficulty.
    - **`Worksheet`** with properties: worksheet ID, creation date, list of question IDs, generated PDF path.
    - **`Score`** with properties: student identifier, question reference, correctness, timestamp.
  - Implements serialization/deserialization methods (e.g., for JSON import/export).

- **`repositories.py`**
  - Implements CRUD operations for each model.
  - Contains methods like `add_question()`, `delete_question()`, `update_question()`, `filter_questions(criteria)`.
  - Contains specialized queries for analytics and performance tracking.

- **`migrations.py`**
  - Contains functions to initialize and update the database schema.
  - Helps version control the database schema for future changes.

### 2.3. **Business Logic Layer (`business/`)**

- **`question_manager.py`**
  - Orchestrates the creation, update, and deletion of questions.
  - Performs business validation (e.g., ensuring required fields are populated).
  - Interacts with `repositories.py` to commit changes to the database.

- **`worksheet_generator.py`**
  - Accepts a list of selected question IDs (or filtering criteria).
  - Randomizes question order and shuffles answer choices (maintaining the mapping to the correct answer).
  - Prepares data for rendering (both for live preview and PDF generation).
  - Integrates with the rendering module to produce final outputs.

- **`import_export_manager.py`**
  - Reads and validates JSON files based on the provided schema.
  - Maps JSON data to `Question` objects.
  - Handles bulk inserts via the DAL and reports errors or schema mismatches.
  - Exports questions to JSON format with proper schema.
  - Handles image references during import/export.

- **`settings_manager.py`**
  - Manages application settings through the ConfigManager.
  - Provides validation for settings values.
  - Handles special cases like directory creation for path settings.
  - Offers methods to get/update settings by category.
  - Provides reset-to-defaults functionality.

- **`scorer.py`**
  - Records user responses.
  - Compares answers with correct answers stored in the database.
  - Computes analytics such as per-question and per-student performance metrics.
  - Exposes methods for the analytics module to generate reports.

### 2.4. **Rendering Module (`rendering/`)**

- **`pdf_generator.py`**
  - Uses a PDF library (e.g., ReportLab) to generate worksheet PDFs.
  - Arranges questions, images, and rendered LaTeX content into a printable layout.
  - Provides functionality to embed an answer key at the end of the document.

- **`latex_renderer.py`**
  - Converts LaTeX strings into rendered formats (images or HTML).
  - Interfaces with a LaTeX engine (or embedded web view) for live previews.
  - Ensures compatibility with both on-screen rendering and PDF generation.

- **`image_renderer.py`**
  - Processes image files referenced by questions.
  - Ensures images are properly resized and formatted for the PDF.
  - Provides caching or lazy-loading if needed for performance.

### 2.5. **User Interface Layer (`ui/`)**

- **`main_window.py`**
  - Manages the overall window layout and navigation between modules.
  - Implements a tabbed interface or menu-driven navigation using PyQt6 for question management, worksheet generation, and analytics.

- **`question_editor.py`**
  - Provides forms for adding/editing questions.
  - Uses file pickers for image selection and supports rich text input for LaTeX equations.
  - Validates input before sending it to the `question_manager`.

- **`question_browser.py`**
  - Allows user to view questions in the database.
  - Support filtering of questions by search, tags, or other associated metadata
  - Paginates the question list, allowing for efficience exploration of large datasets, while working with filtering operations.

- **`worksheet_view.py`**
  - Allows users to select questions (either manually or by filters).
  - Displays live previews of the worksheet with rendered LaTeX and inline images.
  - Offers controls for randomization settings and PDF export.

- **`analytics_dashboard.py`**
  - Displays charts and tables for performance analytics.
  - Integrates with the `scorer` to fetch performance data.
  - Uses embedded chart libraries (e.g., matplotlib with a Qt widget) for interactive reports.

- **`import_export_view.py`**
  - Provides a tabbed interface for importing and exporting questions.
  - Includes file selection, options, and progress reporting.
  - Handles filtering for exports and options for imports.

- **`settings_view.py`**
  - Provides a tabbed interface for configuring application settings.
  - Includes theme and font size selection in the UI tab.
  - Offers file/directory browsing for path configuration.
  - Supports applying changes and resetting to defaults.

### 2.6. **Utility Module (`utils/`)**

- **`logger.py`**
  - Sets up application-wide logging for debugging and error reporting.
  - Provides a standardized interface for logging events across modules.

- **`helpers.py`**
  - Contains utility functions for string manipulation, date formatting, file path resolution, etc.
  - Offers common helper methods used by various parts of the application.

### 2.7. **Testing Module (`tests/`)**

- **Unit tests** for:
  - **DAL components:** Verify CRUD operations and database transactions.
  - **Business logic:** Test worksheet generation randomization, JSON import validation, and scoring calculations.
  - **UI components:** Automated tests for form validation and interface response (using a testing framework that supports GUI testing).

