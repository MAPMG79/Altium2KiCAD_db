Graphical User Interface API
===========================

This section provides detailed API documentation for the graphical user interface of the Altium to KiCAD Database Migration Tool.

GUI Module
---------

.. automodule:: migration_tool.gui
   :members:
   :undoc-members:
   :show-inheritance:

GUI Architecture
--------------

The GUI is built using Tkinter and follows a multi-tab workflow design:

1. **Welcome Screen**: Introduction and basic information
2. **Input Configuration**: Configure Altium database source
3. **Output Configuration**: Configure KiCAD library destination
4. **Migration Options**: Configure mapping and validation settings
5. **Review & Run**: Review settings and start migration
6. **Results**: View migration results and access generated files

Main Application
--------------

The main application class manages the overall GUI application:

.. code-block:: python

   class MigrationApp:
       """Main application class for the GUI."""
       
       def __init__(self, root):
           """Initialize the application."""
           self.root = root
           self.api = MigrationAPI()
           self.config = {}
           self.setup_ui()
           
       def setup_ui(self):
           """Set up the user interface."""
           # Implementation details...
           
       def run_migration(self):
           """Run the migration process."""
           # Implementation details...
           
       def show_results(self, result):
           """Show migration results."""
           # Implementation details...

Tab Classes
----------

Each tab in the GUI is implemented as a separate class:

.. code-block:: python

   class WelcomeTab:
       """Welcome tab with introduction and basic information."""
       
       def __init__(self, parent, controller):
           """Initialize the tab."""
           self.parent = parent
           self.controller = controller
           self.frame = ttk.Frame(parent)
           self.setup_ui()
           
       def setup_ui(self):
           """Set up the user interface for this tab."""
           # Implementation details...

   class InputConfigTab:
       """Input configuration tab for Altium database source."""
       
       def __init__(self, parent, controller):
           """Initialize the tab."""
           self.parent = parent
           self.controller = controller
           self.frame = ttk.Frame(parent)
           self.setup_ui()
           
       def setup_ui(self):
           """Set up the user interface for this tab."""
           # Implementation details...
           
       def test_connection(self):
           """Test the database connection."""
           # Implementation details...

   # Additional tab classes...

Custom Widgets
------------

The GUI includes several custom widgets for specific functionality:

.. code-block:: python

   class MappingRulesEditor:
       """Widget for editing mapping rules."""
       
       def __init__(self, parent):
           """Initialize the widget."""
           self.parent = parent
           self.frame = ttk.Frame(parent)
           self.rules = []
           self.setup_ui()
           
       def setup_ui(self):
           """Set up the user interface for this widget."""
           # Implementation details...
           
       def add_rule(self):
           """Add a new mapping rule."""
           # Implementation details...
           
       def remove_rule(self):
           """Remove a mapping rule."""
           # Implementation details...
           
       def get_rules(self):
           """Get the current mapping rules."""
           # Implementation details...

   class ProgressDialog:
       """Dialog for showing migration progress."""
       
       def __init__(self, parent, title, max_value):
           """Initialize the dialog."""
           self.parent = parent
           self.dialog = tk.Toplevel(parent)
           self.dialog.title(title)
           self.max_value = max_value
           self.setup_ui()
           
       def setup_ui(self):
           """Set up the user interface for this dialog."""
           # Implementation details...
           
       def update_progress(self, value, message=None):
           """Update the progress bar."""
           # Implementation details...
           
       def close(self):
           """Close the dialog."""
           # Implementation details...

Utility Functions
--------------

The GUI module includes several utility functions:

.. code-block:: python

   def show_error(parent, title, message):
       """Show an error dialog."""
       messagebox.showerror(title, message, parent=parent)
       
   def show_info(parent, title, message):
       """Show an information dialog."""
       messagebox.showinfo(title, message, parent=parent)
       
   def ask_directory(parent, title):
       """Ask the user to select a directory."""
       return filedialog.askdirectory(title=title, parent=parent)
       
   def ask_file(parent, title, filetypes):
       """Ask the user to select a file."""
       return filedialog.askopenfilename(title=title, filetypes=filetypes, parent=parent)