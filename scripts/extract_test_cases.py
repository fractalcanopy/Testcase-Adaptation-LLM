import pandas as pd
import os
import sys
from pathlib import Path

# Add the project root to the Python path to allow importing from 'src'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from process_dataset import extract_info_from_row
from src.utils import get_code_from_github


def extract_test_cases(dataset_path: str, output_dir: str):
    """
    Extracts all source test cases from the dataset CSV and saves them as separate files.

    Args:
        dataset_path (str): Path to the CSV dataset file
        output_dir (str): Directory to save extracted test case files
    """
    try:
        # Read the dataset
        df = pd.read_csv(dataset_path, sep=";")
        print(f"Successfully loaded dataset from '{dataset_path}'")
        print(f"Found {len(df)} rows in the dataset")

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        print(f"Output directory: {output_dir}")

        successful_extractions = 0
        failed_extractions = 0
        skipped_duplicates = 0

        # Track already processed files to avoid duplicates
        processed_files = set()

        print("\n--- Starting test case extraction ---")

        for index, row in df.iterrows():
            info = extract_info_from_row(row)
            if not info:
                print(f"Row {index + 1}: Failed to extract info from row")
                failed_extractions += 1
                continue

            # Get the test file name from the path
            test_file_name = Path(info["source_test_path"]).name

            # Create a unique identifier for this test case
            unique_id = f"{info['source_project']}_{test_file_name}"

            # Skip if we've already processed this exact test case
            if unique_id in processed_files:
                print(
                    f"Row {index + 1}: Skipping duplicate - {test_file_name} from {info['source_project']}"
                )
                skipped_duplicates += 1
                continue

            # Fetch source test code from GitHub
            print(
                f"Row {index + 1}: Fetching {test_file_name} from {info['source_project']}"
            )

            source_test_code = get_code_from_github(
                owner_repo=info["source_project"], file_path=info["source_test_path"]
            )

            if not source_test_code:
                print(
                    f"Row {index + 1}: Failed to fetch source code for {info['source_project']}/{info['source_test_path']}"
                )
                failed_extractions += 1
                continue

            # Generate output filename with project prefix to avoid naming conflicts
            safe_project_name = info["source_project"].replace("/", "_")
            output_filename = f"{safe_project_name}_{test_file_name}"
            output_path = os.path.join(output_dir, output_filename)

            # Save the test case to file
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(source_test_code)

                print(f"Row {index + 1}: Successfully saved {output_filename}")
                successful_extractions += 1
                processed_files.add(unique_id)

            except Exception as e:
                print(f"Row {index + 1}: Failed to save {output_filename}: {e}")
                failed_extractions += 1

        # Print summary
        print("\n" + "=" * 60)
        print("TEST CASE EXTRACTION SUMMARY")
        print("=" * 60)
        print(f"Total rows processed: {len(df)}")
        print(f"Successful extractions: {successful_extractions}")
        print(f"Failed extractions: {failed_extractions}")
        print(f"Skipped duplicates: {skipped_duplicates}")
        print(f"Output directory: {output_dir}")
        print("=" * 60)

    except FileNotFoundError:
        print(f"Error: Dataset file not found at '{dataset_path}'")
    except Exception as e:
        print(f"An error occurred: {e}")


def list_unique_test_files(dataset_path: str):
    """
    Lists all unique test files in the dataset without extracting them.

    Args:
        dataset_path (str): Path to the CSV dataset file
    """
    try:
        df = pd.read_csv(dataset_path, sep=";")
        print(f"Dataset contains {len(df)} rows")

        unique_tests = set()

        for index, row in df.iterrows():
            info = extract_info_from_row(row)
            if info:
                test_file_name = Path(info["source_test_path"]).name
                unique_id = f"{info['source_project']}_{test_file_name}"
                unique_tests.add((info["source_project"], test_file_name))

        print(f"\nFound {len(unique_tests)} unique test files:")
        for project, test_file in sorted(unique_tests):
            print(f"  {project} -> {test_file}")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract test cases from dataset CSV")
    parser.add_argument("dataset", help="Path to the dataset CSV file")
    parser.add_argument("output_dir", help="Directory to save extracted test cases")
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Only list unique test files without extracting",
    )

    args = parser.parse_args()

    if args.list_only:
        list_unique_test_files(args.dataset)
    else:
        extract_test_cases(args.dataset, args.output_dir)
