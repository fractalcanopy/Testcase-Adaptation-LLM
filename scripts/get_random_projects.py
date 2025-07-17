### This script randomly selects a subset of projects from a given CSV file and saves the result to a new CSV file.
def get_random_projects(input_file, output_file, num_projects):
    import pandas as pd
    import random

    # Read the input CSV file
    df = pd.read_csv(input_file, sep=";")

    # Check if the number of requested projects is less than available projects
    if num_projects > len(df):
        raise ValueError(
            "Requested number of projects exceeds available projects in the dataset."
        )

    # Randomly select the specified number of projects
    selected_projects = df.sample(n=num_projects, random_state=42)

    # Save the selected projects to a new CSV file
    selected_projects.to_csv(output_file, sep=";", index=False)
    print(f"Randomly selected {num_projects} projects and saved to '{output_file}'.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Randomly select projects from a dataset."
    )
    parser.add_argument(
        "input_file", type=str, help="Path to the input CSV file containing projects."
    )
    parser.add_argument(
        "output_file", type=str, help="Path to save the randomly selected projects."
    )
    parser.add_argument(
        "num_projects", type=int, help="Number of random projects to select."
    )

    args = parser.parse_args()

    get_random_projects(args.input_file, args.output_file, args.num_projects)
