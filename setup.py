#!/usr/bin/env python3
"""
Setup script for Altium to KiCAD Database Migration Tool.
"""

import os
import re
from setuptools import setup, find_packages

# Read the README file
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

# Get version from __init__.py
with open(os.path.join('migration_tool', '__init__.py'), 'r', encoding='utf-8') as f:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M)
    if version_match:
        version = version_match.group(1)
    else:
        version = '0.1.0'

# Core dependencies
install_requires = [
    'pyyaml>=5.1',
    'pyodbc>=4.0.30',
    'fuzzywuzzy>=0.18.0',
    'python-Levenshtein>=0.12.0',
    'tqdm>=4.45.0',
    'colorama>=0.4.3',
    'click>=8.0.0',         # CLI framework
    'fastapi>=0.68.0',      # API framework
    'uvicorn>=0.15.0',      # ASGI server for FastAPI
    'pydantic>=1.8.2',      # Data validation for FastAPI
    'python-multipart>=0.0.5',  # Form data parsing for FastAPI
    'python-jose>=3.3.0',   # JWT authentication for API
]

# Optional database drivers
extras_require = {
    'mysql': ['mysql-connector-python>=8.0.0'],
    'postgresql': ['psycopg2-binary>=2.8.0'],
    'all': [
        'mysql-connector-python>=8.0.0',
        'psycopg2-binary>=2.8.0',
    ],
    'dev': [
        'pytest>=6.0.0',
        'pytest-cov>=2.10.0',
        'black>=21.5b2',
        'flake8>=3.9.0',
        'mypy>=0.812',
        'sphinx>=4.0.0',
        'sphinx-rtd-theme>=0.5.0',
        'pre-commit>=2.12.0',
    ],
}

setup(
    name='altium2kicad',
    version=version,
    description='Tool for migrating Altium DbLib databases to KiCAD format',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Altium2KiCAD Team',
    author_email='info@example.com',
    url='https://github.com/example/altium2kicad',
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={
        'console_scripts': [
            'altium2kicad=migration_tool.cli:main',
            'altium2kicad-gui=migration_tool.gui:main',
            'altium2kicad-api=migration_tool.api:start_api_server',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
    ],
    python_requires='>=3.7',
)