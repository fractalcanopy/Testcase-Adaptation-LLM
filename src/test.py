from utils import parse_maven_error

print("--- Testing parse_maven_error function ---")
sample_error_output = r"""Picked up JAVA_TOOL_OPTIONS: --enable-native-access=ALL-UNNAMED
WARNING: A terminally deprecated method in sun.misc.Unsafe has been called
WARNING: sun.misc.Unsafe::objectFieldOffset has been called by com.google.common.util.concurrent.AbstractFuture$UnsafeAtomicHelper (file:/C:/Program%20Files/apache-maven-3.9.9/lib/guava-33.2.1-jre.jar)
WARNING: Please consider reporting this to the maintainers of class com.google.common.util.concurrent.AbstractFuture$UnsafeAtomicHelper
WARNING: sun.misc.Unsafe::objectFieldOffset will be removed in a future release
[INFO] Scanning for projects...
[INFO] 
[INFO] -----------------------< com.example:project-b >------------------------
[INFO] Building Project B 1.0-SNAPSHOT
[INFO]   from pom.xml
[INFO] --------------------------------[ jar ]---------------------------------
[INFO] 
[INFO] --- clean:3.2.0:clean (default-clean) @ project-b ---
[INFO] Deleting C:\Users\keanu\OneDrive\Desktop\Bachelor Thesis\Testcase Adaptation LLM\dummy_java_projects\ProjectB\target
[INFO] 
[INFO] --- resources:3.3.1:resources (default-resources) @ project-b ---
[INFO] skip non existing resourceDirectory C:\Users\keanu\OneDrive\Desktop\Bachelor Thesis\Testcase Adaptation LLM\dummy_java_projects\ProjectB\src\main\resources
[INFO]
[INFO] --- compiler:3.13.0:compile (default-compile) @ project-b ---
[INFO] Recompiling the module because of changed source code.
[INFO] Compiling 1 source file with javac [debug target 1.8] to target\classes
[WARNING] bootstrap class path is not set in conjunction with -source 8
  not setting the bootstrap class path may lead to class files that cannot run on JDK 8
    --release 8 is recommended instead of -source 8 -target 1.8 because it sets the bootstrap class path automatically
[WARNING] source value 8 is obsolete and will be removed in a future release
[WARNING] target value 8 is obsolete and will be removed in a future release
[WARNING] To suppress warnings about obsolete options, use -Xlint:-options.
[INFO]
[INFO] --- resources:3.3.1:testResources (default-testResources) @ project-b ---
[INFO] skip non existing resourceDirectory C:\Users\keanu\OneDrive\Desktop\Bachelor Thesis\Testcase Adaptation LLM\dummy_java_projects\ProjectB\src\test\resources
[INFO]
[INFO] --- compiler:3.13.0:testCompile (default-testCompile) @ project-b ---
[INFO] Recompiling the module because of changed dependency.
[INFO] Compiling 1 source file with javac [debug target 1.8] to target\test-classes
[INFO] -------------------------------------------------------------
[WARNING] COMPILATION WARNING :
[INFO] -------------------------------------------------------------
[WARNING] bootstrap class path is not set in conjunction with -source 8
  not setting the bootstrap class path may lead to class files that cannot run on JDK 8
    --release 8 is recommended instead of -source 8 -target 1.8 because it sets the bootstrap class path automatically
[WARNING] source value 8 is obsolete and will be removed in a future release
[WARNING] target value 8 is obsolete and will be removed in a future release
[WARNING] To suppress warnings about obsolete options, use -Xlint:-options.
[INFO] 4 warnings
[INFO] -------------------------------------------------------------
[INFO] -------------------------------------------------------------
[ERROR] COMPILATION ERROR :
[INFO] -------------------------------------------------------------
[ERROR] /C:/Users/keanu/OneDrive/Desktop/Bachelor Thesis/Testcase Adaptation LLM/dummy_java_projects/ProjectB/src/test/java/com/example/CalculatorTest.java:[11,35] cannot find symbol
  symbol:   method add(int,int)
  location: variable calculator of type com.example.Calculator
[ERROR] /C:/Users/keanu/OneDrive/Desktop/Bachelor Thesis/Testcase Adaptation LLM/dummy_java_projects/ProjectB/src/test/java/com/example/CalculatorTest.java:[17,36] cannot find symbol
  symbol:   method add(int,int)
  location: variable calculator of type com.example.Calculator
[INFO] 2 errors
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  1.347 s
[INFO] Finished at: 2025-05-30T17:41:34+02:00
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.13.0:testCompile (default-testCompile) on project project-b: Compilation failure: Compilation failure:
[ERROR] /C:/Users/keanu/OneDrive/Desktop/Bachelor Thesis/Testcase Adaptation LLM/dummy_java_projects/ProjectB/src/test/java/com/example/CalculatorTest.java:[11,35] cannot find symbol
[ERROR]   symbol:   method add(int,int)
[ERROR]   location: variable calculator of type com.example.Calculator
[ERROR] /C:/Users/keanu/OneDrive/Desktop/Bachelor Thesis/Testcase Adaptation LLM/dummy_java_projects/ProjectB/src/test/java/com/example/CalculatorTest.java:[17,36] cannot find symbol
[ERROR]   symbol:   method add(int,int)
[ERROR]   location: variable calculator of type com.example.Calculator
[ERROR] -> [Help 1]
[ERROR]
[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.
[ERROR] Re-run Maven using the -X switch to enable full debug logging.
[ERROR]
[ERROR] For more information about the errors and possible solutions, please read the following articles:
[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/MojoFailureException"""
parsed_error = parse_maven_error(sample_error_output)
print("--- Parsed Maven Error ---")
print(parsed_error)