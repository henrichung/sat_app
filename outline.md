## 1. System Overview

**Objective:**  
Develop a high-performance, desktop-based Windows application that lets educators manage a SQL-backed SAT question bank, generate dynamic worksheets (with randomized question and answer order, inline images, and LaTeX-rendered equations), and capture detailed scoring analytics for individual students.

**Core Features:**  
- **Question Management:** CRUD operations for SAT questions, including optional images and metadata.
- **Bulk Import:** Support for JSON import of questions (with a schema provided later).
- **Worksheet Generation:** Dynamic selection of questions, randomization, LaTeX equation rendering, inline image embedding in PDF outputs, and live preview.
- **Scoring & Analytics:** Record students’ responses, compute right/wrong answers, and generate performance reports.

---


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

- **`import_manager.py`**
  - Reads and validates JSON files based on the provided schema.
  - Maps JSON data to `Question` objects.
  - Handles bulk inserts via the DAL and reports errors or schema mismatches.

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

- **`common_widgets.py`**
  - Contains shared UI components (custom buttons, dialogs, progress indicators).
  - Helps maintain consistency across different UI screens.

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

---

## 3. Inter-Module Interaction and Data Flow

1. **Startup Flow:**
   - `main.py` initializes the application by loading configuration via `config_manager`.
   - The database connection is established in `database_manager`, and if needed, migrations are run.

2. **Question Creation/Editing:**
   - The user interacts with the UI via `question_editor.py`.
   - The UI form data is sent to `question_manager.py`, which performs validation and calls methods in `repositories.py` to update the database.
   - Any associated image files are saved to the designated folder and referenced by relative paths.

3. **Worksheet Generation:**
   - The user selects questions or applies filters in `worksheet_view.py`.
   - The `worksheet_generator.py` retrieves question data from the DAL, randomizes orders, and prepares a data structure.
   - This data is sent to `pdf_generator.py` and `latex_renderer.py` to produce a live preview and final PDF.
   - The preview is updated in real time as selections or settings change.

4. **Bulk Import:**
   - The import process is initiated through a dedicated UI dialog that calls `import_manager.py`.
   - The manager parses the JSON file, validates the schema, and uses the DAL’s repository functions to insert new questions.
   - Errors are logged using `logger.py` and feedback is provided in the UI.

5. **Scoring & Analytics:**
   - When a student completes a worksheet, their responses are recorded via the scoring interface.
   - `scorer.py` logs each response, compares it to the correct answers, and updates the `Scores` table.
   - The `analytics_dashboard.py` then queries this data through business logic to generate charts and reports, leveraging matplotlib embedded within the GUI.

---


## 3. Detailed Component Design

### 3.1. Database Design

#### Tables

1. **Questions Table:**
   - `question_id` (Primary Key, Integer)
   - `question_text` (Text)
   - `question_image_path` (Text, nullable)
   - `answer_a` (Text)
   - `answer_b` (Text)
   - `answer_c` (Text)
   - `answer_d` (Text)
   - `answer_image_a` (Text, nullable)
   - `answer_image_b` (Text, nullable)
   - `answer_image_c` (Text, nullable)
   - `answer_image_d` (Text, nullable)
   - `answer_explanation` (Text)
   - `subject_tags` (Text, stored as comma-separated values or a separate mapping table)
   - `difficulty_label` (Text)

2. **Worksheets Table:**
   - `worksheet_id` (Primary Key, Integer)
   - `creation_date` (Datetime)
   - `question_ids` (Text/JSON – list of question IDs selected for the worksheet)
   - `pdf_path` (Text – location of the generated worksheet PDF)

3. **Scores Table:**
   - `score_id` (Primary Key, Integer)
   - `student_id` (Text/Integer, if later extended to multiple users)
   - `worksheet_id` (Foreign Key)
   - `question_id` (Foreign Key)
   - `correct` (Boolean)
   - `timestamp` (Datetime)

*Additional metadata can be incorporated by either expanding these tables or using a key-value mapping approach for extensibility.*

---

### 3.2. Modules & Functionality

#### A. **Question Management Module**
- **UI Forms:**  
  - Add/Edit Question Form with input fields for text, images (file picker), answer options, explanation, tags, and difficulty.
  - List view with filtering capabilities.
- **Functionality:**  
  - CRUD operations integrated with the DAL.
  - Search and filter questions based on tags or difficulty.
  
#### B. **Worksheet Generation Module**
- **Selection Interface:**  
  - Allow users to select questions manually or use filters for random selection.
- **Randomization:**  
  - Randomize question order.
  - Shuffle answer choices per question while preserving the correct answer mapping.
- **Rendering:**  
  - Convert LaTeX to rendered output via embedded web view or pre-rendering images.
  - Integrate with the PDF generation library to create a worksheet PDF with inline images.
- **Live Preview:**  
  - Display an up-to-date preview that refreshes when questions are added/edited.
  
#### C. **Bulk Import Module**
- **File Handler:**  
  - Accept JSON file input.
  - Validate against the expected schema.
- **Import Logic:**  
  - Parse and map JSON fields to database columns.
  - Handle errors gracefully (e.g., log issues and continue with valid entries).

#### D. **Scoring & Analytics Module**
- **Data Entry:**  
  - Simple interface for recording students' responses (right/wrong for each question).
- **Analytics Calculation:**  
  - Calculate performance metrics (e.g., percentage correct per subject, question difficulty analysis).
- **Visualization:**  
  - Use matplotlib to render charts (bar charts, line graphs) to display performance trends.
  
#### E. **Configuration Module**
- **Settings Management:**  
  - Configure file paths (database file, images folder, PDF output location).
  - Store configuration settings in a config file (e.g., JSON or INI format) for ease of customization.


## 4. Project Package & File Structure

A modular package layout helps maintain separation of concerns and facilitates testing, maintenance, and future scalability. For example:

```
sat_app/
├── main.py                     # Application entry point
├── requirements.txt             # Dependencies list
├── setup.py                     # For packaging the application
├── README.md                    # Documentation and setup instructions
├── CHANGELOG.md                 # Track version changes
├── assets/                      # Application icons and resources
├── config/
│   └── config_manager.py       # Loads and validates configuration (database path, image folders, etc.)
├── ui/
│   ├── __init__.py
│   ├── resources/               # UI-specific resources (icons, styles)
│   ├── dialogs/                 # Split complex dialogs into separate modules
│   ├── widgets/                 # Custom widgets implementation
│   ├── main_window.py          # Main application window, window manager
│   ├── question_editor.py      # Dialogs/forms to add/edit questions
│   ├── worksheet_view.py       # Worksheet selection, live preview pane, and PDF export controls
│   ├── analytics_dashboard.py  # Display performance charts and analytics
│   └── common_widgets.py       # Custom UI components and reusable widgets
├── dal/
│   ├── __init__.py
│   ├── database_manager.py     # Connection handling, transactions, and connection pooling (if needed)
│   ├── models.py               # Data model classes: Question, Worksheet, Score
│   ├── repositories.py         # Repositories for each model (CRUD operations, queries, filtering)
│   └── migrations.py           # Schema creation and migration utilities
├── business/
│   ├── __init__.py
│   ├── question_manager.py     # Business logic for question creation, validation, and updating
│   ├── worksheet_generator.py  # Assembles worksheets, performs randomization of questions/answers
│   ├── import_manager.py       # Handles JSON import, schema validation, and bulk insertion logic
│   ├── scorer.py               # Manages scoring, records results, computes analytics
│   ├── export_manager.py        # Handle exporting questions/analytics
│   └── template_manager.py      # Manage worksheet templates
├── rendering/
│   ├── __init__.py
│   ├── pdf_generator.py        # Generates worksheet PDFs, integrates LaTeX and image embedding
│   ├── latex_renderer.py       # Renders LaTeX equations to images/HTML for live preview and PDF generation
│   ├── image_renderer.py       # Handles inline image formatting and processing for the PDF
│   └── template_renderer.py     # Handle customizable worksheet templates
├── utils/
│   ├── __init__.py
│   ├── logger.py               # Centralized logging setup and error handling utilities
│   └── helpers.py              # Miscellaneous helper functions
└── tests/
    ├── __init__.py
    ├── test_database.py        # Unit tests for DAL components
    ├── test_business.py        # Tests for business logic (e.g., worksheet generation, import)
    └── test_ui.py              # UI testing (if using a framework that supports automated UI tests)
```

## 4. Implementation Considerations

- **Technology Stack**
  The application is intended to be built using Python 3.9+, with the PyQT6 package. Database management is meant to use SQLite. PDF generation and LaTeX generation package choice can be left to the development team.

- **Asynchronous Processing:**  
  Long-running tasks (e.g., bulk imports, PDF generation) should run in separate threads or use asynchronous patterns to keep the UI responsive.

- **Error Handling & Logging:**  
  Each module should catch exceptions and report errors via a centralized logging mechanism. UI components can provide user-friendly error messages when needed.

- **Extensibility:**  
  The use of models and repositories in the DAL ensures that adding new metadata or even switching databases in the future can be achieved with minimal impact on the rest of the application. Similarly, the clear separation between business logic and UI allows changes in one layer without major refactoring of the other.

- **Performance:**  
  LaTeX rendering can be resource-intensive, ensure that an efficience latex rendering and image rendering system is in place. There must also be a plan for handling large PDF generation with many images.

- **Testing:**  
  A robust suite of unit and integration tests will be developed to cover the key interactions, ensuring that refactoring or adding new features does not break existing functionality.

---

## 5. Summary

This comprehensive plan defines a multi-package application that clearly separates concerns across configuration, data access, business logic, rendering, and UI. Each module is broken into distinct classes and responsibilities, which not only makes the codebase more maintainable but also allows parallel development and easier unit testing. This design supports both current requirements and future enhancements with minimal friction.

