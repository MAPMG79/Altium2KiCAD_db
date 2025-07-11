#!/usr/bin/env python3
"""
Graphical User Interface for Altium to KiCAD Database Migration Tool.

This module provides a comprehensive GUI for the migration tool using tkinter.
"""

import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import webbrowser
import platform
import subprocess

from migration_tool.core.altium_parser import AltiumDbLibParser
from migration_tool.core.mapping_engine import ComponentMappingEngine
from migration_tool.core.kicad_generator import KiCADDbLibGenerator
from migration_tool.utils.config_manager import ConfigManager
from migration_tool.utils.database_utils import create_connection, execute_query, table_exists
from migration_tool.utils.logging_utils import setup_logging, get_logger


class LoggingHandler(logging.Handler):
    """Custom logging handler that redirects logs to a tkinter Text widget."""
    
    def __init__(self, text_widget):
        """Initialize with a text widget."""
        logging.Handler.__init__(self)
        self.text_widget = text_widget
    
    def emit(self, record):
        """Emit a log record to the text widget."""
        msg = self.format(record)
        
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.configure(state='disabled')
            self.text_widget.yview(tk.END)
        
        # Schedule append in the main thread
        self.text_widget.after(0, append)


class MigrationProgressDialog:
    """Progress dialog for migration operations."""
    
    def __init__(self, parent):
        """Initialize progress dialog."""
        self.window = tk.Toplevel(parent)
        self.window.title("Migration Progress")
        self.window.geometry("500x300")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Progress bar
        self.progress_frame = ttk.Frame(self.window)
        self.progress_frame.pack(pady=10, padx=20, fill='x')
        
        self.progress_label = tk.Label(self.progress_frame, text="Overall Progress:")
        self.progress_label.pack(anchor='w')
        
        self.progress = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.progress.pack(fill='x')
        
        # Task progress
        self.task_label = tk.Label(self.progress_frame, text="Current Task:")
        self.task_label.pack(anchor='w', pady=(10, 0))
        
        self.task_progress = ttk.Progressbar(self.progress_frame, mode='determinate')
        self.task_progress.pack(fill='x')
        
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
        """Update status message."""
        self.status_label.config(text=message)
        self.window.update()
    
    def update_task_progress(self, value, maximum=100):
        """Update task-specific progress bar."""
        self.task_progress['value'] = value
        self.task_progress['maximum'] = maximum
        self.window.update()
    
    def log_message(self, message):
        """Add message to log."""
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.configure(state='disabled')
        self.log_text.yview(tk.END)
        self.window.update()
    
    def cancel(self):
        """Cancel the operation."""
        self.cancelled = True
        self.log_message("Cancelling operation... Please wait.")
        self.cancel_button.config(state='disabled')
    
    def close(self):
        """Close the dialog."""
        self.progress.stop()
        self.window.destroy()


class DatabaseConnectionDialog:
    """Dialog for configuring database connections."""
    
    def __init__(self, parent, connection_string=None, db_type=None):
        """Initialize database connection dialog."""
        self.window = tk.Toplevel(parent)
        self.window.title("Database Connection Configuration")
        self.window.geometry("500x400")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.result = None
        self.connection_string = connection_string
        self.db_type = tk.StringVar(value=db_type or "sqlite")
        
        # Database type selection
        type_frame = ttk.LabelFrame(self.window, text="Database Type", padding=10)
        type_frame.pack(fill='x', padx=20, pady=10)
        
        db_types = [
            ("SQLite", "sqlite"),
            ("Microsoft Access", "access"),
            ("SQL Server", "sqlserver"),
            ("MySQL", "mysql"),
            ("PostgreSQL", "postgresql")
        ]
        
        for i, (text, value) in enumerate(db_types):
            ttk.Radiobutton(
                type_frame, 
                text=text, 
                variable=self.db_type, 
                value=value,
                command=self.update_connection_form
            ).grid(row=i, column=0, sticky='w', padx=5, pady=2)
        
        # Connection parameters frame
        self.params_frame = ttk.LabelFrame(self.window, text="Connection Parameters", padding=10)
        self.params_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # SQLite parameters
        self.sqlite_frame = ttk.Frame(self.params_frame)
        self.sqlite_path = tk.StringVar()
        ttk.Label(self.sqlite_frame, text="Database File:").grid(row=0, column=0, sticky='w', pady=5)
        ttk.Entry(self.sqlite_frame, textvariable=self.sqlite_path, width=40).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.sqlite_frame, text="Browse", command=self.browse_sqlite_file).grid(row=0, column=2, padx=5, pady=5)
        
        # ODBC parameters
        self.odbc_frame = ttk.Frame(self.params_frame)
        
        # Server parameters
        self.server = tk.StringVar()
        self.database = tk.StringVar()
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.port = tk.StringVar()
        self.dsn = tk.StringVar()
        
        ttk.Label(self.odbc_frame, text="Server:").grid(row=0, column=0, sticky='w', pady=5)
        ttk.Entry(self.odbc_frame, textvariable=self.server, width=40).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.odbc_frame, text="Database:").grid(row=1, column=0, sticky='w', pady=5)
        ttk.Entry(self.odbc_frame, textvariable=self.database, width=40).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(self.odbc_frame, text="Username:").grid(row=2, column=0, sticky='w', pady=5)
        ttk.Entry(self.odbc_frame, textvariable=self.username, width=40).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(self.odbc_frame, text="Password:").grid(row=3, column=0, sticky='w', pady=5)
        ttk.Entry(self.odbc_frame, textvariable=self.password, width=40, show='*').grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(self.odbc_frame, text="Port:").grid(row=4, column=0, sticky='w', pady=5)
        ttk.Entry(self.odbc_frame, textvariable=self.port, width=40).grid(row=4, column=1, padx=5, pady=5)
        
        ttk.Label(self.odbc_frame, text="DSN:").grid(row=5, column=0, sticky='w', pady=5)
        ttk.Entry(self.odbc_frame, textvariable=self.dsn, width=40).grid(row=5, column=1, padx=5, pady=5)
        ttk.Label(self.odbc_frame, text="(Optional)").grid(row=5, column=2, sticky='w')
        
        # Connection string preview
        preview_frame = ttk.LabelFrame(self.window, text="Connection String Preview", padding=10)
        preview_frame.pack(fill='x', padx=20, pady=10)
        
        self.preview_text = tk.Text(preview_frame, height=3, width=50, wrap='word')
        self.preview_text.pack(fill='x')
        
        # Buttons
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(button_frame, text="Test Connection", command=self.test_connection).pack(side='left', padx=5)
        ttk.Button(button_frame, text="OK", command=self.save).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side='right', padx=5)
        
        # Initialize form based on current connection
        if connection_string:
            self.parse_connection_string(connection_string)
        
        self.update_connection_form()
    
    def update_connection_form(self):
        """Update the connection form based on selected database type."""
        # Clear frames
        for widget in self.params_frame.winfo_children():
            widget.pack_forget()
        
        # Show appropriate frame
        if self.db_type.get() == "sqlite":
            self.sqlite_frame.pack(fill='both', expand=True)
        else:
            self.odbc_frame.pack(fill='both', expand=True)
        
        # Update connection string preview
        self.update_preview()
    
    def update_preview(self):
        """Update connection string preview."""
        conn_str = self.build_connection_string()
        
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, conn_str)
    
    def build_connection_string(self):
        """Build connection string based on form values."""
        db_type = self.db_type.get()
        
        if db_type == "sqlite":
            return f"sqlite:///{self.sqlite_path.get()}"
        
        elif db_type == "access":
            if self.dsn.get():
                return f"DSN={self.dsn.get()}"
            else:
                return f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.database.get()}"
        
        elif db_type == "sqlserver":
            if self.dsn.get():
                return f"DSN={self.dsn.get()}"
            else:
                conn_str = f"Driver={{ODBC Driver 17 for SQL Server}};Server={self.server.get()}"
                if self.port.get():
                    conn_str += f",{self.port.get()}"
                conn_str += f";Database={self.database.get()}"
                
                if self.username.get():
                    conn_str += f";UID={self.username.get()};PWD={self.password.get()}"
                else:
                    conn_str += ";Trusted_Connection=yes"
                
                return conn_str
        
        elif db_type == "mysql":
            if self.dsn.get():
                return f"DSN={self.dsn.get()}"
            else:
                conn_str = f"Driver={{MySQL ODBC Driver}};Server={self.server.get()}"
                if self.port.get():
                    conn_str += f";Port={self.port.get()}"
                conn_str += f";Database={self.database.get()}"
                
                if self.username.get():
                    conn_str += f";UID={self.username.get()};PWD={self.password.get()}"
                
                return conn_str
        
        elif db_type == "postgresql":
            if self.dsn.get():
                return f"DSN={self.dsn.get()}"
            else:
                conn_str = f"Driver={{PostgreSQL ODBC Driver}};Server={self.server.get()}"
                if self.port.get():
                    conn_str += f";Port={self.port.get()}"
                conn_str += f";Database={self.database.get()}"
                
                if self.username.get():
                    conn_str += f";UID={self.username.get()};PWD={self.password.get()}"
                
                return conn_str
        
        return ""
    
    def parse_connection_string(self, conn_str):
        """Parse connection string to populate form fields."""
        if "sqlite:///" in conn_str:
            self.db_type.set("sqlite")
            self.sqlite_path.set(conn_str.replace("sqlite:///", ""))
        
        elif "DSN=" in conn_str:
            # Extract DSN
            self.dsn.set(conn_str.replace("DSN=", "").split(";")[0])
            
            # Try to determine database type
            if "SQL Server" in conn_str:
                self.db_type.set("sqlserver")
            elif "MySQL" in conn_str:
                self.db_type.set("mysql")
            elif "PostgreSQL" in conn_str:
                self.db_type.set("postgresql")
            elif "Access" in conn_str:
                self.db_type.set("access")
        
        elif "Driver=" in conn_str:
            # Extract driver and determine type
            if "SQL Server" in conn_str:
                self.db_type.set("sqlserver")
            elif "MySQL" in conn_str:
                self.db_type.set("mysql")
            elif "PostgreSQL" in conn_str:
                self.db_type.set("postgresql")
            elif "Access" in conn_str:
                self.db_type.set("access")
                if "DBQ=" in conn_str:
                    self.database.set(conn_str.split("DBQ=")[1].split(";")[0])
            
            # Extract other parameters
            if "Server=" in conn_str:
                server = conn_str.split("Server=")[1].split(";")[0]
                if "," in server:  # Handle SQL Server port
                    server_parts = server.split(",")
                    self.server.set(server_parts[0])
                    if len(server_parts) > 1:
                        self.port.set(server_parts[1])
                else:
                    self.server.set(server)
            
            if "Port=" in conn_str:
                self.port.set(conn_str.split("Port=")[1].split(";")[0])
            
            if "Database=" in conn_str:
                self.database.set(conn_str.split("Database=")[1].split(";")[0])
            
            if "UID=" in conn_str:
                self.username.set(conn_str.split("UID=")[1].split(";")[0])
            
            if "PWD=" in conn_str:
                self.password.set(conn_str.split("PWD=")[1].split(";")[0])
    
    def browse_sqlite_file(self):
        """Browse for SQLite database file."""
        filename = filedialog.askopenfilename(
            title="Select SQLite Database File",
            filetypes=[
                ("SQLite Database", "*.db *.sqlite *.sqlite3"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.sqlite_path.set(filename)
            self.update_preview()
    
    def test_connection(self):
        """Test database connection."""
        conn_str = self.build_connection_string()
        db_type = self.db_type.get()
        
        try:
            conn = create_connection(conn_str, db_type)
            
            # Get table count
            if db_type == "sqlite":
                query = "SELECT name FROM sqlite_master WHERE type='table'"
                tables = execute_query(conn, query)
                table_count = len(tables)
            else:
                # For other database types, try to get table list
                cursor = conn.cursor()
                tables = list(cursor.tables())
                table_count = len(tables)
                cursor.close()
            
            conn.close()
            
            messagebox.showinfo(
                "Connection Successful", 
                f"Successfully connected to the database!\nFound {table_count} tables."
            )
            
        except Exception as e:
            messagebox.showerror(
                "Connection Failed", 
                f"Failed to connect to the database:\n{str(e)}"
            )
    
    def save(self):
        """Save connection settings and close dialog."""
        self.result = {
            'connection_string': self.build_connection_string(),
            'db_type': self.db_type.get()
        }
        self.window.destroy()
    
    def cancel(self):
        """Cancel and close dialog."""
        self.result = None
        self.window.destroy()


class MappingRuleDialog:
    """Dialog for editing mapping rules."""
    
    def __init__(self, parent, rule_type="symbol", existing_rules=None):
        """Initialize mapping rule dialog."""
        self.window = tk.Toplevel(parent)
        self.window.title(f"{rule_type.title()} Mapping Rules")
        self.window.geometry("600x500")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.rule_type = rule_type
        self.existing_rules = existing_rules or {}
        self.result = None
        
        # Main frame
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill='both', expand=True)
        
        # Rules list
        rules_frame = ttk.LabelFrame(main_frame, text="Mapping Rules", padding=10)
        rules_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create treeview for rules
        if rule_type == "category":
            columns = ('altium', 'category', 'subcategory')
            headings = ('Altium Category', 'KiCAD Category', 'KiCAD Subcategory')
        else:
            columns = ('altium', 'kicad')
            headings = ('Altium Value', 'KiCAD Value')
        
        self.rules_tree = ttk.Treeview(rules_frame, columns=columns, show='headings')
        
        for col, heading in zip(columns, headings):
            self.rules_tree.heading(col, text=heading)
            self.rules_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(rules_frame, orient='vertical', command=self.rules_tree.yview)
        self.rules_tree.configure(yscrollcommand=scrollbar.set)
        
        self.rules_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Populate rules
        self.populate_rules()
        
        # Edit frame
        edit_frame = ttk.LabelFrame(main_frame, text="Add/Edit Rule", padding=10)
        edit_frame.pack(fill='x', padx=5, pady=5)
        
        # Input fields
        if rule_type == "category":
            ttk.Label(edit_frame, text="Altium Category:").grid(row=0, column=0, sticky='w', pady=5)
            self.altium_value = tk.StringVar()
            ttk.Entry(edit_frame, textvariable=self.altium_value, width=30).grid(row=0, column=1, padx=5, pady=5)
            
            ttk.Label(edit_frame, text="KiCAD Category:").grid(row=1, column=0, sticky='w', pady=5)
            self.kicad_category = tk.StringVar()
            ttk.Entry(edit_frame, textvariable=self.kicad_category, width=30).grid(row=1, column=1, padx=5, pady=5)
            
            ttk.Label(edit_frame, text="KiCAD Subcategory:").grid(row=2, column=0, sticky='w', pady=5)
            self.kicad_subcategory = tk.StringVar()
            ttk.Entry(edit_frame, textvariable=self.kicad_subcategory, width=30).grid(row=2, column=1, padx=5, pady=5)
            
            ttk.Label(edit_frame, text="Keywords (comma separated):").grid(row=3, column=0, sticky='w', pady=5)
            self.keywords = tk.StringVar()
            ttk.Entry(edit_frame, textvariable=self.keywords, width=30).grid(row=3, column=1, padx=5, pady=5)
        else:
            ttk.Label(edit_frame, text=f"Altium {rule_type.title()}:").grid(row=0, column=0, sticky='w', pady=5)
            self.altium_value = tk.StringVar()
            ttk.Entry(edit_frame, textvariable=self.altium_value, width=30).grid(row=0, column=1, padx=5, pady=5)
            
            ttk.Label(edit_frame, text=f"KiCAD {rule_type.title()}:").grid(row=1, column=0, sticky='w', pady=5)
            self.kicad_value = tk.StringVar()
            ttk.Entry(edit_frame, textvariable=self.kicad_value, width=30).grid(row=1, column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(edit_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Add Rule", command=self.add_rule).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Update Selected", command=self.update_rule).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_rule).pack(side='left', padx=5)
        
        # Selection event
        self.rules_tree.bind('<<TreeviewSelect>>', self.on_rule_select)
        
        # Bottom buttons
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill='x', pady=10)
        
        ttk.Button(bottom_frame, text="Save Rules", command=self.save_rules).pack(side='right', padx=5)
        ttk.Button(bottom_frame, text="Cancel", command=self.cancel).pack(side='right', padx=5)
        ttk.Button(bottom_frame, text="Import Rules", command=self.import_rules).pack(side='left', padx=5)
        ttk.Button(bottom_frame, text="Export Rules", command=self.export_rules).pack(side='left', padx=5)
    
    def populate_rules(self):
        """Populate rules treeview with existing rules."""
        # Clear existing items
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
        
        # Add rules
        if self.rule_type == "category":
            for altium_cat, details in self.existing_rules.items():
                if isinstance(details, dict) and 'category' in details:
                    self.rules_tree.insert('', tk.END, values=(
                        altium_cat, 
                        details.get('category', ''), 
                        details.get('subcategory', '')
                    ))
        else:
            for altium_val, kicad_val in self.existing_rules.items():
                self.rules_tree.insert('', tk.END, values=(altium_val, kicad_val))
    
    def on_rule_select(self, event):
        """Handle rule selection event."""
        selected = self.rules_tree.selection()
        if not selected:
            return
        
        # Get values
        values = self.rules_tree.item(selected[0], 'values')
        
        # Set form values
        self.altium_value.set(values[0])
        
        if self.rule_type == "category":
            self.kicad_category.set(values[1])
            self.kicad_subcategory.set(values[2])
            
            # Get keywords
            altium_cat = values[0]
            if altium_cat in self.existing_rules and 'keywords' in self.existing_rules[altium_cat]:
                keywords = self.existing_rules[altium_cat]['keywords']
                self.keywords.set(', '.join(keywords))
            else:
                self.keywords.set('')
        else:
            self.kicad_value.set(values[1])
    
    def add_rule(self):
        """Add new mapping rule."""
        altium_val = self.altium_value.get().strip()
        
        if not altium_val:
            messagebox.showwarning("Warning", "Altium value cannot be empty")
            return
        
        if self.rule_type == "category":
            kicad_cat = self.kicad_category.get().strip()
            kicad_subcat = self.kicad_subcategory.get().strip()
            keywords_str = self.keywords.get().strip()
            
            if not kicad_cat:
                messagebox.showwarning("Warning", "KiCAD category cannot be empty")
                return
            
            # Parse keywords
            keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
            
            # Add to rules
            self.existing_rules[altium_val] = {
                'category': kicad_cat,
                'subcategory': kicad_subcat,
                'keywords': keywords
            }
            
            # Add to treeview
            self.rules_tree.insert('', tk.END, values=(altium_val, kicad_cat, kicad_subcat))
        
        else:
            kicad_val = self.kicad_value.get().strip()
            
            if not kicad_val:
                messagebox.showwarning("Warning", "KiCAD value cannot be empty")
                return
            
            # Add to rules
            self.existing_rules[altium_val] = kicad_val
            
            # Add to treeview
            self.rules_tree.insert('', tk.END, values=(altium_val, kicad_val))
        
        # Clear form
        self.clear_form()
    
    def update_rule(self):
        """Update selected mapping rule."""
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No rule selected")
            return
        
        altium_val = self.altium_value.get().strip()
        
        if not altium_val:
            messagebox.showwarning("Warning", "Altium value cannot be empty")
            return
        
        # Get original altium value
        original_altium = self.rules_tree.item(selected[0], 'values')[0]
        
        if self.rule_type == "category":
            kicad_cat = self.kicad_category.get().strip()
            kicad_subcat = self.kicad_subcategory.get().strip()
            keywords_str = self.keywords.get().strip()
            
            if not kicad_cat:
                messagebox.showwarning("Warning", "KiCAD category cannot be empty")
                return
            
            # Parse keywords
            keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
            
            # Remove original rule if altium value changed
            if original_altium != altium_val and original_altium in self.existing_rules:
                del self.existing_rules[original_altium]
            
            # Update rules
            self.existing_rules[altium_val] = {
                'category': kicad_cat,
                'subcategory': kicad_subcat,
                'keywords': keywords
            }
            
            # Update treeview
            self.rules_tree.item(selected[0], values=(altium_val, kicad_cat, kicad_subcat))
        
        else:
            kicad_val = self.kicad_value.get().strip()
            
            if not kicad_val:
                messagebox.showwarning("Warning", "KiCAD value cannot be empty")
                return
            
            # Remove original rule if altium value changed
            if original_altium != altium_val and original_altium in self.existing_rules:
                del self.existing_rules[original_altium]
            
            # Update rules
            self.existing_rules[altium_val] = kicad_val
            
            # Update treeview
            self.rules_tree.item(selected[0], values=(altium_val, kicad_val))
        
        # Clear form
        self.clear_form()
    
    def delete_rule(self):
        """Delete selected mapping rule."""
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No rule selected")
            return
        
        # Get altium value
        altium_val = self.rules_tree.item(selected[0], 'values')[0]
        
        # Remove from rules
        if altium_val in self.existing_rules:
            del self.existing_rules[altium_val]
        
        # Remove from treeview
        self.rules_tree.delete(selected[0])
        
        # Clear form
        self.clear_form()
    
    def clear_form(self):
        """Clear form fields."""
        self.altium_value.set('')
        
        if self.rule_type == "category":
            self.kicad_category.set('')
            self.kicad_subcategory.set('')
            self.keywords.set('')
        else:
            self.kicad_value.set('')
    
    def import_rules(self):
        """Import mapping rules from file."""
        filename = filedialog.askopenfilename(
            title=f"Import {self.rule_type.title()} Mapping Rules",
            filetypes=[
                ("YAML files", "*.yaml *.yml"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if not filename:
            return
        
        try:
            # Determine file type
            if filename.lower().endswith(('.yaml', '.yml')):
                import yaml
                with open(filename, 'r') as f:
                    rules = yaml.safe_load(f)
            elif filename.lower().endswith('.json'):
                import json
                with open(filename, 'r') as f:
                    rules = json.load(f)
            else:
                messagebox.showerror("Error", "Unsupported file format")
                return
            
            # Update rules
            if rules:
                self.existing_rules = rules
                self.populate_rules()
                messagebox.showinfo("Success", f"Imported {len(rules)} mapping rules")
            else:
                messagebox.showwarning("Warning", "No rules found in file")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import rules: {str(e)}")
    
    def export_rules(self):
        """Export mapping rules to file."""
        if not self.existing_rules:
            messagebox.showwarning("Warning", "No rules to export")
            return
        
        filename = filedialog.asksaveasfilename(
            title=f"Export {self.rule_type.title()} Mapping Rules",
            defaultextension=".yaml",
            filetypes=[
                ("YAML files", "*.yaml"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if not filename:
            return
        
        try:
            # Determine file type
            if filename.lower().endswith(('.yaml', '.yml')):
                import yaml
                with open(filename, 'w') as f:
                    yaml.dump(self.existing_rules, f, default_flow_style=False)
            elif filename.lower().endswith('.json'):
                import json
                with open(filename, 'w') as f:
                    json.dump(self.existing_rules, f, indent=2)
            else:
                # Default to YAML
                import yaml
                with open(filename, 'w') as f:
                    yaml.dump(self.existing_rules, f, default_flow_style=False)
            
            messagebox.showinfo("Success", f"Exported {len(self.existing_rules)} mapping rules")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export rules: {str(e)}")
    
    def save_rules(self):
        """Save rules and close dialog."""
        self.result = self.existing_rules
        self.window.destroy()
    
    def cancel(self):
        """Cancel and close dialog."""
        self.result = None
        self.window.destroy()


class BatchProcessDialog:
    """Dialog for batch processing multiple databases."""
    
    def __init__(self, parent, config_manager=None):
        """Initialize batch processing dialog."""
        self.window = tk.Toplevel(parent)
        self.window.title("Batch Processing")
        self.window.geometry("700x500")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.parent = parent
        self.config_manager = config_manager or ConfigManager()
        self.result = None
        self.files = []
        
        # Main frame
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill='both', expand=True)
        
        # Input files section
        input_frame = ttk.LabelFrame(main_frame, text="Input Files", padding=10)
        input_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Files list
        self.files_list = tk.Listbox(input_frame, height=10, width=70)
        scrollbar = ttk.Scrollbar(input_frame, orient='vertical', command=self.files_list.yview)
        self.files_list.configure(yscrollcommand=scrollbar.set)
        
        self.files_list.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # File buttons
        file_buttons = ttk.Frame(input_frame)
        file_buttons.pack(fill='x', pady=5)
        
        ttk.Button(file_buttons, text="Add Files", command=self.add_files).pack(side='left', padx=5)
        ttk.Button(file_buttons, text="Add Directory", command=self.add_directory).pack(side='left', padx=5)
        ttk.Button(file_buttons, text="Remove Selected", command=self.remove_file).pack(side='left', padx=5)
        ttk.Button(file_buttons, text="Clear All", command=self.clear_files).pack(side='left', padx=5)
        
        # Output settings
        output_frame = ttk.LabelFrame(main_frame, text="Output Settings", padding=10)
        output_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(output_frame, text="Output Directory:").grid(row=0, column=0, sticky='w', pady=5)
        self.output_dir = tk.StringVar(value="output")
        ttk.Entry(output_frame, textvariable=self.output_dir, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(output_frame, text="Browse", command=self.browse_output_dir).grid(row=0, column=2, padx=5, pady=5)
        
        # Processing options
        options_frame = ttk.LabelFrame(main_frame, text="Processing Options", padding=10)
        options_frame.pack(fill='x', padx=5, pady=5)
        
        # Parallel processing
        self.parallel = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Enable parallel processing", variable=self.parallel).grid(row=0, column=0, sticky='w', pady=2)
        
        ttk.Label(options_frame, text="Worker threads:").grid(row=0, column=1, sticky='w', padx=(20, 5), pady=2)
        self.threads = tk.StringVar(value="4")
        ttk.Spinbox(options_frame, from_=1, to=16, textvariable=self.threads, width=5).grid(row=0, column=2, sticky='w', pady=2)
        
        # Create subdirectories
        self.create_subdirs = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Create subdirectory for each file", variable=self.create_subdirs).grid(row=1, column=0, columnspan=3, sticky='w', pady=2)
        
        # Generate report
        self.generate_report = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Generate batch processing report", variable=self.generate_report).grid(row=2, column=0, columnspan=3, sticky='w', pady=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="Start Processing", command=self.start_processing).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Save Batch", command=self.save_batch).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Load Batch", command=self.load_batch).pack(side='left', padx=5)
    
    def add_files(self):
        """Add files to batch."""
        filenames = filedialog.askopenfilenames(
            title="Select Altium .DbLib Files",
            filetypes=[("Altium Database Library", "*.DbLib"), ("All files", "*.*")]
        )
        
        if not filenames:
            return
        
        for filename in filenames:
            if filename not in self.files:
                self.files.append(filename)
                self.files_list.insert(tk.END, filename)
    
    def add_directory(self):
        """Add all .DbLib files from a directory."""
        directory = filedialog.askdirectory(title="Select Directory with .DbLib Files")
        
        if not directory:
            return
        
        # Find all .DbLib files
        import glob
        pattern = os.path.join(directory, "*.DbLib")
        found_files = glob.glob(pattern)
        
        if not found_files:
            messagebox.showinfo("Information", "No .DbLib files found in the selected directory")
            return
        
        # Add files
        for filename in found_files:
            if filename not in self.files:
                self.files.append(filename)
                self.files_list.insert(tk.END, filename)
        
        messagebox.showinfo("Files Added", f"Added {len(found_files)} .DbLib files from {directory}")
    
    def remove_file(self):
        """Remove selected file from batch."""
        selected = self.files_list.curselection()
        if not selected:
            return
        
        # Remove from list and files
        index = selected[0]
        filename = self.files_list.get(index)
        self.files.remove(filename)
        self.files_list.delete(index)
    
    def clear_files(self):
        """Clear all files from batch."""
        self.files = []
        self.files_list.delete(0, tk.END)
    
    def browse_output_dir(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir.set(directory)
    
    def save_batch(self):
        """Save batch configuration to file."""
        if not self.files:
            messagebox.showwarning("Warning", "No files in batch")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Batch Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            batch_config = {
                'files': self.files,
                'output_dir': self.output_dir.get(),
                'parallel': self.parallel.get(),
                'threads': int(self.threads.get()),
                'create_subdirs': self.create_subdirs.get(),
                'generate_report': self.generate_report.get()
            }
            
            with open(filename, 'w') as f:
                json.dump(batch_config, f, indent=2)
            
            messagebox.showinfo("Success", f"Batch configuration saved to {filename}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save batch configuration: {str(e)}")
    
    def load_batch(self):
        """Load batch configuration from file."""
        filename = filedialog.askopenfilename(
            title="Load Batch Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r') as f:
                batch_config = json.load(f)
            
            # Update UI
            self.clear_files()
            
            for file in batch_config.get('files', []):
                if os.path.exists(file):
                    self.files.append(file)
                    self.files_list.insert(tk.END, file)
            
            self.output_dir.set(batch_config.get('output_dir', 'output'))
            self.parallel.set(batch_config.get('parallel', True))
            self.threads.set(str(batch_config.get('threads', 4)))
            self.create_subdirs.set(batch_config.get('create_subdirs', True))
            self.generate_report.set(batch_config.get('generate_report', True))
            
            messagebox.showinfo("Success", f"Loaded {len(self.files)} files from batch configuration")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load batch configuration: {str(e)}")
    
    def start_processing(self):
        """Start batch processing."""
        if not self.files:
            messagebox.showwarning("Warning", "No files to process")
            return
        
        # Prepare batch configuration
        batch_config = {
            'files': self.files,
            'output_dir': self.output_dir.get(),
            'parallel': self.parallel.get(),
            'threads': int(self.threads.get()),
            'create_subdirs': self.create_subdirs.get(),
            'generate_report': self.generate_report.get()
        }
        
        self.result = batch_config
        self.window.destroy()
    
    def cancel(self):
        """Cancel and close dialog."""
        self.result = None
        self.window.destroy()


class HelpDialog:
    """Help dialog with documentation."""
    
    def __init__(self, parent, topic="general"):
        """Initialize help dialog."""
        self.window = tk.Toplevel(parent)
        self.window.title("Altium to KiCAD Migration Tool Help")
        self.window.geometry("800x600")
        self.window.transient(parent)
        
        # Main frame
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill='both', expand=True)
        
        # Create notebook for help topics
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)
        
        # General help
        general_frame = ttk.Frame(notebook, padding=10)
        notebook.add(general_frame, text="General")
        
        general_text = """
Altium to KiCAD Database Migration Tool
======================================

This tool helps migrate component databases from Altium Designer's .DbLib format to KiCAD's .kicad_dbl format.

Basic Usage:
-----------
1. Select your Altium .DbLib file
2. Configure the output directory
3. Set migration options
4. Start the migration process

The tool will:
- Parse the Altium database structure
- Extract component data
- Map Altium components to KiCAD equivalents
- Generate a SQLite database for KiCAD
- Create a .kicad_dbl file for use in KiCAD
- Generate a detailed migration report

For more detailed instructions, see the other help topics.
"""
        general_label = tk.Label(general_frame, text=general_text, justify='left', wraplength=700)
        general_label.pack(fill='both', expand=True)
        
        # Database configuration help
        db_frame = ttk.Frame(notebook, padding=10)
        notebook.add(db_frame, text="Database Configuration")
        
        db_text = """
Database Configuration
=====================

Supported Database Types:
-----------------------
- SQLite: Standalone file-based database
- Microsoft Access: .mdb or .accdb files
- SQL Server: Microsoft SQL Server databases
- MySQL: MySQL or MariaDB databases
- PostgreSQL: PostgreSQL databases

Connection Settings:
------------------
For SQLite:
- Simply select the database file

For ODBC databases (Access, SQL Server, MySQL, PostgreSQL):
- Server: The database server hostname or IP address
- Database: The database name
- Username/Password: Authentication credentials
- Port: Database server port (optional)
- DSN: Data Source Name (optional, can be used instead of other parameters)

Testing Connections:
------------------
Always use the "Test Connection" button to verify your database connection before starting migration.
"""
        db_label = tk.Label(db_frame, text=db_text, justify='left', wraplength=700)
        db_label.pack(fill='both', expand=True)
        
        # Mapping help
        mapping_frame = ttk.Frame(notebook, padding=10)
        notebook.add(mapping_frame, text="Component Mapping")
        
        mapping_text = """
Component Mapping
================

The tool maps Altium components to KiCAD equivalents using several methods:

1. Direct Mapping:
   - Uses exact matches from mapping rules
   - Custom mapping rules can be added in the Mapping Rules tab

2. Fuzzy Matching:
   - Finds similar symbols/footprints when exact matches aren't available
   - Adjustable threshold controls matching strictness

3. Category-based Mapping:
   - Groups components by category for better organization in KiCAD
   - Custom categories can be defined in mapping rules

Confidence Scores:
----------------
Each mapping is assigned a confidence score (0.0-1.0):
- High (>0.8): Reliable mapping, likely correct
- Medium (0.5-0.8): Reasonable mapping, may need review
- Low (<0.5): Uncertain mapping, should be manually verified

Custom Mapping Rules:
------------------
You can create custom mapping rules for:
- Symbols: Map Altium symbol names to KiCAD symbol names
- Footprints: Map Altium footprint names to KiCAD footprint names
- Categories: Define how components should be categorized

Rules can be imported/exported as YAML or JSON files.
"""
        mapping_label = tk.Label(mapping_frame, text=mapping_text, justify='left', wraplength=700)
        mapping_label.pack(fill='both', expand=True)
        
        # Batch processing help
        batch_frame = ttk.Frame(notebook, padding=10)
        notebook.add(batch_frame, text="Batch Processing")
        
        batch_text = """
Batch Processing
==============

The batch processing feature allows you to migrate multiple Altium database files in a single operation.

Features:
-------
- Process multiple .DbLib files
- Parallel processing for faster migration
- Individual output directories for each database
- Comprehensive batch report

Options:
------
- Parallel Processing: Process multiple files simultaneously
- Worker Threads: Number of concurrent processing threads
- Create Subdirectories: Create separate output directory for each file
- Generate Report: Create a summary report of the batch process

Batch Configurations:
------------------
You can save and load batch configurations to reuse them later.
"""
        batch_label = tk.Label(batch_frame, text=batch_text, justify='left', wraplength=700)
        batch_label.pack(fill='both', expand=True)
        
        # Troubleshooting help
        trouble_frame = ttk.Frame(notebook, padding=10)
        notebook.add(trouble_frame, text="Troubleshooting")
        
        trouble_text = """
Troubleshooting
=============

Common Issues and Solutions:

Database Connection Problems:
--------------------------
- Verify database path or server details
- Check username and password
- Ensure ODBC drivers are installed
- Test connection before migration

Low Confidence Mappings:
---------------------
- Add custom mapping rules
- Check for typos in component names
- Review mapping rules for similar components

Missing Components:
----------------
- Check database tables are correctly identified
- Verify required fields are present
- Ensure database connection is stable

Performance Issues:
---------------
- Enable parallel processing
- Increase worker threads (for multi-core systems)
- Enable caching for repeated operations
- For large databases, try increasing batch size

Error Logs:
---------
Error logs are saved in the output directory and can help diagnose issues.
"""
        trouble_label = tk.Label(trouble_frame, text=trouble_text, justify='left', wraplength=700)
        trouble_label.pack(fill='both', expand=True)
        
        # Set initial tab based on topic
        if topic == "database":
            notebook.select(1)
        elif topic == "mapping":
            notebook.select(2)
        elif topic == "batch":
            notebook.select(3)
        elif topic == "troubleshooting":
            notebook.select(4)
        
        # Close button
        ttk.Button(main_frame, text="Close", command=self.window.destroy).pack(pady=10)


class StatusBar(ttk.Frame):
    """Status bar for the main application window."""
    
    def __init__(self, parent):
        """Initialize status bar."""
        super().__init__(parent, relief=tk.SUNKEN, padding=(2, 2))
        
        # Status message
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self, textvariable=self.status_var, anchor='w')
        self.status_label.pack(side='left', fill='x', expand=True)
        
        # Progress indicator
        self.progress_var = tk.IntVar(value=0)
        self.progress = ttk.Progressbar(
            self,
            orient='horizontal',
            length=100,
            mode='determinate',
            variable=self.progress_var
        )
        self.progress.pack(side='right', padx=5)
        
        # Initially hide progress bar
        self.progress.pack_forget()
    
    def set_status(self, message):
        """Set status message."""
        self.status_var.set(message)
        self.update_idletasks()
    
    def show_progress(self, show=True):
        """Show or hide progress bar."""
        if show:
            self.progress.pack(side='right', padx=5)
        else:
            self.progress.pack_forget()
        self.update_idletasks()
    
    def set_progress(self, value, maximum=100):
        """Set progress bar value."""
        self.progress_var.set(value)
        self.progress['maximum'] = maximum
        self.update_idletasks()


class MigrationToolMainWindow(tk.Tk):
    """Main application window for the Altium to KiCAD Database Migration Tool."""
    
    def __init__(self, config_path=None, theme="system", window_size=(1024, 768)):
        """Initialize the main application window."""
        super().__init__()
        
        # Set window title and size
        self.title("Altium to KiCAD Database Migration Tool")
        self.geometry(f"{window_size[0]}x{window_size[1]}")
        self.minsize(800, 600)
        
        # Configuration Management
        self.config_manager = ConfigManager(config_path)
        self.config_path = config_path
        
        # State Management
        self.current_project = {}
        self.source_connection = None
        self.target_settings = {}
        self.mapping_rules = {
            'symbol': {},
            'footprint': {},
            'category': {}
        }
        
        # Core Components
        self.parser = None
        self.mapping_engine = None
        self.generator = None
        
        # Migration State
        self.migration_thread = None
        self.is_migrating = False
        self.migration_results = None
        
        # Setup UI
        self.setup_ui()
        self.setup_menus()
        self.setup_logging()
        
        # Apply theme
        self.on_theme_change(theme)
        
        # Load configuration
        self.load_configuration(config_path)
        
        # Set up protocol for window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """Set up the main UI components."""
        # Main frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill='both', expand=True)
        
        # Create notebook for tabs
        self.main_notebook = ttk.Notebook(self.main_frame)
        self.main_notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.source_tab = self.create_source_tab()
        self.mapping_tab = self.create_mapping_tab()
        self.output_tab = self.create_output_tab()
        self.review_tab = self.create_review_tab()
        
        # Add tabs to notebook
        self.main_notebook.add(self.source_tab, text="Source")
        self.main_notebook.add(self.mapping_tab, text="Mapping")
        self.main_notebook.add(self.output_tab, text="Output")
        self.main_notebook.add(self.review_tab, text="Review")
        # Create log container
        self.log_container = ttk.Frame(self.main_frame)
        self.log_container.pack(fill='x', expand=False, padx=10, pady=(0, 10))
        
        # Create log controls frame (always visible)
        self.log_controls = ttk.Frame(self.log_container)
        self.log_controls.pack(fill='x', expand=False)
        
        # Log panel toggle button
        self.log_visible = tk.BooleanVar(value=True)
        self.log_toggle_button = ttk.Checkbutton(
            self.log_controls,
            text="Show Log",
            variable=self.log_visible,
            command=self.toggle_log_panel
        )
        self.log_toggle_button.pack(side='left', padx=5, pady=2)
        
        # Clear log button
        self.clear_log_button = ttk.Button(
            self.log_controls,
            text="Clear Log",
            command=self.clear_log
        )
        self.clear_log_button.pack(side='left', padx=5, pady=2)
        
        # Create log panel (collapsible)
        self.log_frame = ttk.LabelFrame(self.log_container, text="Log")
        self.log_frame.pack(fill='x', expand=False, pady=(5, 0))
        
        # Log text widget
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=8, width=80)
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.log_text.config(state='disabled')
        
        
        # Status bar
        self.status_bar = StatusBar(self)
        self.status_bar.pack(fill='x', side='bottom')
        
        # Set initial status
        self.status_bar.set_status("Ready")
    
    def setup_menus(self):
        """Set up the application menus."""
        # Create menu bar
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        
        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        
        file_menu.add_command(label="New Project", command=self.reset_project)
        file_menu.add_command(label="Open Project...", command=self.load_project)
        file_menu.add_command(label="Save Project", command=lambda: self.save_project())
        file_menu.add_command(label="Save Project As...", command=lambda: self.save_project(path=None))
        file_menu.add_separator()
        file_menu.add_command(label="Import Configuration...", command=self.import_configuration)
        file_menu.add_command(label="Export Configuration...", command=self.export_configuration)
        file_menu.add_separator()
        
        # Recent projects submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Projects", menu=self.recent_menu)
        
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Database menu
        db_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Database", menu=db_menu)
        
        db_menu.add_command(label="Connect to Database...", command=self.open_database_connection_dialog)
        db_menu.add_command(label="Test Connection", command=self.test_connection)
        
        # Mapping menu
        mapping_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Mapping", menu=mapping_menu)
        
        mapping_menu.add_command(label="Symbol Rules...", command=lambda: self.open_mapping_rules_dialog("symbol"))
        mapping_menu.add_command(label="Footprint Rules...", command=lambda: self.open_mapping_rules_dialog("footprint"))
        mapping_menu.add_command(label="Category Rules...", command=lambda: self.open_mapping_rules_dialog("category"))
        
        # Batch menu
        batch_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Batch", menu=batch_menu)
        
        batch_menu.add_command(label="Batch Processing...", command=self.open_batch_processing_dialog)
        
        # Tools menu
        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Tools", menu=tools_menu)
        
        tools_menu.add_command(label="Validate Mappings", command=self.validate_migration_readiness)
        
        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        
        help_menu.add_command(label="Documentation", command=lambda: self.show_help("general"))
        help_menu.add_command(label="About", command=lambda: self.show_help("about"))
    
    def setup_logging(self):
        """Set up logging to the log panel."""
        # Create and configure the log handler
        self.log_handler = LoggingHandler(self.log_text)
        self.log_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        self.log_handler.setFormatter(formatter)
        
        # Get the logger and add the handler
        logger = get_logger()
        logger.addHandler(self.log_handler)
        
        # Log startup message
        logger.info("Application started")
    
    def load_configuration(self, config_path=None):
        """Load configuration from file."""
        try:
            if config_path:
                config = self.config_manager.load_config(config_path)
                self.status_bar.set_status(f"Configuration loaded from {config_path}")
                logging.info(f"Configuration loaded from {config_path}")
            else:
                config = self.config_manager.load_default_config()
                self.status_bar.set_status("Default configuration loaded")
                logging.info("Default configuration loaded")
            
            # Apply configuration to UI
            self.apply_configuration(config)
            
        except Exception as e:
            self.status_bar.set_status("Error loading configuration")
            logging.error(f"Error loading configuration: {str(e)}")
            messagebox.showerror("Configuration Error", f"Failed to load configuration: {str(e)}")
    
    def apply_configuration(self, config):
        """Apply configuration to the UI and state."""
        # Apply source connection
        if 'source_connection' in config:
            self.source_connection = config['source_connection']
            if self.source_connection:
                self.conn_status_var.set("Connected")
                self.conn_string_var.set(self.source_connection.get('connection_string', ''))
        
        # Apply target settings
        target_settings = config.get('target_settings', {})
        if target_settings:
            if 'output_dir' in target_settings:
                self.output_dir.set(target_settings['output_dir'])
            if 'db_name' in target_settings:
                self.db_name.set(target_settings['db_name'])
            if 'lib_name' in target_settings:
                self.lib_name.set(target_settings['lib_name'])
            if 'create_sqlite' in target_settings:
                self.create_sqlite.set(target_settings['create_sqlite'])
            if 'create_kicad_dbl' in target_settings:
                self.create_kicad_dbl.set(target_settings['create_kicad_dbl'])
            if 'generate_report' in target_settings:
                self.generate_report.set(target_settings['generate_report'])
        
        # Apply mapping rules
        if 'mapping_rules' in config:
            self.mapping_rules = config['mapping_rules']
            # Update mapping rule counts
            for rule_type, rules in self.mapping_rules.items():
                if rule_type in self.mapping_count_vars:
                    self.mapping_count_vars[rule_type].set(f"{len(rules)} rules defined")
        
        # Apply confidence threshold
        if 'confidence_threshold' in config:
            self.confidence_threshold.set(config['confidence_threshold'])
        
        # Apply window geometry if available
        if 'window_geometry' in config:
            geometry = config['window_geometry']
            if all(key in geometry for key in ['width', 'height', 'x', 'y']):
                self.geometry(f"{geometry['width']}x{geometry['height']}+{geometry['x']}+{geometry['y']}")
        
        # Log configuration applied
        logging.info("Configuration applied to UI")
    
    def open_database_connection_dialog(self):
        """Open the database connection dialog."""
        dialog = DatabaseConnectionDialog(self,
                                         connection_string=self.source_connection['connection_string'] if self.source_connection else None,
                                         db_type=self.source_connection['db_type'] if self.source_connection else None)
        self.wait_window(dialog.window)
        
        if dialog.result:
            self.source_connection = dialog.result
            self.status_bar.set_status(f"Connected to {dialog.result['db_type']} database")
            logging.info(f"Connected to {dialog.result['db_type']} database")
            
            # Update UI to reflect connection
            # TODO: Update connection status in source tab
    
    def import_configuration(self):
        """Import configuration from file."""
        filename = filedialog.askopenfilename(
            title="Import Configuration",
            filetypes=[
                ("YAML files", "*.yaml *.yml"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if not filename:
            return
        
        try:
            config = self.config_manager.load_config(filename)
            self.apply_configuration(config)
            
            self.status_bar.set_status(f"Configuration imported from {filename}")
            logging.info(f"Configuration imported from {filename}")
            
            messagebox.showinfo("Import Successful", f"Configuration imported from {filename}")
            
        except Exception as e:
            error_msg = f"Failed to import configuration: {str(e)}"
            self.status_bar.set_status("Error importing configuration")
            logging.error(error_msg)
            messagebox.showerror("Import Error", error_msg)
    
    def export_configuration(self):
        """Export configuration to file."""
        filename = filedialog.asksaveasfilename(
            title="Export Configuration",
            defaultextension=".yaml",
            filetypes=[
                ("YAML files", "*.yaml"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if not filename:
            return
        
        try:
            # Prepare configuration
            config = {
                'source_connection': self.source_connection,
                'target_settings': {
                    'output_dir': self.output_dir.get(),
                    'db_name': self.db_name.get(),
                    'lib_name': self.lib_name.get(),
                    'create_sqlite': self.create_sqlite.get(),
                    'create_kicad_dbl': self.create_kicad_dbl.get(),
                    'generate_report': self.generate_report.get()
                },
                'mapping_rules': self.mapping_rules,
                'confidence_threshold': self.confidence_threshold.get()
            }
            # Update config manager with current configuration
            self.config_manager.config = config
            
            # Save configuration
            self.config_manager.save_config(filename)
            
            
            self.status_bar.set_status(f"Configuration exported to {filename}")
            logging.info(f"Configuration exported to {filename}")
            
            messagebox.showinfo("Export Successful", f"Configuration exported to {filename}")
            
        except Exception as e:
            error_msg = f"Failed to export configuration: {str(e)}"
            self.status_bar.set_status("Error exporting configuration")
            logging.error(error_msg)
            messagebox.showerror("Export Error", error_msg)
    
    def open_mapping_rules_dialog(self, rule_type):
        """Open the mapping rules dialog."""
        dialog = MappingRuleDialog(self, rule_type=rule_type, existing_rules=self.mapping_rules.get(rule_type, {}))
        self.wait_window(dialog.window)
        
        if dialog.result:
            self.mapping_rules[rule_type] = dialog.result
            self.status_bar.set_status(f"Updated {rule_type} mapping rules")
            logging.info(f"Updated {rule_type} mapping rules: {len(dialog.result)} rules defined")
            
            # Update UI to reflect new rules
            if rule_type in self.mapping_count_vars:
                self.mapping_count_vars[rule_type].set(f"{len(dialog.result)} rules defined")
    
    def browse_output_dir(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir.set(directory)
    
    def open_batch_processing_dialog(self):
        """Open the batch processing dialog."""
        dialog = BatchProcessDialog(self, config_manager=self.config_manager)
        self.wait_window(dialog.window)
        
        if dialog.result:
            # Start batch processing
            self.status_bar.set_status(f"Starting batch processing of {len(dialog.result['files'])} files")
            logging.info(f"Starting batch processing of {len(dialog.result['files'])} files")
            
            # TODO: Implement batch processing logic
    
    def show_help(self, topic="general"):
        """Show the help dialog."""
        dialog = HelpDialog(self, topic=topic)
        # No need to wait for this non-modal dialog
    
    def show_migration_progress(self):
        """Show the migration progress dialog."""
        dialog = MigrationProgressDialog(self)
        return dialog
    
    def auto_generate_rules(self):
        """Auto-generate mapping rules based on component analysis."""
        if not self.source_connection:
            messagebox.showwarning("Warning", "Please connect to a database first")
            return
        
        try:
            # Show progress
            self.status_bar.set_status("Auto-generating mapping rules...")
            self.status_bar.show_progress(True)
            
            # This is a placeholder for the auto-generation logic
            # In a real implementation, this would analyze the database
            # and generate intelligent mapping suggestions
            
            # For now, just show a message
            messagebox.showinfo(
                "Auto-Generate Rules",
                "Auto-generation of mapping rules is not yet implemented.\n\n"
                "This feature will analyze your Altium database and suggest "
                "appropriate mappings based on component names and properties."
            )
            
            self.status_bar.set_status("Ready")
            self.status_bar.show_progress(False)
            
        except Exception as e:
            error_msg = f"Failed to auto-generate rules: {str(e)}"
            self.status_bar.set_status("Error generating rules")
            logging.error(error_msg)
            messagebox.showerror("Error", error_msg)
            self.status_bar.show_progress(False)
    
    def toggle_log_panel(self):
        """Toggle the visibility of the log panel."""
        if self.log_visible.get():
            self.log_frame.pack(fill='x', expand=False, pady=(5, 0))
        else:
            self.log_frame.pack_forget()
    
    def clear_log(self):
        """Clear the log panel."""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
        logging.info("Log cleared")
    
    def test_connection(self):
        """Test the current database connection."""
        if not self.source_connection:
            messagebox.showwarning("Warning", "No database connection configured")
            return
        
        try:
            conn = create_connection(
                self.source_connection['connection_string'],
                self.source_connection['db_type']
            )
            messagebox.showinfo("Connection Test", "Database connection successful")
            conn.close()
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to database: {str(e)}")
    
    def create_source_tab(self):
        """Create the Source tab."""
        tab = ttk.Frame(self.main_notebook, padding=10)
        
        # Database connection section
        conn_frame = ttk.LabelFrame(tab, text="Database Connection", padding=10)
        conn_frame.pack(fill='x', padx=5, pady=5)
        
        # Connection status
        self.conn_status_var = tk.StringVar(value="Not Connected")
        conn_status_label = ttk.Label(conn_frame, text="Status:")
        conn_status_label.grid(row=0, column=0, sticky='w', padx=5, pady=5)
        conn_status_value = ttk.Label(conn_frame, textvariable=self.conn_status_var)
        conn_status_value.grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        # Connection string
        self.conn_string_var = tk.StringVar()
        conn_string_label = ttk.Label(conn_frame, text="Connection:")
        conn_string_label.grid(row=1, column=0, sticky='w', padx=5, pady=5)
        conn_string_value = ttk.Entry(conn_frame, textvariable=self.conn_string_var, width=50, state='readonly')
        conn_string_value.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        # Connect button
        connect_button = ttk.Button(
            conn_frame,
            text="Connect to Database",
            command=self.open_database_connection_dialog
        )
        connect_button.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        
        # Table selection section
        table_frame = ttk.LabelFrame(tab, text="Table Selection", padding=10)
        table_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Table list
        table_list_label = ttk.Label(table_frame, text="Available Tables:")
        table_list_label.grid(row=0, column=0, sticky='w', padx=5, pady=5)
        
        self.table_list = tk.Listbox(table_frame, height=8, width=40)
        table_list_scroll = ttk.Scrollbar(table_frame, orient='vertical', command=self.table_list.yview)
        self.table_list.configure(yscrollcommand=table_list_scroll.set)
        
        self.table_list.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        table_list_scroll.grid(row=1, column=1, sticky='ns', pady=5)
        
        # Field mapping preview
        preview_frame = ttk.LabelFrame(tab, text="Field Preview", padding=10)
        preview_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Preview treeview
        columns = ('field', 'type', 'sample')
        self.field_preview = ttk.Treeview(preview_frame, columns=columns, show='headings')
        
        for col, heading in zip(columns, ('Field Name', 'Data Type', 'Sample Value')):
            self.field_preview.heading(col, text=heading)
            self.field_preview.column(col, width=100)
        
        preview_scroll = ttk.Scrollbar(preview_frame, orient='vertical', command=self.field_preview.yview)
        self.field_preview.configure(yscrollcommand=preview_scroll.set)
        
        self.field_preview.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        preview_scroll.pack(side='right', fill='y', pady=5)
        
        # Configure grid weights
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(1, weight=1)
        
        return tab
    
    def create_mapping_tab(self):
        """Create the Mapping tab."""
        tab = ttk.Frame(self.main_notebook, padding=10)
        
        # Mapping rules section
        rules_frame = ttk.Frame(tab)
        rules_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Symbol mapping
        symbol_frame = ttk.LabelFrame(rules_frame, text="Symbol Mapping Rules", padding=10)
        symbol_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        
        self.symbol_count_var = tk.StringVar(value="0 rules defined")
        ttk.Label(symbol_frame, textvariable=self.symbol_count_var).pack(anchor='w', pady=5)
        
        ttk.Button(
            symbol_frame,
            text="Edit Symbol Rules",
            command=lambda: self.open_mapping_rules_dialog("symbol")
        ).pack(fill='x', pady=5)
        
        # Footprint mapping
        footprint_frame = ttk.LabelFrame(rules_frame, text="Footprint Mapping Rules", padding=10)
        footprint_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        
        self.footprint_count_var = tk.StringVar(value="0 rules defined")
        ttk.Label(footprint_frame, textvariable=self.footprint_count_var).pack(anchor='w', pady=5)
        
        ttk.Button(
            footprint_frame,
            text="Edit Footprint Rules",
            command=lambda: self.open_mapping_rules_dialog("footprint")
        ).pack(fill='x', pady=5)
        
        # Category mapping
        category_frame = ttk.LabelFrame(rules_frame, text="Category Mapping Rules", padding=10)
        category_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)
        
        self.category_count_var = tk.StringVar(value="0 rules defined")
        ttk.Label(category_frame, textvariable=self.category_count_var).pack(anchor='w', pady=5)
        
        ttk.Button(
            category_frame,
            text="Edit Category Rules",
            command=lambda: self.open_mapping_rules_dialog("category")
        ).pack(fill='x', pady=5)
        
        # Mapping settings
        settings_frame = ttk.LabelFrame(tab, text="Mapping Settings", padding=10)
        settings_frame.pack(fill='x', padx=5, pady=5)
        
        # Confidence threshold
        ttk.Label(settings_frame, text="Confidence Threshold:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        
        self.confidence_threshold = tk.DoubleVar(value=0.7)
        confidence_scale = ttk.Scale(
            settings_frame,
            from_=0.0,
            to=1.0,
            variable=self.confidence_threshold,
            orient='horizontal',
            length=200
        )
        confidence_scale.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        confidence_value = ttk.Label(settings_frame, textvariable=tk.StringVar(value="0.7"))
        self.confidence_threshold.trace_add(
            "write",
            lambda *args: confidence_value.config(text=f"{self.confidence_threshold.get():.1f}")
        )
        confidence_value.grid(row=0, column=2, sticky='w', padx=5, pady=5)
        
        # Auto-generate rules
        ttk.Button(
            settings_frame,
            text="Auto-Generate Rules",
            command=self.auto_generate_rules
        ).grid(row=1, column=0, columnspan=3, sticky='ew', padx=5, pady=5)
        
        # Configure grid weights
        rules_frame.columnconfigure(0, weight=1)
        rules_frame.columnconfigure(1, weight=1)
        rules_frame.rowconfigure(0, weight=1)
        rules_frame.rowconfigure(1, weight=1)
        
        # Store variables for updating
        self.mapping_count_vars = {
            'symbol': self.symbol_count_var,
            'footprint': self.footprint_count_var,
            'category': self.category_count_var
        }
        
        return tab
    
    def create_output_tab(self):
        """Create the Output tab."""
        tab = ttk.Frame(self.main_notebook, padding=10)
        
        # Output directory section
        dir_frame = ttk.LabelFrame(tab, text="Output Directory", padding=10)
        dir_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(dir_frame, text="Output Directory:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        
        self.output_dir = tk.StringVar(value=os.path.join(os.getcwd(), "output"))
        output_entry = ttk.Entry(dir_frame, textvariable=self.output_dir, width=50)
        output_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        browse_button = ttk.Button(
            dir_frame,
            text="Browse",
            command=self.browse_output_dir
        )
        browse_button.grid(row=0, column=2, padx=5, pady=5)
        
        # KiCAD database settings
        kicad_frame = ttk.LabelFrame(tab, text="KiCAD Database Settings", padding=10)
        kicad_frame.pack(fill='x', padx=5, pady=5)
        
        # Database name
        ttk.Label(kicad_frame, text="Database Name:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        
        self.db_name = tk.StringVar(value="kicad_library")
        db_name_entry = ttk.Entry(kicad_frame, textvariable=self.db_name, width=30)
        db_name_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        # Library name
        ttk.Label(kicad_frame, text="Library Name:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        
        self.lib_name = tk.StringVar(value="Migrated Library")
        lib_name_entry = ttk.Entry(kicad_frame, textvariable=self.lib_name, width=30)
        lib_name_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        # Field mapping
        field_frame = ttk.LabelFrame(tab, text="Field Mapping", padding=10)
        field_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Field mapping treeview
        columns = ('altium', 'kicad', 'required')
        self.field_mapping = ttk.Treeview(field_frame, columns=columns, show='headings')
        
        for col, heading in zip(columns, ('Altium Field', 'KiCAD Field', 'Required')):
            self.field_mapping.heading(col, text=heading)
            self.field_mapping.column(col, width=100)
        
        field_scroll = ttk.Scrollbar(field_frame, orient='vertical', command=self.field_mapping.yview)
        self.field_mapping.configure(yscrollcommand=field_scroll.set)
        
        self.field_mapping.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        field_scroll.pack(side='right', fill='y', pady=5)
        
        # Export options
        export_frame = ttk.LabelFrame(tab, text="Export Options", padding=10)
        export_frame.pack(fill='x', padx=5, pady=5)
        
        # Create SQLite database
        self.create_sqlite = tk.BooleanVar(value=True)
        sqlite_check = ttk.Checkbutton(
            export_frame,
            text="Create SQLite Database",
            variable=self.create_sqlite
        )
        sqlite_check.grid(row=0, column=0, sticky='w', padx=5, pady=2)
        
        # Create .kicad_dbl file
        self.create_kicad_dbl = tk.BooleanVar(value=True)
        kicad_dbl_check = ttk.Checkbutton(
            export_frame,
            text="Create .kicad_dbl File",
            variable=self.create_kicad_dbl
        )
        kicad_dbl_check.grid(row=1, column=0, sticky='w', padx=5, pady=2)
        
        # Generate report
        self.generate_report = tk.BooleanVar(value=True)
        report_check = ttk.Checkbutton(
            export_frame,
            text="Generate Migration Report",
            variable=self.generate_report
        )
        report_check.grid(row=2, column=0, sticky='w', padx=5, pady=2)
        
        # Configure grid weights
        dir_frame.columnconfigure(1, weight=1)
        kicad_frame.columnconfigure(1, weight=1)
        
        return tab
    
    def create_review_tab(self):
        """Create the Review tab."""
        tab = ttk.Frame(self.main_notebook, padding=10)
        
        # Validation summary section
        validation_frame = ttk.LabelFrame(tab, text="Validation Summary", padding=10)
        validation_frame.pack(fill='x', padx=5, pady=5)
        
        # Validation status
        self.validation_status = tk.StringVar(value="Not Validated")
        validation_label = ttk.Label(validation_frame, textvariable=self.validation_status, font=('TkDefaultFont', 10, 'bold'))
        validation_label.pack(anchor='w', pady=5)
        
        # Validation details
        self.validation_text = tk.Text(validation_frame, height=8, width=60, wrap='word')
        validation_scroll = ttk.Scrollbar(validation_frame, orient='vertical', command=self.validation_text.yview)
        self.validation_text.configure(yscrollcommand=validation_scroll.set)
        
        self.validation_text.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        validation_scroll.pack(side='right', fill='y', pady=5)
        self.validation_text.config(state='disabled')
        
        # Migration statistics
        stats_frame = ttk.LabelFrame(tab, text="Migration Statistics", padding=10)
        stats_frame.pack(fill='x', padx=5, pady=5)
        
        # Statistics grid
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill='both', expand=True)
        
        # Source components
        ttk.Label(stats_grid, text="Source Components:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.source_count = tk.StringVar(value="0")
        ttk.Label(stats_grid, textvariable=self.source_count).grid(row=0, column=1, sticky='w', padx=5, pady=2)
        
        # Mappable components
        ttk.Label(stats_grid, text="Mappable Components:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.mappable_count = tk.StringVar(value="0")
        ttk.Label(stats_grid, textvariable=self.mappable_count).grid(row=1, column=1, sticky='w', padx=5, pady=2)
        
        # High confidence mappings
        ttk.Label(stats_grid, text="High Confidence Mappings:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.high_conf_count = tk.StringVar(value="0")
        ttk.Label(stats_grid, textvariable=self.high_conf_count).grid(row=2, column=1, sticky='w', padx=5, pady=2)
        
        # Medium confidence mappings
        ttk.Label(stats_grid, text="Medium Confidence Mappings:").grid(row=3, column=0, sticky='w', padx=5, pady=2)
        self.med_conf_count = tk.StringVar(value="0")
        ttk.Label(stats_grid, textvariable=self.med_conf_count).grid(row=3, column=1, sticky='w', padx=5, pady=2)
        
        # Low confidence mappings
        ttk.Label(stats_grid, text="Low Confidence Mappings:").grid(row=4, column=0, sticky='w', padx=5, pady=2)
        self.low_conf_count = tk.StringVar(value="0")
        ttk.Label(stats_grid, textvariable=self.low_conf_count).grid(row=4, column=1, sticky='w', padx=5, pady=2)
        
        # Action buttons
        action_frame = ttk.Frame(tab)
        action_frame.pack(fill='x', padx=5, pady=10)
        
        # Validate button
        validate_button = ttk.Button(
            action_frame,
            text="Validate Migration",
            command=self.validate_migration_readiness
        )
        validate_button.pack(side='left', padx=5)
        
        # Start migration button
        self.start_button = ttk.Button(
            action_frame,
            text="Start Migration",
            command=self.start_migration,
            state='disabled'
        )
        self.start_button.pack(side='right', padx=5)
        
        return tab
    
    def validate_migration_readiness(self):
        """Validate if the system is ready for migration."""
        validation_issues = []
        
        # Check database connection
        if not self.source_connection:
            validation_issues.append("No database connection configured")
        
        # Check mapping rules
        if not self.mapping_rules.get('symbol'):
            validation_issues.append("No symbol mapping rules defined")
        
        if not self.mapping_rules.get('footprint'):
            validation_issues.append("No footprint mapping rules defined")
        
        # Check output settings
        if not self.output_dir.get():
            validation_issues.append("No output directory specified")
        
        # Update validation status
        if validation_issues:
            self.validation_status.set("Validation Failed")
            self.start_button.config(state='disabled')
            
            # Update validation text
            self.validation_text.config(state='normal')
            self.validation_text.delete(1.0, tk.END)
            self.validation_text.insert(tk.END, "The following issues need to be resolved:\n\n")
            for issue in validation_issues:
                self.validation_text.insert(tk.END, f"• {issue}\n")
            self.validation_text.config(state='disabled')
            
            # Log issues
            logging.warning("Migration validation failed")
            for issue in validation_issues:
                logging.warning(f"Validation issue: {issue}")
        else:
            self.validation_status.set("Ready for Migration")
            self.start_button.config(state='normal')
            
            # Update validation text
            self.validation_text.config(state='normal')
            self.validation_text.delete(1.0, tk.END)
            self.validation_text.insert(tk.END, "All validation checks passed. Ready to start migration.")
            self.validation_text.config(state='disabled')
            
            # Log success
            logging.info("Migration validation successful")
        
        return len(validation_issues) == 0
    
    def start_migration(self):
        """Start the migration process."""
        if not self.validate_migration_readiness():
            messagebox.showerror("Error", "Cannot start migration. Please resolve validation issues.")
            return
        
        # Create progress dialog
        progress_dialog = self.show_migration_progress()
        
        # Prepare migration parameters
        output_dir = self.output_dir.get()
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Set migration flag
        self.is_migrating = True
        
        # Disable start button
        self.start_button.config(state='disabled')
        
        # Update status
        self.status_bar.set_status("Migration in progress...")
        self.status_bar.show_progress(True)
        
        # Start migration in a separate thread
        self.migration_thread = threading.Thread(
            target=self._run_migration,
            args=(progress_dialog, output_dir)
        )
        self.migration_thread.daemon = True
        self.migration_thread.start()
    
    def _run_migration(self, progress_dialog, output_dir):
        """Run the migration process in a separate thread."""
        try:
            # Initialize components if needed
            if not self.parser:
                progress_dialog.update_status("Initializing parser...")
                self.parser = AltiumDbLibParser(self.source_connection['connection_string'],
                                               self.source_connection['db_type'])
            
            if not self.mapping_engine:
                progress_dialog.update_status("Initializing mapping engine...")
                self.mapping_engine = ComponentMappingEngine(
                    symbol_rules=self.mapping_rules.get('symbol', {}),
                    footprint_rules=self.mapping_rules.get('footprint', {}),
                    category_rules=self.mapping_rules.get('category', {})
                )
            
            if not self.generator:
                progress_dialog.update_status("Initializing KiCAD generator...")
                self.generator = KiCADDbLibGenerator(
                    output_dir=output_dir,
                    db_name=self.db_name.get(),
                    lib_name=self.lib_name.get()
                )
            
            # Parse Altium database
            progress_dialog.update_status("Parsing Altium database...")
            components = self.parser.parse()
            
            # Update component count
            self.source_count.set(str(len(components)))
            
            # Map components
            progress_dialog.update_status("Mapping components...")
            mapped_components = []
            high_conf = 0
            med_conf = 0
            low_conf = 0
            
            for i, component in enumerate(components):
                # Update progress
                progress_dialog.update_task_progress(i + 1, len(components))
                
                # Map component
                mapped = self.mapping_engine.map_component(component)
                mapped_components.append(mapped)
                
                # Update confidence counts
                if mapped.get('confidence', 0) > 0.8:
                    high_conf += 1
                elif mapped.get('confidence', 0) > 0.5:
                    med_conf += 1
                else:
                    low_conf += 1
                
                # Check if cancelled
                if progress_dialog.cancelled:
                    progress_dialog.update_status("Migration cancelled")
                    break
            
            # Update statistics
            self.mappable_count.set(str(len(mapped_components)))
            self.high_conf_count.set(str(high_conf))
            self.med_conf_count.set(str(med_conf))
            self.low_conf_count.set(str(low_conf))
            
            if not progress_dialog.cancelled:
                # Generate KiCAD database
                progress_dialog.update_status("Generating KiCAD database...")
                self.generator.generate(mapped_components)
                
                # Generate report if requested
                if self.generate_report.get():
                    progress_dialog.update_status("Generating migration report...")
                    self.generate_migration_report(output_dir, components, mapped_components)
                
                # Complete migration
                progress_dialog.update_status("Migration completed successfully")
                
                # Store results
                self.migration_results = {
                    'total': len(components),
                    'mapped': len(mapped_components),
                    'high_confidence': high_conf,
                    'medium_confidence': med_conf,
                    'low_confidence': low_conf,
                    'output_dir': output_dir
                }
                
                # Log success
                logging.info(f"Migration completed: {len(components)} components processed")
            
        except Exception as e:
            # Log error
            error_msg = f"Migration failed: {str(e)}"
            logging.error(error_msg)
            progress_dialog.update_status(f"Error: {str(e)}")
            
            # Show error in UI
            self.after(0, lambda: messagebox.showerror("Migration Error", error_msg))
        
        finally:
            # Reset migration state
            self.is_migrating = False
            self.migration_thread = None
            
            # Update UI
            self.after(0, lambda: self.status_bar.set_status("Ready"))
            self.after(0, lambda: self.status_bar.show_progress(False))
            self.after(0, lambda: self.start_button.config(state='normal'))
            
            # Close progress dialog
            self.after(2000, progress_dialog.close)
    
    def generate_migration_report(self, output_dir, components, mapped_components):
        """Generate a migration report."""
        report_path = os.path.join(output_dir, "migration_report.html")
        
        try:
            with open(report_path, 'w') as f:
                f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Altium to KiCAD Migration Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .high {{ color: green; }}
        .medium {{ color: orange; }}
        .low {{ color: red; }}
        .summary {{ margin-bottom: 30px; }}
    </style>
</head>
<body>
    <h1>Altium to KiCAD Migration Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>Migration Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Total Components: {len(components)}</p>
        <p>Mapped Components: {len(mapped_components)}</p>
        <p>High Confidence Mappings: {self.high_conf_count.get()}</p>
        <p>Medium Confidence Mappings: {self.med_conf_count.get()}</p>
        <p>Low Confidence Mappings: {self.low_conf_count.get()}</p>
    </div>
    
    <h2>Component Mapping Details</h2>
    <table>
        <tr>
            <th>Altium Component</th>
            <th>KiCAD Component</th>
            <th>Confidence</th>
            <th>Notes</th>
        </tr>
""")
                
                # Add component rows
                for component in mapped_components:
                    confidence = component.get('confidence', 0)
                    confidence_class = "high" if confidence > 0.8 else "medium" if confidence > 0.5 else "low"
                    
                    f.write(f"""
        <tr>
            <td>{component.get('original_name', 'Unknown')}</td>
            <td>{component.get('mapped_name', 'Unknown')}</td>
            <td class="{confidence_class}">{confidence:.2f}</td>
            <td>{component.get('notes', '')}</td>
        </tr>
""")
                
                # Close HTML
                f.write("""
    </table>
</body>
</html>
""")
            
            logging.info(f"Migration report generated: {report_path}")
            
        except Exception as e:
            logging.error(f"Failed to generate migration report: {str(e)}")
    
    def save_project(self, path=None):
        """Save the current project state."""
        if not path:
            path = filedialog.asksaveasfilename(
                title="Save Project",
                defaultextension=".a2k",
                filetypes=[("Altium to KiCAD Project", "*.a2k"), ("All files", "*.*")]
            )
            
            if not path:
                return False
        
        try:
            # Prepare project data
            project_data = {
                'source_connection': self.source_connection,
                'target_settings': {
                    'output_dir': self.output_dir.get(),
                    'db_name': self.db_name.get(),
                    'lib_name': self.lib_name.get(),
                    'create_sqlite': self.create_sqlite.get(),
                    'create_kicad_dbl': self.create_kicad_dbl.get(),
                    'generate_report': self.generate_report.get()
                },
                'mapping_rules': self.mapping_rules,
                'confidence_threshold': self.confidence_threshold.get()
            }
            
            # Save to file
            with open(path, 'w') as f:
                json.dump(project_data, f, indent=2)
            
            # Update config path
            self.config_path = path
            
            # Update window title
            self.title(f"Altium to KiCAD Database Migration Tool - {os.path.basename(path)}")
            
            # Update status
            self.status_bar.set_status(f"Project saved to {path}")
            logging.info(f"Project saved to {path}")
            
            # Add to recent projects
            self.add_recent_project(path)
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to save project: {str(e)}"
            self.status_bar.set_status("Error saving project")
            logging.error(error_msg)
            messagebox.showerror("Save Error", error_msg)
            return False
    
    def load_project(self, path=None):
        """Load a project from file."""
        if not path:
            path = filedialog.askopenfilename(
                title="Open Project",
                filetypes=[("Altium to KiCAD Project", "*.a2k"), ("All files", "*.*")]
            )
            
            if not path:
                return False
        
        try:
            # Load from file
            with open(path, 'r') as f:
                project_data = json.load(f)
            
            # Apply project data
            self.source_connection = project_data.get('source_connection')
            
            target_settings = project_data.get('target_settings', {})
            self.output_dir.set(target_settings.get('output_dir', ''))
            self.db_name.set(target_settings.get('db_name', 'kicad_library'))
            self.lib_name.set(target_settings.get('lib_name', 'Migrated Library'))
            self.create_sqlite.set(target_settings.get('create_sqlite', True))
            self.create_kicad_dbl.set(target_settings.get('create_kicad_dbl', True))
            self.generate_report.set(target_settings.get('generate_report', True))
            
            self.mapping_rules = project_data.get('mapping_rules', {
                'symbol': {},
                'footprint': {},
                'category': {}
            })
            
            self.confidence_threshold.set(project_data.get('confidence_threshold', 0.7))
            
            # Update UI
            if self.source_connection:
                self.conn_status_var.set("Connected")
                self.conn_string_var.set(self.source_connection.get('connection_string', ''))
            
            # Update mapping rule counts
            for rule_type, rules in self.mapping_rules.items():
                if rule_type in self.mapping_count_vars:
                    self.mapping_count_vars[rule_type].set(f"{len(rules)} rules defined")
            
            # Update config path
            self.config_path = path
            
            # Update window title
            self.title(f"Altium to KiCAD Database Migration Tool - {os.path.basename(path)}")
            
            # Update status
            self.status_bar.set_status(f"Project loaded from {path}")
            logging.info(f"Project loaded from {path}")
            
            # Add to recent projects
            self.add_recent_project(path)
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to load project: {str(e)}"
            self.status_bar.set_status("Error loading project")
            logging.error(error_msg)
            messagebox.showerror("Load Error", error_msg)
            return False
    
    def reset_project(self):
        """Reset the project to initial state."""
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset the project? All unsaved changes will be lost."):
            # Reset state
            self.source_connection = None
            self.target_settings = {}
            self.mapping_rules = {
                'symbol': {},
                'footprint': {},
                'category': {}
            }
            
            # Reset UI
            self.conn_status_var.set("Not Connected")
            self.conn_string_var.set("")
            
            self.output_dir.set(os.path.join(os.getcwd(), "output"))
            self.db_name.set("kicad_library")
            self.lib_name.set("Migrated Library")
            
            self.create_sqlite.set(True)
            self.create_kicad_dbl.set(True)
            self.generate_report.set(True)
            
            self.confidence_threshold.set(0.7)
            
            # Reset mapping rule counts
            for var in self.mapping_count_vars.values():
                var.set("0 rules defined")
            
            # Reset statistics
            self.source_count.set("0")
            self.mappable_count.set("0")
            self.high_conf_count.set("0")
            self.med_conf_count.set("0")
            self.low_conf_count.set("0")
            
            # Reset validation
            self.validation_status.set("Not Validated")
            self.validation_text.config(state='normal')
            self.validation_text.delete(1.0, tk.END)
            self.validation_text.config(state='disabled')
            
            # Reset start button
            self.start_button.config(state='disabled')
            
            # Reset config path
            self.config_path = None
            
            # Reset window title
            self.title("Altium to KiCAD Database Migration Tool")
            
            # Update status
            self.status_bar.set_status("Project reset")
            logging.info("Project reset")
    
    def add_recent_project(self, path):
        """Add a project to the recent projects list."""
        # Load recent projects
        recent_projects = self.config_manager.get_config_value('recent_projects', [])
        
        # Add current project to the top
        if path in recent_projects:
            recent_projects.remove(path)
        recent_projects.insert(0, path)
        
        # Keep only the 5 most recent
        recent_projects = recent_projects[:5]
        
        # Save back to config
        self.config_manager.set_config_value('recent_projects', recent_projects)
        
        # Update menu
        self.update_recent_projects_menu()
    
    def update_recent_projects_menu(self):
        """Update the recent projects menu."""
        # Clear current menu
        self.recent_menu.delete(0, tk.END)
        
        # Get recent projects
        recent_projects = self.config_manager.get_config_value('recent_projects', [])
        
        if not recent_projects:
            self.recent_menu.add_command(label="No recent projects", state='disabled')
        else:
            for path in recent_projects:
                # Use basename for display
                name = os.path.basename(path)
                self.recent_menu.add_command(
                    label=name,
                    command=lambda p=path: self.load_project(p)
                )
    
    def on_closing(self):
        """Handle window closing event."""
        if self.is_migrating:
            if not messagebox.askyesno("Migration in Progress",
                                      "A migration is currently in progress. Are you sure you want to exit?"):
                return
        
        # Save window geometry
        geometry = {
            'width': self.winfo_width(),
            'height': self.winfo_height(),
            'x': self.winfo_x(),
            'y': self.winfo_y()
        }
        self.config_manager.set_config_value('window_geometry', geometry)
        
        # Destroy window
        self.destroy()
    
    def on_theme_change(self, theme):
        """Change the application theme."""
        try:
            # Save theme preference
            self.config_manager.set_config_value('theme', theme)
            
            # Apply theme
            if theme == "light":
                self.tk.call("set_theme", "light")
            elif theme == "dark":
                self.tk.call("set_theme", "dark")
            else:  # system
                # Detect system theme
                if platform.system() == "Windows":
                    import winreg
                    try:
                        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                        key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                        if value == 0:
                            self.tk.call("set_theme", "dark")
                        else:
                            self.tk.call("set_theme", "light")
                    except:
                        # Default to light theme if detection fails
                        self.tk.call("set_theme", "light")
                else:
                    # Default to light theme on non-Windows platforms
                    self.tk.call("set_theme", "light")
        except tk.TclError:
            # If theme engine is not available, ignore
            pass
        
        # Update status
        self.status_bar.set_status(f"Theme changed to {theme}")
        logging.info(f"Theme changed to {theme}")


def main(config_path=None, theme="system", window_size=(1024, 768)):
    """Main entry point for the GUI application."""
    # Create and configure the main application window
    app = MigrationToolMainWindow(
        config_path=config_path,
        theme=theme,
        window_size=window_size
    )
    
    # Start the application
    app.mainloop()