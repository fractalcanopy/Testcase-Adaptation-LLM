# Project Context: LLM-Powered Test Case Adaptation Tool (Python)

## 1. Project Goal

The primary goal of this Python project is to develop a prototype tool that automates the **adaptation and integration of existing Java unit test cases** from one software fork into another. The tool will leverage Large Language Models (LLMs) to diagnose integration failures and suggest necessary code modifications to make the test case compatible with the target project. This project is part of a Bachelor thesis.

## 2. Core Functionality / Workflow

The tool is envisioned to follow these main steps:

1.  **Input:**
    * A specific Java unit test case (as source code string) from a source fork.
    * Information about the target project (e.g., relevant source code files of the unit under test (UUT), potentially build configuration files like `pom.xml` or `build.gradle`).
    * The benchmark dataset will be from Mukelabai et al. ASE 2023 paper (Java projects).

2.  **Initial Adaptation Attempt:**
    * The tool will first try a direct application of the test case into a representation of the target project (e.g., copy-pasting the test file).

3.  **Build & Execution Check:**
    * The tool will then attempt to compile the target project with the integrated test case.
    * If compilation is successful, it will attempt to run the test case.

4.  **LLM Analysis on Failure (Compilation or Test Execution):**
    * If the build fails (compilation error) or the test fails to execute correctly (runtime error or assertion failure):
        * The tool will parse and analyze the error message(s).
        * It will construct a detailed prompt for an LLM. This prompt will include:
            * The original test case code.
            * The relevant code from the target project's UUT.
            * The specific build error message(s) or test failure details.
            * Contextual information about the differences between the source and target UUTs if inferable.

5.  **LLM Suggestion & Output:**
    * The LLM will be queried to:
        * Diagnose the cause of the failure.
        * Suggest specific code modifications (refactorings) for the *test case* to make it compatible and correct for the target project.
    * The tool will present the LLM's assessment and suggested code changes to the user (initially, this might be console output; a more sophisticated interface is not a primary focus).

## 3. Key Technologies & Libraries

* **Programming Language:** Python (version 3.10+ recommended)
* **LLM APIs:**
    * **Perplexity API:** For initial exploration and development (due to available credits).
    * **Google Gemini API:** As another model for comparison and evaluation.
* **API Interaction:**
    * `requests` library: For making HTTP calls to the Perplexity API and potentially the GitHub API (if needed to fetch specific file versions, though the primary input is an existing test case).
    * `google-generativeai` SDK: For interacting with the Gemini API.
* **Environment Management:**
    * `python-dotenv`: For managing API keys securely via a `.env` file.
    * Virtual environments (`venv`): To isolate project dependencies.
* **Build System Interaction (for Java projects in the benchmark):**
    * The tool might need to invoke Java build tools (e.g., Maven, Gradle) externally using `subprocess` in Python to compile and run tests in the target project context. This is a complex part and might involve simplifying assumptions for the prototype.
* **Code Analysis (Potentially):**
    * Basic string manipulation and parsing for test case code and error messages.
    * More advanced static analysis libraries for Java (e.g., via Python wrappers or by parsing output from Java tools) are a *potential extension* but not the initial core.

## 4. Project Structure (Tentative/Planned)

```
project_root/
|-- venv/                     # Virtual environment
|-- src/                      # Main source code
|   |-- main.py               # Orchestrates the workflow
|   |-- llm_analyzer.py       # Functions for LLM interaction (prompting, parsing responses)
|   |-- java_env_manager.py   # (Hypothetical) Functions to manage/interact with Java build/test execution
|   |-- test_adapter.py       # Core logic for the adaptation workflow steps
|   |-- utils.py              # Utility functions
|-- tests/                    # Unit tests for THIS Python tool
|-- data/                     # To store benchmark dataset files (test cases, project snippets)
|-- .env                      # For API keys (GITIGNORED)
|-- .gitignore
|-- requirements.txt
|-- README.md
```

## 5. Core Challenges to Address (from Research Questions)

* **RQ1:** LLM effectiveness in diagnosing build failures from direct test integration and suggesting initial fixes.
* **RQ2:** LLM capability for basic test refactoring (e.g., renames, parameter changes).
* **RQ3:** LLM capability for complex test adaptations (e.g., structural/semantic changes, Type 3/4 clones).

## 6. Development Notes

* The project uses Git for version control.
* The primary input for the tool is *existing* Java test cases and corresponding target project contexts. The tool does *not* focus on discovering or selecting which tests to propagate.
* The evaluation will be based on the Mukelabai et al. ASE 2023 benchmark.
* Focus is on the LLM's ability to understand code, errors, and suggest adaptations for *Java* test cases.

This `CONTEXT.md` should give AI assistants a good overview of what your Python project is about, its goals, how it's structured, and the technologies involved. Remember to keep it updated as your project evolves!

