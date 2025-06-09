# LLM-Powered Test Case Adaptation Tool

This project is a Python-based prototype tool designed to automate the adaptation and integration of existing Java unit test cases from one software fork into another. It leverages Large Language Models (LLMs) to diagnose integration failures and suggest code modifications to make test cases compatible with the target project. This tool is being developed as part of a Bachelor thesis.

## Core Functionality / Workflow

The tool follows these main steps:

1.  **Input:**

    - A specific Java unit test case (as source code).
    - The target Java project's relevant source code (Unit Under Test - UUT).
    - The tool is designed with the Mukelabai et al. ASE 2023 benchmark dataset in mind.

2.  **Initial Adaptation Attempt:**

    - The tool first attempts to integrate the source test case directly into the target project structure.

3.  **Build & Execution Check:**

    - It then tries to compile the target project with the new test case.
    - If compilation succeeds, it attempts to run the test case.

4.  **LLM Analysis on Failure:**

    - If the build or test execution fails, the tool:
      - Parses the error messages.
      - Constructs a detailed prompt for an LLM, including the original test code, target UUT code, and error details.

5.  **LLM Suggestion & Output:**
    - The LLM is queried to diagnose the failure and suggest code modifications for the test case.
    - The tool outputs the LLM's analysis and suggested changes.

## Key Technologies & Libraries

- **Programming Language:** Python (3.10+)
- **LLM APIs:**
  - Google Gemini API (`google-generativeai`)
- **API Interaction:**
  - `requests` (for general HTTP calls)
- **Environment Management:**
  - `python-dotenv` (for API keys)
  - `venv` (for virtual environments)
- **Java Build System Interaction:**
  - `subprocess` (to invoke Maven for compiling and testing Java projects)

## Project Structure

```
Testcase-Adaptation-LLM/
|-- .env                      # For API keys (GITIGNORED)
|-- .gitignore
|-- CONTEXT.md                # Detailed project context for AI assistants
|-- create_dummy_projects.py  # Script to set up dummy Java projects for testing
|-- dummy_java_projects/      # Dummy Java projects (ProjectA, ProjectB) (GITIGNORED)
|   |-- ProjectA/
|   |-- ProjectB/
|-- requirements.txt          # Python dependencies
|-- src/                      # Main source code
|   |-- main.py               # Orchestrates the workflow
|   |-- llm_analyzer.py       # Functions for LLM interaction
|   |-- java_env_manager.py   # Functions to manage Java build/test execution
|   |-- utils.py              # Utility functions
|   |-- test_apis.py          # Scripts for testing LLM API connections
|   |-- test.py               # (Likely a script for isolated testing of components)
|-- README.md                 # This file
```

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
    - Add your API keys to the `.env` file. For example:
      ```env
      GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
      # PERPLEXITY_API_KEY="YOUR_PERPLEXITY_API_KEY" # If using Perplexity
      ```
    - Ensure `.env` is listed in your `.gitignore` file (it is, by default).

5.  **Create Dummy Java Projects:**
    - Run the script to create the necessary dummy Java projects for testing the workflow:
      ```bash
      python create_dummy_projects.py
      ```
    - This will create `dummy_java_projects/ProjectA` and `dummy_java_projects/ProjectB`.

## Usage

The main workflow is orchestrated by `src/main.py`. It attempts to adapt a test case from a source project (ProjectA) to a target project (ProjectB) where a method has been renamed, causing a compilation error.

To run the main workflow:

```bash
cd src
python main.py
```

The script will:

1.  Read a test case from `dummy_java_projects/ProjectA`.
2.  Attempt to compile it within `dummy_java_projects/ProjectB` (this will initially fail).
3.  Parse the Maven compilation error.
4.  Construct a prompt for the LLM (Gemini).
5.  Query the LLM for a fix.
6.  Apply the suggested fix to the test case in ProjectB.
7.  Attempt to re-compile ProjectB.
8.  Print the results of each step.

## Development Notes

- The primary input for the tool is existing Java test cases and corresponding target project contexts.
- The evaluation will be based on the Mukelabai et al. ASE 2023 benchmark.
- The focus is on the LLM's ability to understand Java code, errors, and suggest adaptations for Java test cases.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## License

This project is currently unlicensed. (Consider adding an OSI approved license like MIT or Apache 2.0).
