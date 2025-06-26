import os
import re
import requests


def save_java_test_to_target(
    java_code_string: str,
    test_filename: str,
    target_project_root: str = "data/target_project",
):
    """
    Saves a string of Java test code as a .java file into a 'test' subdirectory
    of the specified target project root.

    Args:
        java_code_string (str): The Java test code as a string.
        test_filename (str): The desired filename for the .java file (e.g., "MyTest.java").
        target_project_root (str): The root path of the dummy target project.
                                   Defaults to "data/target_project".
    """
    if not test_filename.endswith(".java"):
        test_filename += ".java"

    # Define the path to the 'test' subdirectory
    test_subdirectory = os.path.join(target_project_root, "test")

    # Create the directories if they don't exist
    os.makedirs(test_subdirectory, exist_ok=True)

    # Define the full path for the Java test file
    file_path = os.path.join(test_subdirectory, test_filename)

    # Write the Java code to the file
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(java_code_string)
        print(f"Successfully saved Java test case to: {file_path}")
    except IOError as e:
        print(f"Error saving Java test case: {e}")


def parse_maven_error(error_output: str) -> dict:
    """
    Parses Maven error output to extract key error information.

    Args:
        error_output (str): The stderr output from the Maven build.

    Returns:
        dict: A dictionary containing extracted error details.
              Keys might include "error_type", "symbol", "location", "raw_message".
              Returns an empty dictionary if no specific Java compilation error is found.
    """
    if not error_output:
        return {}

    # Regex to find "cannot find symbol" errors (English) - now more robust
    cannot_find_symbol_match = re.search(
        r"\[ERROR\] .*cannot find symbol\s*\n"
        r"^(?:\[ERROR\])?\s*symbol:\s*(method|variable|class|interface|package)\s*([^\n\r]*)\s*\n"
        r"^(?:\[ERROR\])?\s*location:\s*([^\n\r]*)",
        error_output,
        re.MULTILINE | re.IGNORECASE,
    )
    if cannot_find_symbol_match:
        return {
            "error_type": "cannot find symbol",
            "symbol_type": cannot_find_symbol_match.group(1).strip(),
            "symbol_name": cannot_find_symbol_match.group(2).strip(),
            "location": cannot_find_symbol_match.group(3).strip(),
            "raw_message": cannot_find_symbol_match.group(0),
        }

    # Regex to find "Symbol nicht gefunden" errors (German)
    german_cannot_find_symbol_match = re.search(
        r"\[ERROR\] .*Symbol nicht gefunden\s*\n"
        r"^(?:\[ERROR\])?\s*Symbol:\s*(Methode|Variable|Klasse|Schnittstelle|Paket)\s*([^\n\r]*)\s*\n"
        r"^(?:\[ERROR\])?\s*Ort:\s*([^\n\r]*)",
        error_output,
        re.MULTILINE | re.IGNORECASE,
    )
    if german_cannot_find_symbol_match:
        german_type = german_cannot_find_symbol_match.group(1).strip().lower()
        type_map = {
            "methode": "method",
            "variable": "variable",
            "klasse": "class",
            "schnittstelle": "interface",
            "paket": "package",
        }
        return {
            "error_type": "cannot find symbol",
            "symbol_type": type_map.get(german_type, german_type),
            "symbol_name": german_cannot_find_symbol_match.group(2).strip(),
            "location": german_cannot_find_symbol_match.group(3).strip(),
            "raw_message": german_cannot_find_symbol_match.group(0),
        }

    # Regex for "method X in class Y cannot be applied to given types"
    method_not_applicable_match = re.search(
        r"\[ERROR\] .*method (.*) in (class|interface) (.*) cannot be applied to given types;\s*\n"
        r"\[ERROR\]\s*required:\s*([^\n\r]*)\s*\n"
        r"\[ERROR\]\s*found:\s*([^\n\r]*)\s*\n"
        r"\[ERROR\]\s*reason:\s*([^\n\r]*)",
        error_output,
        re.MULTILINE,
    )
    if method_not_applicable_match:
        return {
            "error_type": "method not applicable",
            "method_name": method_not_applicable_match.group(1).strip(),
            "class_type": method_not_applicable_match.group(2).strip(),
            "class_name": method_not_applicable_match.group(3).strip(),
            "required_params": method_not_applicable_match.group(4).strip(),
            "found_params": method_not_applicable_match.group(5).strip(),
            "reason": method_not_applicable_match.group(6).strip(),
            "raw_message": method_not_applicable_match.group(0),
        }

    # General [ERROR] message capture if no specific pattern matched above
    # This looks for the first significant [ERROR] line that doesn't look like a path
    general_error_match = re.search(
        r"\[ERROR\] ([A-Za-z].*)$", error_output, re.MULTILINE
    )
    if general_error_match:
        # Attempt to find a more specific error message if it's a common Maven one
        mojo_failure_match = re.search(
            r"\[ERROR\] Failed to execute goal .*:(.*) \((.*)\) on project (.*): (.*) -> \[Help 1\]",
            error_output,
            re.MULTILINE,
        )
        if mojo_failure_match:
            return {
                "error_type": "maven_mojo_failure",
                "goal": mojo_failure_match.group(1).strip(),
                "mojo": mojo_failure_match.group(2).strip(),
                "project": mojo_failure_match.group(3).strip(),
                "message": mojo_failure_match.group(4).strip(),
                "raw_message": mojo_failure_match.group(0),
            }
        return {
            "error_type": "general_error",
            "message": general_error_match.group(1).strip(),
            "raw_message": general_error_match.group(0),
        }

    # Fallback for non-compilation errors from java_env_manager itself
    if (
        "Error: Project directory" in error_output
        or "Error: Maven command" in error_output
        or "An unexpected error occurred" in error_output
    ):
        return {
            "error_type": "environment_error",
            "message": error_output.strip(),
            "raw_message": error_output.strip(),
        }

    return {
        "error_type": "unknown",
        "message": "Could not parse a specific error message.",
        "raw_message": error_output[:500],
    }  # Return first 500 chars if unknown


def extract_java_code_from_llm_response(llm_response: str) -> str | None:
    """
    Extracts a Java code block from the LLM's raw text response.
    Assumes the Java code is enclosed in ```java ... ``` or ``` ... ```.

    Args:
        llm_response (str): The raw text response from the LLM.

    Returns:
        str | None: The extracted Java code string, or None if no block is found.
    """
    # Try to find ```java ... ```
    match = re.search(r"```java\s*([\s\S]*?)\s*```", llm_response, re.MULTILINE)
    if match:
        return match.group(1).strip()

    # If not found, try to find ``` ... ``` (generic code block)
    # This is less specific, so it's a fallback.
    match = re.search(r"```\s*([\s\S]*?)\s*```", llm_response, re.MULTILINE)
    if match:
        # Basic check to see if it looks like Java (e.g., contains "public class")
        # This is a heuristic and might not be perfect.
        potential_code = match.group(1).strip()
        if (
            "public class" in potential_code
            or "package" in potential_code
            or "@Test" in potential_code
        ):
            return potential_code

    # If still no specific Java block, look for any code block and assume it might be Java
    # if it contains typical Java keywords. This is a broader fallback.
    if (
        "public class" in llm_response
        or "package" in llm_response
        or "@Test" in llm_response
    ):
        # Attempt to find the first occurrence of a code block if the LLM output is *only* code
        # This is a very simple heuristic for cases where the LLM might just return code without backticks.
        # It's risky and should be used with caution.
        # A more robust way would be to rely on the LLM always using markdown.
        # For now, we prioritize markdown blocks.
        # If the response starts with "package" or "public class" and has no backticks,
        # we might assume the whole response is the code. This is highly dependent on LLM behavior.
        # Given the example, the LLM *does* use backticks.
        pass  # Sticking to backtick extraction for now as per the example.

    print("Could not extract Java code block from LLM response.")
    return None


def get_code_from_github(
    owner_repo: str, file_path: str, commit_sha: str | None = None
) -> str | None:
    """
    Fetches the raw content of a specific file from a GitHub repository.
    If a commit SHA or branch name is provided, it fetches that specific version.
    If `commit_sha` is None, it fetches the version from the repository's default branch.

    Args:
        owner_repo (str): The repository owner and name (e.g., "owner/repo").
        file_path (str): The path to the file within the repository.
        commit_sha (str | None, optional): The commit SHA or branch name.
                                           Defaults to None (latest from default branch).

    Returns:
        str | None: The content of the file as a string, or None if an error occurs.
    """
    # Basic validation for owner/repo format
    if "/" not in owner_repo or len(owner_repo.split("/")) != 2:
        print(f"Error: Invalid owner/repo format: {owner_repo}. Expected 'owner/repo'.")
        return None

    ref_to_use = commit_sha

    if not ref_to_use:
        # If no commit_sha is provided, find the default branch via GitHub API
        api_url = f"https://api.github.com/repos/{owner_repo.strip('/')}"
        print(f"No commit SHA provided. Fetching default branch from {api_url}...")
        try:
            # Note: GitHub API has rate limits for unauthenticated requests.
            # For heavy use, consider adding an authentication token.
            response = requests.get(api_url)
            response.raise_for_status()
            repo_info = response.json()
            default_branch = repo_info.get("default_branch")
            if not default_branch:
                print(f"Error: Could not determine default branch for {owner_repo}.")
                return None
            print(f"Default branch for {owner_repo} is '{default_branch}'.")
            # Use the full ref for the default branch to create a more specific URL.
            ref_to_use = f"refs/heads/{default_branch}"
        except requests.exceptions.HTTPError as e:
            print(
                f"Error fetching repository info from GitHub API: {e.response.status_code} {e.response.reason}"
            )
            print(f"URL: {api_url}")
            return None
        except requests.exceptions.RequestException as e:
            print(
                f"An error occurred while requesting repository info from GitHub: {e}"
            )
            return None

    # Construct the raw content URL
    raw_url = f"https://raw.githubusercontent.com/{owner_repo.strip('/')}/{ref_to_use}/{file_path}"

    try:
        print(f"Fetching file from: {raw_url}")
        response = requests.get(raw_url)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        return response.text
    except requests.exceptions.HTTPError as e:
        print(
            f"Error fetching file from GitHub: {e.response.status_code} {e.response.reason}"
        )
        print(f"URL: {raw_url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while requesting the file from GitHub: {e}")
        return None


if __name__ == "__main__":
    # Example Usage:
    sample_java_test_code = """
package com.example.test;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

public class MySimpleTest {

    @Test
    void addition() {
        assertEquals(2, 1 + 1);
    }
}
"""
    # This will create data/target_project/test/MySimpleTest.java
    # save_java_test_to_target(sample_java_test_code, "MySimpleTest.java")

    # Example with a different target project location
    # This will create custom_project/test/AnotherTest.java
    # save_java_test_to_target(sample_java_test_code, "AnotherTest", target_project_root="custom_project")

    print("\n--- Testing error parsing ---")
    # Example error from Project B (cannot find symbol)
    project_b_error = """
[INFO] Scanning for projects...
[INFO]
[INFO] ----------------------< com.example:project-b >-----------------------
[INFO] Building Project B 1.0-SNAPSHOT
[INFO]   from pom.xml
[INFO] --------------------------------[ jar ]---------------------------------
[INFO]
[INFO] --- resources:3.3.1:resources (default-resources) @ project-b ---
[INFO] skip non existing resourceDirectory C:\\Users\\keanu\\OneDrive\\Desktop\\Bachelor Thesis\\Testcase Adaptation LLM\\dummy_java_projects\\ProjectB\\src\\main\\resources
[INFO]
[INFO] --- compiler:3.13.0:compile (default-compile) @ project-b ---
[INFO] Changes detected - recompiling the module! :
[INFO]  C:\\Users\\keanu\\OneDrive\\Desktop\\Bachelor Thesis\\Testcase Adaptation LLM\\dummy_java_projects\\ProjectB\\src\\main\\java\\com\\example\\Calculator.java
[INFO]
[INFO] --- resources:3.3.1:testResources (default-testResources) @ project-b ---
[INFO] skip non existing resourceDirectory C:\\Users\\keanu\\OneDrive\\Desktop\\Bachelor Thesis\\Testcase Adaptation LLM\\dummy_java_projects\\ProjectB\\src\\test\\resources
[INFO]
[INFO] --- compiler:3.13.0:testCompile (default-testCompile) @ project-b ---
[INFO] Changes detected - recompiling the module! :
[INFO]  C:\\Users\\keanu\\OneDrive\\Desktop\\Bachelor Thesis\\Testcase Adaptation LLM\\dummy_java_projects\\ProjectB\\src\\test\\java\\com\\example\\CalculatorTest.java
[INFO] -------------------------------------------------------------
[ERROR] COMPILATION ERROR :
[INFO] -------------------------------------------------------------
[ERROR] c:\\Users\\keanu\\OneDrive\\Desktop\\Bachelor Thesis\\Testcase Adaptation LLM\\dummy_java_projects\\ProjectB\\src\\test\\java\\com\\example\\CalculatorTest.java:[13,30] cannot find symbol
[ERROR]   symbol:   method add(int,int)
[ERROR]   location: variable calculator of type com.example.Calculator
[ERROR] c:\\Users\\keanu\\OneDrive\\Desktop\\Bachelor Thesis\\Testcase Adaptation LLM\\dummy_java_projects\\ProjectB\\src\\test\\java\\com\\example\\CalculatorTest.java:[19,30] cannot find symbol
[ERROR]   symbol:   method add(int,int)
[ERROR]   location: variable calculator of type com.example.Calculator
[INFO] 2 errors
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  0.726 s
[INFO] Finished at: 2025-05-30T17:00:00+02:00
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.13.0:testCompile (default-testCompile) on project project-b: Compilation failure
[ERROR] c:\\Users\\keanu\\OneDrive\\Desktop\\Bachelor Thesis\\Testcase Adaptation LLM\\dummy_java_projects\\ProjectB\\src\\test\\java\\com\\example\\CalculatorTest.java:[13,30] cannot find symbol
[ERROR]   symbol:   method add(int,int)
[ERROR]   location: variable calculator of type com.example.Calculator
[ERROR] c:\\Users\\keanu\\OneDrive\\Desktop\\Bachelor Thesis\\Testcase Adaptation LLM\\dummy_java_projects\\ProjectB\\src\\test\\java\\com\\example\\CalculatorTest.java:[19,30] cannot find symbol
[ERROR]   symbol:   method add(int,int)
[ERROR]   location: variable calculator of type com.example.Calculator
[ERROR] -> [Help 1]
[ERROR]
[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.
[ERROR] Re-run Maven using the -X switch to enable full debug logging.
[ERROR]
[ERROR] For more information about the errors and possible solutions, please read the following articles:
[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/MojoFailureException
    """
    parsed_error_b = parse_maven_error(project_b_error)
    print(f"Parsed Project B Error: {parsed_error_b}\n")

    non_existent_error = "Error: Project directory 'non_existent_project' not found."
    parsed_non_existent = parse_maven_error(non_existent_error)
    print(f"Parsed Non-Existent Project Error: {parsed_non_existent}\n")

    no_error = ""
    parsed_no_error = parse_maven_error(no_error)
    print(f"Parsed No Error: {parsed_no_error}\n")

    unknown_error = "[INFO] Some other info\n[WARNING] A warning\n[FOO] Unknown stuff"
    parsed_unknown = parse_maven_error(unknown_error)
    print(f"Parsed Unknown Error: {parsed_unknown}\n")

    # Example of a different compilation error (method not applicable)
    method_not_applicable_error = """
[ERROR] COMPILATION ERROR :
[INFO] -------------------------------------------------------------
[ERROR] /path/to/SomeFile.java:[42,10] method foo in class com.example.Bar cannot be applied to given types;
[ERROR]   required: java.lang.String,int
[ERROR]   found:    int,java.lang.String
[ERROR]   reason: argument mismatch; int cannot be converted to java.lang.String
[INFO] 1 error
    """
    parsed_method_error = parse_maven_error(method_not_applicable_error)
    print(f"Parsed Method Not Applicable Error: {parsed_method_error}")

    print("\n--- Testing LLM response parsing ---")
    sample_llm_response_java = """
Some introductory text.
```java
package com.example;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

public class CalculatorTest {

    @Test
    void testAdd() {
        Calculator calculator = new Calculator();
        assertEquals(5, calculator.sum(2, 3), "2 + 3 should equal 5");
    }
}
```
Some concluding text.
    """
    extracted_code = extract_java_code_from_llm_response(sample_llm_response_java)
    print(f"Extracted Java code:\n{extracted_code}")

    sample_llm_response_generic = """
The LLM says:
```
public class MyClass {
    // some java like code
}
```
That's the suggestion.
    """
    extracted_code_generic = extract_java_code_from_llm_response(
        sample_llm_response_generic
    )
    print(f"\nExtracted generic code (as Java):\n{extracted_code_generic}")

    sample_llm_response_no_code = "This is just some text without a code block."
    extracted_code_no_code = extract_java_code_from_llm_response(
        sample_llm_response_no_code
    )
    print(f"\nExtracted from no code response: {extracted_code_no_code}")

    sample_llm_response_only_code_in_java_block = """```java
package com.example;

public class OnlyTest {
    @Test
    void simpleTest() {
        assertEquals(1, 1);
    }
}
```"""
    extracted_only_code = extract_java_code_from_llm_response(
        sample_llm_response_only_code_in_java_block
    )
    print(f"\nExtracted from only code in java block:\n{extracted_only_code}")

    print("\n--- Testing GitHub code fetching ---")
    # Example 1: Fetching a specific file from the latest (default branch) version of a repo
    print("\nFetching latest README.md from psf/requests...")
    owner_repo_1 = "psf/requests"
    file_path_1 = "README.md"
    latest_code = get_code_from_github(owner_repo=owner_repo_1, file_path=file_path_1)
    if latest_code:
        print(
            f"Successfully fetched latest code (first 100 chars):\n{latest_code[:100]}..."
        )
    else:
        print("Failed to fetch latest code.")

    # Example 2: Fetching a file from a specific commit
    print("\nFetching README.rst from a specific commit in psf/requests...")
    owner_repo_2 = "psf/requests"
    # A specific commit SHA from the requests repo history
    commit_sha_2 = "a75728a6b5511813846f675e05715a258a9d99b3"
    file_path_2 = "README.rst"  # The file was README.rst at that commit
    specific_code = get_code_from_github(
        owner_repo=owner_repo_2, file_path=file_path_2, commit_sha=commit_sha_2
    )
    if specific_code:
        print(
            f"Successfully fetched specific version (first 100 chars):\n{specific_code[:100]}..."
        )
    else:
        print("Failed to fetch specific version.")
