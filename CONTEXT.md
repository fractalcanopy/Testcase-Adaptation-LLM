# Project Context: LLM-Powered Test Case Adaptation Tool (Python)

## 1. Project Goal

The primary goal of this Python project is to develop a prototype tool that automates the **adaptation and integration of existing Java unit test cases** from one software fork into another. The tool will leverage Large Language Models (LLMs) to diagnose integration failures and suggest necessary code modifications to make the test case compatible with the target project. This project is part of a Bachelor thesis.

## 2. Core Functionality / Workflow

The tool follows these main steps, as implemented in `src/main.py`:

1.  **Input:**
    *   A specific Java unit test case (as a source code file) from a source project.
    *   The target Java project, including its source code (Unit Under Test - UUT) and `pom.xml`.
    *   The benchmark dataset is intended to be from Mukelabai et al. ASE 2023 paper (Java projects). The `scripts/explore_dataset.py` script is used for initial data exploration.

2.  **Initial Adaptation Attempt:**
    *   The tool copies the source test case file directly into the target project's Maven source structure (`src/test/java/...`).

3.  **Build & Execution Check:**
    *   The tool invokes a Maven build (`mvn clean test-compile`) on the target project using Python's `subprocess` module, as seen in `src/java_env_manager.py`.

4.  **LLM Analysis on Failure (Compilation):**
    *   If the build fails, the tool captures the `stderr` output from Maven.
    *   It parses the Maven error messages using regular expressions (`src/utils.py`) to identify specific compilation errors like "cannot find symbol".
    *   It constructs a detailed prompt for an LLM (`src/llm_analyzer.py`). This prompt includes:
        *   The original test case code.
        *   The relevant code from the target project's UUT.
        *   The parsed build error message.
        *   The content of the target project's `pom.xml`.

5.  **LLM Suggestion & Re-evaluation:**
    *   The LLM (Google Gemini) is queried to suggest code modifications for the *test case* to fix the build error.
    *   The tool extracts the Java code block from the LLM's response (`src/utils.py`).
    *   It overwrites the test case in the target project with the suggested code.
    *   It attempts to build the project again to verify if the fix was successful.

## 3. Key Technologies & Libraries

*   **Programming Language:** Python (3.10+)
*   **LLM APIs:**
    *   **Google Gemini API:** The primary model used for code generation and analysis, via the `google-generativeai` SDK.
*   **API Interaction:**
    *   `requests`: For fetching files from GitHub (`get_code_from_github` in `utils.py`).
*   **Environment Management:**
    *   `python-dotenv`: For managing API keys securely via a `.env` file.
    *   Virtual environments (`venv`): To isolate project dependencies.
*   **Build System Interaction (Java):**
    *   The `subprocess` module is used to invoke Maven (`mvn`) to compile and test Java projects.
*   **Code & Error Analysis:**
    *   The `re` module is used for regex-based parsing of Maven error logs.
    *   `pandas` is used for exploring the CSV benchmark dataset.

## 4. Current Project Structure

```
Testcase-Adaptation-LLM/
|-- .env                      # For API keys (GITIGNORED)
|-- .gitignore
|-- CONTEXT.md                # This file: Detailed project context for AI assistants
|-- create_dummy_projects.py  # Script to set up dummy Java projects for testing
|-- dummy_java_projects/      # Dummy Java projects (ProjectA, ProjectB) (GITIGNORED)
|-- requirements.txt          # Python dependencies
|-- README.md                 # Project overview, setup, and usage instructions
|-- scripts/
|   |-- explore_dataset.py    # Script to read and inspect the benchmark dataset
|-- src/                      # Main source code
    |-- main.py               # Orchestrates the end-to-end adaptation workflow
    |-- llm_analyzer.py       # Functions for constructing LLM prompts
    |-- java_env_manager.py   # Functions to invoke Maven builds on Java projects
    |-- utils.py              # Helper functions (error parsing, code extraction, file I/O)
    |-- test_apis.py          # Script for testing connections to LLM APIs
    |-- test.py               # Script for isolated testing of components
```

## 5. Core Challenges to Address (from Research Questions)

*   **RQ1:** LLM effectiveness in diagnosing build failures from direct test integration and suggesting initial fixes.
*   **RQ2:** LLM capability for basic test refactoring (e.g., renames, parameter changes).
*   **RQ3:** LLM capability for complex test adaptations (e.g., structural/semantic changes, Type 3/4 clones).

## 6. Development Notes

*   The project uses Git for version control.
*   The primary input for the tool is *existing* Java test cases and corresponding target project contexts. The tool does *not* focus on discovering or selecting which tests to propagate.
*   The evaluation will be based on the Mukelabai et al. ASE 2023 benchmark.
*   Focus is on the LLM's ability to understand Java code, errors, and suggest adaptations for *Java* test cases.

This `CONTEXT.md` should give AI assistants a good overview of what your Python project is about, its goals, how it's structured, and the technologies involved. Remember to keep it updated as your project evolves!

