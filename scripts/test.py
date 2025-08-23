import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path to allow importing from 'src'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from src.utils import get_code_from_github


if __name__ == "__main__":
    load_dotenv()

    test_code = get_code_from_github(
        "pires/obd-java-api",
        "src/test/java/com/github/pires/obd/exceptions/UnsupportedCommandExceptionTest.java",
    )

    print("Retrieved test code:")
    print(test_code)
