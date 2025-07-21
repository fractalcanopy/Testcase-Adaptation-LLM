import os
import subprocess
from dotenv import load_dotenv

from .utils import (
    parse_maven_error,
    parse_gradle_error,
    parse_build_error,
    extract_java_code_from_llm_response,
    extract_xml_code_from_llm_response,
    extract_gradle_code_from_llm_response,  # Add this import
    get_code_from_github,
)
from .java_env_manager import (
    invoke_maven_build,
    invoke_gradle_build,
    invoke_build,
    detect_build_system,
)  # Add these imports
from .llm_analyzer import (
    construct_llm_prompt,
    construct_pom_fix_prompt,
    construct_gradle_fix_prompt,
)  # Add gradle prompt function
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


def set_java_8_environment():
    """
    Sets environment variables to use JDK 8 for Maven builds.
    """
    try:
        # Get JDK 8 home path
        result = subprocess.run(
            ["/usr/libexec/java_home", "-v", "1.8"],
            capture_output=True,
            text=True,
            check=True,
        )
        java_8_home = result.stdout.strip()

        # Set environment variables
        os.environ["JAVA_HOME"] = java_8_home
        os.environ["PATH"] = f"{java_8_home}/bin:{os.environ.get('PATH', '')}"

        print(f"Set JAVA_HOME to: {java_8_home}")
        return True
    except subprocess.CalledProcessError:
        print("Error: JDK 8 not found. Please install JDK 8 first.")
        return False


def query_llm_for_maven_fix(
    target_project_path: str,
    build_system: str,
    error_for_prompt: str,
    gemini_api_key: str,
):
    build_file_path = os.path.join(target_project_path, "pom.xml")
    build_file_content = read_file_content(build_file_path)

    if build_file_content and error_for_prompt:
        # Construct prompt to fix pom.xml
        build_fix_prompt = construct_pom_fix_prompt(
            error_for_prompt, build_file_content
        )

        # Query LLM and apply fix
        try:
            import google.generativeai as genai

            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(build_fix_prompt)
            llm_suggestion = response.text

            # Extract and apply fix
            suggested_build_file = extract_xml_code_from_llm_response(llm_suggestion)
            print("\n--- LLM Suggested pom.xml Fix ---")
            print("--------------------------------------------------")
            print(suggested_build_file)
            print("--------------------------------------------------")
            if suggested_build_file:
                print("LLM suggested a fix for pom.xml. Applying and re-building...")
                with open(build_file_path, "w", encoding="utf-8") as f:
                    f.write(suggested_build_file)
                pom_fix_applied = True

                # Re-build to verify the fix
                return_code, _, stderr_str = invoke_build(
                    target_project_path, build_system
                )
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


def query_llm_for_gradle_fix(
    target_project_path: str,
    build_system: str,
    error_for_prompt: str,
    gemini_api_key: str,
):
    # Try both build.gradle and build.gradle.kts
    gradle_file_path = os.path.join(target_project_path, "build.gradle")
    if not os.path.exists(gradle_file_path):
        gradle_file_path = os.path.join(target_project_path, "build.gradle.kts")

    build_file_content = read_file_content(gradle_file_path)

    if build_file_content and error_for_prompt:
        # Construct prompt to fix build.gradle
        build_fix_prompt = construct_gradle_fix_prompt(
            error_for_prompt, build_file_content
        )

        # Query LLM and apply fix
        try:
            import google.generativeai as genai

            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(build_fix_prompt)
            llm_suggestion = response.text

            # Extract and apply fix (assuming gradle files are in code blocks)
            # For Gradle projects, use the new extraction function
            if build_system == "gradle":
                # Extract Gradle build file content
                suggested_build_file = extract_gradle_code_from_llm_response(
                    llm_suggestion
                )
                if not suggested_build_file:
                    # Fallback to generic code extraction
                    suggested_build_file = extract_java_code_from_llm_response(
                        llm_suggestion
                    )

            print("\n--- LLM Suggested build.gradle Fix ---")
            print("--------------------------------------------------")
            print(suggested_build_file)
            print("--------------------------------------------------")
            if suggested_build_file:
                print(
                    "LLM suggested a fix for build.gradle. Applying and re-building..."
                )
                with open(gradle_file_path, "w", encoding="utf-8") as f:
                    f.write(suggested_build_file)
                gradle_fix_applied = True

                # Re-build to verify the fix
                return_code, _, stderr_str = invoke_build(
                    target_project_path, build_system
                )
                if return_code == 0:
                    print("SUCCESS: Pre-build check passed after fixing build.gradle.")
                else:
                    print(
                        "FAILURE: Pre-build check failed again after applying build.gradle fix."
                    )
                    print(f"Error:\n{stderr_str}")
                    print("Aborting workflow.")
                    global_metrics.record_pre_build_result(False, gradle_fix_applied)
                    global_metrics.finish_tracking()
                    return
            else:
                print(
                    "LLM did not provide a valid build.gradle fix. Aborting workflow."
                )
                global_metrics.record_pre_build_result(False, gradle_fix_applied)
                global_metrics.finish_tracking()
                return
        except Exception as e:
            print(f"An error occurred while trying to fix build.gradle: {e}")
            global_metrics.record_pre_build_result(False, gradle_fix_applied)
            global_metrics.finish_tracking()
            return


def pre_build_check(
    target_project_path: str,
    build_system: str,
    gemini_api_key: str,
    query_llm: bool = False,
) -> tuple[int, bool, bool]:
    # Invoke the build process
    return_code, stdout_str, stderr_str = invoke_build(
        target_project_path, build_system
    )

    pom_fix_applied = False
    gradle_fix_applied = False

    if return_code != 0:
        print(
            f"Pre-build check FAILED. The target {build_system} project does not compile on its own. Error message: {stdout_str}"
        )
        if query_llm:
            print(f"Attempting to fix {build_system} build issues using LLM…")
            # Parse error based on build system
            parsed_error = parse_build_error(
                stdout_str if stdout_str else stderr_str, build_system
            )
            error_for_prompt = parsed_error.get("raw_message", stderr_str)

            # Read build file based on build system
            if build_system == "maven":
                query_llm_for_maven_fix(
                    target_project_path,
                    build_system,
                    error_for_prompt,
                    gemini_api_key,
                )
                pom_fix_applied = True

            elif build_system == "gradle":
                query_llm_for_gradle_fix(
                    target_project_path,
                    build_system,
                    error_for_prompt,
                    gemini_api_key,
                )
                gradle_fix_applied = True

            # ... do NOT call global_metrics.finish_tracking() here ...
            return return_code, pom_fix_applied, gradle_fix_applied
        else:
            print("Could not read build file or build error. Aborting workflow.")
            global_metrics.record_pre_build_result(
                False, pom_fix_applied or gradle_fix_applied
            )
            global_metrics.finish_tracking()
            return return_code, pom_fix_applied, gradle_fix_applied
    # Pre‐build succeeded
    print(
        f"SUCCESS: Pre-build check passed. Target {build_system} project builds correctly."
    )
    return return_code, pom_fix_applied, gradle_fix_applied


def save_test_file(
    original_code: str,
    source_path: str,
    target_root: str,
    target_class_relpath: str | None = None,
) -> str:
    """Write the test into the target project under the same module and package as the target class."""
    filename = os.path.basename(source_path)
    pkg = ""
    # If we know the target class path, mirror its package under test
    if target_class_relpath:
        class_dir = os.path.dirname(target_class_relpath).replace("\\", "/")
        parts = class_dir.split("src/main/java/")
        if len(parts) > 1:
            base_dir, pkg = parts
            dest_dir = os.path.join(target_root, base_dir, "src", "test", "java", pkg)
        else:
            # fallback to original source-based logic
            parts = os.path.dirname(source_path.replace("\\", "/")).split(
                "src/test/java/"
            )
            base_dir = parts[0] if len(parts) > 1 else ""
            pkg = parts[1] if len(parts) > 1 else ""
            dest_dir = os.path.join(target_root, base_dir, "src", "test", "java", pkg)
    else:
        # preserve original source-test location
        parts = os.path.dirname(source_path.replace("\\", "/")).split("src/test/java/")
        base_dir = parts[0] if len(parts) > 1 else ""
        pkg = parts[1] if len(parts) > 1 else ""
        dest_dir = os.path.join(target_root, base_dir, "src", "test", "java", pkg)

    os.makedirs(dest_dir, exist_ok=True)
    full_path = os.path.join(dest_dir, filename)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(original_code)
    print(f"Saved test to {full_path}")
    return full_path


def adaptation_loop(
    test_file: str,
    target_root: str,
    class_relpath: str,
    build_system: str,
    max_attempts: int,
    api_key: str,
):
    """Steps B–J: build, parse failures, prompt LLM, rewrite test, repeat."""
    current_code = open(test_file).read()
    for attempt in range(1, max_attempts + 1):
        print(f"\nAttempt {attempt}/{max_attempts}: building…")
        code, out, err = invoke_build(target_root, build_system)
        if code == 0:
            global_metrics.record_adaptation_attempt(attempt, True)
            print("Build succeeded")
            return True

        global_metrics.record_adaptation_attempt(attempt, False)
        parsed = parse_build_error(out or err, build_system)
        err_msg = parsed.get("message") or parsed.get("raw_message", err or out)
        print(f"Parsed error: {err_msg}")

        # read target class
        cls_path = os.path.join(target_root, class_relpath)
        class_code = open(cls_path, "r", encoding="utf-8").read()

        # build prompt & query LLM
        prompt = construct_llm_prompt(
            original_test_case_code=current_code,
            parsed_build_error=err_msg,
            target_class_code=class_code,
            target_class_name=os.path.basename(cls_path),
            build_file_content=None,
            build_file_name="",
        )
        suggestion = query_llm(prompt, api_key)
        print("\n--- LLM Suggestion ---")
        print("--------------------------------------------------")
        print(suggestion)
        print("--------------------------------------------------")
        new_test = extract_java_code_from_llm_response(suggestion)
        if not new_test:
            print("No code extracted; aborting.")
            break

        # write new test and retry
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(new_test)
        current_code = new_test

    print("Adaptation failed after max attempts")
    return False


def query_llm(prompt: str, api_key: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    return model.generate_content(prompt).text


def main(
    original_test_case_code: str,
    source_test_origin_path: str,
    target_project_path: str,
    target_class_relative_path: str,
    max_attempts: int = 3,
):
    """
    Main orchestrator for the test case adaptation workflow.
    Supports both Maven and Gradle projects.

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

    # Detect build system
    build_system = detect_build_system(target_project_path)
    print(f"Detected build system: {build_system}")

    if build_system == "unknown":
        print(
            "Error: Could not detect build system. Project must have pom.xml (Maven) or build.gradle (Gradle)."
        )
        global_metrics.record_pre_build_result(False, False)
        global_metrics.finish_tracking()
        return

    return_code, pom_fix_applied, gradle_fix_applied = pre_build_check(
        target_project_path, build_system, gemini_api_key
    )

    # Record pre-build result
    global_metrics.record_pre_build_result(
        return_code == 0, pom_fix_applied or gradle_fix_applied
    )

    if return_code != 0:
        print(
            f"Pre-build check failed with return code {return_code}. Aborting workflow."
        )
        global_metrics.finish_tracking()
        return

    test_file = save_test_file(
        original_test_case_code,
        source_test_origin_path,
        target_project_path,
        target_class_relative_path,
    )
    success = adaptation_loop(
        test_file,
        target_project_path,
        target_class_relative_path,
        build_system,
        max_attempts,
        gemini_api_key,
    )

    print("Workflow finished:", "SUCCESS" if success else "FAILURE")
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
