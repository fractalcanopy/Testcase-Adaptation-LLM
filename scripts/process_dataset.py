import pandas as pd
import os
import re  # noqa: F401
import subprocess
import sys

# Add the project root to the Python path to allow importing from 'src'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

# Import after adding project root to path
from src.main import main as run_adaptation_workflow  # noqa: E402
from src.main import pre_build_check  # noqa: E402
from src.utils import get_code_from_github  # noqa: E402
from src.metrics_tracker import global_metrics  # noqa: E402


def clone_repo(project_name: str, projects_base_dir: str):
    """
    Clones a GitHub repository if it doesn't already exist locally.

    Args:
        project_name (str): The name of the project in 'owner/repo' format.
        projects_base_dir (str): The base directory to clone projects into.
    """
    try:
        repo_name = project_name.split("/")[-1]
        target_clone_path = os.path.join(projects_base_dir, repo_name)
        clone_url = f"https://github.com/{project_name}.git"

        if os.path.isdir(target_clone_path):
            print(
                f"Project '{project_name}' already exists at '{target_clone_path}'. Skipping clone."
            )
            return

        print(f"Cloning '{project_name}' into '{target_clone_path}'...")
        subprocess.run(
            ["git", "clone", clone_url, target_clone_path],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"Successfully cloned '{project_name}'.")

    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository '{project_name}':")
        print(e.stderr)
    except Exception as e:
        print(f"An unexpected error occurred during clone: {e}")


def format_file_path(file_path: str, project_name: str) -> str:
    """
    Formats the file path by removing the prefix before the project name
    and converting backslashes to forward slashes.

    Args:
        file_path (str): The original file path from the dataset.
        project_name (str): The project name (e.g., 'jsight/rewrite').

    Returns:
        str: The formatted, relative file path.
    """
    # Normalize the project name to use backslashes for matching in the Windows path
    # This handles both 'owner/repo' and just 'repo'
    project_path_part = project_name.replace("/", "\\")

    # Normalize the file path to handle mixed slashes and find the project part
    normalized_file_path = file_path.replace("/", "\\")

    # Find the starting position of the project path part
    try:
        index = normalized_file_path.rindex(project_path_part)
        # Get the substring after the project name part
        # e.g., after 'jsight\rewrite', which is '\api\src\...'
        relative_path = normalized_file_path[index + len(project_path_part) :]
        # Strip leading backslash and convert all to forward slashes
        return relative_path.lstrip("\\").replace("\\", "/")
    except ValueError:
        # Fallback if the project name isn't in the path as expected
        # This might happen if the path format is unexpected
        # We can try to find a common root like 'src/'
        if "src\\" in normalized_file_path:
            return normalized_file_path.split("src\\", 1)[1].replace("\\", "/")
        return normalized_file_path.replace("\\", "/")


def extract_info_from_row(row: pd.Series) -> dict | None:
    """
    Extracts and formats required information from a single row of the DataFrame.
    """
    try:
        source_project = row["sourceUUTProject"]
        target_project = row["targetUUTProject"]

        raw_source_test_path = row["testCaseSourceFilePath"]
        raw_target_uut_path = row["targetUUTFilePath"]

        formatted_source_test_path = format_file_path(
            raw_source_test_path, source_project
        )
        formatted_target_uut_path = format_file_path(
            raw_target_uut_path, target_project
        )

        return {
            "source_project": source_project,
            "source_test_path": formatted_source_test_path,
            "target_project": target_project,
            "target_uut_path": formatted_target_uut_path,
        }
    except KeyError as e:
        print(f"Error: Missing expected column in dataset: {e}")
        return None


def process_dataset(file_path: str, projects_base_dir: str, num_rows: int = 5):
    """
    Reads the dataset CSV and processes each row to extract and format information.
    """
    try:
        df = pd.read_csv(file_path, sep=";")
        print(f"Successfully loaded dataset from '{file_path}'.\n")

        print(f"--- Processing first {num_rows} rows ---")
        for index, row in df.head(num_rows).iterrows():
            info = extract_info_from_row(row)
            if info:
                print(f"Row {index + 1}:")
                print(f"  Source Project: {info['source_project']}")
                print(f"  Source Test Path: {info['source_test_path']}")
                print(f"  Target Project: {info['target_project']}")
                print(f"  Target UUT Path: {info['target_uut_path']}")

                # Clone the target project repository
                clone_repo(info["target_project"], projects_base_dir)

                # --- Integration with main.py ---
                print("\n--- Preparing to run adaptation workflow ---")

                # 1. Fetch source test code from GitHub
                source_test_code = get_code_from_github(
                    owner_repo=info["source_project"],
                    file_path=info["source_test_path"],
                )
                if not source_test_code:
                    print(
                        f"Could not fetch source code for {info['source_project']}/{info['source_test_path']}. Skipping row."
                    )
                    print("-" * 20)
                    continue

                # 2. Determine local path for the cloned target project
                target_repo_name = info["target_project"].split("/")[-1]
                target_project_local_path = os.path.join(
                    projects_base_dir, target_repo_name
                )

                if not os.path.isdir(target_project_local_path):
                    print(
                        f"Error: Target project directory not found at '{target_project_local_path}' after clone attempt. Skipping row."
                    )
                    print("-" * 20)
                    continue

                # 3. Update the global metrics tracker with source project info
                if (
                    hasattr(global_metrics, "current_result")
                    and global_metrics.current_result
                ):
                    global_metrics.current_result.source_project = info[
                        "source_project"
                    ]

                # 4. Run the main adaptation workflow
                print(f"--- Starting adaptation for Row {index + 1} ---")
                run_adaptation_workflow(
                    original_test_case_code=source_test_code,
                    source_test_origin_path=info["source_test_path"],
                    target_project_path=target_project_local_path,
                    target_class_relative_path=info["target_uut_path"],
                    max_attempts=3,
                    source_project_name=info["source_project"],
                    target_project_name=info["target_project"],
                )
                print(f"--- Finished adaptation for Row {index + 1} ---")
                # --- End of Integration ---

                print("-" * 20)

        # After processing all rows, save metrics and print summary
        print("\n" + "=" * 60)
        print("DATASET PROCESSING COMPLETE")
        print("=" * 60)

        global_metrics.save_results()
        global_metrics.print_summary()

    except FileNotFoundError:
        print(f"Error: Dataset file not found at '{file_path}'")
    except Exception as e:
        print(f"An error occurred: {e}")


def filter_projects_by_prebuild(
    input_csv: str,
    output_csv: str,
    projects_base_dir: str,
    gemini_api_key: str = "",
):
    """
    Reads the dataset CSV, performs a pre-build check for each target project,
    and appends rows that compile successfully to a new CSV.
    """
    import pandas as pd
    import os

    df = pd.read_csv(input_csv, sep=";")
    # Ensure output CSV exists with header
    if not os.path.exists(output_csv):
        df.head(0).to_csv(output_csv, sep=";", index=False)

    for _, row in df.iterrows():
        info = extract_info_from_row(row)
        if not info:
            continue

        # ensure repo is present
        clone_repo(info["target_project"], projects_base_dir)
        repo_name = info["target_project"].split("/")[-1]
        local_path = os.path.join(projects_base_dir, repo_name)
        if not os.path.isdir(local_path):
            continue

        # detect build system and run pre-build check (no LLM)
        from src.main import detect_build_system

        build_system = detect_build_system(local_path)
        return_code, _, _ = pre_build_check(
            local_path, build_system, gemini_api_key, query_llm=False
        )

        if return_code == 0:
            # append the entire original row
            row.to_frame().T.to_csv(
                output_csv, sep=";", index=False, header=False, mode="a"
            )


if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dataset_file = os.path.join(project_root, "data", "test.csv")
    projects_dir = os.path.join(project_root, "data", "projects")

    # Ensure the base directory for projects exists
    os.makedirs(projects_dir, exist_ok=True)

    if os.path.exists(dataset_file):
        process_dataset(dataset_file, projects_dir, num_rows=100)
        # now filter by compile success
        compile_csv = os.path.join(
            project_root, "data", "testcaseTargetUUTPairMatchingSourceCompile.csv"
        )
        # filter_projects_by_prebuild(dataset_file, compile_csv, projects_dir)

    else:
        print(f"Dataset file not found at '{dataset_file}'.")
        print("Please ensure the dataset is available at that location.")
