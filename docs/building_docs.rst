Building Documentation
===================

This guide explains how to build the documentation for the Altium to KiCAD Database Migration Tool.

Prerequisites
------------

Before building the documentation, make sure you have the following prerequisites:

* Python 3.7 or higher
* Sphinx documentation generator
* sphinx_rtd_theme (Read the Docs theme)

You can install the documentation dependencies with:

.. code-block:: bash

    pip install sphinx sphinx_rtd_theme

Building Documentation Locally
-----------------------------

Using Provided Scripts
~~~~~~~~~~~~~~~~~~~~~

The project includes scripts to simplify building the documentation:

**Windows**:

.. code-block:: bash

    # Using the batch script
    scripts\build_docs.bat

**Linux/macOS**:

.. code-block:: bash

    # Using the shell script (make it executable first)
    chmod +x scripts/build_docs.sh
    ./scripts/build_docs.sh

**Python Script (Cross-platform)**:

.. code-block:: bash

    # Using the Python script
    python scripts/build_docs.py

These scripts will:

1. Build the documentation using Sphinx
2. Copy the built files to the ``docs_build/html`` directory
3. Open the documentation in your default web browser

Manual Build
~~~~~~~~~~~

If you prefer to build the documentation manually:

.. code-block:: bash

    # Navigate to the docs directory
    cd docs

    # Build the HTML documentation
    make html

    # On Windows, if make is not available
    sphinx-build -b html . _build/html

The built documentation will be available in the ``docs/_build/html`` directory.

Viewing the Documentation
------------------------

After building, open ``docs_build/html/index.html`` (or ``docs/_build/html/index.html`` if built manually) in your web browser to view the documentation.

Troubleshooting ReadTheDocs.org Build Issues
-------------------------------------------

If you encounter issues with ReadTheDocs.org builds:

1. Build the documentation locally using one of the methods above
2. Check the console output for errors
3. Fix any issues in the documentation source files
4. Rebuild and verify locally before pushing changes

Common issues include:

* Missing dependencies in the ReadTheDocs configuration
* Syntax errors in reStructuredText files
* Missing or incorrect references
* Import errors when autodoc tries to import Python modules

Using the GitHub Actions Workflow
--------------------------------

The project includes a GitHub Actions workflow for building and deploying the documentation:

1. The workflow is defined in ``.github/workflows/docs_build.yml``
2. It automatically builds the documentation when changes are pushed to the main branch
3. The built documentation is deployed to GitHub Pages
4. You can view the deployed documentation at ``https://[your-username].github.io/Altium2KiCAD_db/docs-build/``

You can also manually trigger the workflow from the GitHub Actions tab in the repository.

Contributing to Documentation
---------------------------

When contributing to the documentation:

1. Build and test your changes locally
2. Ensure all links and references work correctly
3. Follow the reStructuredText syntax and conventions
4. Submit a pull request with your changes

For more information on reStructuredText syntax, see the `Sphinx documentation <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>`_.