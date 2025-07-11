#!/usr/bin/env python3
"""
Standalone Maven POM Maintenance Script

This script recursively scans for pom.xml files, removes problematic com.sun.tools dependencies,
and updates Maven plugin versions to their latest releases.

Usage:
    python pom_maintenance.py [root_directory]

If no directory is provided, uses current working directory.
"""

import xml.etree.ElementTree as ET
import subprocess
import logging
import os
import glob
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("pom_maintenance.log")],
)
logger = logging.getLogger(__name__)


class POMMaintenanceProcessor:
    """Handles POM file maintenance operations."""

    def __init__(self, root_directory: str):
        self.root_directory = Path(root_directory).resolve()
        self.processed_poms: List[str] = []
        self.modified_poms: List[str] = []
        self.failed_poms: List[str] = []
        self.updated_plugins: Dict[str, List[str]] = {}

    def find_pom_files(self) -> List[Path]:
        """Recursively find all pom.xml files in the root directory."""
        pom_files = []

        logger.info(f"Scanning for pom.xml files in: {self.root_directory}")

        # Use glob to find all pom.xml files recursively
        pattern = str(self.root_directory / "**" / "pom.xml")
        for pom_path in glob.glob(pattern, recursive=True):
            pom_files.append(Path(pom_path))

        logger.info(f"Found {len(pom_files)} pom.xml files")
        return pom_files

    def parse_pom(self, pom_path: Path) -> Optional[Tuple[ET.ElementTree, ET.Element]]:
        """Parse a POM file and return the tree and root element."""
        try:
            tree = ET.parse(pom_path)
            root = tree.getroot()

            # Register the Maven namespace if present
            if root.tag.startswith("{"):
                namespace = root.tag.split("}")[0] + "}"
                ET.register_namespace("", namespace[1:-1])

            return tree, root
        except ET.ParseError as e:
            logger.error(f"Failed to parse {pom_path}: {e}")
            self.failed_poms.append(str(pom_path))
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing {pom_path}: {e}")
            self.failed_poms.append(str(pom_path))
            return None

    def get_namespace(self, root: ET.Element) -> str:
        """Extract the Maven namespace from the root element."""
        if root.tag.startswith("{"):
            return root.tag.split("}")[0] + "}"
        return ""

    def remove_problematic_dependencies(self, root: ET.Element, namespace: str) -> bool:
        """Remove com.sun.tools dependencies from the POM."""
        modified = False

        # Find all dependencies elements (both in main dependencies and dependencyManagement)
        dependencies_elements = root.findall(f".//{namespace}dependencies")

        for dependencies in dependencies_elements:
            dependencies_to_remove = []

            for dependency in dependencies.findall(f"{namespace}dependency"):
                group_id_elem = dependency.find(f"{namespace}groupId")
                artifact_id_elem = dependency.find(f"{namespace}artifactId")

                if group_id_elem is not None and artifact_id_elem is not None:
                    group_id = group_id_elem.text
                    artifact_id = artifact_id_elem.text

                    # Remove any com.sun:tools dependency regardless of scope
                    # Also check for variations like com.sun.tools
                    if (group_id == "com.sun" and artifact_id == "tools") or (
                        group_id == "com.sun.tools"
                    ):
                        scope_elem = dependency.find(f"{namespace}scope")
                        scope = scope_elem.text if scope_elem is not None else "compile"

                        logger.info(
                            f"Removing problematic dependency: {group_id}:{artifact_id} (scope: {scope})"
                        )
                        dependencies_to_remove.append(dependency)
                        modified = True

            # Remove the problematic dependencies
            for dependency in dependencies_to_remove:
                dependencies.remove(dependency)

        return modified

    def add_java_compiler_profile(self, root: ET.Element, namespace: str) -> bool:
        """Add a profile to handle Java version compatibility issues."""
        # Check if profiles section exists
        profiles_elem = root.find(f"{namespace}profiles")
        if profiles_elem is None:
            profiles_elem = ET.SubElement(root, f"{namespace}profiles")

        # Check if java-version profile already exists
        for profile in profiles_elem.findall(f"{namespace}profile"):
            id_elem = profile.find(f"{namespace}id")
            if id_elem is not None and id_elem.text == "java-version-compatibility":
                return False  # Profile already exists

        # Create new profile for Java version compatibility
        profile = ET.SubElement(profiles_elem, f"{namespace}profile")

        profile_id = ET.SubElement(profile, f"{namespace}id")
        profile_id.text = "java-version-compatibility"

        activation = ET.SubElement(profile, f"{namespace}activation")
        jdk = ET.SubElement(activation, f"{namespace}jdk")
        jdk.text = "[11,)"  # Activate for Java 11 and above

        properties = ET.SubElement(profile, f"{namespace}properties")

        # Set compiler properties for modern Java versions
        source_prop = ET.SubElement(properties, f"{namespace}maven.compiler.source")
        source_prop.text = "11"

        target_prop = ET.SubElement(properties, f"{namespace}maven.compiler.target")
        target_prop.text = "11"

        release_prop = ET.SubElement(properties, f"{namespace}maven.compiler.release")
        release_prop.text = "11"

        logger.info("Added Java version compatibility profile")
        return True

    def write_pom(self, tree: ET.ElementTree, pom_path: Path) -> bool:
        """Write the modified POM back to file."""
        try:
            # Write with XML declaration and proper formatting
            tree.write(pom_path, encoding="utf-8", xml_declaration=True, method="xml")
            return True
        except Exception as e:
            logger.error(f"Failed to write {pom_path}: {e}")
            return False

    def run_maven_versions_update(self, pom_directory: Path) -> Tuple[bool, List[str]]:
        """Run Maven versions plugin to update plugin versions."""
        updated_plugins = []

        try:
            # Change to the POM directory
            original_cwd = os.getcwd()
            os.chdir(pom_directory)

            # Run the Maven versions plugin command
            cmd = [
                "mvn",
                "versions:use-latest-versions",
                "-Dincludes=org.apache.maven.plugins:*",
                "-DgenerateBackupPoms=false",
                "-q",  # Quiet output
            ]

            logger.info(f"Running Maven versions update in: {pom_directory}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode == 0:
                # Parse output to extract updated plugins
                output_lines = result.stdout.split("\n")
                for line in output_lines:
                    if "Updated" in line and "org.apache.maven.plugins" in line:
                        # Extract plugin information from Maven output
                        if "->" in line:
                            plugin_info = line.strip()
                            updated_plugins.append(plugin_info)

                logger.info(f"Successfully updated plugins in {pom_directory}")
                return True, updated_plugins
            else:
                logger.warning(
                    f"Maven versions update failed in {pom_directory}: {result.stderr}"
                )
                return False, []

        except subprocess.TimeoutExpired:
            logger.error(f"Maven versions update timed out in {pom_directory}")
            return False, []
        except Exception as e:
            logger.error(f"Error running Maven versions update in {pom_directory}: {e}")
            return False, []
        finally:
            # Restore original working directory
            os.chdir(original_cwd)

    def check_for_tools_jar_usage(self, pom_path: Path) -> bool:
        """Check if the POM content mentions tools.jar anywhere."""
        try:
            with open(pom_path, "r", encoding="utf-8") as f:
                content = f.read()
                return "tools.jar" in content.lower()
        except Exception:
            return False

    def process_pom_file(self, pom_path: Path) -> None:
        """Process a single POM file."""
        logger.info(f"Processing: {pom_path}")
        self.processed_poms.append(str(pom_path))

        # Check if this POM mentions tools.jar
        has_tools_jar = self.check_for_tools_jar_usage(pom_path)
        if has_tools_jar:
            logger.info(f"Found tools.jar reference in {pom_path}")

        # Parse the POM
        parse_result = self.parse_pom(pom_path)
        if parse_result is None:
            return

        tree, root = parse_result
        namespace = self.get_namespace(root)

        # Remove problematic dependencies
        pom_modified = self.remove_problematic_dependencies(root, namespace)

        # Add Java compatibility profile if tools.jar was found
        if has_tools_jar:
            profile_added = self.add_java_compiler_profile(root, namespace)
            pom_modified = pom_modified or profile_added

        # Write back if modified
        if pom_modified:
            if self.write_pom(tree, pom_path):
                self.modified_poms.append(str(pom_path))
                logger.info(f"Modified POM saved: {pom_path}")
            else:
                logger.error(f"Failed to save modified POM: {pom_path}")
                return

        # Run Maven versions update
        pom_directory = pom_path.parent
        success, updated_plugins = self.run_maven_versions_update(pom_directory)

        if success and updated_plugins:
            self.updated_plugins[str(pom_path)] = updated_plugins
            logger.info(f"Updated {len(updated_plugins)} plugins in {pom_path}")

    def run_dependency_tree_analysis(self) -> None:
        """Run Maven dependency tree to identify problematic dependencies."""
        try:
            logger.info("Running Maven dependency tree analysis...")
            original_cwd = os.getcwd()
            os.chdir(self.root_directory)

            cmd = [
                "mvn",
                "dependency:tree",
                "-Dverbose=true",
                "-DoutputFile=dependency-tree.txt",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                logger.info(
                    "Dependency tree analysis completed. Check dependency-tree.txt for details."
                )
            else:
                logger.warning(f"Dependency tree analysis failed: {result.stderr}")

        except Exception as e:
            logger.error(f"Error running dependency tree analysis: {e}")
        finally:
            os.chdir(original_cwd)

    def process_all_poms(self) -> None:
        """Process all POM files in the root directory."""
        pom_files = self.find_pom_files()

        if not pom_files:
            logger.warning("No pom.xml files found")
            return

        logger.info(f"Starting processing of {len(pom_files)} POM files")

        for pom_path in pom_files:
            try:
                self.process_pom_file(pom_path)
            except Exception as e:
                logger.error(f"Unexpected error processing {pom_path}: {e}")
                self.failed_poms.append(str(pom_path))

        # Run dependency tree analysis to help diagnose issues
        self.run_dependency_tree_analysis()

        self.print_summary()

    def print_summary(self) -> None:
        """Print a summary of the processing results."""
        print("\n" + "=" * 80)
        print("POM MAINTENANCE SUMMARY")
        print("=" * 80)

        print(f"Total POMs processed: {len(self.processed_poms)}")
        print(f"POMs with dependency changes: {len(self.modified_poms)}")
        print(f"POMs with plugin updates: {len(self.updated_plugins)}")
        print(f"Failed POMs: {len(self.failed_poms)}")

        if self.modified_poms:
            print("\n--- POMs with removed com.sun.tools dependencies ---")
            for pom_path in self.modified_poms:
                print(f"  • {pom_path}")

        if self.updated_plugins:
            print("\n--- Plugin Updates ---")
            for pom_path, plugins in self.updated_plugins.items():
                print(f"  {pom_path}:")
                for plugin in plugins:
                    print(f"    • {plugin}")

        if self.failed_poms:
            print("\n--- Failed POMs ---")
            for pom_path in self.failed_poms:
                print(f"  • {pom_path}")

        print("\n--- Next Steps ---")
        print("1. Check 'pom_maintenance.log' for detailed processing logs")
        print("2. Review 'dependency-tree.txt' for dependency analysis")
        print("3. Try building with: mvn clean compile -X")
        print("4. Consider using Java 8 if tools.jar dependencies persist")
        print("=" * 80)


def check_maven_availability() -> bool:
    """Check if Maven is available in the system PATH."""
    try:
        result = subprocess.run(
            ["mvn", "--version"], capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def find_tools_jar_references(root_directory: str) -> None:
    """Search for any direct references to tools.jar in POM files."""
    logger.info("Searching for tools.jar references in POM files...")

    pattern = str(Path(root_directory) / "**" / "pom.xml")
    tools_jar_files = []

    for pom_path in glob.glob(pattern, recursive=True):
        try:
            with open(pom_path, "r", encoding="utf-8") as f:
                content = f.read()
                if "tools.jar" in content.lower():
                    tools_jar_files.append(pom_path)
                    logger.info(f"Found tools.jar reference in: {pom_path}")
        except Exception as e:
            logger.warning(f"Could not read {pom_path}: {e}")

    if tools_jar_files:
        print(f"\n--- Found tools.jar references in {len(tools_jar_files)} files ---")
        for file_path in tools_jar_files:
            print(f"  • {file_path}")
    else:
        print("\n--- No direct tools.jar references found in POM files ---")


def main():
    """Main entry point."""
    # Check if Maven is available
    if not check_maven_availability():
        logger.error(
            "Maven (mvn) is not available in PATH. Please install Maven first."
        )
        sys.exit(1)

    # Get root directory from command line argument or use current directory
    if len(sys.argv) > 1:
        root_directory = sys.argv[1]
    else:
        root_directory = os.getcwd()

    # Validate root directory
    if not os.path.isdir(root_directory):
        logger.error(f"Directory does not exist: {root_directory}")
        sys.exit(1)

    logger.info(f"Starting POM maintenance for directory: {root_directory}")

    # First, search for tools.jar references
    find_tools_jar_references(root_directory)

    # Create processor and run
    processor = POMMaintenanceProcessor(root_directory)
    processor.process_all_poms()

    logger.info("POM maintenance completed")


if __name__ == "__main__":
    main()
