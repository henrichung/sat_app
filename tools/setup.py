from setuptools import setup, find_packages

setup(
    name="sat_app",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "matplotlib>=3.10.0",
        "numpy>=2.2.0",
        "PyQt6>=6.8.0",
        "pillow>=11.0.0",
        "reportlab>=4.3.0",
        "pycairo>=1.27.0",
        "sympy>=1.13.0",
        "PyPDF2>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "sat_app=sat_app.main:main",
        ],
    },
    python_requires='>=3.9',
    author="",
    author_email="",
    description="SAT Question Bank & Worksheet Generator",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)