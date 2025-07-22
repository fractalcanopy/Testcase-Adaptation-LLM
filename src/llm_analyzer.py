import os
from dotenv import load_dotenv


def construct_gradle_fix_prompt(error_output: str, gradle_content: str) -> str:
    """
    Constructs a prompt for the LLM to fix Gradle build configuration issues.

    Args:
        error_output (str): The error output from the Gradle build
        gradle_content (str): The content of the current build.gradle file

    Returns:
        str: The constructed prompt for the LLM
    """
    prompt = f"""
You are a Java build system expert. A Gradle project is failing to build with the following error:

ERROR OUTPUT:
{error_output}

CURRENT BUILD.GRADLE:
{gradle_content}

Please provide a corrected version of the build.gradle file that addresses the build error. 
Focus on common issues like:
- Missing or incorrect dependencies
- Wrong Java version configuration
- Missing plugins
- Incorrect repository configurations
- Version compatibility issues

Provide your response with the corrected build.gradle file in a ```gradle code block.
Only provide the corrected build.gradle content, no additional explanation.
"""
    return prompt


def construct_llm_prompt(
    original_test_case_code: str,
    parsed_build_error: str,
    target_class_code: str,
    target_class_name: str,
    build_file_content: str | None = None,
    build_file_name: str = "build file",
) -> str:
    """
    Constructs a comprehensive prompt for the LLM to suggest test case adaptations.
    Updated to support both Maven and Gradle projects.

    Args:
        original_test_case_code (str): The Java test case code that failed to compile.
        parsed_build_error (str): The parsed error message from the build system.
        target_class_code (str): The source code of the target class being tested.
        target_class_name (str): The name of the target class file.
        build_file_content (str | None): The content of the build configuration file (pom.xml or build.gradle).
        build_file_name (str): The name of the build file (e.g., "pom.xml" or "build.gradle").

    Returns:
        str: The constructed prompt string for the LLM.
    """
    build_system = (
        "Maven"
        if "pom.xml" in build_file_name
        else "Gradle"
        if "build.gradle" in build_file_name
        else "unknown"
    )

    # Determine test framework from build file
    test_framework = "JUnit"
    if build_file_content:
        if "junit-jupiter" in build_file_content or "junit:junit" in build_file_content:
            test_framework = "JUnit"
        elif "testng" in build_file_content:
            test_framework = "TestNG"
        elif "spock" in build_file_content:
            test_framework = "Spock"

    build_context = ""
    if build_file_content:
        build_context = f"""
BUILD CONFIGURATION ({build_file_name}):
{build_file_content}
"""

    prompt = f"""
You are a Java testing expert specializing in test case adaptation for {build_system} projects.

I have a Java test case that fails to compile in the target project. Your task is to modify the test case code to make it compatible with the target project while preserving the original test intent.

BUILD ERROR:
{parsed_build_error}

ORIGINAL TEST CASE:
{original_test_case_code}

TARGET CLASS CODE ({target_class_name}):
{target_class_code}
{build_context}

Please analyze the error and provide a corrected version of the test case that:
1. Fixes the compilation error
2. Maintains the original test intent and behavior
3. Uses the appropriate testing framework ({test_framework})
4. Follows Java best practices
5. Is compatible with the target project structure

Important considerations:
- Look for method signature changes, class name changes, or package structure differences
- Ensure proper imports are included
- Maintain the same test assertions and logic where possible
- If the target class has different method names or signatures, adapt the test accordingly

Classification: Please choose exactly one type of adaptation that best describes the change, and do not combine multiple types. Select one of:
- Type-1: Identical code (no changes needed)
- Type-2: Renamed identifiers (method names, variable names, etc.)
- Type-3: Added/removed statements
- Type-4: Semantic changes (different logic/approach)

Provide your response with the corrected Java test case in a ```java code block, followed
"""
    return prompt


def construct_pom_fix_prompt(build_error: str, pom_content: str) -> str:
    """
    Assembles a structured prompt for an LLM to suggest fixes for a failing pom.xml.

    Args:
        build_error (str): The parsed build error message.
        pom_content (str): The content of the pom.xml file.

    Returns:
        str: A formatted prompt string for the LLM.
    """
    prompt = f"""The following Maven build failed. The error seems to be related to the project configuration in the `pom.xml` file.
    The build error was:
    ```
    {build_error}
    ```
    ---
    Here is the content of the `pom.xml` file:
    ```xml
    {pom_content}
    ```
    ---
    Please analyze the build error and the `pom.xml`.
    Your task is to provide a corrected version of the `pom.xml` file that resolves the build error.

    Provide ONLY the complete, corrected `pom.xml` file content inside a single XML code block. Do not add any explanations before or after the code block.
    """
    return prompt


if __name__ == "__main__":
    # Example Usage:
    sample_test_case = """
package com.example;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

public class CalculatorTest {
    @Test
    void testAdd() {
        Calculator calculator = new Calculator();
        // This line will cause an error if 'add' was renamed to 'sum'
        assertEquals(5, calculator.add(2, 3), "2 + 3 should equal 5");
    }
}
"""

    sample_error = """
[ERROR] c:\\path\\to\\ProjectB\\src\\test\\java\\com\\example\\CalculatorTest.java:[10,30] cannot find symbol
[ERROR]   symbol:   method add(int,int)
[ERROR]   location: variable calculator of type com.example.Calculator
"""

    sample_target_class_code = """
package com.example;

public class Calculator {
    // Method renamed from 'add' to 'sum' in this target project
    public int sum(int a, int b) {
        return a + b;
    }
}
"""

    sample_pom_xml = """
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>project-b</artifactId>
    <version>1.0-SNAPSHOT</version>
    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter-api</artifactId>
            <!-- This version might be different from the one the test was written for -->
            <version>5.8.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
"""
    generated_prompt = construct_llm_prompt(
        original_test_case_code=sample_test_case,
        parsed_build_error=sample_error,
        target_class_code=sample_target_class_code,
        target_class_name="Calculator.java",
        build_file_content=sample_pom_xml,
        build_file_name="pom.xml",
    )
    print("--- Generated LLM Prompt ---")
    print(generated_prompt)

    # Example using the parse_maven_error function from utils.py
    # This assumes utils.py is in the same directory or accessible via PYTHONPATH
    try:
        from utils import (
            parse_maven_error,
        )  # Assuming utils.py is in the same directory for this example

        # A more complete error message string
        full_error_output = """
[INFO] Scanning for projects...
[INFO] Building Project B 1.0-SNAPSHOT
[INFO] -------------------------------------------------------------
[ERROR] COMPILATION ERROR :
[INFO] -------------------------------------------------------------
[ERROR] c:\\Users\\user\\ProjectB\\src\\test\\java\\com\\example\\CalculatorTest.java:[13,30] cannot find symbol
[ERROR]   symbol:   method add(int,int)
[ERROR]   location: variable calculator of type com.example.Calculator
[INFO] 1 error
[INFO] -------------------------------------------------------------
        """
        parsed_error_dict = parse_maven_error(full_error_output)

        # Construct a more specific error string for the prompt from the parsed dictionary
        if parsed_error_dict.get("error_type") == "cannot find symbol":
            error_for_prompt = (
                f"Cannot find symbol: {parsed_error_dict.get('symbol_type')} {parsed_error_dict.get('symbol_name')}\n"
                f"Location: {parsed_error_dict.get('location')}"
            )
        else:
            error_for_prompt = parsed_error_dict.get(
                "raw_message", "No specific error message parsed."
            )

        generated_prompt_with_parsed_error = construct_llm_prompt(
            original_test_case_code=sample_test_case,
            parsed_build_error=error_for_prompt,
            target_class_code=sample_target_class_code,
            target_class_name="Calculator.java",
            build_file_content=sample_pom_xml,
            build_file_name="pom.xml",
        )
        print("\n--- Generated LLM Prompt (with error parsed from utils) ---")
        print(generated_prompt_with_parsed_error)

        """# Now, let's test the Gemini API with the generated prompt
        from test_apis import test_gemini_api
        load_dotenv()
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        test_gemini_api(gemini_api_key, generated_prompt_with_parsed_error)"""

    except ImportError:
        print(
            "\nCould not import parse_maven_error from utils.py for the second example."
        )
        print(
            "Ensure utils.py is in the correct path or run this script from the 'src' directory."
        )
