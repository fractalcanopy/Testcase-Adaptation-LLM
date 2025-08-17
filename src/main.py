import os
import subprocess
import shutil
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


def fix_pom_file(pom_path: str) -> bool:
    """
    Replace old <source> and <target> tags and common maven.compiler/java.version
    and java.source/target.version properties to 1.8 so that Maven will compile under Java 8.
    Return True if file was modified.
    """
    import re

    with open(pom_path, "r", encoding="utf-8") as f:
        content = f.read()

    new_content = content
    # legacy compiler plugin tags
    new_content = new_content.replace(
        "<source>1.6</source>", "<source>1.8</source>"
    ).replace("<target>1.6</target>", "<target>1.8</target>")

    # maven.compiler properties
    new_content = re.sub(
        r"<maven\.compiler\.source>.*?</maven\.compiler\.source>",
        "<maven.compiler.source>1.8</maven.compiler.source>",
        new_content,
    )
    new_content = re.sub(
        r"<maven\.compiler\.target>.*?</maven\.compiler\.target>",
        "<maven.compiler.target>1.8</maven.compiler.target>",
        new_content,
    )

    # java.version property
    new_content = re.sub(
        r"<java\.version>.*?</java\.version>",
        "<java.version>1.8</java.version>",
        new_content,
    )

    # java.source.version / java.target.version properties
    new_content = re.sub(
        r"<java\.source\.version>.*?</java\.source\.version>",
        "<java.source.version>1.8</java.source.version>",
        new_content,
    )
    new_content = re.sub(
        r"<java\.target\.version>.*?</java\.target\.version>",
        "<java.target.version>1.8</java.target.version>",
        new_content,
    )

    if new_content != content:
        with open(pom_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True

    return False


def check_build(
    project_path: str, build_system: str = None, command: list = None
) -> bool:
    """
    Attempts to fix the build of a project by invoking the appropriate build system.
    """
    return_code, stdout, stderr = invoke_build(project_path, build_system, command)
    print(f"Build return code: {return_code}")
    if return_code == 0:
        print(f"Build succeeded for project at {project_path}")
        return True
    else:
        # Try to fix pom.xml if it's a Maven project
        if build_system == "maven":
            pom_path = os.path.join(project_path, "pom.xml")
            if os.path.exists(pom_path):
                if fix_pom_file(pom_path):
                    print(f"Updated {pom_path} to use Java 1.8")
                    # Retry the build after fixing the pom.xml
                    return_code, stdout, stderr = invoke_build(
                        project_path, build_system, command
                    )
                    if return_code == 0:
                        print(f"Build succeeded after fixing {pom_path}")
                        return True
                    else:
                        print(f"Build still failed after fixing {pom_path}")
                else:
                    print(f"No changes made to {pom_path}")
            else:
                print(f"No pom.xml found at {pom_path}")
        return False


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
        if check_build(target_project_path, build_system):
            print(
                f"Build succeeded for {build_system} project at {target_project_path} after LLM fix."
            )
            pom_fix_applied = True if build_system == "maven" else False
            return 0, pom_fix_applied, gradle_fix_applied
        print(
            f"Pre-build check FAILED. The target {build_system} project does not compile on its own. Error message: {stdout_str[:-100]}"
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
) -> tuple[str, str | None]:
    """
    Write the test into the target project preserving its source-test directory structure.
    Returns (new_test_path, backup_path_or_None).
    If a file already existed at the destination, it is copied to <filename>.bak_adaptation
    so it can be restored on failure.
    """

    filename = os.path.basename(source_path)
    # normalize to forward‐slashes for splitting
    source_norm = source_path.replace("\\", "/")
    # get the directory portion
    dir_path = os.path.dirname(source_norm)
    # split out everything after 'src/test/java/'
    parts = dir_path.split("src/test/java/")
    if len(parts) > 1:
        base_dir, relative_test_pkg = parts
        dest_dir = os.path.join(
            target_root, base_dir, "src", "test", "java", relative_test_pkg
        )
    else:
        # fallback: mirror the source_path directory under the target root
        dest_dir = os.path.join(target_root, dir_path)

    os.makedirs(dest_dir, exist_ok=True)
    full_path = os.path.join(dest_dir, filename)
    backup_path: str | None = None
    if os.path.exists(full_path):
        backup_path = full_path + ".bak_adaptation"
        shutil.copy2(full_path, backup_path)
        print(f"Existing test detected; backed up original to {backup_path}")
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(original_code)
    print(f"Saved test to {full_path}")
    return full_path, backup_path


def _prune_empty_parent_dirs(start_path: str, stop_markers: set[str]) -> None:
    """
    Walk upward removing empty directories until encountering a directory
    whose basename is in stop_markers or a non-empty directory.
    """
    cur = os.path.dirname(start_path)
    while cur and os.path.basename(cur) not in stop_markers:
        try:
            if not os.listdir(cur):
                os.rmdir(cur)
                cur = os.path.dirname(cur)
            else:
                break
        except OSError:
            break


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

        # Improved error parsing with better handling
        try:
            parsed = parse_build_error(out or err, build_system)
            err_msg = parsed.get("message") or parsed.get("raw_message", err or out)
            print(f"Parsed error: {err_msg}")

            # Check if error is related to dataset file not found
            if "Dataset file not found" in err_msg:
                print(
                    "Build error is related to missing dataset file. This suggests the test is attempting to access the dataset directly."
                )
                print(
                    "Consider modifying the test to use mock data instead of accessing the dataset file directly."
                )
                break
        except Exception as e:
            print(f"Error parsing build error: {str(e)}")
            err_msg = err or out
            print(f"Using raw error message: {err_msg}")

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
        global_metrics.record_llm_usage(suggestion)
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

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-pro")
        response = model.generate_content(prompt)
        print(f"Full response: {response}")
        return response.text
    except Exception as e:
        print(f"Error querying LLM API: {str(e)}")
        # Return a formatted error that won't break the rest of the workflow
        return f"An error occurred when querying the LLM: {str(e)}"


def main(
    original_test_case_code: str,
    source_test_origin_path: str,
    target_project_path: str,
    target_class_relative_path: str,
    max_attempts: int = 3,
    cleanup_on_failure: bool = True,  # <--- new parameter
    source_project_name: str | None = None,
    target_project_name: str | None = None,
):
    """
    Main orchestrator for the test case adaptation workflow.
    Supports both Maven and Gradle projects.

    Args:
        original_test_case_code: Source Java test case content.
        source_test_origin_path: Original path of the test (for package structure).
        target_project_path: Root of target project.
        target_class_relative_path: Relative path to target class under test.
        max_attempts: Max LLM adaptation attempts.
        cleanup_on_failure: If True (default) restore/remove the inserted test
            when adaptation fails. If False, keep the (failed) adapted test file
            and, if a prior test existed, its backup <name>.bak_adaptation so you
            can inspect differences manually.
        source_project_name: Optional source project name for metrics.
        target_project_name: Optional target project name for metrics.
    """
    # Start metrics tracking
    source_project = source_project_name or "unknown"
    target_project = target_project_name or os.path.basename(target_project_path)
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
    gemini_api_key = os.getenv("GEMINI_API_KEY_2")
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

    test_file, backup_file = save_test_file(
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

    # Cleanup / restore logic after adaptation attempts
    if success:
        if backup_file and os.path.exists(backup_file):
            try:
                os.remove(backup_file)
            except OSError:
                pass
    else:
        if cleanup_on_failure:
            if backup_file and os.path.exists(backup_file):
                try:
                    shutil.move(backup_file, test_file)
                    print(
                        f"Adaptation failed. Restored original test file: {test_file}"
                    )
                except OSError as e:
                    print(f"Failed to restore original test file: {e}")
            else:
                try:
                    os.remove(test_file)
                    print(f"Adaptation failed. Removed inserted test file: {test_file}")
                    _prune_empty_parent_dirs(
                        test_file, stop_markers={"test", "java", "src"}
                    )
                except OSError as e:
                    print(f"Failed to remove inserted test file: {e}")
        else:
            # Leave both the adapted (failed) test and any backup for inspection
            if backup_file and os.path.exists(backup_file):
                print(
                    f"Adaptation failed. Cleanup disabled; keeping adapted test at {test_file} "
                    f"and original backup at {backup_file}"
                )
            else:
                print(
                    f"Adaptation failed. Cleanup disabled; keeping inserted test at {test_file}"
                )

    print("Workflow finished:", "SUCCESS" if success else "FAILURE")
    global_metrics.finish_tracking()


if __name__ == "__main__":
    # --- Configuration ---
    USE_DUMMY_PROJECTS = False
    CLEANUP_ON_FAILURE = True  # Set to False to keep failed adaptation artifacts

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
                    cleanup_on_failure=CLEANUP_ON_FAILURE,
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
                source_project_name=source_repo,
                target_project_name=target_repo,
                cleanup_on_failure=CLEANUP_ON_FAILURE,
            )
