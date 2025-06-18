import pandas as pd
import os


def read_dataset(file_path: str) -> pd.DataFrame | None:
    """
    Reads the dataset from a CSV file into a pandas DataFrame.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        pd.DataFrame | None: The loaded DataFrame, or None if the file is not found.
    """
    if not os.path.exists(file_path):
        print(f"Error: Dataset file not found at '{file_path}'")
        print("Please ensure the dataset file is present in the 'data' directory.")
        return None

    print(f"Reading dataset from '{file_path}'...")
    try:
        df = pd.read_csv(file_path, sep=";")
        return df
    except Exception as e:
        print(f"An error occurred while reading the CSV file: {e}")
        return None


def main():
    """
    Main function to load and inspect the dataset.
    """
    # Assume the script is run from the project root.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dataset_file = os.path.join(
        project_root, "data", "testcaseTargetUUTPairMatching.csv"
    )

    dataset_df = read_dataset(dataset_file)

    if dataset_df is not None:
        print("\nSuccessfully loaded dataset. First 5 rows:")
        print("---------------------------------------------")
        print(dataset_df.head())
        print("---------------------------------------------")


if __name__ == "__main__":
    main()
