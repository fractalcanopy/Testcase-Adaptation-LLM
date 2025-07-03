import os
from dotenv import load_dotenv


def construct_llm_prompt(
    original_test_case_code: str,
    parsed_build_error: str,
    target_class_code: str,
    target_class_name: str = "the relevant class",  # Optional: to make the prompt more specific
    build_file_content: str | None = None,
    build_file_name: str = "build file",
) -> str:
    """
    Assembles a structured prompt for an LLM to suggest fixes for a failing Java test case.

    Args:
        original_test_case_code (str): The source code of the original Java test case.
        parsed_build_error (str): The parsed build error message from the target project.
        target_class_code (str): The source code of the relevant class(es) in the target project.
        target_class_name (str, optional): The name of the target class, for a more specific prompt.
                                           Defaults to "the relevant class".
        build_file_content (str | None, optional): The content of the build file (e.g., pom.xml). Defaults to None.
        build_file_name (str, optional): The name of the build file. Defaults to "build file".

    Returns:
        str: A formatted prompt string for the LLM.
    """
    prompt = f"""The following Java test case failed to compile in a target project:
```java
{original_test_case_code}
```
---
The build error was:
```
{parsed_build_error}
```
---
Here is the relevant code from the target project's {target_class_name}:
```java
{target_class_code}
```
"""
    if build_file_content:
        lang = (
            "xml"
            if "pom.xml" in build_file_name.lower()
            else "groovy"
            if "build.gradle" in build_file_name.lower()
            else ""
        )
        prompt += f"""---
Here is the content of the target project's build file ({build_file_name}):
```{lang}
{build_file_content}
```
"""

    prompt += """---
Please analyze the build error in the context of the provided test case, target class code, and build file.
Suggest specific modifications to the *test case code only* to fix the build error and make it compatible with the target project's class.

After suggesting the changes, classify the relationship between the original and the modified test case as a code clone of Type-1, Type-2, Type-3, or Type-4 based on these definitions:
- **Type-1:** Exact copy, only whitespace or comments differ.
- **Type-2:** Syntactically identical, but with changes in variable names, types, or literals.
- **Type-3:** Copied with further modifications like adding, removing, or changing statements.
- **Type-4:** Semantically similar code that achieves the same goal but with different syntax.

Explain shortly why the changes are necessary and your reasoning for the classification.
Provide ONLY the modified test case code.
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
