import os

# Define file contents as multi-line strings
POM_XML_CONTENT_A = """
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>project-a</artifactId>
    <version>1.0-SNAPSHOT</version>
    <packaging>jar</packaging>

    <name>Project A</name>

    <properties>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter-api</artifactId>
            <version>5.10.2</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter-engine</artifactId>
            <version>5.10.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.2.5</version>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.13.0</version>
                <configuration>
                    <source>1.8</source>
                    <target>1.8</target>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
"""

POM_XML_CONTENT_B = """
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>project-b</artifactId>
    <version>1.0-SNAPSHOT</version>
    <packaging>jar</packaging>

    <name>Project B</name>

    <properties>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter-api</artifactId>
            <version>5.10.2</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter-engine</artifactId>
            <version>5.10.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.2.5</version>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.13.0</version>
                <configuration>
                    <source>1.8</source>
                    <target>1.8</target>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
"""

CALCULATOR_A_JAVA_CONTENT = """
package com.example;

public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
}
"""

CALCULATOR_B_JAVA_CONTENT = """
package com.example;

public class Calculator {
    // Method renamed from 'add' to 'sum'
    public int sum(int a, int b) {
        return a + b;
    }
}
"""

CALCULATOR_TEST_JAVA_CONTENT = """
package com.example;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

public class CalculatorTest {

    @Test
    void testAdd() {
        Calculator calculator = new Calculator();
        assertEquals(5, calculator.add(2, 3), "2 + 3 should equal 5");
    }

    @Test
    void testAddNegative() {
        Calculator calculator = new Calculator();
        assertEquals(-1, calculator.add(-2, 1), "-2 + 1 should equal -1");
    }
}
"""

def create_file(path, content):
    """Helper function to create a file and write content to it."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip())
    print(f"Created: {path}")

def setup_dummy_projects(base_dir="dummy_java_projects"):
    """Creates ProjectA and ProjectB with their respective files."""
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        print(f"Created base directory: {base_dir}")

    # --- Project A ---
    project_a_dir = os.path.join(base_dir, "ProjectA")
    project_a_main_pkg_dir = os.path.join(project_a_dir, "src", "main", "java", "com", "example")
    project_a_test_pkg_dir = os.path.join(project_a_dir, "src", "test", "java", "com", "example")

    create_file(os.path.join(project_a_dir, "pom.xml"), POM_XML_CONTENT_A)
    create_file(os.path.join(project_a_main_pkg_dir, "Calculator.java"), CALCULATOR_A_JAVA_CONTENT)
    create_file(os.path.join(project_a_test_pkg_dir, "CalculatorTest.java"), CALCULATOR_TEST_JAVA_CONTENT)
    print("--- Project A setup complete ---")

    # --- Project B ---
    project_b_dir = os.path.join(base_dir, "ProjectB")
    project_b_main_pkg_dir = os.path.join(project_b_dir, "src", "main", "java", "com", "example")
    project_b_test_pkg_dir = os.path.join(project_b_dir, "src", "test", "java", "com", "example")

    create_file(os.path.join(project_b_dir, "pom.xml"), POM_XML_CONTENT_B)
    create_file(os.path.join(project_b_main_pkg_dir, "Calculator.java"), CALCULATOR_B_JAVA_CONTENT)
    # For Project B, we use the same test file content which is expected to fail compilation
    create_file(os.path.join(project_b_test_pkg_dir, "CalculatorTest.java"), CALCULATOR_TEST_JAVA_CONTENT)
    print("--- Project B setup complete ---")

if __name__ == "__main__":
    # You can change 'dummy_java_projects' to any path you prefer
    # e.g., os.path.join("data", "dummy_java_projects") if you want it inside your 'data' folder
    setup_dummy_projects("dummy_java_projects")
    print("\nDummy Java projects created successfully.")
    print(f"Navigate to '{os.path.join('dummy_java_projects', 'ProjectA')}' and run 'mvn clean install'.")
    print(f"Navigate to '{os.path.join('dummy_java_projects', 'ProjectB')}' and run 'mvn clean install' (this one should fail compilation).")
