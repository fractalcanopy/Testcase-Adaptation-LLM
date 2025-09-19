import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path to allow importing from 'src'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)
# "source_project": "hybridtheory/gelfj",
# source_test_path": "src/test/java/org/graylog2/GelfMessageTest.java",
from src.utils import get_code_from_github


if __name__ == "__main__":
    load_dotenv()

    test_code = get_code_from_github(
        "joker1/redline",
        "src/test/java/org/redline_rpm/ant/RedlineTaskTest.java",
    )

    print("Retrieved test code:")
    print(test_code)
