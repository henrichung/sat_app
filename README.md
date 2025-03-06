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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.