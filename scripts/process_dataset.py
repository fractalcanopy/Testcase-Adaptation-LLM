import pandas as pd
import os
import re


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


def process_dataset(file_path: str, num_rows: int = 5):
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
                print("-" * 20)

    except FileNotFoundError:
        print(f"Error: Dataset file not found at '{file_path}'")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dataset_file = os.path.join(
        project_root, "data", "testcaseTargetUUTPairMatching.csv"
    )

    if os.path.exists(dataset_file):
        process_dataset(dataset_file, num_rows=3)
    else:
        print(f"Dataset file not found at '{dataset_file}'.")
        print("Please ensure the dataset is available at that location.")
