import subprocess
import os

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
        command = ["mvn", "clean", "test-compile"] # Default Maven command

    if not os.path.isdir(project_dir):
        return -1, "", f"Error: Project directory '{project_dir}' not found."

    try:
        # On Windows, Maven commands (mvn.cmd) are often batch scripts,
        # so using shell=True can be more reliable, or ensure mvn is directly executable.
        # For cross-platform compatibility and security, it's better to ensure 'mvn'
        # (or 'mvn.cmd' on Windows) is in the PATH and avoid shell=True if possible.
        # If 'mvn' is not found, you might need to provide the full path to mvn.cmd
        # or use shell=True (with caution).
        is_windows = os.name == 'nt'
        
        process = subprocess.Popen(
            command,
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # Decodes stdout and stderr as text
            shell=is_windows # Helps find mvn.cmd on Windows; be cautious with shell=True
        )
        stdout, stderr = process.communicate()
        return_code = process.returncode
        return return_code, stdout, stderr
    except FileNotFoundError:
        return -1, "", f"Error: Maven command ('{command[0]}') not found. Make sure Maven is installed and in your PATH."
    except Exception as e:
        return -1, "", f"An unexpected error occurred: {e}"

if __name__ == '__main__':
    # --- Test with Project A (should succeed) ---
    project_a_path = os.path.join("..", "dummy_java_projects", "ProjectA") # Adjust path if running from src/
    # If create_dummy_projects.py is in the root, and this script is in src/, then:
    project_a_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dummy_java_projects", "ProjectA"))


    print(f"--- Building Project A ({project_a_path}) ---")
    return_code_a, stdout_a, stderr_a = invoke_maven_build(project_a_path)

    print(f"Project A Return Code: {return_code_a}")
    print("Project A STDOUT:")
    print(stdout_a[-500:]) # Print last 500 chars of STDOUT
    if return_code_a != 0:
        print("Project A STDERR:")
        print(stderr_a)
    print("-" * 30)

    # --- Test with Project B (should fail compilation) ---
    project_b_path = os.path.join("..", "dummy_java_projects", "ProjectB") # Adjust path
    project_b_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dummy_java_projects", "ProjectB"))

    print(f"--- Building Project B ({project_b_path}) ---")
    return_code_b, stdout_b, stderr_b = invoke_maven_build(project_b_path)

    print(f"Project B Return Code: {return_code_b}")
    print("Project B STDOUT (last 500 chars):")
    print(stdout_b[-500:])
    if return_code_b != 0: # Expecting non-zero for Project B due to compilation error
        print("Project B STDERR:")
        print(stderr_b) # This should contain the compilation error
    print("-" * 30)

    # --- Test with a non-existent directory ---
    non_existent_path = "non_existent_project"
    print(f"--- Building Non-Existent Project ({non_existent_path}) ---")
    return_code_ne, stdout_ne, stderr_ne = invoke_maven_build(non_existent_path)
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