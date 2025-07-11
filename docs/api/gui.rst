Graphical User Interface (GUI)
============================

The Altium to KiCAD Database Migration Tool provides a graphical user interface for users who prefer a visual approach to migration operations.

Overview
--------

The GUI is built using Python's Tkinter library and provides a user-friendly interface for:

* Configuring migration settings
* Selecting input and output files/directories
* Customizing mapping rules
* Monitoring migration progress
* Viewing migration results and statistics
* Exporting reports

The GUI is implemented through two main classes:

* ``MigrationProgressDialog``: Displays progress during migration operations
* ``AltiumToKiCADMigrationApp``: The main application window with tabs for different functions

Main Application Window
----------------------

The main application window is divided into several tabs:

* **Configuration**: Input/output settings and migration options
* **Mapping Rules**: Customization of symbol and footprint mappings
* **Results**: Migration statistics and issues
* **About**: Information about the tool

.. code-block:: python

   class AltiumToKiCADMigrationApp:
       """Main application for Altium to KiCAD database migration"""
       
       def __init__(self):
           self.root = tk.Tk()
           self.root.title("Altium to KiCAD Database Migration Tool")
           self.root.geometry("800x600")
           
           # Configuration variables
           self.altium_dblib_path = tk.StringVar()
           self.output_directory = tk.StringVar()
           self.kicad_library_path = tk.StringVar()
           
           # Migration components
           self.parser = None
           self.mapper = None
           self.generator = None
           
           self.setup_ui()
           self.setup_logging()

GUI Components
-------------

Configuration Tab
~~~~~~~~~~~~~~~

The Configuration tab allows users to:

* Select an Altium .DbLib file
* Choose an output directory
* Specify KiCAD library paths (optional)
* Configure migration options
* Start the migration process
* Test database connection
* Reset configuration

.. code-block:: python

   def setup_config_tab(self, notebook):
       """Setup configuration tab"""
       config_frame = ttk.Frame(notebook)
       notebook.add(config_frame, text="Configuration")
       
       # Title
       title_label = tk.Label(config_frame, text="Altium to KiCAD Database Migration", 
                             font=('Arial', 16, 'bold'))
       title_label.pack(pady=10)
       
       # Input file selection
       input_frame = ttk.LabelFrame(config_frame, text="Input Configuration", padding=10)
       input_frame.pack(fill='x', padx=20, pady=10)
       
       ttk.Label(input_frame, text="Altium .DbLib File:").grid(row=0, column=0, sticky='w', pady=5)
       ttk.Entry(input_frame, textvariable=self.altium_dblib_path, width=50).grid(row=0, column=1, padx=5, pady=5)
       ttk.Button(input_frame, text="Browse", command=self.browse_altium_file).grid(row=0, column=2, padx=5, pady=5)

Mapping Rules Tab
~~~~~~~~~~~~~~~

The Mapping Rules tab allows users to:

* View symbol mappings
* Add custom mappings
* Edit existing mappings

.. code-block:: python

   def setup_mapping_tab(self, notebook):
       """Setup mapping customization tab"""
       mapping_frame = ttk.Frame(notebook)
       notebook.add(mapping_frame, text="Mapping Rules")
       
       # Symbol mapping section
       symbol_frame = ttk.LabelFrame(mapping_frame, text="Symbol Mappings", padding=10)
       symbol_frame.pack(fill='both', expand=True, padx=20, pady=10)
       
       # Create treeview for symbol mappings
       self.symbol_tree = ttk.Treeview(symbol_frame, columns=('Altium', 'KiCAD', 'Confidence'), show='headings')
       self.symbol_tree.heading('Altium', text='Altium Symbol')
       self.symbol_tree.heading('KiCAD', text='KiCAD Symbol')
       self.symbol_tree.heading('Confidence', text='Confidence')

Results Tab
~~~~~~~~~

The Results tab displays:

* Migration statistics
* Issues and warnings
* Export options

.. code-block:: python

   def setup_results_tab(self, notebook):
       """Setup results and statistics tab"""
       results_frame = ttk.Frame(notebook)
       notebook.add(results_frame, text="Results")
       
       # Statistics section
       stats_frame = ttk.LabelFrame(results_frame, text="Migration Statistics", padding=10)
       stats_frame.pack(fill='x', padx=20, pady=10)
       
       self.stats_text = tk.Text(stats_frame, height=8, width=70)
       self.stats_text.pack(fill='x')
       
       # Issues section
       issues_frame = ttk.LabelFrame(results_frame, text="Issues and Warnings", padding=10)
       issues_frame.pack(fill='both', expand=True, padx=20, pady=10)

About Tab
~~~~~~~~

The About tab provides information about the tool, including:

* Version information
* Features
* Requirements
* Usage tips
* Support information

Progress Dialog
--------------

The ``MigrationProgressDialog`` class displays progress during migration operations:

.. code-block:: python

   class MigrationProgressDialog:
       """Progress dialog for migration operations"""
       
       def __init__(self, parent):
           self.window = tk.Toplevel(parent)
           self.window.title("Migration Progress")
           self.window.geometry("500x300")
           self.window.transient(parent)
           self.window.grab_set()
           
           # Progress bar
           self.progress = ttk.Progressbar(self.window, mode='indeterminate')
           self.progress.pack(pady=10, padx=20, fill='x')
           
           # Status label
           self.status_label = tk.Label(self.window, text="Initializing...")
           self.status_label.pack(pady=5)
           
           # Log text area
           self.log_text = scrolledtext.ScrolledText(self.window, height=10, width=60)
           self.log_text.pack(pady=10, padx=20, fill='both', expand=True)
           
           # Cancel button
           self.cancel_button = ttk.Button(self.window, text="Cancel", command=self.cancel)
           self.cancel_button.pack(pady=5)
           
           self.cancelled = False
           self.progress.start()

Key Methods
----------

Starting Migration
~~~~~~~~~~~~~~~~

The ``start_migration`` method initiates the migration process:

.. code-block:: python

   def start_migration(self):
       """Start the migration process"""
       # Validate inputs
       if not self.altium_dblib_path.get():
           messagebox.showerror("Error", "Please select an Altium .DbLib file")
           return
       
       if not self.output_directory.get():
           messagebox.showerror("Error", "Please select an output directory")
           return
       
       # Start migration in background thread
       progress_dialog = MigrationProgressDialog(self.root)
       
       def migration_worker():
           try:
               self.run_migration(progress_dialog)
               progress_dialog.log_message("Migration completed successfully!")
               
               # Update results tab
               self.root.after(0, self.load_migration_results)
               
           except Exception as e:
               progress_dialog.log_message(f"Migration failed: {str(e)}")
               self.logger.error(f"Migration failed: {str(e)}")
           finally:
               progress_dialog.close()
       
       thread = threading.Thread(target=migration_worker)
       thread.daemon = True
       thread.start()

Running Migration
~~~~~~~~~~~~~~~

The ``run_migration`` method performs the actual migration:

.. code-block:: python

   def run_migration(self, progress_dialog):
       """Run the actual migration process"""
       # Import migration modules
       from altium_parser import AltiumDbLibParser
       from mapping_engine import ComponentMappingEngine
       from kicad_generator import KiCADDbLibGenerator
       
       progress_dialog.update_status("Parsing Altium database configuration...")
       progress_dialog.log_message("Starting migration process")
       
       # Step 1: Parse Altium DbLib
       progress_dialog.log_message("Parsing Altium .DbLib file...")
       parser = AltiumDbLibParser()
       config = parser.parse_dblib_file(self.altium_dblib_path.get())
       
       # Step 2: Extract data
       progress_dialog.update_status("Extracting component data...")
       progress_dialog.log_message("Extracting component data from database...")
       altium_data = parser.extract_all_data(config)
       
       # Step 3: Map components
       progress_dialog.update_status("Mapping components to KiCAD format...")
       progress_dialog.log_message("Initializing component mapping engine...")
       mapper = ComponentMappingEngine(self.kicad_library_path.get())
       
       # Step 4: Generate KiCAD database
       progress_dialog.update_status("Generating KiCAD database library...")
       progress_dialog.log_message("Creating KiCAD database and library files...")
       generator = KiCADDbLibGenerator(self.output_directory.get())
       result = generator.generate(all_mappings)

Loading Results
~~~~~~~~~~~~~

The ``load_migration_results`` method loads and displays migration results:

.. code-block:: python

   def load_migration_results(self):
       """Load and display migration results"""
       try:
           # Load migration report
           report_path = Path(self.output_directory.get()) / "migration_report.json"
           with open(report_path, 'r') as f:
               report = json.load(f)
           
           # Update statistics
           self.stats_text.delete(1.0, tk.END)
           stats_text = f"""Migration Summary:
Total Components: {report['migration_summary']['total_components']}
High Confidence: {report['migration_summary']['high_confidence']}
Medium Confidence: {report['migration_summary']['medium_confidence']}
Low Confidence: {report['migration_summary']['low_confidence']}

Table Details:
"""
           # Update issues tree
           for item in self.issues_tree.get_children():
               self.issues_tree.delete(item)
           
           for recommendation in report.get('recommendations', []):
               self.issues_tree.insert('', tk.END, values=('Warning', 'General', recommendation))
           
           # Show success message
           messagebox.showinfo("Migration Complete", 
                              f"Migration completed successfully!\n"
                              f"Generated {report['migration_summary']['total_components']} components.\n"
                              f"Output saved to: {self.output_directory.get()}")

Exporting Reports
~~~~~~~~~~~~~~~

The ``export_report`` method exports migration reports:

.. code-block:: python

   def export_report(self):
       """Export migration report"""
       if not hasattr(self, 'migration_result'):
           messagebox.showwarning("Warning", "No migration results to export")
           return
       
       filename = filedialog.asksaveasfilename(
           title="Export Migration Report",
           defaultextension=".txt",
           filetypes=[("Text files", "*.txt"), ("JSON files", "*.json"), ("All files", "*.*")]
       )
       
       if filename:
           try:
               report_path = Path(self.output_directory.get()) / "migration_report.json"
               if filename.endswith('.json'):
                   # Copy JSON report
                   import shutil
                   shutil.copy2(report_path, filename)
               else:
                   # Create text report
                   with open(report_path, 'r') as f:
                       report = json.load(f)
                   
                   with open(filename, 'w') as f:
                       f.write("Altium to KiCAD Migration Report\n")
                       f.write("="*40 + "\n\n")
                       f.write(f"Migration Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                       f.write(f"Source File: {self.altium_dblib_path.get()}\n")
                       f.write(f"Output Directory: {self.output_directory.get()}\n\n")

Running the Application
---------------------

The application can be run using the ``main`` function:

.. code-block:: python

   def main():
       """Main entry point"""
       app = AltiumToKiCADMigrationApp()
       app.run()

   if __name__ == "__main__":
       main()

GUI Workflow
-----------

1. **Configuration**:
   * Select Altium .DbLib file
   * Choose output directory
   * Configure migration options

2. **Test Connection** (optional):
   * Test connection to Altium database
   * View database structure

3. **Customize Mappings** (optional):
   * Add custom symbol/footprint mappings
   * Adjust mapping rules

4. **Run Migration**:
   * Start migration process
   * Monitor progress in dialog
   * View logs in real-time

5. **View Results**:
   * Review migration statistics
   * Check for issues and warnings
   * Export detailed report

6. **Open Output** (optional):
   * Open output folder to view generated files

Integration with Other Modules
-----------------------------

The GUI integrates with other modules of the migration tool:

* ``AltiumDbLibParser``: For parsing Altium database files
* ``ComponentMappingEngine``: For mapping components
* ``KiCADDbLibGenerator``: For generating KiCAD database files

See Also
--------

* :doc:`cli` - Command Line Interface documentation
* :doc:`core` - Core API documentation
* :doc:`utils` - Utility functions documentation