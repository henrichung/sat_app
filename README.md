# SAT Question Bank & Worksheet Generator

A desktop application for educators to manage an SAT question bank, generate dynamic worksheets with randomized questions, LaTeX equation rendering, and capture detailed scoring analytics.

## Features

- **Question Management**: Create, read, update, and delete SAT questions with optional images
- **Worksheet Generation**: Generate PDF worksheets with randomized question order and answer choices
- **LaTeX Equation Rendering**: Support for LaTeX equations in questions and answers
- **Analytics**: Track student performance and generate reports
- **Bulk Import/Export**: Import and export questions in JSON format

## System Overview

**Objective:**  
Develop a high-performance, desktop-based Windows application that lets educators manage a SQL-backed SAT question bank, generate dynamic worksheets (with randomized question and answer order, inline images, and LaTeX-rendered equations), and capture detailed scoring analytics for individual students.

## Installation Options

### 1. Install from Anaconda Cloud (Recommended)

The easiest way to install SAT App is from Anaconda Cloud:

```bash
# Create and activate a new environment
conda create -n sat_app_env python=3.13
conda activate sat_app_env
conda install -c henrichung sat_app

# Launch the application
sat_app
```

### 2. Direct Installation from Package File

If you received the `.conda` package file directly:

```bash
# Create and activate a new environment
conda create -n sat_app_env python=3.13
conda activate sat_app_env
conda install --use-local /path/to/sat_app-0.1.0-py313.conda

# Launch the application
sat_app
```

### 3. Build and Install Conda Package Locally

1. Clone the repository:
   ```bash
   git clone https://github.com/henrichung/sat_app.git
   cd sat_app
   ```

2. Build the conda package:
   ```bash
   # Navigate to conda recipe directory
   cd conda-recipe
   
   # Build the package
   conda build .
   
   # For Python 3.13 specifically
   conda build --python=3.13 .
   ```

3. Install the built package:
   ```bash
   # The build process will show the exact path
   conda install -c local sat_app
   
   # Or specify the path directly
   conda install /path/to/conda-bld/linux-64/sat_app-0.1.0-py313.conda
   ```

4. Launch the application:
   ```bash
   sat_app
   ```

### 4. Development Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/henrichung/sat_app.git
   cd sat_app
   ```

2. Create and activate a conda environment:
   ```bash
   conda env create -f environment.yml
   conda activate sat_app
   ```

3. Install in development mode:
   ```bash
   pip install -e .
   ```

4. Run the application:
   ```bash
   # Run directly 
   python sat_app/main.py
   
   # Or using the entry point
   sat_app
   ```

## Development Guide

### Build & Test Commands
- Activate environment: `mamba activate sat_app_env`
- Run app: `python main.py`
- Run tests: `pytest tests/`
- Run single test: `pytest tests/path_to_test.py::TestClass::test_function -v`
- Lint code: `flake8 sat_app/`
- Type check: `mypy sat_app/`

### Code Style Guidelines
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

### Project Structure

The application follows a modular architecture with clear separation between UI, business logic, data access, and rendering components:

- `config/`: Configuration management
  - `config_manager.py`: Loads settings from configuration file, provides global access to settings, validates paths

- `dal/`: Data Access Layer (database operations)
  - `models.py`: Data model classes (Question, Worksheet, Score)
  - `repositories.py`: CRUD operations and query functionality
  - `database_manager.py`: Database connection and transaction handling
  - `migrations.py`: Database schema creation and updates

- `business/`: Business logic
  - `question_manager.py`: Question validation and operations
  - `manager_factory.py`: Factory for instantiating business layer managers
  - `worksheet_generator.py`: Worksheet creation and randomization
  - `import_export_manager.py`: Bulk import/export functionality
  - `settings_manager.py`: Manages application settings
  - `scorer.py`: Student response handling and scoring

- `rendering/`: PDF generation and LaTeX rendering
  - `pdf_generator.py`: Generates worksheet PDFs with ReportLab
  - `latex_renderer.py`: Converts LaTeX strings into rendered formats
  - `image_renderer.py`: Processes images for PDF inclusion

- `ui/`: User interface components
  - `main_window.py`: Overall window layout and navigation
  - `question_editor.py`: Forms for adding/editing questions
  - `question_browser.py`: View/filter questions in the database
  - `worksheet_view.py`: Create worksheets with question selection
  - `analytics_dashboard.py`: Performance analytics charts and tables
  - `import_export_view.py`: Import/export question data
  - `settings_view.py`: Configure application settings
  - `components/`: Reusable UI components

- `utils/`: Utility functions
  - `logger.py`: Centralized logging configuration
  - `helpers.py`: Common utility functions

- `tests/`: Test suite for all components

## Development History

### [2025-03-02] Initial Development
- Initialized project repository with github
- Created core components (config, database, models, repositories, UI)
- Implemented business layer with question management
- Created UI for question editing and browsing
- Added worksheet generation with randomization
- Implemented PDF generation with LaTeX support

### [2025-03-03] Feature Completion
- Enhanced LaTeX equation rendering
- Added analytics module for student performance tracking
- Implemented import/export functionality
- Created settings module for application configuration
- PROJECT MILESTONE: All core features completed

## Distribution

### Publishing to Anaconda Cloud

To share your package with others through Anaconda Cloud:

1. Create an Anaconda Cloud account if you don't have one
2. Install the anaconda-client package:
   ```bash
   conda install anaconda-client
   ```

3. Login to your account:
   ```bash
   anaconda login
   ```

4. Upload your package:
   ```bash
   # Path shown at the end of conda build output
   anaconda upload /path/to/conda-bld/linux-64/sat_app-0.1.0-py313.conda
   ```

5. Users can now install your package with:
   ```bash
   conda install -c yourusername sat_app
   ```

### Creating a Custom Channel

For internal distribution or offline installation:

1. Set up a web server with a directory structure:
   ```
   /channel/
   └── linux-64/
       ├── sat_app-0.1.0-py313.conda
       └── repodata.json
   ```

2. Run `conda index /channel` to generate metadata

3. Users install with:
   ```bash
   conda install -c http://your-server/channel sat_app
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.