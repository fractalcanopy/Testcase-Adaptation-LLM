import csv
import random
import os
import sys
from pathlib import PurePath  # noqa: F401
from typing import Optional

# Add the project root to the Python path to allow importing from 'src'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)
from src.java_env_manager import invoke_build  # noqa: E402


def write_matching_rows(
    input_csv: str,
    output_csv: str,
    max_results: int,
    rng: Optional[random.Random] = None,
    verbose: bool = False,
) -> int:
    """
    Scan the input CSV and write *at most* max_results rows
    (max. one per ecosystem) that satisfy the match rule
    to output_csv, preserving exactly the original column order.
    Return the number of rows written.

    A row is a "match" within its own ecosystem if
    basename(sourceUUTFilePath) == basename(targetUUTFilePath),
    where basename means "text after the last '/' or '\'.
    """

    # Use the provided RNG or create a new one
    if rng is None:
        rng = random.Random()

    # Dictionary to store the first match for each ecosystem
    first_match = {}
    fieldnames = None
    total_rows = 0

    if verbose:
        print(f"Processing input file: {input_csv}")

    # Read the input CSV file in streaming mode
    with open(input_csv, "r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile, delimiter=";")
        fieldnames = reader.fieldnames

        # Check if the required headers are present
        required_headers = ["ecosystemID", "sourceUUTFilePath", "targetUUTFilePath"]
        if not all(header in fieldnames for header in required_headers):
            raise ValueError(
                f"Input CSV is missing one or more required headers: {required_headers}"
            )

        # Process each row
        for row in reader:
            total_rows += 1
            ecosystem_id = row["ecosystemID"]

            # Skip if we already found a match for this ecosystem
            if ecosystem_id in first_match:
                continue

            # Skip if missing file paths or empty ecosystem ID
            if (
                not row["sourceUUTFilePath"]
                or not row["targetUUTFilePath"]
                or not ecosystem_id
            ):
                if verbose:
                    print(
                        f"Skipping row with missing path or empty ecosystem ID: {row}"
                    )
                continue

            # Extract just the filenames (text after the last slash or backslash)
            source_path = row["sourceUUTFilePath"].strip()
            target_path = row["targetUUTFilePath"].strip()

            # Extract just the filenames using string operations to be extra careful
            source_file = source_path.split("\\")[-1]
            target_file = target_path.split("\\")[-1]

            # Handle possible forward slashes too
            if "/" in source_file:
                source_file = source_file.split("/")[-1]
            if "/" in target_file:
                target_file = target_file.split("/")[-1]

            if verbose and total_rows % 1000 == 0:
                print(f"Processing row {total_rows}, ecosystem {ecosystem_id}")
                print(f"  Source path: {source_path}")
                print(f"  Target path: {target_path}")
                print(f"  Source filename: {source_file}")
                print(f"  Target filename: {target_file}")

            # Check if the filenames match (case insensitive for robustness)
            if (
                source_file
                and target_file
                and source_file.lower() == target_file.lower()
            ):
                if verbose:
                    print(f"Match found for ecosystem {ecosystem_id}: {source_file}")
                first_match[ecosystem_id] = row

    if verbose:
        print(f"Processed {total_rows} rows total")
        print(f"Found {len(first_match)} matching ecosystems")

    # Shuffle the ecosystem IDs
    ecosystem_ids = list(first_match.keys())
    rng.shuffle(ecosystem_ids)

    # Limit to max_results
    ecosystem_ids = ecosystem_ids[:max_results]

    if verbose:
        print(f"Selected {len(ecosystem_ids)} ecosystems after limiting to max_results")

    # Write to the output CSV file, preserving the original column order
    with open(output_csv, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(
            outfile, fieldnames=fieldnames, delimiter=";", quoting=csv.QUOTE_MINIMAL
        )
        writer.writeheader()

        # Write rows up to max_results or until we run out of candidates
        rows_written = 0
        for ecosystem_id in ecosystem_ids:
            writer.writerow(first_match[ecosystem_id])
            rows_written += 1

    return rows_written


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract matching rows from a CSV file where source and target file names match."
    )
    parser.add_argument("input_file", type=str, help="Path to the input CSV file")
    parser.add_argument("output_file", type=str, help="Path to save the matching rows")
    parser.add_argument(
        "max_results", type=int, help="Maximum number of results to output"
    )
    parser.add_argument(
        "--seed", type=int, help="Random seed for reproducibility", default=None
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    rng = random.Random(args.seed) if args.seed is not None else None

    rows_written = write_matching_rows(
        args.input_file, args.output_file, args.max_results, rng, args.verbose
    )

    print(f"Wrote {rows_written} matching rows to {args.output_file}")
