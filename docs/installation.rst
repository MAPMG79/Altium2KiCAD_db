Installation
============

This guide will help you install the Altium to KiCAD Database Migration Tool.

Prerequisites
------------

Before installing the tool, make sure you have the following prerequisites:

* Python 3.7 or higher
* pip (Python package installer)
* Database drivers for your specific database type:
    * For Microsoft Access: pyodbc and Access ODBC driver
    * For SQL Server: pyodbc and SQL Server ODBC driver
    * For SQLite: No additional drivers needed (included with Python)
    * For MySQL/MariaDB: pyodbc and MySQL ODBC driver or pymysql
    * For PostgreSQL: pyodbc and PostgreSQL ODBC driver or psycopg2

Installing from PyPI
-------------------

The easiest way to install the tool is from PyPI using pip:

.. code-block:: bash

    pip install altium2kicad

This will install the tool and all its dependencies.

Installing from Source
---------------------

To install the latest development version from source:

1. Clone the repository:

   .. code-block:: bash

       git clone https://github.com/yourusername/altium2kicad.git
       cd altium2kicad

2. Install the package in development mode:

   .. code-block:: bash

       pip install -e .

   This will install the package in "editable" mode, meaning changes to the source code will be immediately available without reinstalling.

3. For development, install additional dependencies:

   .. code-block:: bash

       pip install -r requirements-dev.txt

Verifying Installation
---------------------

To verify that the installation was successful, run:

.. code-block:: bash

    altium2kicad --version

You should see the version number of the tool displayed.

Installing GUI Dependencies
--------------------------

The GUI interface uses tkinter, which is included with most Python installations. However, if you're on Linux, you might need to install it separately:

**Ubuntu/Debian**:

.. code-block:: bash

    sudo apt-get install python3-tk

**Fedora**:

.. code-block:: bash

    sudo dnf install python3-tkinter

**Arch Linux**:

.. code-block:: bash

    sudo pacman -S tk

Troubleshooting
--------------

Database Driver Issues
~~~~~~~~~~~~~~~~~~~~~

If you encounter issues with database connectivity, make sure you have the appropriate ODBC drivers installed for your database type.

For Microsoft Access on Windows:
    The Microsoft Access ODBC driver should be included with Windows.

For SQL Server:
    Download and install the Microsoft ODBC Driver for SQL Server from the Microsoft website.

For other database types:
    Refer to the documentation for your specific database for ODBC driver installation instructions.

ImportError: No module named 'tkinter'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you get this error when trying to run the GUI, you need to install tkinter as described in the "Installing GUI Dependencies" section.

Permission Errors
~~~~~~~~~~~~~~~

If you get permission errors during installation, try:

.. code-block:: bash

    pip install --user altium2kicad

Or use a virtual environment:

.. code-block:: bash

    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install altium2kicad