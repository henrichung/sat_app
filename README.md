# SAT Question Bank & Worksheet Generator

A desktop Windows application for educators to manage an SAT question bank, generate dynamic worksheets with randomized questions, LaTeX equation rendering, and capture detailed scoring analytics.

## Features

- **Question Management**: Create, read, update, and delete SAT questions with optional images
- **Worksheet Generation**: Generate PDF worksheets with randomized question order and answer choices
- **LaTeX Equation Rendering**: Support for LaTeX equations in questions and answers
- **Analytics**: Track student performance and generate reports
- **Bulk Import/Export**: Import and export questions in JSON format

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/sat_app.git
   cd sat_app
   ```

2. Create and activate a virtual environment (recommended):
   ```
   # Using conda/mamba
   mamba create -n sat_app_env python=3.9
   mamba activate sat_app_env
   
   # Or using venv
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python sat_app/main.py
   ```

## Project Structure

The application follows a modular architecture:

- `config/`: Configuration management
- `dal/`: Data Access Layer (database operations)
  - `models.py`: Data model classes (Question, Worksheet, Score)
  - `repositories.py`: CRUD operations and query functionality
  - `database_manager.py`: Database connection and transaction handling
  - `migrations.py`: Database schema creation and updates
- `business/`: Business logic
  - `question_manager.py`: Question validation and operations
  - `manager_factory.py`: Factory for instantiating business layer managers
  - `worksheet_generator.py`: Worksheet creation and randomization
  - `import_manager.py`: Bulk import functionality
  - `scorer.py`: Student response handling and scoring
- `rendering/`: PDF generation and LaTeX rendering
- `ui/`: User interface components
- `utils/`: Utility functions
  - `logger.py`: Centralized logging configuration
- `tests/`: Test suite

## Development

1. Install development dependencies:
   ```
   pip install -r requirements-dev.txt
   ```

2. Run tests:
   ```
   pytest tests/
   ```

3. Check code style:
   ```
   flake8 sat_app/
   ```

4. Run type checking:
   ```
   mypy sat_app/
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.