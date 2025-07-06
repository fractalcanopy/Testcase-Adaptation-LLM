import json
import re
import os  # noqa: F401
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class AdaptationResult:
    """Represents the result of a single test case adaptation attempt."""

    # Project information
    source_project: str
    source_test_path: str
    target_project: str
    target_uut_path: str

    # Build and adaptation results
    pre_build_success: bool
    final_build_success: bool
    total_attempts: int
    successful_attempt: Optional[int]  # Which attempt succeeded (1, 2, 3, etc.)

    # LLM classification (if available)
    clone_classification: Optional[str]  # Type-1, Type-2, Type-3, Type-4

    # Error and timing information
    initial_error_type: Optional[str]
    final_error_message: Optional[str]
    execution_time_seconds: Optional[float]

    # Additional metadata
    timestamp: str
    gemini_api_used: bool
    pom_fix_applied: bool

    # NEW: Additional useful metrics
    build_failed_initially: bool = False  # Did the first build attempt fail?
    llm_response_length: Optional[int] = None  # Length of LLM response for analysis


class MetricsTracker:
    """Tracks and analyzes performance metrics for the test adaptation tool."""

    def __init__(self, output_file: str = "adaptation_metrics.json"):
        self.results: List[AdaptationResult] = []
        self.output_file = output_file
        self.current_result: Optional[AdaptationResult] = None
        self.start_time: Optional[float] = None

    def start_tracking(
        self,
        source_project: str,
        source_test_path: str,
        target_project: str,
        target_uut_path: str,
    ) -> None:
        """Initialize tracking for a new adaptation attempt."""
        import time

        self.start_time = time.time()
        self.current_result = AdaptationResult(
            source_project=source_project,
            source_test_path=source_test_path,
            target_project=target_project,
            target_uut_path=target_uut_path,
            pre_build_success=False,
            final_build_success=False,
            total_attempts=0,
            successful_attempt=None,
            clone_classification=None,
            initial_error_type=None,
            final_error_message=None,
            execution_time_seconds=None,
            timestamp=datetime.now().isoformat(),
            gemini_api_used=False,
            pom_fix_applied=False,
            build_failed_initially=False,
            llm_response_length=None,
        )

    def record_pre_build_result(
        self, success: bool, pom_fix_applied: bool = False
    ) -> None:
        """Record the result of the pre-build check."""
        if self.current_result:
            self.current_result.pre_build_success = success
            self.current_result.pom_fix_applied = pom_fix_applied

    def record_adaptation_attempt(
        self, attempt_number: int, success: bool, error_message: Optional[str] = None
    ) -> None:
        """Record the result of an adaptation attempt."""
        if self.current_result:
            self.current_result.total_attempts = max(
                self.current_result.total_attempts, attempt_number
            )

            # Record if the first build attempt failed
            if attempt_number == 1 and not success:
                self.current_result.build_failed_initially = True

            if success and self.current_result.successful_attempt is None:
                self.current_result.successful_attempt = attempt_number
                self.current_result.final_build_success = True

            if not success and attempt_number == self.current_result.total_attempts:
                self.current_result.final_error_message = error_message

    def record_initial_error(self, error_type: str) -> None:
        """Record the type of initial error encountered."""
        if self.current_result:
            self.current_result.initial_error_type = error_type

    def record_llm_usage(self, llm_response: str) -> None:
        """Extract and record LLM classification from the response."""
        if self.current_result:
            self.current_result.gemini_api_used = True
            self.current_result.llm_response_length = (
                len(llm_response) if llm_response else 0
            )

            # Extract classification using regex
            classification = self.extract_classification(llm_response)
            if classification:
                self.current_result.clone_classification = classification

    def extract_classification(self, llm_response: str) -> Optional[str]:
        """Extract Type-1, Type-2, Type-3, or Type-4 classification from LLM response."""
        if not llm_response:
            return None

        # Look for patterns like "Type-1", "Type-2", etc.
        pattern = r"\b(Type-[1-4])\b"
        matches = re.findall(pattern, llm_response, re.IGNORECASE)

        if matches:
            # Return the first match, normalized to proper case
            return matches[0].capitalize()

        return None

    def finish_tracking(self) -> None:
        """Finalize the current tracking session."""
        if self.current_result and self.start_time:
            import time

            self.current_result.execution_time_seconds = time.time() - self.start_time
            self.results.append(self.current_result)
            self.current_result = None
            self.start_time = None

    def save_results(self) -> None:
        """Save all results to a JSON file."""
        try:
            # Convert dataclasses to dictionaries
            data = {
                "results": [asdict(result) for result in self.results],
                "summary": self.get_summary_stats(),
                "generated_at": datetime.now().isoformat(),
            }

            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"Metrics saved to: {self.output_file}")
        except Exception as e:
            print(f"Error saving metrics: {e}")

    def get_summary_stats(self) -> Dict[str, Any]:
        """Calculate and return summary statistics."""
        if not self.results:
            return {}

        total_adaptations = len(self.results)
        successful_adaptations = sum(1 for r in self.results if r.final_build_success)
        pre_build_failures = sum(1 for r in self.results if not r.pre_build_success)
        pom_fixes_applied = sum(1 for r in self.results if r.pom_fix_applied)
        initial_build_failures = sum(
            1 for r in self.results if r.build_failed_initially
        )
        llm_usage_count = sum(1 for r in self.results if r.gemini_api_used)

        # Classification distribution
        classifications = {}
        for result in self.results:
            if result.clone_classification:
                classifications[result.clone_classification] = (
                    classifications.get(result.clone_classification, 0) + 1
                )

        # Attempt distribution
        attempt_counts = {}
        for result in self.results:
            if result.successful_attempt:
                attempt_counts[result.successful_attempt] = (
                    attempt_counts.get(result.successful_attempt, 0) + 1
                )

        # Error type distribution
        error_types = {}
        for result in self.results:
            if result.initial_error_type:
                error_types[result.initial_error_type] = (
                    error_types.get(result.initial_error_type, 0) + 1
                )

        # Average execution time
        execution_times = [
            r.execution_time_seconds for r in self.results if r.execution_time_seconds
        ]
        avg_execution_time = (
            sum(execution_times) / len(execution_times) if execution_times else 0
        )

        return {
            "total_adaptations": total_adaptations,
            "successful_adaptations": successful_adaptations,
            "success_rate": successful_adaptations / total_adaptations
            if total_adaptations > 0
            else 0,
            "pre_build_failures": pre_build_failures,
            "pom_fixes_applied": pom_fixes_applied,
            "initial_build_failures": initial_build_failures,
            "llm_usage_count": llm_usage_count,
            "classification_distribution": classifications,
            "success_by_attempt": attempt_counts,
            "error_type_distribution": error_types,
            "average_execution_time_seconds": avg_execution_time,
            "max_execution_time_seconds": max(execution_times)
            if execution_times
            else 0,
            "min_execution_time_seconds": min(execution_times)
            if execution_times
            else 0,
        }

    def print_summary(self) -> None:
        """Print a summary of the current results."""
        stats = self.get_summary_stats()

        print("\n" + "=" * 50)
        print("ADAPTATION PERFORMANCE SUMMARY")
        print("=" * 50)

        if not stats:
            print("No adaptations tracked yet.")
            return

        print(f"Total adaptations: {stats['total_adaptations']}")
        print(f"Successful adaptations: {stats['successful_adaptations']}")
        print(f"Success rate: {stats['success_rate']:.2%}")
        print(f"Pre-build failures: {stats['pre_build_failures']}")
        print(f"Initial build failures: {stats['initial_build_failures']}")
        print(f"POM fixes applied: {stats['pom_fixes_applied']}")
        print(f"LLM usage count: {stats['llm_usage_count']}")

        if stats["classification_distribution"]:
            print(f"\nClone classification distribution:")  # noqa: F541
            for class_type, count in stats["classification_distribution"].items():
                print(f"  {class_type}: {count}")

        if stats["success_by_attempt"]:
            print(f"\nSuccess by attempt number:")  # noqa: F541
            for attempt, count in sorted(stats["success_by_attempt"].items()):
                print(f"  Attempt {attempt}: {count}")

        if stats["error_type_distribution"]:
            print(f"\nError type distribution:")  # noqa: F541
            for error_type, count in stats["error_type_distribution"].items():
                print(f"  {error_type}: {count}")

        print(f"\nTiming:")  # noqa: F541
        print(
            f"  Average execution time: {stats['average_execution_time_seconds']:.2f}s"
        )
        print(f"  Max execution time: {stats['max_execution_time_seconds']:.2f}s")
        print(f"  Min execution time: {stats['min_execution_time_seconds']:.2f}s")

        print("=" * 50)


# Global instance for easy access
global_metrics = MetricsTracker()
