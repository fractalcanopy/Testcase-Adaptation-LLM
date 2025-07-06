import os
from dotenv import load_dotenv

from .utils import (
    parse_maven_error,
    extract_java_code_from_llm_response,
    extract_xml_code_from_llm_response,  # Import the new function
    get_code_from_github,
)
from .java_env_manager import invoke_maven_build
from .llm_analyzer import construct_llm_prompt, construct_pom_fix_prompt
from .metrics_tracker import global_metrics


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
    max_attempts: int = 3,  # NEW: allow multiple adaptation attempts
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
        max_attempts (int): Maximum number of LLM adaptation attempts if build keeps failing.
    """
    # Start metrics tracking
    source_project = "unknown"  # Will be set by process_dataset.py
    target_project = os.path.basename(target_project_path)
    global_metrics.start_tracking(
        source_project,
        source_test_origin_path,
        target_project,
        target_class_relative_path,
    )

    print(f"--- Starting Test Adaptation Workflow ---")  # noqa: F541
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
        global_metrics.finish_tracking()
        return

    # --- Pre-Build Check ---
    print(
        f"\n--- Pre-Build Check: Verifying target project '{target_project_path}' builds correctly ---"
    )
    return_code, stdout_str, stderr_str = invoke_maven_build(target_project_path)
    pom_fix_applied = False

    if return_code != 0:
        print("Pre-build check FAILED. The target project does not compile on its own.")
        print("Attempting to fix the build configuration (pom.xml)...")

        # Parse error
        parsed_error = parse_maven_error(stdout_str if stdout_str else stderr_str)
        error_for_prompt = parsed_error.get("raw_message", stderr_str)

        # Read pom.xml
        pom_path = os.path.join(target_project_path, "pom.xml")
        pom_content = read_file_content(pom_path)

        if pom_content and error_for_prompt:
            # Construct prompt to fix pom.xml
            pom_fix_prompt = construct_pom_fix_prompt(error_for_prompt, pom_content)

            # Query LLM
            try:
                import google.generativeai as genai

                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(pom_fix_prompt)
                llm_suggestion = response.text

                # Extract and apply fix
                suggested_pom = extract_xml_code_from_llm_response(llm_suggestion)
                print("\n--- LLM Suggested pom.xml Fix ---")
                print("--------------------------------------------------")
                print(suggested_pom)
                print("--------------------------------------------------")
                if suggested_pom:
                    print(
                        "LLM suggested a fix for pom.xml. Applying and re-building..."
                    )
                    with open(pom_path, "w", encoding="utf-8") as f:
                        f.write(suggested_pom)
                    pom_fix_applied = True

                    # Re-build to verify the fix
                    return_code, _, stderr_str = invoke_maven_build(target_project_path)
                    if return_code == 0:
                        print("SUCCESS: Pre-build check passed after fixing pom.xml.")
                    else:
                        print(
                            "FAILURE: Pre-build check failed again after applying pom.xml fix."
                        )
                        print(f"Error:\n{stderr_str}")
                        print("Aborting workflow.")
                        global_metrics.record_pre_build_result(False, pom_fix_applied)
                        global_metrics.finish_tracking()
                        return
                else:
                    print("LLM did not provide a valid pom.xml fix. Aborting workflow.")
                    global_metrics.record_pre_build_result(False, pom_fix_applied)
                    global_metrics.finish_tracking()
                    return
            except Exception as e:
                print(f"An error occurred while trying to fix pom.xml: {e}")
                global_metrics.record_pre_build_result(False, pom_fix_applied)
                global_metrics.finish_tracking()
                return
        else:
            print("Could not read pom.xml or build error. Aborting workflow.")
            global_metrics.record_pre_build_result(False, pom_fix_applied)
            global_metrics.finish_tracking()
            return
    else:
        print("SUCCESS: Pre-build check passed. Target project builds correctly.")

    # Record pre-build result
    global_metrics.record_pre_build_result(return_code == 0, pom_fix_applied)

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
        global_metrics.finish_tracking()
        return

    # --- Adaptation loop ---
    attempt = 1
    current_test_code = original_test_case_code
    while attempt <= max_attempts:
        print(
            f"\nStep B: Attempting to build target project '{target_project_path}'... (Attempt {attempt}/{max_attempts})"
        )
        return_code, stdout_str, stderr_str = invoke_maven_build(target_project_path)
        print(f"Maven build return code: {return_code}")
        if stderr_str:
            print(f"Maven STDERR:\n{stderr_str}")

        # Step C: Check build result
        if return_code == 0:
            print(f"\nStep C: Success on attempt {attempt}! Build was successful.")
            global_metrics.record_adaptation_attempt(attempt, True)
            break
        else:
            print(
                f"\nStep C: Build failed on attempt {attempt}. Proceeding to LLM analysis."
            )

            # Step D: Parse Maven error
            print("\nStep D: Parsing Maven error output...")
            parsed_error = parse_maven_error(stdout_str if stdout_str else stderr_str)
            if not parsed_error or parsed_error.get("error_type") == "unknown":
                print("Could not parse a specific error, or error type is unknown.")
                error_for_prompt = stderr_str if stderr_str else stdout_str
                if not error_for_prompt:
                    error_for_prompt = "No detailed error message captured from build."
                error_type = "unknown"
            elif parsed_error.get("error_type") == "environment_error":
                print(f"Environment error: {parsed_error.get('message')}")
                print("Cannot proceed with LLM analysis for environment errors.")
                global_metrics.record_initial_error("environment_error")
                global_metrics.record_adaptation_attempt(
                    attempt, False, parsed_error.get("message")
                )
                global_metrics.finish_tracking()
                return
            else:
                error_type = parsed_error.get("error_type", "unknown")
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

            # Record initial error type (only for first attempt)
            if attempt == 1:
                global_metrics.record_initial_error(error_type)

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
                global_metrics.record_adaptation_attempt(
                    attempt, False, "Could not read target class file"
                )
                global_metrics.finish_tracking()
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
                original_test_case_code=current_test_code,
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
                global_metrics.record_adaptation_attempt(attempt, False, "No API key")
                break
            else:
                try:
                    import google.generativeai as genai

                    genai.configure(api_key=gemini_api_key)
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    response = model.generate_content(llm_prompt)
                    llm_suggestion = response.text

                    # Record LLM usage and extract classification
                    global_metrics.record_llm_usage(llm_suggestion)

                except Exception as e:
                    print(f"Error during LLM API call: {e}")
                    llm_suggestion = f"Error during LLM API call: {e}"
                    global_metrics.record_adaptation_attempt(attempt, False, str(e))
                    break

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
                    current_test_code = (
                        suggested_java_code  # Use new code for next prompt if needed
                    )
                except IOError as e:
                    print(f"Error writing suggested Java code to file: {e}")
                    global_metrics.record_adaptation_attempt(attempt, False, str(e))
                    break
            else:
                print("No Java code block found in LLM suggestion. Cannot apply fix.")
                global_metrics.record_adaptation_attempt(
                    attempt, False, "No code block found in LLM response"
                )
                break

        attempt += 1

    # Record final attempt result if we exited the loop due to max attempts
    if return_code != 0 and attempt > max_attempts:
        global_metrics.record_adaptation_attempt(
            max_attempts, False, "Max attempts exceeded"
        )

    if return_code != 0:
        print(
            f"\n--- Test Adaptation Workflow Finished: Build failed after {max_attempts} attempts ---"
        )
    else:
        print(f"\n--- Test Adaptation Workflow Finished: Build succeeded ---")  # noqa: F541

    # Finish metrics tracking
    global_metrics.finish_tracking()


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
        source_repo = "gresrun/jesque"
        source_test_file_in_repo = "src/test/java/net/greghaines/jesque/meta/dao/impl/TestQueueInfoDAORedisImpl.java"

        target_repo = "dbrambilla/jesque"
        target_uut_file_in_repo = (
            "src/main/java/net/greghaines/jesque/meta/dao/QueueInfoDAO.java"
        )

        # 2. Define local path for the cloned target project
        target_project_local_path = os.path.join(
            project_root_dir, "data", "projects", "jesque"
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
