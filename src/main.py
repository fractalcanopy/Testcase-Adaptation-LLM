import os
from dotenv import load_dotenv

from utils import (
    save_java_test_to_target,
    parse_maven_error,
    extract_java_code_from_llm_response,
)
from java_env_manager import invoke_maven_build
from llm_analyzer import construct_llm_prompt
from test_apis import test_gemini_api


def read_file_content(file_path: str) -> str | None:
    """Reads the content of a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None


def main(
    source_test_file_path: str,
    target_project_path: str,
    target_class_relative_path: str,
):
    """
    Main orchestrator for the test case adaptation workflow.

    Args:
        source_test_file_path (str): Absolute or relative path to the source Java test case file.
        target_project_path (str): Absolute or relative path to the root of the target Java project.
        target_class_relative_path (str): Relative path of the target class file
                                           within the target project (e.g., "src/main/java/com/example/Calculator.java").
    """
    print(f"--- Starting Test Adaptation Workflow ---")
    print(f"Source Test File: {source_test_file_path}")
    print(f"Target Project Path: {target_project_path}")
    print(f"Target Class Relative Path: {target_class_relative_path}")

    # Step 0: Load environment variables (for API keys)
    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print(
            "Error: GEMINI_API_KEY not found in .env file. Please set it to use the Gemini API."
        )
        # Depending on desired behavior, you might want to exit or handle this differently.
        # For now, we'll let it proceed, and test_gemini_api will likely fail if called.

    # Step A.1: Read the source test file content
    original_test_case_code = read_file_content(source_test_file_path)
    if original_test_case_code is None:
        print("Exiting due to error reading source test file.")
        return

    source_test_filename = os.path.basename(source_test_file_path)

    # Step A.2: Save the Java test file to the target project
    # Assuming the test should go into a standard Maven test directory structure.
    # utils.save_java_test_to_target expects the target project root and will create a 'test' subfolder.
    # We need to ensure the package structure is also handled if not already in save_java_test_to_target.
    # For now, save_java_test_to_target saves it directly into target_project_root/test/
    # This might need adjustment if the test file needs to be in a specific package subfolder within target_project_root/src/test/java/...
    # For the dummy projects, CalculatorTest.java is in com.example.
    # Let's define the target test directory more precisely for Maven structure.
    target_test_src_root = os.path.join(target_project_path, "src", "test", "java")
    # We need to extract the package path from the original test case to place it correctly.
    # This is a simplification; a robust solution would parse the package statement.
    # For now, we assume the test file is named correctly and save_java_test_to_target handles the path.
    # The current save_java_test_to_target saves to `target_project_root/test/filename.java`.
    # This needs to be `target_project_path/src/test/java/com/example/TestFile.java` for Maven.
    # Let's adjust how we call save_java_test_to_target or modify it.
    # For simplicity, we'll assume `save_java_test_to_target` is good enough for now,
    # but acknowledge this is a point for refinement for correct package structures.
    # A quick fix: determine the package from source_test_file_path if possible, or assume a default.
    # For the dummy projects, the test is `com.example.CalculatorTest`.
    # The `save_java_test_to_target` function in `utils.py` saves to `target_project_root/test/filename.java`.
    # This is NOT standard Maven structure. This will likely cause compilation issues if not addressed.
    # For now, we proceed with the current behavior of `save_java_test_to_target`.
    print(
        f"\nStep A: Saving test file '{source_test_filename}' to target project '{target_project_path}'..."
    )
    # We need to provide the *content* and the *filename* to save_java_test_to_target.
    # The `target_project_root` for `save_java_test_to_target` should be the directory where the `test` folder will be created.
    # If `target_project_path` is `dummy_java_projects/ProjectB`, then tests will be saved in `dummy_java_projects/ProjectB/test/`.
    # This is still not `src/test/java/...`. This is a known limitation of the current `save_java_test_to_target`.
    # For the purpose of this script, we will proceed.
    # A proper implementation would involve creating the package structure under `target_project_path/src/test/java/`.

    # Let's assume the test file should be placed in the correct package structure within the target project's test source folder.
    # This part requires more robust path handling. For now, we'll use a simplified approach.
    # We'll copy the test file to `target_project_path/src/test/java/com/example/`
    # This assumes the package is `com.example`.
    # A better `save_java_test_to_target` would handle this.
    # For now, let's manually construct the path for the dummy projects.
    package_path = "com/example"  # Assuming this for dummy projects
    target_test_file_dir = os.path.join(
        target_project_path, "src", "test", "java", package_path
    )
    os.makedirs(target_test_file_dir, exist_ok=True)
    target_test_file_full_path = os.path.join(
        target_test_file_dir, source_test_filename
    )

    try:
        with open(target_test_file_full_path, "w", encoding="utf-8") as f:
            f.write(original_test_case_code)
        print(f"Successfully saved Java test case to: {target_test_file_full_path}")
    except IOError as e:
        print(f"Error saving Java test case to {target_test_file_full_path}: {e}")
        return

    # Step B: Invoke Maven build on the target project
    print(f"\nStep B: Attempting to build target project '{target_project_path}'...")
    return_code, stdout_str, stderr_str = invoke_maven_build(target_project_path)
    print(f"Maven build return code: {return_code}")
    # print(f"Maven STDOUT:\n{stdout_str}") # Can be very verbose
    if stderr_str:
        print(f"Maven STDERR:\n{stderr_str}")

    # Step C: Check build result
    if return_code == 0:
        print("\nStep C: Success on first try! Build was successful.")
        # Optionally, run tests here if build includes test execution that passed
    else:
        print("\nStep C: Build failed. Proceeding to LLM analysis.")

        # Step D: Parse Maven error
        print("\nStep D: Parsing Maven error output...")
        parsed_error = parse_maven_error(
            stderr_str if stderr_str else stdout_str
        )  # Pass stderr, or stdout if stderr is empty
        if not parsed_error or parsed_error.get("error_type") == "unknown":
            print("Could not parse a specific error, or error type is unknown.")
            # Use raw error if parsing fails significantly
            error_for_prompt = stderr_str if stderr_str else stdout_str
            if not error_for_prompt:
                error_for_prompt = "No detailed error message captured from build."
        elif parsed_error.get("error_type") == "environment_error":
            print(f"Environment error: {parsed_error.get('message')}")
            print("Cannot proceed with LLM analysis for environment errors.")
            return
        else:
            # Construct a concise error message for the prompt from the parsed dictionary
            if parsed_error.get("error_type") == "cannot find symbol":
                error_for_prompt = (
                    f"Cannot find symbol: {parsed_error.get('symbol_type')} {parsed_error.get('symbol_name')}\n"
                    f"Location: {parsed_error.get('location')}"
                )
            elif parsed_error.get("error_type") == "method not applicable":
                error_for_prompt = (
                    f"Method not applicable: {parsed_error.get('method_name')} in {parsed_error.get('class_type')} {parsed_error.get('class_name')}\n"
                    f"Required: {parsed_error.get('required_params')}\n"
                    f"Found: {parsed_error.get('found_params')}\n"
                    f"Reason: {parsed_error.get('reason')}"
                )
            else:  # general_error, maven_mojo_failure, etc.
                error_for_prompt = parsed_error.get(
                    "message",
                    parsed_error.get(
                        "raw_message", "No specific error message parsed."
                    ),
                )
        print(f"Parsed error for prompt: {error_for_prompt}")

        # Step E: Read content of the relevant target class file
        print("\nStep E: Reading target class code...")
        target_class_full_path = os.path.join(
            target_project_path, target_class_relative_path
        )
        target_class_code = read_file_content(target_class_full_path)
        if target_class_code is None:
            print(
                f"Could not read target class file at {target_class_full_path}. Cannot proceed with LLM analysis."
            )
            return

        target_class_name_for_prompt = os.path.basename(target_class_full_path)

        # Step F: Construct LLM prompt
        print("\nStep F: Constructing LLM prompt...")
        llm_prompt = construct_llm_prompt(
            original_test_case_code=original_test_case_code,
            parsed_build_error=error_for_prompt,
            target_class_code=target_class_code,
            target_class_name=target_class_name_for_prompt,
        )
        # print(f"--- Generated LLM Prompt ---\n{llm_prompt}\n--------------------------") # For debugging

        # Step G: Call LLM API
        print("\nStep G: Querying LLM for suggestions...")
        if not gemini_api_key:
            print("Gemini API key not available. Skipping LLM query.")
            llm_suggestion = "Error: Gemini API key not configured."
        else:
            try:
                # test_gemini_api currently prints the response.
                # For this workflow, we need it to return the response.
                # Modifying test_gemini_api or creating a new function would be ideal.
                # For now, let's assume test_gemini_api can be adapted or we capture its output if needed.
                # The current test_gemini_api prints a complex object. We need the text part.

                # Let's modify the call to get the text directly if possible,
                # or adjust test_gemini_api to return the text.
                # For now, we'll call it as is and it will print.
                # To make it fit Step H, test_gemini_api should return the suggestion string.

                # --- Temporary modification to how test_gemini_api is used ---
                # This is a placeholder. Ideally, test_gemini_api returns the text.
                import google.generativeai as genai  # Import here for this temporary direct call

                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel(
                    "gemini-1.5-flash"
                )  # Using 1.5 flash as 2.0 is not a model name
                response = model.generate_content(llm_prompt)
                llm_suggestion = response.text  # Extract text part
            except Exception as e:
                print(f"Error during LLM API call: {e}")
                llm_suggestion = f"Error during LLM API call: {e}"

        # Step H: Print raw LLM suggestion
        print("\nStep H: Raw LLM Suggestion:")
        print("--------------------------------------------------")
        print(llm_suggestion)
        print("--------------------------------------------------")

        # Step I: Extract code from LLM response
        print("\nStep I: Extracting Java code from LLM suggestion...")
        suggested_java_code = extract_java_code_from_llm_response(llm_suggestion)

        if suggested_java_code:
            print("Successfully extracted Java code from LLM response.")
            # print(f"--- Suggested Code ---\n{suggested_java_code}\n----------------------") # For debugging

            # Step J: Apply LLM suggestion and re-build
            print(
                f"\nStep J: Applying LLM suggestion to '{target_test_file_full_path}' and re-building..."
            )
            try:
                with open(target_test_file_full_path, "w", encoding="utf-8") as f:
                    f.write(suggested_java_code)
                print(
                    f"Successfully updated test file with LLM suggestion: {target_test_file_full_path}"
                )

                # Re-invoke Maven build
                print(
                    f"Attempting to build target project '{target_project_path}' with applied suggestion..."
                )
                return_code_after_fix, stdout_after_fix, stderr_after_fix = (
                    invoke_maven_build(target_project_path)
                )
                print(
                    f"Maven build return code after applying suggestion: {return_code_after_fix}"
                )

                if stderr_after_fix:
                    print(
                        f"Maven STDERR after applying suggestion:\n{stderr_after_fix}"
                    )

                if return_code_after_fix == 0:
                    print("\nLLM suggestion successfully fixed the build!")
                else:
                    print("\nBuild still fails after applying LLM suggestion.")
                    # Optionally, parse the new error:
                    # new_parsed_error = parse_maven_error(stderr_after_fix if stderr_after_fix else stdout_after_fix)
                    # print(f"New parsed error: {new_parsed_error}")

            except IOError as e:
                print(f"Error writing suggested Java code to file: {e}")
            except Exception as e:
                print(
                    f"An unexpected error occurred during suggestion application or re-build: {e}"
                )
        else:
            print("No Java code block found in LLM suggestion. Cannot apply fix.")

    print(f"\n--- Test Adaptation Workflow Finished ---")


if __name__ == "__main__":
    # --- Configuration for the dummy projects ---

    # Relative path from project_root (where this script might be run from after cd src)
    # or use absolute paths.
    # Assuming this script (main.py) is in the 'src' directory.
    project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Option 1: Project A's test (should succeed in Project A, but we'll try it in Project B)
    # This test is designed for Calculator.add method
    source_test_path = os.path.join(
        project_root_dir,
        "dummy_java_projects",
        "ProjectA",
        "src",
        "test",
        "java",
        "com",
        "example",
        "CalculatorTest.java",
    )

    # Target Project B (where Calculator.add is renamed to Calculator.sum)
    target_proj_path = os.path.join(project_root_dir, "dummy_java_projects", "ProjectB")
    target_cls_rel_path = os.path.join(
        "src", "main", "java", "com", "example", "Calculator.java"
    )  # Relative to target_proj_path

    # Before running, ensure dummy projects are created by running `create_dummy_projects.py` from the project root.
    # And ensure .env file with GEMINI_API_KEY is present in the project root.

    if not os.path.exists(source_test_path):
        print(f"Error: Source test file not found: {source_test_path}")
        print("Please ensure dummy projects are created and paths are correct.")
    elif not os.path.exists(target_proj_path):
        print(f"Error: Target project directory not found: {target_proj_path}")
        print("Please ensure dummy projects are created and paths are correct.")
    else:
        main(
            source_test_file_path=source_test_path,
            target_project_path=target_proj_path,
            target_class_relative_path=target_cls_rel_path,
        )

    # Example of how you might run it for Project A (where it should pass)
    # print("\n\n--- Running on Project A (expecting success) ---")
    # target_proj_a_path = os.path.join(project_root_dir, "dummy_java_projects", "ProjectA")
    # main(
    #     source_test_file_path=source_test_path, # Same test file
    #     target_project_path=target_proj_a_path,
    #     target_class_relative_path=target_cls_rel_path # Calculator.java in Project A
    # )
