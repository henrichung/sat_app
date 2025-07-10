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

## Development

### Build & Test Commands
- Activate environment: `mamba activate sat_app_env`
- Run app: `python main.py`
- Run tests: `pytest tests/`
- Run single test: `pytest tests/path_to_test.py::TestClass::test_function -v`
- Lint code: `flake8 sat_app/`
- Type check: `mypy sat_app/`

### Building the Application
The application has been standardized on PyQt6 for its GUI components.

#### Executable Build Process
To build the application executable:
```bash
tools/simple_build.bat     # Windows
tools/simple_build.sh      # Linux/macOS
```

#### Conda Package Build Process
```bash
tools/build_conda_package.bat   # Windows
tools/build_conda_package.sh    # Linux/macOS
```

### Code Style Guidelines
- **Python version**: 3.9+
- **UI Framework**: PyQt6
- **Database**: SQLite
- **Naming**: Snake_case for functions/variables, PascalCase for classes
- **Type hints**: Required for all function parameters and return values
- **Documentation**: Docstrings for all classes and non-trivial functions
- **Line length**: Max 100 characters

### Project Structure
The application follows a modular architecture with clear separation between UI, business logic, data access, and rendering components:

- `config/`: Configuration management
- `dal/`: Data Access Layer (database operations)
- `business/`: Business logic (question management, worksheet generation)
- `rendering/`: PDF generation and LaTeX rendering
- `ui/`: User interface components
- `utils/`: Utility functions
- `tests/`: Test suite for all components

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.