import subprocess
import os
from .utils import parse_maven_error


def detect_build_system(project_dir: str) -> str:
    """
    Detects the build system used by the project.

    Args:
        project_dir (str): Path to the project directory

    Returns:
        str: 'maven' if pom.xml exists, 'gradle' if build.gradle exists, 'unknown' otherwise
    """
    if os.path.exists(os.path.join(project_dir, "pom.xml")):
        return "maven"
    elif os.path.exists(os.path.join(project_dir, "build.gradle")) or os.path.exists(
        os.path.join(project_dir, "build.gradle.kts")
    ):
        return "gradle"
    else:
        return "unknown"


def invoke_maven_build(project_dir: str, command: list = None):
    """
    Navigates to the specified Java project directory and executes a Maven build command.

    Args:
        project_dir (str): The absolute or relative path to the Java project directory.
        command (list, optional): The Maven command and its arguments as a list of strings.
                                  Defaults to ["mvn", "clean", "test-compile"].

    Returns:
        tuple: (return_code, stdout_str, stderr_str)
               return_code (int): The exit code of the Maven command.
               stdout_str (str): The standard output from the command.
               stderr_str (str): The standard error from the command.
    """
    if command is None:
        command = ["mvn", "clean", "test-compile"]  # Default Maven command

    if not os.path.isdir(project_dir):
        return -1, "", f"Error: Project directory '{project_dir}' not found."

    try:
        # On Windows, Maven commands (mvn.cmd) are often batch scripts,
        # so using shell=True can be more reliable, or ensure mvn is directly executable.
        # For cross-platform compatibility and security, it's better to ensure 'mvn'
        # (or 'mvn.cmd' on Windows) is in the PATH and avoid shell=True if possible.
        # If 'mvn' is not found, you might need to provide the full path to mvn.cmd
        # or use shell=True (with caution).
        is_windows = os.name == "nt"

        process = subprocess.Popen(
            command,
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # Decodes stdout and stderr as text
            shell=is_windows,  # Helps find mvn.cmd on Windows; be cautious with shell=True
        )
        stdout, stderr = process.communicate()
        return_code = process.returncode
        return return_code, stdout, stderr
    except FileNotFoundError:
        return (
            -1,
            "",
            f"Error: Maven command ('{command[0]}') not found. Make sure Maven is installed and in your PATH.",
        )
    except Exception as e:
        return -1, "", f"An unexpected error occurred: {e}"


def invoke_gradle_build(project_dir: str, command: list = None):
    """
    Navigates to the specified Java project directory and executes a Gradle build command.

    Args:
        project_dir (str): The absolute or relative path to the Java project directory.
        command (list, optional): The Gradle command and its arguments as a list of strings.
                                  Defaults to ["./gradlew", "clean", "testClasses"].

    Returns:
        tuple: (return_code, stdout_str, stderr_str)
               return_code (int): The exit code of the Gradle command.
               stdout_str (str): The standard output from the command.
               stderr_str (str): The standard error from the command.
    """
    if command is None:
        # Use gradlew wrapper if available, otherwise fall back to gradle
        gradlew_path = os.path.join(project_dir, "gradlew")
        if os.path.exists(gradlew_path):
            command = ["./gradlew", "clean", "testClasses"]
        else:
            command = ["gradle", "clean", "testClasses"]

    if not os.path.isdir(project_dir):
        return -1, "", f"Error: Project directory '{project_dir}' not found."

    try:
        is_windows = os.name == "nt"

        # On Windows, use gradlew.bat instead of gradlew
        if is_windows and command[0] == "./gradlew":
            command[0] = "gradlew.bat"

        process = subprocess.Popen(
            command,
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=is_windows,
        )
        stdout, stderr = process.communicate()
        return_code = process.returncode
        return return_code, stdout, stderr
    except FileNotFoundError:
        return (
            -1,
            "",
            f"Error: Gradle command ('{command[0]}') not found. Make sure Gradle is installed and in your PATH.",
        )
    except Exception as e:
        return -1, "", f"An unexpected error occurred: {e}"


def invoke_build(project_dir: str, build_system: str = None, command: list = None):
    """
    Invokes the appropriate build system for the project.

    Args:
        project_dir (str): Path to the project directory
        build_system (str, optional): Build system to use ('maven' or 'gradle').
                                     If None, will auto-detect.
        command (list, optional): Custom command to run. If None, uses default.

    Returns:
        tuple: (return_code, stdout_str, stderr_str)
    """
    if build_system is None:
        build_system = detect_build_system(project_dir)

    if build_system == "maven":
        return invoke_maven_build(project_dir, command)
    elif build_system == "gradle":
        return invoke_gradle_build(project_dir, command)
    else:
        return (
            -1,
            "",
            f"Error: Unknown build system. Project must have pom.xml (Maven) or build.gradle (Gradle).",
        )


if __name__ == "__main__":
    use_dummy_projects = False  # Set to False to use real projects

    return_code, stdout, stderr = invoke_maven_build(
        "data/projects/rewrite", command=["mvn", "clean", "test-compile"]
    )

    filtered_error = parse_maven_error(stdout)
    print(f"Filtered Error: {filtered_error}")
    # Print last 500 chars of STDOUT

    if use_dummy_projects:
        # --- Test with Project A (should succeed) ---
        project_a_path = os.path.join(
            "..", "dummy_java_projects", "ProjectA"
        )  # Adjust path if running from src/
        # If create_dummy_projects.py is in the root, and this script is in src/, then:
        project_a_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "..", "dummy_java_projects", "ProjectA"
            )
        )

        print(f"--- Building Project A ({project_a_path}) ---")
        return_code_a, stdout_a, stderr_a = invoke_build(project_a_path)

        print(f"Project A Return Code: {return_code_a}")
        print("Project A STDOUT:")
        print(stdout_a[-500:])  # Print last 500 chars of STDOUT
        if return_code_a != 0:
            print("Project A STDERR:")
            print(stderr_a)
        print("-" * 30)

        # --- Test with Project B (should fail compilation) ---
        project_b_path = os.path.join(
            "..", "dummy_java_projects", "ProjectB"
        )  # Adjust path
        project_b_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "..", "dummy_java_projects", "ProjectB"
            )
        )

        print(f"--- Building Project B ({project_b_path}) ---")
        return_code_b, stdout_b, stderr_b = invoke_build(project_b_path)

        print(f"Project B Return Code: {return_code_b}")
        print("Project B STDOUT (last 500 chars):")
        print(stdout_b[-500:])
        if (
            return_code_b != 0
        ):  # Expecting non-zero for Project B due to compilation error
            print("Project B STDERR:")
            print(stderr_b)  # This should contain the compilation error
        print("-" * 30)

        # --- Test with a non-existent directory ---
        non_existent_path = "non_existent_project"
        print(f"--- Building Non-Existent Project ({non_existent_path}) ---")
        return_code_ne, stdout_ne, stderr_ne = invoke_build(non_existent_path)
        print(f"Non-Existent Project Return Code: {return_code_ne}")
        print(f"Non-Existent Project STDERR: {stderr_ne}")
        print("-" * 30)

        # --- Test with Maven not found (simulated by providing a wrong command) ---
        # This test is more conceptual unless you temporarily rename your mvn executable
        # print(f"--- Building with invalid Maven command ---")
        # return_code_inv, stdout_inv, stderr_inv = invoke_maven_build(project_a_path, command=["invalid_mvn_cmd", "clean"])
        # print(f"Invalid Command Return Code: {return_code_inv}")
        # print(f"Invalid Command STDERR: {stderr_inv}")
        # print("-" * 30)
