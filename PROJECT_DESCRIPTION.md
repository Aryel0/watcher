    # Project Description: Semantic Codebase Analyst

This project implements a "Semantic Codebase Analyst" designed to act as a digital twin of a software project. Unlike traditional file watchers that only track timestamps, this system builds and maintains a comprehensive Knowledge Graph of the code structure.

# Agent803 Watcher: Semantic Codebase Analyst

## Executive Summary

**Agent803 Watcher** is an advanced, local-first code analysis tool designed to transform static file collections into a queryable **Knowledge Graph**. unlike traditional "grep" or file search tools, Watcher understands the *semantic relationships* within your code—linking classes to their defined methods, files to their dependencies, and historical changes to their authors.

Built for developers, auditors, and AI agents, it provides a strictly **No-Code / Low-Config** experience, operating entirely locally without needing complex CI/CD pipelines or cloud dependencies. It features a real-time file watcher, a rich Terminal User Interface (TUI), and powerful graph query capabilities.

---

## Key Features

### 1. Semantic Knowledge Graph

Instead of treating code as text, Watcher builds a directed property graph:

- **Nodes**: Files, Directories, Classes, Functions, Imports, Authors, Snapshots.
- **Edges**: `DEFINES` (File->Class), `IMPORTS` (File->Module), `CALLS` (Function->Function), `INHERITS` (Class->Class).
- **Polyglot Support**: Deep AST analysis for Python (`.py`, `.ipynb`) and regex-based structural analysis for JavaScript, C, HTML, CSS, and JSON.

### 2. Interactive TUI (Terminal User Interface)

A professional-grade terminal application (`watcher ui`) for exploring the codebase:

- **Tree Browser**: Navigate the project structure grouped by node type.
- **Impact Analysis**: Instantly view "Influenced By" (Incoming) and "Influences" (Outgoing) relationships.
- **Rich Metadata**: View function signatures (`def foo(x: int) -> bool`), docstrings, and class inheritance hierarchies.
- **Compare Mode**: Side-by-side comparison of files (content diffs) or symbols (graph topology differences).

### 3. Local History & Time Travel

- **Snapshotting**: Automatically captures file revisions on save.
- **No-Git Dependency**: Works in "No-Code" environments where Git might not be initialized.
- **Revision Graph**: Tracks how files evolve over time (`AFFECTS` edges from Snapshots to Files).

### 4. Code Quality & Insight (Planned)

- **Cyclomatic Complexity**: Highlights overly complex functions.
- **Dead Code Detection**: Identifies "Orphan Nodes" (functions with 0 callers).

---

## Installation

Project is managed with modern Python tooling (`pyproject.toml`).

```bash
# Clone the repository
git clone https://github.com/your-org/agent803.git
cd agent803/watcher

# Install in editable mode
pip install -e .
```

---

## Usage Guide

### 1. The Watcher Service

Start the real-time daemon to monitor and index your project:

```bash
python -m watcher
```

*The service runs in the background, updating the graph as you modify files.*

### 2. Interactive Explorer (TUI)

Launch the visual interface:

```bash
watcher ui
```

- **Navigation**: Use Arrow Keys.
- **Search**: Type in the top bar to filter nodes.
- **Compare**: Press `c` on a node -> Select another node to compare.

### 3. CLI Commands

For quick queries or integration with other tools:

```bash
# Analyze a specific file
watcher inspect ./my_script.py

# Query the graph for a symbol
watcher where MyClass

# Export graph to JSON/GraphML
watcher export --format json
```

---

## Technical Architecture

- **Core**: Python 3.10+
- **Graph Database**: `networkx` identifying topological relationships.
- **Parsing**:
  - `ast` module for Python (Symbol table, Docstrings, Signatures).
  - `watchdog` for OS-level file system events.
- **UI**: `Textual` framework for reactive TUI components.
- **Storage**: Local JSON/Pickle based persistence (GraphML compliant export).

## Professional Use Cases

1. **Onboarding**: New developers can use the "Impact Analysis" to understand what breaks if they change a core function.
2. **Code Audit**: Quickly list all dependencies and "orphan" functions before a release.
3. **AI Context**: Export the Knowledge Graph to JSON to give LLMs a structural understanding of the codebase, reducing hallucination in code generation tasks.
    - **TUI**: A rich terminal user interface for interactive exploration, allowing developers to visualize the project structure and drill down into specific components.

## Technical Implementation

The system is built in Python, leveraging `networkx` for graph management, `watchdog` for file monitoring, and `Textual` for the user interface. It is designed to be language-agnostic in architecture, with the current implementation featuring a robust Python AST parser.
