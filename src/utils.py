import os
import re

def save_java_test_to_target(java_code_string: str, test_filename: str, target_project_root: str = "data/target_project"):
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

    # Regex to find "cannot find symbol" errors
    cannot_find_symbol_match = re.search(
        r"\[ERROR\] .*cannot find symbol\s*\n"
        r"\[ERROR\]\s*symbol:\s*(method|variable|class|interface|package)\s*([^\n\r]*)\s*\n"
        r"\[ERROR\]\s*location:\s*([^\n\r]*)",
        error_output,
        re.MULTILINE
    )
    if cannot_find_symbol_match:
        return {
            "error_type": "cannot find symbol",
            "symbol_type": cannot_find_symbol_match.group(1).strip(),
            "symbol_name": cannot_find_symbol_match.group(2).strip(),
            "location": cannot_find_symbol_match.group(3).strip(),
            "raw_message": cannot_find_symbol_match.group(0)
        }

    # Regex for "method X in class Y cannot be applied to given types"
    method_not_applicable_match = re.search(
        r"\[ERROR\] .*method (.*) in (class|interface) (.*) cannot be applied to given types;\s*\n"
        r"\[ERROR\]\s*required:\s*([^\n\r]*)\s*\n"
        r"\[ERROR\]\s*found:\s*([^\n\r]*)\s*\n"
        r"\[ERROR\]\s*reason:\s*([^\n\r]*)",
        error_output,
        re.MULTILINE
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
            "raw_message": method_not_applicable_match.group(0)
        }

    # General [ERROR] message capture if no specific pattern matched above
    # This looks for the first significant [ERROR] line that doesn't look like a path
    general_error_match = re.search(r"\[ERROR\] ([A-Za-z].*)$", error_output, re.MULTILINE)
    if general_error_match:
        # Attempt to find a more specific error message if it's a common Maven one
        mojo_failure_match = re.search(r"\[ERROR\] Failed to execute goal .*:(.*) \((.*)\) on project (.*): (.*) -> \[Help 1\]", error_output, re.MULTILINE)
        if mojo_failure_match:
            return {
                "error_type": "maven_mojo_failure",
                "goal": mojo_failure_match.group(1).strip(),
                "mojo": mojo_failure_match.group(2).strip(),
                "project": mojo_failure_match.group(3).strip(),
                "message": mojo_failure_match.group(4).strip(),
                "raw_message": mojo_failure_match.group(0)
            }
        return {
            "error_type": "general_error",
            "message": general_error_match.group(1).strip(),
            "raw_message": general_error_match.group(0)
        }
        
    # Fallback for non-compilation errors from java_env_manager itself
    if "Error: Project directory" in error_output or "Error: Maven command" in error_output or "An unexpected error occurred" in error_output:
        return {
            "error_type": "environment_error",
            "message": error_output.strip(),
            "raw_message": error_output.strip()
        }

    return {"error_type": "unknown", "message": "Could not parse a specific error message.", "raw_message": error_output[:500]} # Return first 500 chars if unknown

if __name__ == '__main__':
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