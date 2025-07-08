# LLM-Powered Test Case Adaptation Tool

This project is a Python-based prototype tool designed to automate the adaptation and integration of existing Java unit test cases from one software fork into another. It leverages Large Language Models (LLMs) to diagnose integration failures and suggest code modifications to make test cases compatible with the target project. This tool includes comprehensive metrics tracking and performance analysis capabilities. This tool is being developed as part of a Bachelor thesis.

## Core Functionality / Workflow

The tool follows these main steps:

1.  **Input:**
    - A specific Java unit test case (as source code).
    - The target Java project's relevant source code (Unit Under Test - UUT).
    - Supports both local dummy projects and real dataset processing.
    - Designed with the Mukelabai et al. ASE 2023 benchmark dataset in mind.

2.  **Pre-Build Validation:**
    - Validates that the target project builds correctly before adaptation.
    - Automatically attempts to fix common build configuration issues (pom.xml).
    - Records pre-build success/failure in metrics.

3.  **Initial Adaptation Attempt:**
    - Places the source test case into the target project with correct package structure.
    - Attempts initial compilation.

4.  **Iterative Build & LLM Analysis:**
    - Supports multiple adaptation attempts (configurable, default: 3).
    - On build failure:
      - Parses Maven error messages with detailed categorization.
      - Constructs context-aware prompts for LLM analysis.
      - Extracts clone type classifications (Type-1 through Type-4) from LLM responses.
      - Applies suggested fixes and retries compilation.

5.  **Comprehensive Metrics Tracking:**
    - Tracks success rates, error types, execution times, and LLM usage.
    - Records clone classifications and adaptation attempt patterns.
    - Generates detailed performance reports and summaries.

## Key Technologies & Libraries

- **Programming Language:** Python (3.10+)
- **LLM APIs:**
  - Google Gemini API (`google-generativeai`)
- **Data Processing:**
  - `requests` (for GitHub API interaction)
  - JSON-based metrics storage and analysis
- **Environment Management:**
  - `python-dotenv` (for API keys)
  - `venv` (for virtual environments)
- **Java Build System Interaction:**
  - `subprocess` (to invoke Maven for compiling and testing Java projects)
- **Metrics & Analysis:**
  - Built-in performance tracking and statistical analysis

## Project Structure

```
Testcase-Adaptation-LLM/
|-- .env                      # For API keys (GITIGNORED)
|-- .gitignore
|-- adaptation_metrics.json   # Generated metrics and performance data
|-- CONTEXT.md                # Detailed project context for AI assistants
|-- create_dummy_projects.py  # Script to set up dummy Java projects for testing
|-- dummy_java_projects/      # Dummy Java projects (ProjectA, ProjectB) (GITIGNORED)
|   |-- ProjectA/
|   |-- ProjectB/
|-- requirements.txt          # Python dependencies
|-- src/                      # Main source code
|   |-- main.py               # Orchestrates the workflow
|   |-- llm_analyzer.py       # Functions for LLM interaction and prompt construction
|   |-- java_env_manager.py   # Functions to manage Java build/test execution
|   |-- utils.py              # Utility functions (error parsing, code extraction)
|   |-- metrics_tracker.py    # Comprehensive metrics tracking and analysis
|   |-- process_dataset.py    # Dataset processing for batch operations
|   |-- test_apis.py          # Scripts for testing LLM API connections
|-- data/                     # Dataset and project storage
|   |-- projects/             # Cloned target projects
|-- README.md                 # This file
```

## Key Features

### Advanced Error Parsing
- Categorizes Maven compilation errors (cannot find symbol, package does not exist, etc.)
- Extracts specific error details (symbol names, locations, types)
- Handles environment errors and unknown error types gracefully

### LLM Integration
- Context-aware prompt construction including:
  - Original test case code
  - Target class implementation
  - Build configuration (pom.xml)
  - Specific error details
- Automatic extraction of Java code blocks from LLM responses
- Clone type classification extraction (Type-1 through Type-4)

### Metrics and Performance Tracking
- **Adaptation Success Rates:** Overall and per-attempt success tracking
- **Error Analysis:** Distribution of error types and patterns
- **LLM Usage Metrics:** Response lengths and classification accuracy
- **Timing Analysis:** Execution time statistics and bottleneck identification
- **Build Configuration:** Pre-build failures and automatic fixes applied

### Dataset Processing
- GitHub API integration for fetching source test cases
- Support for processing benchmark datasets
- Batch processing capabilities for multiple test case adaptations

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd Testcase-Adaptation-LLM
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up API Keys:**
    - Create a `.env` file in the project root (`Testcase-Adaptation-LLM/.env`).
    - Add your API keys to the `.env` file:
      ```env
      GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
      ```
    - Ensure `.env` is listed in your `.gitignore` file (it is, by default).

5.  **Create Dummy Java Projects (for testing):**
    ```bash
    python create_dummy_projects.py
    ```

## Usage

### Basic Workflow

The main workflow is orchestrated by `src/main.py`. You can configure it to use either dummy projects or real dataset:

```bash
cd src
python main.py
```

### Configuration Options

In `main.py`, set `USE_DUMMY_PROJECTS = True` for testing with dummy projects, or `False` for real dataset processing.

### Real Dataset Usage

For real dataset processing:

1. **Clone target repositories:**
   ```bash
   mkdir -p data/projects
   git clone https://github.com/dbrambilla/jesque.git data/projects/jesque
   ```

2. **Configure source and target:**
   - Edit the repository and file paths in `main.py`
   - The tool will automatically fetch source test cases from GitHub

### Metrics Analysis

After running adaptations, view comprehensive metrics:

```bash
python -c "from metrics_tracker import global_metrics; global_metrics.print_summary()"
```

Metrics are automatically saved to `adaptation_metrics.json` with detailed statistics including:
- Success rates and attempt distributions
- Error type categorization
- Clone classification results
- Performance timing analysis

### Example Metrics Output

```json
{
  "summary": {
    "total_adaptations": 2,
    "successful_adaptations": 2,
    "success_rate": 1.0,
    "classification_distribution": {
      "Type-2": 1
    },
    "success_by_attempt": {
      "1": 1,
      "2": 1
    },
    "error_type_distribution": {
      "cannot find symbol": 1
    },
    "average_execution_time_seconds": 18.49
  }
}
```

## Advanced Features

### Multiple Adaptation Attempts
The tool supports up to 3 adaptation attempts by default, using iterative LLM feedback to refine solutions.

### Automatic Build Configuration Fixes
Automatically detects and attempts to fix common Maven build issues, particularly pom.xml configuration problems.

### Clone Type Classification
Extracts and records clone type classifications (Type-1 through Type-4) from LLM responses for research analysis.

### GitHub Integration
Direct integration with GitHub API for fetching source test cases from repositories, enabling seamless dataset processing.

## Development Notes

- The tool is designed for the Mukelabai et al. ASE 2023 benchmark evaluation.
- Comprehensive metrics collection enables detailed performance analysis and research insights.
- The architecture supports extension to additional LLM providers and build systems.
- Error parsing is specifically tuned for Maven/Java compilation errors.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## License

This project is currently unlicensed. (Consider adding an OSI approved license like MIT or Apache 2.0).
