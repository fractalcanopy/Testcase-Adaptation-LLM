# Project Context: LLM-Powered Test Case Adaptation Tool (Python)

## 1. Project Goal

The primary goal of this Python project is to develop a prototype tool that automates the **adaptation and integration of existing Java unit test cases** from one software fork into another. The tool leverages Large Language Models (LLMs) to diagnose integration failures and suggest necessary code modifications to make the test case compatible with the target project. This project is part of a Bachelor thesis and includes comprehensive metrics tracking and performance analysis capabilities for research evaluation.

## 2. Core Functionality / Workflow

The tool follows these main steps, as implemented across the core modules:

1.  **Input & Dataset Processing:**

    - Processes benchmark datasets (Mukelabai et al. ASE 2023) via `scripts/process_dataset.py`
    - Fetches source test cases directly from GitHub repositories using `src/utils.py`
    - Supports both dummy projects for testing and real dataset processing
    - Filters projects by build success using `scripts/write_matching_projects.py`

2.  **Pre-Build Validation:**

    - Validates that target projects build correctly before adaptation attempts
    - Automatically detects build systems (Maven/Gradle) via `src/java_env_manager.py`
    - Applies automatic fixes for common build configuration issues (pom.xml)
    - Records pre-build success/failure in comprehensive metrics

3.  **Test Case Integration:**

    - Places source test cases into target project's Maven/Gradle structure
    - Handles package structure alignment and file placement
    - Creates backup copies for restoration on failure

4.  **Iterative Build & LLM Analysis:**

    - Supports multiple adaptation attempts (configurable, default: 3)
    - On build failure:
      - Parses Maven/Gradle error messages with detailed categorization (`src/utils.py`)
      - Constructs context-aware prompts including test code, UUT code, build config, and error details (`src/llm_analyzer.py`)
      - Extracts clone type classifications (Type-1 through Type-4) from LLM responses
      - Applies suggested fixes and retries compilation

5.  **Comprehensive Metrics & Analysis:**
    - Tracks adaptation success rates, error types, execution times via `src/metrics_tracker.py`
    - Records LLM usage metrics, response lengths, and classification accuracy
    - Generates detailed performance reports and research-oriented analytics
    - Supports multiple output formats (JSON) for further analysis

## 3. Key Technologies & Libraries

- **Programming Language:** Python (3.10+)
- **LLM APIs:**
  - **Google Gemini API:** Primary model for code analysis and generation (`google-generativeai`)
- **Data Processing:**
  - `requests`: GitHub API integration for fetching source test cases
  - `pandas`: Dataset processing and CSV manipulation
  - JSON-based metrics storage and analysis
- **Environment Management:**
  - `python-dotenv`: Secure API key management via `.env` files
  - Virtual environments (`venv`): Dependency isolation
- **Java Build System Interaction:**
  - `subprocess`: Maven/Gradle build invocation and output capture
  - Support for both Maven (`mvn`) and Gradle (`gradle`) build systems
- **Metrics & Analysis:**
  - Built-in performance tracking and statistical analysis
  - Research-oriented data collection for academic evaluation

## 4. Core Scripts & Modules

### Primary Components:

- **`src/main.py`** - Main orchestration module that coordinates the entire adaptation workflow
- **`src/utils.py`** - Core utility functions for error parsing, code extraction, GitHub integration, and file operations
- **`src/metrics_tracker.py`** - Comprehensive metrics collection, analysis, and reporting system
- **`src/java_env_manager.py`** - Java build system management (Maven/Gradle detection, execution, error handling)
- **`src/llm_analyzer.py`** - LLM integration, prompt construction, and response processing

### Dataset Processing:

- **`scripts/process_dataset.py`** - Batch processing of benchmark datasets, repository cloning, and workflow orchestration
- **`scripts/write_matching_projects.py`** - Dataset filtering, project matching, and build validation

### Supporting Scripts:

- **`scripts/explore_dataset.py`** - Dataset exploration and analysis tools
- **`scripts/pom_maintenance.py`** - POM file maintenance and build configuration fixes
- **`create_dummy_projects.py`** - Test project generation for development and testing

## 5. Current Project Structure

```
Testcase-Adaptation-LLM/
|-- .env                      # API keys (GITIGNORED)
|-- .gitignore
|-- adaptation_metrics*.json  # Generated metrics and performance data
|-- CONTEXT.md                # This file: Project context for AI assistants
|-- create_dummy_projects.py  # Dummy Java project generation for testing
|-- dummy_java_projects/      # Test projects (ProjectA, ProjectB) (GITIGNORED)
|-- requirements.txt          # Python dependencies
|-- README.md                 # Comprehensive project documentation
|-- data/                     # Dataset and project storage
|   |-- projects/             # Cloned target projects for processing
|   |-- *.csv                 # Benchmark datasets
|-- scripts/                  # Dataset processing and utility scripts
|   |-- process_dataset.py    # Main dataset processing pipeline
|   |-- write_matching_projects.py  # Project filtering and validation
|   |-- explore_dataset.py    # Dataset exploration tools
|   |-- pom_maintenance.py    # Build configuration maintenance
|-- src/                      # Core source code
    |-- main.py               # Primary workflow orchestration
    |-- metrics_tracker.py    # Comprehensive metrics and analytics
    |-- utils.py              # Core utilities (parsing, GitHub, file ops)
    |-- java_env_manager.py   # Java build system management
    |-- llm_analyzer.py       # LLM integration and prompt engineering
    |-- test_apis.py          # API connection testing
    |-- test.py               # Component testing utilities
```

## 6. Research Focus & Evaluation

- **RQ1:** LLM effectiveness in diagnosing build failures and suggesting fixes
- **RQ2:** LLM capability for basic test refactoring (method renames, parameter changes)
- **RQ3:** LLM capability for complex adaptations (structural/semantic changes, Type-3/4 clones)

### Metrics & Analysis:

- Adaptation success rates across different clone types
- Error categorization and resolution patterns
- LLM response quality and accuracy measurements
- Performance benchmarking and execution time analysis
- Build configuration fix effectiveness

## 7. Development Notes

- Designed specifically for the Mukelabai et al. ASE 2023 benchmark evaluation
- Supports both controlled testing (dummy projects) and real-world dataset processing
- Comprehensive error handling and recovery mechanisms
- Configurable cleanup behavior for failed adaptations
- Extensible architecture for additional LLM providers and build systems
- Focus on Java projects with Maven/Gradle build systems

This tool represents a complete research prototype for automated test case adaptation with detailed performance tracking and analysis capabilities suitable for academic
