import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import json
import os
from pathlib import Path
import logging
from datetime import datetime

# Import our migration modules
from altium_parser import AltiumDbLibParser
from mapping_engine import ComponentMappingEngine
from kicad_generator import KiCADDbLibGenerator

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
    
    def update_status(self, message):
        """Update status message"""
        self.status_label.config(text=message)
        self.window.update()
    
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.window.update()
    
    def cancel(self):
        """Cancel the operation"""
        self.cancelled = True
        self.window.destroy()
    
    def close(self):
        """Close the dialog"""
        self.progress.stop()
        self.window.destroy()

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
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('migration.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Configuration tab
        self.setup_config_tab(notebook)
        
        # Mapping tab
        self.setup_mapping_tab(notebook)
        
        # Results tab
        self.setup_results_tab(notebook)
        
        # About tab
        self.setup_about_tab(notebook)
    
    def run_migration(self):
        """Run the migration process"""
        # Show progress dialog
        progress_dialog = MigrationProgressDialog(self.root)
        
        def migration_thread():
            try:
                # Step 1: Parse Altium DbLib
                progress_dialog.update_status("Parsing Altium DbLib file...")
                progress_dialog.log_message(f"Opening {self.altium_dblib_path.get()}")
                
                self.parser = AltiumDbLibParser()
                altium_config = self.parser.parse_dblib_file(self.altium_dblib_path.get())
                
                progress_dialog.log_message(f"Detected database type: {altium_config['database_type']}")
                progress_dialog.log_message(f"Found {len(altium_config['tables'])} tables")
                
                # Step 2: Extract component data
                progress_dialog.update_status("Extracting component data...")
                all_data = self.parser.extract_all_data(altium_config)
                
                total_components = sum(len(table_data['data']) for table_data in all_data.values())
                progress_dialog.log_message(f"Extracted {total_components} components")
                
                # Step 3: Map components
                progress_dialog.update_status("Mapping components to KiCAD...")
                self.mapper = ComponentMappingEngine(self.kicad_library_path.get())
                
                component_mappings = {}
                for table_name, table_data in all_data.items():
                    progress_dialog.log_message(f"Mapping components from {table_name}...")
                    mappings = self.mapper.map_table_data(table_name, table_data)
                    component_mappings[table_name] = mappings
                    progress_dialog.log_message(f"Mapped {len(mappings)} components from {table_name}")
                
                # Step 4: Generate KiCAD library
                progress_dialog.update_status("Generating KiCAD database library...")
                self.generator = KiCADDbLibGenerator(self.output_directory.get())
                result = self.generator.generate(component_mappings)
                
                progress_dialog.log_message(f"Generated KiCAD database library at {result['database_path']}")
                progress_dialog.log_message(f"Generated KiCAD DbLib file at {result['dblib_path']}")
                
                # Complete
                progress_dialog.update_status("Migration completed successfully!")
                
            except Exception as e:
                progress_dialog.log_message(f"Error: {str(e)}")
                progress_dialog.update_status("Migration failed!")
                self.logger.exception("Migration failed")
            finally:
                # Close the progress dialog
                self.root.after(0, progress_dialog.close)
        
        # Start migration in a separate thread
        thread = threading.Thread(target=migration_thread)
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    app = AltiumToKiCADMigrationApp()
    app.root.mainloop()