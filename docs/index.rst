Altium to KiCAD Database Migration Tool
=======================================

.. image:: https://img.shields.io/badge/version-1.0.0-blue.svg
   :target: https://github.com/yourusername/Altium2KiCAD_db
   :alt: Version

.. image:: https://img.shields.io/badge/license-MIT-green.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License

Welcome to the documentation for the **Altium to KiCAD Database Migration Tool**. This tool helps you migrate component libraries from Altium's DbLib format to KiCAD's database library format, making it easier to transition between these two popular EDA platforms.

Features
--------

* Parse Altium DbLib files and connected databases
* Map Altium components to KiCAD equivalents
* Generate KiCAD-compatible SQLite database libraries
* Support for multiple database types (SQLite, MySQL, PostgreSQL, MS SQL)
* Intelligent symbol and footprint mapping
* Batch processing for large libraries
* Graphical and command-line interfaces
* Detailed logging and reporting
* Customizable mapping rules

Getting Started
--------------

If you're new to the tool, start with the :doc:`installation guide <user_guide/installation>` and then follow the :doc:`quickstart tutorial <user_guide/quickstart>` to perform your first migration.

.. toctree::
   :maxdepth: 2
   :caption: User Guide
   
   user_guide/installation
   user_guide/quickstart
   user_guide/basic_usage
   user_guide/advanced_features
   user_guide/troubleshooting
   user_guide/faq

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide
   
   developer_guide/architecture
   developer_guide/api_reference
   developer_guide/contributing
   developer_guide/extending

.. toctree::
   :maxdepth: 2
   :caption: Examples & Tutorials
   
   examples/basic_migration
   examples/batch_processing
   examples/custom_mapping
   examples/enterprise_setup

.. toctree::
   :maxdepth: 1
   :caption: API Reference
   
   api/core
   api/utils
   api/cli
   api/gui

Indices and tables
-----------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Support
-------

If you encounter any issues or have questions, please check the :doc:`troubleshooting guide <user_guide/troubleshooting>` and :doc:`FAQ <user_guide/faq>`. If you still need help, please `open an issue <https://github.com/yourusername/Altium2KiCAD_db/issues>`_ on GitHub.

License
-------

This project is licensed under the MIT License - see the LICENSE file for details.

Acknowledgments
--------------

* Altium and KiCAD communities
* Contributors to the project
* Open-source EDA ecosystem