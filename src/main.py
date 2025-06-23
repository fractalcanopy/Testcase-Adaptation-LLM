import os
from dotenv import load_dotenv

from utils import (
    parse_maven_error,
    extract_java_code_from_llm_response,
    get_code_from_github,
)
from java_env_manager import invoke_maven_build
from llm_analyzer import construct_llm_prompt


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
    original_test_case_code: str,
    source_test_origin_path: str,
    target_project_path: str,
    target_class_relative_path: str,
):
    """
    Main orchestrator for the test case adaptation workflow.

    Args:
        original_test_case_code (str): The content of the source Java test case file.
        source_test_origin_path (str): The original path of the test case (either in a repo or local FS).
                                       Used to determine package structure.
        target_project_path (str): Absolute or relative path to the root of the target Java project.
        target_class_relative_path (str): Relative path of the target class file
                                           within the target project (e.g., "src/main/java/com/example/Calculator.java").
    """
    print(f"--- Starting Test Adaptation Workflow ---")
    print(f"Source Test Origin: {source_test_origin_path}")
    print(f"Target Project Path: {target_project_path}")
    print(f"Target Class Relative Path: {target_class_relative_path}")

    # Step 0: Load environment variables (for API keys)
    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print(
            "Error: GEMINI_API_KEY not found in .env file. Please set it to use the Gemini API."
        )

    if not original_test_case_code:
        print("Exiting due to empty source test case code.")
        return

    # Step A: Place the test file into the target project with correct package structure
    source_test_filename = os.path.basename(source_test_origin_path)
    print(
        f"\nStep A: Saving test file '{source_test_filename}' to target project '{target_project_path}'..."
    )

    # Determine package path from the source path to replicate it in the target
    package_path = ""
    path_parts = os.path.dirname(source_test_origin_path.replace("\\", "/")).split(
        "src/test/java/"
    )
    if len(path_parts) > 1:
        package_path = path_parts[1]

    if not package_path:
        print(
            "Warning: Could not determine package path from source. Placing test in 'src/test/java' root."
        )

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
    if stderr_str:
        print(f"Maven STDERR:\n{stderr_str}")

    # Step C: Check build result
    if return_code == 0:
        print("\nStep C: Success on first try! Build was successful.")
    else:
        print("\nStep C: Build failed. Proceeding to LLM analysis.")

        # Step D: Parse Maven error
        print("\nStep D: Parsing Maven error output...")
        parsed_error = parse_maven_error(stderr_str if stderr_str else stdout_str)
        if not parsed_error or parsed_error.get("error_type") == "unknown":
            print("Could not parse a specific error, or error type is unknown.")
            error_for_prompt = stderr_str if stderr_str else stdout_str
            if not error_for_prompt:
                error_for_prompt = "No detailed error message captured from build."
        elif parsed_error.get("error_type") == "environment_error":
            print(f"Environment error: {parsed_error.get('message')}")
            print("Cannot proceed with LLM analysis for environment errors.")
            return
        else:
            if parsed_error.get("error_type") == "cannot find symbol":
                error_for_prompt = (
                    f"Cannot find symbol: {parsed_error.get('symbol_type')} {parsed_error.get('symbol_name')}\n"
                    f"Location: {parsed_error.get('location')}"
                )
            else:
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

        # Step E.1: Read build file (e.g., pom.xml)
        print("\nStep E.1: Reading build file...")
        build_file_path = os.path.join(target_project_path, "pom.xml")
        build_file_content = read_file_content(build_file_path)
        build_file_name = os.path.basename(build_file_path)
        if build_file_content is None:
            print(
                f"Could not read build file at {build_file_path}. Proceeding without it."
            )
            build_file_name = "build file"

        # Step F: Construct LLM prompt
        print("\nStep F: Constructing LLM prompt...")
        llm_prompt = construct_llm_prompt(
            original_test_case_code=original_test_case_code,
            parsed_build_error=error_for_prompt,
            target_class_code=target_class_code,
            target_class_name=target_class_name_for_prompt,
            build_file_content=build_file_content,
            build_file_name=build_file_name,
        )

        # Step G: Call LLM API
        print("\nStep G: Querying LLM for suggestions...")
        llm_suggestion = ""
        if not gemini_api_key:
            print("Gemini API key not available. Skipping LLM query.")
            llm_suggestion = "Error: Gemini API key not configured."
        else:
            try:
                import google.generativeai as genai

                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(llm_prompt)
                llm_suggestion = response.text
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
                return_code_after_fix, _, stderr_after_fix = invoke_maven_build(
                    target_project_path
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

            except IOError as e:
                print(f"Error writing suggested Java code to file: {e}")
        else:
            print("No Java code block found in LLM suggestion. Cannot apply fix.")

    print(f"\n--- Test Adaptation Workflow Finished ---")


if __name__ == "__main__":
    # --- Configuration ---
    # Set this flag to False to use the real data from your dataset.
    # Set it to True to use the local dummy projects.
    USE_DUMMY_PROJECTS = False

    project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    if USE_DUMMY_PROJECTS:
        # --- Configuration for the DUMMY projects ---
        print("--- Using DUMMY projects for workflow ---")
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
        target_proj_path = os.path.join(
            project_root_dir, "dummy_java_projects", "ProjectB"
        )
        target_cls_rel_path = os.path.join(
            "src", "main", "java", "com", "example", "Calculator.java"
        )

        if not os.path.exists(source_test_path) or not os.path.exists(target_proj_path):
            print("Error: Dummy project files not found.")
            print("Please run 'python create_dummy_projects.py' from the project root.")
        else:
            test_code = read_file_content(source_test_path)
            if test_code:
                main(
                    original_test_case_code=test_code,
                    source_test_origin_path=source_test_path,
                    target_project_path=target_proj_path,
                    target_class_relative_path=target_cls_rel_path,
                )
    else:
        # --- Configuration for REAL data from dataset ---
        print("--- Using REAL data for workflow ---")

        # 1. Define repository and file details from your dataset
        source_repo = "jsight/rewrite"
        source_test_file_in_repo = (
            "api/src/test/java/org/ocpsoft/rewrite/util/ParseToolsTest.java"
        )

        target_repo = "ALRubinger/rewrite"
        target_uut_file_in_repo = "impl-config/src/main/java/org/ocpsoft/rewrite/bind/parse/CapturingGroup.java"

        # 2. Define local path for the cloned target project
        target_project_local_path = os.path.join(
            project_root_dir, "data", "projects", "rewrite-target"
        )

        # 3. Fetch the source test case from GitHub
        print(
            f"\nFetching source test case from GitHub: {source_repo}/{source_test_file_in_repo}"
        )
        source_test_code = get_code_from_github(
            owner_repo=source_repo, file_path=source_test_file_in_repo
        )

        # 4. Check if everything is ready
        if not source_test_code:
            print("Failed to fetch source test code from GitHub. Exiting.")
        elif not os.path.isdir(target_project_local_path):
            print(
                f"Error: Target project directory not found at '{target_project_local_path}'"
            )
            print(
                f"Please clone the target repository '{target_repo}' into that directory:"
            )
            print(
                f'git clone https://github.com/{target_repo}.git "{target_project_local_path}"'
            )
        else:
            # 5. Run the main workflow
            main(
                original_test_case_code=source_test_code,
                source_test_origin_path=source_test_file_in_repo,
                target_project_path=target_project_local_path,
                target_class_relative_path=target_uut_file_in_repo,
            )
