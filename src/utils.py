import os

def save_java_test_to_target(java_code_string: str, test_filename: str, target_project_root: str = "data/target_project"):
    """
    Saves a string of Java test code as a .java file into a 'test' subdirectory
    of the specified target project root.

    Args:
        java_code_string (str): The Java test code as a string.
        test_filename (str): The desired filename for the .java file (e.g., "MyTest.java").
        target_project_root (str): The root path of the dummy target project.
                                   Defaults to "data/target_project".
    """
    if not test_filename.endswith(".java"):
        test_filename += ".java"

    # Define the path to the 'test' subdirectory
    test_subdirectory = os.path.join(target_project_root, "test")

    # Create the directories if they don't exist
    os.makedirs(test_subdirectory, exist_ok=True)

    # Define the full path for the Java test file
    file_path = os.path.join(test_subdirectory, test_filename)

    # Write the Java code to the file
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(java_code_string)
        print(f"Successfully saved Java test case to: {file_path}")
    except IOError as e:
        print(f"Error saving Java test case: {e}")

if __name__ == '__main__':
    # Example Usage:
    sample_java_test_code = """
package com.example.test;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

public class MySimpleTest {

    @Test
    void addition() {
        assertEquals(2, 1 + 1);
    }
}
"""
    # This will create data/target_project/test/MySimpleTest.java
    save_java_test_to_target(sample_java_test_code, "MySimpleTest.java")

    # Example with a different target project location
    # This will create custom_project/test/AnotherTest.java
    # save_java_test_to_target(sample_java_test_code, "AnotherTest", target_project_root="custom_project")