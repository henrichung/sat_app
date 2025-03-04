# CLAUDE.md - Development Guidelines

## Build & Test Commands
- Activate environment: `mamba activate sat_app_env`
- Run app: `python main.py`
- Run tests: `pytest tests/`
- Run single test: `pytest tests/path_to_test.py::TestClass::test_function -v`
- Lint code: `flake8 sat_app/`
- Type check: `mypy sat_app/`

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

Follow the package structure in outline.md with clear separation between UI, business logic, data access, and rendering components.