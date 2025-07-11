#!/usr/bin/env python3
"""Debug version of GUI launcher to diagnose issues"""

import sys
import tkinter as tk
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
if project_root not in sys.path:
    sys.path.insert(0, str(project_root))

print("Starting GUI debug test...")

# Test basic tkinter
try:
    print("Testing basic tkinter...")
    root = tk.Tk()
    root.title("Test Window")
    root.geometry("400x300")
    
    label = tk.Label(root, text="If you can see this, tkinter is working!")
    label.pack(pady=50)
    
    button = tk.Button(root, text="Close", command=root.quit)
    button.pack()
    
    print("Tkinter test window created. Starting mainloop...")
    root.mainloop()
    print("Tkinter test completed successfully.")
    
except Exception as e:
    print(f"Tkinter test failed: {e}")
    sys.exit(1)

# Now test the actual GUI
print("\nTesting migration tool GUI...")

try:
    from migration_tool.gui import MigrationToolMainWindow
    print("Successfully imported MigrationToolMainWindow")
    
    # Create the main window with debug output
    print("Creating main window...")
    app = MigrationToolMainWindow()
    print("Main window created successfully")
    
    # Check if window exists
    print(f"Window exists: {app.winfo_exists()}")
    print(f"Window geometry: {app.geometry()}")
    
    # Start the mainloop
    print("Starting mainloop...")
    app.mainloop()
    print("Mainloop ended")
    
except Exception as e:
    print(f"Error during GUI initialization: {e}")
    import traceback
    traceback.print_exc()