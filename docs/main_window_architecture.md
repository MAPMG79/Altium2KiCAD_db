# Main Application Window Architecture Design

## Overview

This document describes the architecture design for the main application window of the Altium to KiCAD Database Migration Tool. The design provides a comprehensive GUI framework that integrates with existing dialog classes and provides a smooth user experience for database migration workflows.

## 1. Main Application Class Structure

### Class Name: `MigrationToolMainWindow`

**Inheritance:** 
- Inherits from `tk.Tk` (main window)
- Implements a state management pattern

### Key Attributes

```python
class MigrationToolMainWindow(tk.Tk):
    # Configuration Management
    config_manager: ConfigManager
    config_path: Optional[str]
    
    # State Management
    current_project: Dict[str, Any]  # Active migration project state
    source_connection: Optional[Dict[str, str]]  # Altium DB connection
    target_settings: Dict[str, Any]  # KiCAD output settings
    mapping_rules: Dict[str, Dict]  # Symbol, footprint, category rules
    
    # Core Components
    parser: Optional[AltiumDbLibParser]
    mapping_engine: Optional[ComponentMappingEngine]
    generator: Optional[KiCADDbLibGenerator]
    
    # UI Components
    log_handler: LoggingHandler
    main_notebook: ttk.Notebook
    status_bar: StatusBar
    
    # Migration State
    migration_thread: Optional[threading.Thread]
    is_migrating: bool
    migration_results: Optional[Dict]
```

### Key Methods

```python
# Initialization
def __init__(self, config_path=None, theme="system", window_size=(1024, 768))
def setup_ui(self)
def setup_menus(self)
def setup_logging(self)
def load_configuration(self, config_path=None)

# Dialog Management
def open_database_connection_dialog(self)
def open_mapping_rules_dialog(self, rule_type)
def open_batch_processing_dialog(self)
def show_help(self, topic="general")
def show_migration_progress(self)

# State Management
def save_project(self, path=None)
def load_project(self, path)
def reset_project(self)
def validate_migration_readiness(self)

# Migration Operations
def start_migration(self)
def cancel_migration(self)
def handle_migration_complete(self, results)

# Event Handlers
def on_closing(self)
def on_theme_change(self, theme)
```

## 2. UI Layout Design

### Main Window Structure

```
┌─────────────────────────────────────────────────────────┐
│ Menu Bar                                                │
├─────────────────────────────────────────────────────────┤
│ Tool Bar (Quick Actions)                                │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Main Content Area (Notebook)                        │ │
│ │ ┌─────────────┬─────────────┬────────────┬────────┐│ │
│ │ │ Source      │ Mapping     │ Output     │ Review ││ │
│ │ ├─────────────┴─────────────┴────────────┴────────┤│ │
│ │ │                                                   ││ │
│ │ │ Tab Content Area                                  ││ │
│ │ │                                                   ││ │
│ │ └───────────────────────────────────────────────────┘│ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Log Panel (Collapsible)                             │ │
│ │                                                      │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ Status Bar                                              │
└─────────────────────────────────────────────────────────┘
```

### Tab Organization

1. **Source Tab:**
   - Database connection configuration
   - Table selection
   - Field mapping preview
   - Quick stats (components found, etc.)

2. **Mapping Tab:**
   - Symbol mapping rules management
   - Footprint mapping rules management
   - Category mapping rules management
   - Confidence threshold settings
   - Mapping preview

3. **Output Tab:**
   - Output directory selection
   - KiCAD database settings
   - Field mapping configuration
   - Export options

4. **Review Tab:**
   - Pre-migration summary
   - Validation results
   - Mapping statistics
   - Migration action buttons

### Menu Structure

```
File
├── New Project
├── Open Project...
├── Save Project
├── Save Project As...
├── ─────────────────
├── Import Configuration...
├── Export Configuration...
├── ─────────────────
├── Recent Projects
├── ─────────────────
└── Exit

Edit
├── Preferences...
├── ─────────────────
├── Clear Log
└── Reset Settings

Database
├── Connect to Database...
├── Test Connection
├── ─────────────────
├── Refresh Tables
└── View Schema

Mapping
├── Symbol Rules...
├── Footprint Rules...
├── Category Rules...
├── ─────────────────
├── Import Rules...
├── Export Rules...
├── ─────────────────
└── Auto-Generate Rules

Tools
├── Batch Processing...
├── Validate Mappings
├── ─────────────────
├── Generate Report
└── Export Statistics

View
├── Theme
│   ├── Light
│   ├── Dark
│   └── System
├── ─────────────────
├── Show Log Panel
├── Show Status Bar
└── Full Screen

Help
├── Documentation
├── Getting Started
├── ─────────────────
├── Database Help
├── Mapping Help
├── Troubleshooting
├── ─────────────────
└── About
```

## 3. Integration Patterns

### Dialog Launch Pattern

```python
def open_dialog_pattern(self, DialogClass, **kwargs):
    """Standard pattern for launching modal dialogs"""
    dialog = DialogClass(self, **kwargs)
    self.wait_window(dialog.window)
    return dialog.result
```

### Data Flow Architecture

```
Main Window State
    ↓
Dialog (reads initial state)
    ↓
User Interaction
    ↓
Dialog Result
    ↓
Main Window State Update
    ↓
UI Update & Validation
```

### Event Handling

- Use observer pattern for state changes
- Dialogs return results via `dialog.result` attribute
- Main window validates and applies changes
- Triggers UI updates across all affected components

## 4. Configuration Management

### Configuration Hierarchy

1. Default configuration (from `default_config.yaml`)
2. User configuration (from home directory)
3. Project configuration (project-specific overrides)
4. Runtime configuration (CLI arguments)

### Configuration Loading Strategy

```python
def load_configuration(self, config_path=None):
    # 1. Load defaults
    config = self.config_manager.load_defaults()
    
    # 2. Merge user config
    user_config = self.config_manager.load_user_config()
    config = deep_merge(config, user_config)
    
    # 3. Merge project config if provided
    if config_path:
        project_config = self.config_manager.load_config(config_path)
        config = deep_merge(config, project_config)
    
    # 4. Apply to application state
    self.apply_configuration(config)
```

### State Persistence

- Auto-save project state on significant changes
- Save window geometry and UI preferences
- Maintain recent projects list
- Store last used directories

## 5. Implementation Strategy

### Phase 1: Core Structure
1. Create `MigrationToolMainWindow` class
2. Implement basic window setup and layout
3. Add menu bar and status bar
4. Implement configuration loading

### Phase 2: Tab Implementation
1. Create Source tab with database connection UI
2. Create Mapping tab with rules management
3. Create Output tab with settings
4. Create Review tab with summary

### Phase 3: Dialog Integration
1. Wire up existing dialogs to menu items
2. Implement data flow between dialogs and main window
3. Add state validation after dialog interactions

### Phase 4: Migration Workflow
1. Implement migration preparation and validation
2. Add progress tracking with MigrationProgressDialog
3. Handle migration results and error reporting
4. Add post-migration actions

### Phase 5: Polish & Features
1. Add keyboard shortcuts
2. Implement drag-and-drop support
3. Add context menus
4. Implement undo/redo for configurations
5. Add tooltips and status messages

### Entry Point Implementation

```python
def main(config_path=None, theme="system", window_size=(1024, 768)):
    """Main entry point for the GUI application"""
    # Create and configure main window
    app = MigrationToolMainWindow(
        config_path=config_path,
        theme=theme,
        window_size=window_size
    )
    
    # Start the application
    app.mainloop()
```

## 6. Architecture Diagrams

### Class Architecture Diagram

```mermaid
classDiagram
    class MigrationToolMainWindow {
        -ConfigManager config_manager
        -str config_path
        -dict current_project
        -dict source_connection
        -dict target_settings
        -dict mapping_rules
        -AltiumDbLibParser parser
        -ComponentMappingEngine mapping_engine
        -KiCADDbLibGenerator generator
        -LoggingHandler log_handler
        -ttk.Notebook main_notebook
        -StatusBar status_bar
        -bool is_migrating
        +__init__(config_path, theme, window_size)
        +setup_ui()
        +setup_menus()
        +load_configuration()
        +start_migration()
        +save_project()
        +load_project()
    }
    
    class LoggingHandler {
        -text_widget
        +emit(record)
    }
    
    class MigrationProgressDialog {
        -window
        -progress
        -cancelled
        +update_status(message)
        +update_task_progress(value)
        +log_message(message)
    }
    
    class DatabaseConnectionDialog {
        -window
        -result
        -db_type
        +build_connection_string()
        +test_connection()
        +save()
    }
    
    class MappingRuleDialog {
        -window
        -rule_type
        -existing_rules
        -result
        +add_rule()
        +update_rule()
        +import_rules()
        +export_rules()
    }
    
    class BatchProcessDialog {
        -window
        -files
        -result
        +add_files()
        +start_processing()
        +save_batch()
    }
    
    class HelpDialog {
        -window
        -topic
        +show_topic(topic)
    }
    
    MigrationToolMainWindow --> LoggingHandler : uses
    MigrationToolMainWindow --> MigrationProgressDialog : launches
    MigrationToolMainWindow --> DatabaseConnectionDialog : launches
    MigrationToolMainWindow --> MappingRuleDialog : launches
    MigrationToolMainWindow --> BatchProcessDialog : launches
    MigrationToolMainWindow --> HelpDialog : launches
    MigrationToolMainWindow --> ConfigManager : uses
    MigrationToolMainWindow --> AltiumDbLibParser : uses
    MigrationToolMainWindow --> ComponentMappingEngine : uses
    MigrationToolMainWindow --> KiCADDbLibGenerator : uses
```

### UI Component Hierarchy

```mermaid
graph TD
    A[MigrationToolMainWindow] --> B[Menu Bar]
    A --> C[Tool Bar]
    A --> D[Main Content Area]
    A --> E[Log Panel]
    A --> F[Status Bar]
    
    B --> B1[File Menu]
    B --> B2[Edit Menu]
    B --> B3[Database Menu]
    B --> B4[Mapping Menu]
    B --> B5[Tools Menu]
    B --> B6[View Menu]
    B --> B7[Help Menu]
    
    D --> G[ttk.Notebook]
    G --> G1[Source Tab]
    G --> G2[Mapping Tab]
    G --> G3[Output Tab]
    G --> G4[Review Tab]
    
    G1 --> G1A[Connection Status]
    G1 --> G1B[Table Selection]
    G1 --> G1C[Field Preview]
    
    G2 --> G2A[Symbol Rules]
    G2 --> G2B[Footprint Rules]
    G2 --> G2C[Category Rules]
    
    G3 --> G3A[Output Directory]
    G3 --> G3B[KiCAD Settings]
    G3 --> G3C[Export Options]
    
    G4 --> G4A[Validation Summary]
    G4 --> G4B[Migration Stats]
    G4 --> G4C[Action Buttons]
    
    E --> E1[ScrolledText Widget]
    E --> E2[Clear Button]
    E --> E3[Toggle Visibility]
```

### Data Flow Diagram

```mermaid
flowchart LR
    subgraph User Interface
        UI[Main Window]
        D1[Database Dialog]
        D2[Mapping Dialog]
        D3[Batch Dialog]
    end
    
    subgraph State Management
        PS[Project State]
        CS[Connection State]
        MS[Mapping State]
        OS[Output State]
    end
    
    subgraph Core Components
        AP[Altium Parser]
        ME[Mapping Engine]  
        KG[KiCAD Generator]
    end
    
    subgraph Configuration
        DC[Default Config]
        UC[User Config]
        PC[Project Config]
        CM[Config Manager]
    end
    
    UI --> D1
    UI --> D2
    UI --> D3
    
    D1 --> CS
    D2 --> MS
    
    UI --> PS
    PS --> CS
    PS --> MS
    PS --> OS
    
    CS --> AP
    MS --> ME
    OS --> KG
    
    DC --> CM
    UC --> CM
    PC --> CM
    CM --> PS
    
    AP --> ME
    ME --> KG
```

### Migration Workflow State Machine

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> ConfiguringSource : Configure Source
    
    ConfiguringSource --> SourceConfigured : Valid Connection
    ConfiguringSource --> Idle : Cancel
    
    SourceConfigured --> ConfiguringMapping : Configure Mapping
    SourceConfigured --> Idle : Reset
    
    ConfiguringMapping --> MappingConfigured : Rules Set
    ConfiguringMapping --> SourceConfigured : Back
    
    MappingConfigured --> ConfiguringOutput : Configure Output
    MappingConfigured --> ConfiguringMapping : Edit Rules
    
    ConfiguringOutput --> ReadyToMigrate : Settings Complete
    ConfiguringOutput --> MappingConfigured : Back
    
    ReadyToMigrate --> Validating : Start Migration
    ReadyToMigrate --> ConfiguringOutput : Edit Settings
    
    Validating --> Migrating : Validation Pass
    Validating --> ReadyToMigrate : Validation Fail
    
    Migrating --> MigrationComplete : Success
    Migrating --> MigrationFailed : Error
    Migrating --> Idle : Cancel
    
    MigrationComplete --> Idle : New Migration
    MigrationFailed --> ReadyToMigrate : Retry
    MigrationFailed --> Idle : Cancel
```

### Dialog Integration Pattern

```mermaid
sequenceDiagram
    participant MW as Main Window
    participant DI as Dialog Instance
    participant ST as State Manager
    participant UI as UI Components
    
    MW->>MW: User triggers action
    MW->>DI: Create Dialog(current_state)
    DI->>DI: Initialize with state
    DI->>DI: Show modal window
    
    loop User Interaction
        DI->>DI: Handle user input
        DI->>DI: Validate input
    end
    
    alt User Saves
        DI->>DI: Set result
        DI->>MW: Return result
        MW->>ST: Update state
        ST->>UI: Trigger UI update
        UI->>UI: Refresh views
    else User Cancels
        DI->>MW: Return None
        MW->>MW: No state change
    end
```

### Configuration Loading Sequence

```mermaid
sequenceDiagram
    participant APP as Application
    participant CM as ConfigManager
    participant FS as File System
    participant MW as Main Window
    
    APP->>CM: Initialize ConfigManager
    
    CM->>FS: Load default_config.yaml
    FS-->>CM: Default config
    
    CM->>FS: Check user config exists
    alt User config exists
        CM->>FS: Load user config
        FS-->>CM: User config
        CM->>CM: Merge with defaults
    end
    
    alt CLI config path provided
        CM->>FS: Load project config
        FS-->>CM: Project config
        CM->>CM: Merge with current
    end
    
    CM-->>APP: Final configuration
    APP->>MW: Create window with config
    MW->>MW: Apply configuration
    MW->>MW: Setup UI with config
```

### Component Interaction Overview

```mermaid
graph TB
    subgraph Main Application
        MW[Main Window]
        TB[Tab Container]
        MB[Menu Bar]
        SB[Status Bar]
        LP[Log Panel]
    end
    
    subgraph Dialogs
        DCD[Database Connection]
        MRD[Mapping Rules]
        BPD[Batch Process]
        HD[Help Dialog]
        MPD[Migration Progress]
    end
    
    subgraph Core Engine
        AP[Altium Parser]
        ME[Mapping Engine]
        KG[KiCAD Generator]
    end
    
    subgraph State & Config
        SM[State Manager]
        CM[Config Manager]
        PM[Project Manager]
    end
    
    MW --> TB
    MW --> MB
    MW --> SB
    MW --> LP
    
    MB --> DCD
    MB --> MRD
    MB --> BPD
    MB --> HD
    
    MW --> MPD
    
    MW --> SM
    SM --> CM
    SM --> PM
    
    SM --> AP
    SM --> ME
    SM --> KG
    
    style MW fill:#f9f,stroke:#333,stroke-width:4px
    style SM fill:#bbf,stroke:#333,stroke-width:2px
```

## Key Design Benefits

1. **Clear Separation of Concerns**
   - UI logic separated from business logic
   - State management centralized
   - Configuration handling isolated

2. **Extensible Architecture**
   - Easy to add new tabs or dialogs
   - Plugin-friendly design
   - Clear integration points

3. **User-Friendly Workflow**
   - Step-by-step migration process
   - Clear visual feedback
   - Comprehensive help system

4. **Professional UI/UX**
   - Modern tabbed interface
   - Consistent dialog patterns
   - Real-time logging and status updates

5. **Robust State Management**
   - Project save/load functionality
   - Configuration persistence
   - Undo/redo capability (future enhancement)

This architecture provides a solid foundation for implementing the main application window while maintaining compatibility with existing components and allowing for future enhancements.