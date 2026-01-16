"""Unified documentation update script for Python, TypeScript, and JavaScript projects.

This script automatically detects the project type and runs appropriate documentation
update operations including file structure, file lists, tests, API documentation,
code maps, health checks, and session archiving.

Supported project types:
- Python: Uses pdoc for API docs, codedocs_python.py for code maps
- TypeScript: Uses TypeDoc for API docs, codedocs_typescript.js for code maps
- JavaScript: Uses JSDoc for API docs, codedocs_javascript.js for code maps

Auto-detection uses detect_project_languages() from wsd_utils for consistent
language detection across all WSD tools. Override with --project-type flag if needed.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, TypedDict

# Add scripts directory to path for wsd_utils import
_scripts_dir = Path(__file__).parent
sys.path.insert(0, str(_scripts_dir))

from wsd_utils import (  # noqa: E402
    detect_package_manager,
    detect_project_languages,
    get_check_dirs,
    get_node_check_dirs,
    is_script_available,
)

# Language Configuration Registry
# Maps language identifiers to their configuration for documentation generation.
# This registry-based design enables iteration over all detected languages and
# makes adding new language support straightforward (per Design Decision 10).
LANGUAGE_CONFIG: dict[str, dict[str, Any]] = {
    "python": {
        "display_name": "Python",
        "code_patterns": "*.py",
        "test_patterns": "test_*.py,*_test.py",
        "get_source_dirs": get_check_dirs,
        "coverage_dir": "coverage-python",
        "coverage_report": "Python-Coverage-Report.md",
        "test_runner": "run_python_tests",
        "api_doc_generator": "generate_python_api_docs",
        "code_map_generator": "generate_python_code_map",
        "health_check_runner": "run_python_health_check",
    },
    "typescript": {
        "display_name": "TypeScript",
        "code_patterns": "*.ts,*.tsx",
        "test_patterns": "*.test.ts,*.spec.ts",
        "get_source_dirs": get_node_check_dirs,
        "coverage_dir": "coverage-node",
        "coverage_report": "TypeScript-Coverage-Report.md",
        "test_runner": "run_node_tests",
        "api_doc_generator": "generate_node_api_docs",
        "code_map_generator": "generate_node_code_map",
        "health_check_runner": "run_node_health_check",
    },
    "javascript": {
        "display_name": "Javascript",
        "code_patterns": "*.js,*.jsx",
        "test_patterns": "*.test.js,*.spec.js",
        "get_source_dirs": get_node_check_dirs,
        "coverage_dir": "coverage-node",
        "coverage_report": "Javascript-Coverage-Report.md",
        "test_runner": "run_node_tests",
        "api_doc_generator": "generate_node_api_docs",
        "code_map_generator": "generate_node_code_map",
        "health_check_runner": "run_node_health_check",
    },
}


def _get_language_function(language: str, function_key: str) -> Any:
    """Get a function reference from the language configuration registry.

    Dispatches to the appropriate function name based on language and function type.
    This helper enables registry-based lookups for language-specific operations.

    Args:
        language: Language identifier (e.g., "python", "typescript", "javascript")
        function_key: Configuration key for the function (e.g., "test_runner",
            "api_doc_generator", "code_map_generator")

    Returns:
        Configuration value if language and key exist in registry, None otherwise.
        Return type varies by key: str for function names, callable for get_source_dirs.

    Raises:
        KeyError: If function_key is not a valid configuration key for the language.
    """
    if language not in LANGUAGE_CONFIG:
        return None
    config = LANGUAGE_CONFIG[language]
    if function_key not in config:
        raise KeyError(
            f"Invalid function_key '{function_key}' for language '{language}'. "
            f"Valid keys: {list(config.keys())}"
        )
    return config[function_key]


def validate_python_config() -> list[str]:
    """Validate Python project configuration in pyproject.toml.

    Checks for required [tool.wsd] configuration section and validates
    the check_dirs field. Exits with helpful error message if configuration
    is missing or invalid.

    Returns:
        List of configured check directories.

    Raises:
        SystemExit: If pyproject.toml is missing, [tool.wsd] section is missing,
            or check_dirs is not a list.
    """
    # Import tomllib conditionally for Python 3.10 compatibility
    try:
        import tomllib  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        import tomli as tomllib

    project_root = Path(__file__).resolve().parent.parent
    pyproject_path = project_root / "pyproject.toml"

    # Check for pyproject.toml existence
    if not pyproject_path.exists():
        print("ERROR: pyproject.toml not found in project root.")
        print("Workscope-Dev requires pyproject.toml with [tool.wsd] configuration.")
        sys.exit(1)

    # Parse pyproject.toml
    try:
        with pyproject_path.open("rb") as f:
            config = tomllib.load(f)
    except Exception as e:
        print(f"ERROR: Failed to parse pyproject.toml: {e}")
        sys.exit(1)

    # Check for [tool.wsd] section
    wsd_config = config.get("tool", {}).get("wsd", {})
    check_dirs = wsd_config.get("check_dirs")

    if check_dirs is None:
        print("ERROR: [tool.wsd] configuration missing or incomplete in pyproject.toml.")
        print("Add this to your pyproject.toml:")
        print()
        print("[tool.wsd]")
        print('check_dirs = ["src", "tests"]')
        sys.exit(1)

    # Validate check_dirs is a list
    if not isinstance(check_dirs, list):
        print("ERROR: check_dirs must be a list in pyproject.toml")
        sys.exit(1)

    return [str(d) for d in check_dirs if isinstance(d, str)]


# Define project root based on the script's location
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "docs" / "reports"
DEV_REPORTS_DIR = PROJECT_ROOT / "dev" / "reports"

# Detect project languages and package manager for Node.js projects
PROJECT_LANGUAGES = detect_project_languages()
PKG_MANAGER = (
    detect_package_manager()
    if ("typescript" in PROJECT_LANGUAGES or "javascript" in PROJECT_LANGUAGES)
    else None
)


class TestCommandConfig(TypedDict):
    """Configuration for a test command."""

    cmd: list[str]
    log_file: Path


def run_command(
    cmd: list[str],
    capture_output: bool = False,
    cwd: Path = PROJECT_ROOT,
    env: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    """Run a command and return its results.

    Args:
        cmd: Command and arguments to run
        capture_output: Whether to capture command output
        cwd: Working directory for the command
        env: Optional environment variables

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            cwd=cwd,
            env=env,
            check=False,
        )
        return (
            result.returncode,
            result.stdout if result.stdout else "",
            result.stderr if result.stderr else "",
        )
    except Exception as e:
        print(f"Error running command {' '.join(cmd)}: {e}")
        return (-1, "", str(e))


def update_file_structure() -> bool:
    """Update the project file structure documentation using the tree command.

    Returns:
        True if successful, False otherwise
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    print("\nUpdating project file structure (using tree command)...")

    # Comprehensive exclusion list for both Python and TypeScript projects
    tree_command = [
        "tree",
        "-a",
        "--gitignore",
        "--prune",
        "-I",
        (
            "node_modules|.git|.vscode|.idea|__pycache__|*.pyc|.DS_Store|"
            "dist|build|*.egg-info|.env|.pytest_cache|.mypy_cache|target|venv|.venv|"
            ".ruff_cache|.coverage|htmlcov|.tox|.nox|"
            ".claude|dev|archive|demos"
        ),
    ]
    returncode, stdout, stderr = run_command(tree_command, capture_output=True)

    report_file = REPORTS_DIR / "Project-File-Structure.md"
    if returncode == 0:
        with report_file.open("w", encoding="utf-8") as f:
            f.write("```\n")
            f.write(stdout)
            f.write("\n```\n")
        print(f"File structure report updated: {report_file.relative_to(PROJECT_ROOT)}")
        return True
    error_message = (
        f"Error running tree command (Code: {returncode}):\n{stderr}\nSTDOUT (if any):\n{stdout}"
    )
    print(error_message)
    with report_file.open("w", encoding="utf-8") as f:
        f.write(f"# Error Generating File Structure\n\n{error_message}")
    return False


def get_file_list_configs(languages: set[str]) -> list[dict[str, Any]]:
    """Return file list configurations for all detected languages.

    Uses the LANGUAGE_CONFIG registry to dynamically generate language-specific
    configurations for code file lists. Documentation-related configurations
    use standard WSD documentation paths and are language-agnostic.

    Args:
        languages: Set of detected project languages (e.g., {"python", "javascript"})

    Returns:
        List of configuration dictionaries for file_list.py
    """
    configs: list[dict[str, Any]] = []

    # Generate language-specific code file configs for each detected language
    for language in sorted(languages):
        if language not in LANGUAGE_CONFIG:
            continue

        lang_config = LANGUAGE_CONFIG[language]
        display_name = lang_config["display_name"]
        code_patterns = lang_config["code_patterns"]
        test_patterns = lang_config["test_patterns"]
        get_dirs_func = lang_config["get_source_dirs"]
        source_dirs = get_dirs_func()

        # Determine exclude patterns based on language
        core_exclude = "__pycache__" if language == "python" else "node_modules"
        test_exclude = "__pycache__,conftest.py" if language == "python" else None

        # All Source Code Files for this language
        configs.append(
            {
                "title": f"{display_name} All Source Code Files",
                "folders": source_dirs,
                "output_file": f"{display_name}-All-Code-Files.md",
                "include_patterns": code_patterns,
                "exclude_patterns": None,
            }
        )

        # Core Source Code Files for this language (excludes test directories)
        core_dirs = [d for d in source_dirs if "test" not in d.lower()]
        configs.append(
            {
                "title": f"{display_name} Core Source Code Files",
                "folders": core_dirs,
                "output_file": f"{display_name}-Core-Code-Files.md",
                "include_patterns": code_patterns,
                "exclude_patterns": core_exclude,
            }
        )

        # Test Files for this language
        test_dirs = [d for d in source_dirs if "test" in d.lower()]
        configs.append(
            {
                "title": f"{display_name} Test Files",
                "folders": test_dirs,
                "output_file": f"{display_name}-Test-Files.md",
                "include_patterns": test_patterns,
                "exclude_patterns": test_exclude,
            }
        )

    # Language-agnostic documentation configs (shared across all languages)
    doc_configs: list[dict[str, Any]] = [
        {
            "title": "Project Documentation",
            "folders": ["docs"],
            "output_file": "Project-Documentation.md",
            "include_patterns": "*.md,*.rst",
            "exclude_patterns": "archive,reports,read-only",
        },
        {
            "title": "Core Documentation",
            "folders": ["docs/core", "docs/features"],
            "output_file": "Core-Documentation.md",
            "include_patterns": "*.md",
            "exclude_patterns": None,
        },
        {
            "title": "Project Tickets",
            "folders": ["docs/tickets"],
            "output_file": "Project-Tickets.md",
            "include_patterns": "*.md",
            "exclude_patterns": None,
        },
    ]

    configs.extend(doc_configs)
    return configs


def _build_file_list_command(file_list_script: Path, config: dict[str, Any]) -> list[str]:
    """Build command for file_list.py script with all arguments.

    Args:
        file_list_script: Path to the file_list.py script
        config: Configuration dictionary with title, folders, output_file, and optional patterns

    Returns:
        Complete command list ready for execution
    """
    cmd = ["python", str(file_list_script)]
    cmd.extend(["-h", config["title"]])

    folder_paths_str = ",".join([str(PROJECT_ROOT / f) for f in config["folders"]])
    cmd.extend(["-d", folder_paths_str])

    output_path = REPORTS_DIR / config["output_file"]
    cmd.extend(["-o", str(output_path)])

    if config["include_patterns"]:
        cmd.extend(["-i", config["include_patterns"]])
    if config["exclude_patterns"]:
        cmd.extend(["-e", config["exclude_patterns"]])

    return cmd


def _print_file_list_result(
    config: dict[str, Any], returncode: int, stdout: str, stderr: str
) -> bool:
    """Print results from file list generation command.

    Args:
        config: Configuration dictionary with title and output_file
        returncode: Command return code
        stdout: Command stdout output
        stderr: Command stderr output

    Returns:
        True if command succeeded, False otherwise
    """
    output_path = REPORTS_DIR / config["output_file"]

    if returncode == 0:
        print(f"    Successfully generated: {output_path.relative_to(PROJECT_ROOT)}")
        if stdout:
            for line in stdout.strip().split("\n"):
                print(f"      {line}")
        return True

    print(f"    ERROR generating: {output_path.relative_to(PROJECT_ROOT)}")
    if stdout:
        print(f"      STDOUT:\n{stdout}")
    if stderr:
        print(f"      STDERR:\n{stderr}")
    return False


def update_file_lists(languages: set[str]) -> bool:
    """Update various file list reports using file_list.py script.

    Args:
        languages: Set of detected project languages (e.g., {"python", "javascript"})

    Returns:
        True if all reports generated successfully, False otherwise
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    print("\nUpdating specific file list reports using file_list.py...")

    file_list_script = PROJECT_ROOT / "scripts" / "file_list.py"
    if not file_list_script.exists():
        print(f"Warning: file_list.py script not found at {file_list_script}")
        return False

    configurations = get_file_list_configs(languages)
    if not configurations:
        print(f"Warning: No file list configurations for languages: {languages}")
        return True

    all_succeeded = True
    for config in configurations:
        cmd = _build_file_list_command(file_list_script, config)

        output_path = REPORTS_DIR / config["output_file"]
        print(f"  Generating: {config['title']} -> {output_path.relative_to(PROJECT_ROOT)}")

        returncode, stdout, stderr = run_command(cmd, capture_output=True, cwd=PROJECT_ROOT)

        if not _print_file_list_result(config, returncode, stdout, stderr):
            all_succeeded = False

        print("-" * 20)

    if all_succeeded:
        print("All specific file list reports generated successfully.")
    else:
        print("Some specific file list reports failed to generate. Please check errors above.")
    return all_succeeded


def _parse_pytest_output(stdout: str) -> dict[str, Any]:
    """Parse pytest output to extract test counts and failure details.

    Args:
        stdout: Standard output from pytest execution

    Returns:
        Dictionary containing:
        - passed: Number of passed tests
        - failed: Number of failed tests
        - total: Total number of tests
        - duration: Test execution duration string
        - failures: List of (test_name, reason) tuples for failed tests
    """
    result: dict[str, Any] = {
        "passed": 0,
        "failed": 0,
        "total": 0,
        "duration": "",
        "failures": [],
    }

    # Extract test results from pytest summary line
    # Format: "=== 140 passed in 0.23s ===" or "=== 5 failed, 135 passed in 0.23s ==="
    summary_match = re.search(
        r"=+\s*(?:(\d+)\s*failed,?\s*)?(?:(\d+)\s*passed).*?in\s*([\d.]+s)\s*=+",
        stdout,
    )
    if summary_match:
        result["failed"] = int(summary_match.group(1) or 0)
        result["passed"] = int(summary_match.group(2) or 0)
        result["total"] = result["passed"] + result["failed"]
        result["duration"] = summary_match.group(3) or ""

    # Extract failed tests
    if "FAILED" in stdout:
        failed_tests = re.findall(r"FAILED (.+?) - (.+)", stdout)
        for test, reason in failed_tests:
            result["failures"].append((test, reason))

    return result


class MergedTestInput(TypedDict, total=False):
    """Input data for merged test summary generation."""

    python: "PythonTestResult"
    node: "NodeTestResult"


class HealthCheckMergeInput(TypedDict, total=False):
    """Input data for merged health check summary generation.

    Aggregates health check results from multiple language-specific health check
    runners for unified summary generation. Keys are optional since a project may
    have only Python, only Node.js, or both.

    Attributes:
        python: Results from Python health check execution via health_check.py.
            Contains success status, stdout/stderr, return code, and report file path.
        node: Results from Node.js health check execution via health_check.js.
            Contains success status, stdout/stderr, return code, and report file path.
    """

    python: "PythonHealthCheckResult"
    node: "NodeHealthCheckResult"


def _generate_merged_test_summary(
    summary_file: Path,
    test_results: MergedTestInput,
) -> None:
    """Generate unified Test-Summary.md combining results from all language test runners.

    Creates a single Test-Summary.md file with per-language sections, combining test
    results from Python (pytest) and/or Node.js (Jest/Playwright) test runners.

    Args:
        summary_file: Path where summary markdown file should be written
        test_results: Dictionary mapping language keys to their test result data.
            Keys are "python" and/or "node". Values are PythonTestResult or
            NodeTestResult TypedDicts containing stdout, log file paths, etc.
    """
    with summary_file.open("w") as f:
        f.write("# Test Summary Report\n\n")
        timestamp = subprocess.run(
            ["date"], check=False, capture_output=True, text=True
        ).stdout.strip()
        f.write(f"**Generated at:** {timestamp}\n\n")

        # Aggregate statistics
        total_passed = 0
        total_failed = 0
        all_failures: list[tuple[str, str, str]] = []  # (language, test, reason)

        # Python section
        if "python" in test_results:
            python_result = test_results["python"]
            pytest_data = _parse_pytest_output(python_result["stdout"])

            f.write("## Python Tests (pytest)\n\n")
            f.write(f"- **Passed:** {pytest_data['passed']}\n")
            f.write(f"- **Failed:** {pytest_data['failed']}\n")
            f.write(f"- **Total:** {pytest_data['total']}\n")
            if pytest_data["duration"]:
                f.write(f"- **Duration:** {pytest_data['duration']}\n")
            f.write("\n")

            total_passed += pytest_data["passed"]
            total_failed += pytest_data["failed"]

            for test, reason in pytest_data["failures"]:
                all_failures.append(("Python", test, reason))

            raw_log = python_result["raw_log_file"]
            f.write(f"Raw output: [{raw_log.name}](../../{raw_log.relative_to(PROJECT_ROOT)})\n\n")

        # Node.js section
        if "node" in test_results:
            node_result = test_results["node"]
            jest_data = _parse_jest_output(node_result["jest_stdout"])
            playwright_data = _parse_playwright_output(node_result["playwright_stdout"])

            # Determine language name from coverage report filename
            coverage_name = node_result["coverage_report_file"].stem
            if coverage_name.startswith("TypeScript"):
                lang_name = "TypeScript"
            elif coverage_name.startswith("Javascript"):
                lang_name = "JavaScript"
            else:
                lang_name = "Node.js"

            f.write(f"## {lang_name} Tests\n\n")

            # Jest subsection
            f.write("### Jest (Unit Tests)\n\n")
            if node_result["jest_skipped"]:
                f.write("**Status:** SKIPPED (test script not configured)\n")
            elif jest_data["total"] > 0:
                f.write(f"- **Test Suites:** {jest_data['suites_passed']} passed, ")
                f.write(f"{jest_data['suites_failed']} failed, {jest_data['suites_total']} total\n")
                f.write(f"- **Tests:** {jest_data['passed']} passed, ")
                f.write(f"{jest_data['failed']} failed, {jest_data['total']} total\n")
                if jest_data["duration"]:
                    f.write(f"- **Duration:** {jest_data['duration']}\n")
            else:
                f.write("No Jest test results found.\n")
            f.write("\n")

            # Playwright subsection
            f.write("### Playwright (E2E Tests)\n\n")
            if node_result["playwright_skipped"]:
                f.write("**Status:** SKIPPED (test:e2e script not configured)\n")
            elif playwright_data["total"] > 0:
                f.write(f"- **Tests:** {playwright_data['passed']} passed, ")
                f.write(f"{playwright_data['failed']} failed, {playwright_data['total']} total\n")
                if playwright_data["duration"]:
                    f.write(f"- **Duration:** {playwright_data['duration']}\n")
            else:
                f.write("No Playwright test results found.\n")
            f.write("\n")

            total_passed += jest_data["passed"] + playwright_data["passed"]
            total_failed += jest_data["failed"] + playwright_data["failed"]

            for test, reason in jest_data["failures"]:
                all_failures.append((lang_name, test, reason))
            for test, reason in playwright_data["failures"]:
                all_failures.append((lang_name, test, reason))

            jest_log = node_result["jest_log_file"]
            pw_log = node_result["playwright_log_file"]
            f.write(f"Raw output: [{jest_log.name}](../../{jest_log.relative_to(PROJECT_ROOT)}), ")
            f.write(f"[{pw_log.name}](../../{pw_log.relative_to(PROJECT_ROOT)})\n\n")

        # Overall summary
        f.write("---\n\n")
        f.write("## Overall Summary\n\n")
        f.write(f"**Total Passed:** {total_passed}\n")
        f.write(f"**Total Failed:** {total_failed}\n")
        f.write(f"**Grand Total:** {total_passed + total_failed}\n\n")

        # Combined failures section
        if all_failures:
            f.write("## All Failed Tests\n\n")
            for lang, test, reason in all_failures:
                f.write(f"- **[{lang}]** `{test}`\n  - {reason}\n")
            f.write("\n")


def _parse_health_check_output(stdout: str) -> dict[str, Any]:
    """Parse health check script output to extract check results.

    Extracts individual check statuses from the HEALTH CHECK SUMMARY table
    produced by health_check.py or health_check.js.

    Args:
        stdout: Standard output from health check script execution.

    Returns:
        Dictionary containing:
        - checks: List of (check_name, status, details) tuples for each check.
        - passed_count: Number of checks that passed.
        - failed_count: Number of checks that failed.
        - skipped_count: Number of checks that were skipped.
        - warning_count: Number of checks with warnings.
    """
    result: dict[str, Any] = {
        "checks": [],
        "passed_count": 0,
        "failed_count": 0,
        "skipped_count": 0,
        "warning_count": 0,
    }

    # Parse the summary table lines
    # Format: "Check Name           ✅ PASSED" or "Check Name           ❌ FAILED    Details"
    lines = stdout.split("\n")
    in_table = False

    for line in lines:
        # Detect table boundaries
        if "HEALTH CHECK SUMMARY" in line:
            in_table = True
            continue
        if in_table and line.startswith("=" * 10):
            # End of table (closing separator)
            if result["checks"]:  # Only break if we've found checks
                break
            continue
        if in_table and line.startswith("-" * 10):
            continue  # Skip separator line

        # Skip header row
        if in_table and "Check" in line and "Status" in line:
            continue

        # Parse check result lines
        if in_table and line.strip():
            # Extract status emoji and text
            if "✅ PASSED" in line:
                result["passed_count"] += 1
                status = "PASSED"
            elif "❌ FAILED" in line:
                result["failed_count"] += 1
                status = "FAILED"
            elif "⏭️" in line or "SKIPPED" in line:
                result["skipped_count"] += 1
                status = "SKIPPED"
            elif "⚠️" in line or "WARNING" in line:
                result["warning_count"] += 1
                status = "WARNING"
            else:
                continue  # Not a valid check line

            # Extract check name (everything before the status indicator)
            parts = line.split()
            if len(parts) >= 2:
                # Find where the status starts and extract check name
                for i, part in enumerate(parts):
                    if part in ("✅", "❌", "⏭️", "⚠️"):
                        check_name = " ".join(parts[:i])
                        # Details are everything after status text
                        details_start = i + 2  # Skip emoji and status word
                        details = (
                            " ".join(parts[details_start:]) if len(parts) > details_start else ""
                        )
                        result["checks"].append((check_name, status, details))
                        break

    return result


def _generate_merged_health_summary(
    summary_file: Path,
    health_results: HealthCheckMergeInput,
) -> None:
    """Generate unified Health-Check-Summary.md combining results from all language health checks.

    Creates a single Health-Check-Summary.md file with per-language sections, combining
    health check results from Python (health_check.py) and/or Node.js (health_check.js)
    health check runners.

    Args:
        summary_file: Path where summary markdown file should be written.
        health_results: Dictionary mapping language keys to their health check result data.
            Keys are "python" and/or "node". Values are PythonHealthCheckResult or
            NodeHealthCheckResult TypedDicts containing success status, stdout/stderr,
            return code, and report file path.
    """
    with summary_file.open("w") as f:
        f.write("# Health Check Summary Report\n\n")
        timestamp = subprocess.run(
            ["date"], check=False, capture_output=True, text=True
        ).stdout.strip()
        f.write(f"**Generated at:** {timestamp}\n\n")

        # Track overall status
        all_passed = True
        total_checks_passed = 0
        total_checks_failed = 0
        total_checks_skipped = 0
        total_checks_warning = 0

        # Python section
        if "python" in health_results:
            python_result = health_results["python"]
            parsed = _parse_health_check_output(python_result["stdout"])

            f.write("## Python Health Check\n\n")

            if python_result["success"]:
                f.write("**Status:** ✅ PASSED\n\n")
            else:
                f.write("**Status:** ❌ FAILED\n\n")
                all_passed = False

            # Write check details
            if parsed["checks"]:
                f.write("| Check | Status | Details |\n")
                f.write("|-------|--------|--------|\n")
                for check_name, status, details in parsed["checks"]:
                    status_emoji = {
                        "PASSED": "✅",
                        "FAILED": "❌",
                        "SKIPPED": "⏭️",
                        "WARNING": "⚠️",
                    }.get(status, "")
                    f.write(f"| {check_name} | {status_emoji} {status} | {details} |\n")
                f.write("\n")

            total_checks_passed += parsed["passed_count"]
            total_checks_failed += parsed["failed_count"]
            total_checks_skipped += parsed["skipped_count"]
            total_checks_warning += parsed["warning_count"]

            # Link to raw report
            report_file = python_result["report_file"]
            rel_path = report_file.relative_to(PROJECT_ROOT)
            f.write(f"Full report: [{report_file.name}](../../{rel_path})\n\n")

        # Node.js section
        if "node" in health_results:
            node_result = health_results["node"]
            parsed = _parse_health_check_output(node_result["stdout"])

            # Determine language name from report filename
            report_name = node_result["report_file"].stem
            if report_name.startswith("TypeScript"):
                lang_name = "TypeScript"
            elif report_name.startswith("Javascript"):
                lang_name = "JavaScript"
            else:
                lang_name = "Node.js"

            f.write(f"## {lang_name} Health Check\n\n")

            if node_result["success"]:
                f.write("**Status:** ✅ PASSED\n\n")
            else:
                f.write("**Status:** ❌ FAILED\n\n")
                all_passed = False

            # Write check details
            if parsed["checks"]:
                f.write("| Check | Status | Details |\n")
                f.write("|-------|--------|--------|\n")
                for check_name, status, details in parsed["checks"]:
                    status_emoji = {
                        "PASSED": "✅",
                        "FAILED": "❌",
                        "SKIPPED": "⏭️",
                        "WARNING": "⚠️",
                    }.get(status, "")
                    f.write(f"| {check_name} | {status_emoji} {status} | {details} |\n")
                f.write("\n")

            total_checks_passed += parsed["passed_count"]
            total_checks_failed += parsed["failed_count"]
            total_checks_skipped += parsed["skipped_count"]
            total_checks_warning += parsed["warning_count"]

            # Link to raw report
            report_file = node_result["report_file"]
            rel_path = report_file.relative_to(PROJECT_ROOT)
            f.write(f"Full report: [{report_file.name}](../../{rel_path})\n\n")

        # Overall summary
        f.write("---\n\n")
        f.write("## Overall Summary\n\n")

        if all_passed:
            f.write("**Overall Status:** ✅ ALL CHECKS PASSED\n\n")
        else:
            f.write("**Overall Status:** ❌ SOME CHECKS FAILED\n\n")

        f.write(f"- **Passed:** {total_checks_passed}\n")
        f.write(f"- **Failed:** {total_checks_failed}\n")
        if total_checks_warning > 0:
            f.write(f"- **Warnings:** {total_checks_warning}\n")
        if total_checks_skipped > 0:
            f.write(f"- **Skipped:** {total_checks_skipped}\n")
        f.write(
            f"- **Total:** {total_checks_passed + total_checks_failed + total_checks_skipped}\n"
        )


def _parse_jest_output(stdout: str) -> dict[str, Any]:
    """Parse Jest test output to extract test counts and failure details.

    Args:
        stdout: Standard output from Jest test execution

    Returns:
        Dictionary containing:
        - passed: Number of passed tests
        - failed: Number of failed tests
        - total: Total number of tests
        - suites_passed: Number of passed test suites
        - suites_failed: Number of failed test suites
        - suites_total: Total number of test suites
        - duration: Test execution duration string
        - failures: List of (test_name, reason) tuples for failed tests
    """
    result: dict[str, Any] = {
        "passed": 0,
        "failed": 0,
        "total": 0,
        "suites_passed": 0,
        "suites_failed": 0,
        "suites_total": 0,
        "duration": "",
        "failures": [],
    }

    # Parse test suite summary: "Test Suites: 2 failed, 10 passed, 12 total"
    suites_match = re.search(
        r"Test Suites:\s*(?:(\d+)\s*failed,\s*)?(?:(\d+)\s*passed,\s*)?(\d+)\s*total",
        stdout,
    )
    if suites_match:
        result["suites_failed"] = int(suites_match.group(1) or 0)
        result["suites_passed"] = int(suites_match.group(2) or 0)
        result["suites_total"] = int(suites_match.group(3) or 0)

    # Parse test summary: "Tests: 5 failed, 84 passed, 89 total"
    tests_match = re.search(
        r"Tests:\s*(?:(\d+)\s*failed,\s*)?(?:(\d+)\s*passed,\s*)?(\d+)\s*total",
        stdout,
    )
    if tests_match:
        result["failed"] = int(tests_match.group(1) or 0)
        result["passed"] = int(tests_match.group(2) or 0)
        result["total"] = int(tests_match.group(3) or 0)

    # Parse duration: "Time: 2.145s" or "Time: 2.145 s"
    time_match = re.search(r"Time:\s*([\d.]+)\s*s", stdout)
    if time_match:
        result["duration"] = f"{time_match.group(1)}s"

    # Extract failed test names and reasons
    # Jest format: "FAIL path/to/test.ts" followed by test descriptions
    pattern = (
        r"FAIL\s+(.+?\.(?:ts|js|tsx|jsx))\s*\n"
        r"(.*?)(?=\n\s*(?:PASS|FAIL|Test Suites:)|\Z)"
    )
    fail_blocks = re.findall(pattern, stdout, re.DOTALL)
    for file_path, block in fail_blocks:
        # Extract individual test failures: "✕ test name (duration)"
        test_failures = re.findall(r"✕\s+(.+?)(?:\s+\(\d+\s*m?s\))?$", block, re.MULTILINE)
        for test_name in test_failures:
            result["failures"].append((f"{file_path}: {test_name.strip()}", "Test failed"))

    return result


def _parse_playwright_output(stdout: str) -> dict[str, Any]:
    """Parse Playwright test output to extract test counts and failure details.

    Args:
        stdout: Standard output from Playwright test execution

    Returns:
        Dictionary containing:
        - passed: Number of passed tests
        - failed: Number of failed tests
        - total: Total number of tests
        - duration: Test execution duration string
        - failures: List of (test_name, reason) tuples for failed tests
    """
    result: dict[str, Any] = {
        "passed": 0,
        "failed": 0,
        "total": 0,
        "duration": "",
        "failures": [],
    }

    # Parse summary line: "15 passed (1.0m)" or "2 failed, 13 passed (1.5m)"
    # Also handles: "15 passed" without duration
    summary_match = re.search(
        r"(?:(\d+)\s*failed,?\s*)?(\d+)\s*passed(?:\s*\(([^)]+)\))?",
        stdout,
    )
    if summary_match:
        result["failed"] = int(summary_match.group(1) or 0)
        result["passed"] = int(summary_match.group(2) or 0)
        result["total"] = result["passed"] + result["failed"]
        result["duration"] = summary_match.group(3) or ""

    # Extract failed test details
    # Playwright format: "✘  [browser] > file.spec.ts:line:col > test name (duration)"
    # or: "✗  [browser] > file.spec.ts:line:col > test name"
    fail_pattern = (
        r"[✘✗]\s*\[([^\]]+)\]\s*>\s*([^>]+?)\s*>\s*(.+?)"
        r"(?:\s+\([\d.]+[ms]+\))?\s*$"
    )
    fail_matches = re.findall(fail_pattern, stdout, re.MULTILINE)
    for browser, file_info, test_name in fail_matches:
        result["failures"].append(
            (f"[{browser}] {file_info.strip()}: {test_name.strip()}", "Test failed")
        )

    return result


def _generate_node_test_summary(
    summary_file: Path,
    jest_stdout: str,
    playwright_stdout: str,
    jest_log_file: Path,
    playwright_log_file: Path,
) -> None:
    """Generate markdown test summary report from Jest and Playwright outputs.

    Creates a unified Test-Summary.md file combining results from both test runners,
    matching the format used for Python test summaries.

    Args:
        summary_file: Path where summary markdown file should be written
        jest_stdout: Standard output from Jest test execution
        playwright_stdout: Standard output from Playwright test execution
        jest_log_file: Path to Jest raw output log file for reference linking
        playwright_log_file: Path to Playwright raw output log file for reference linking
    """
    jest_results = _parse_jest_output(jest_stdout)
    playwright_results = _parse_playwright_output(playwright_stdout)

    with summary_file.open("w") as f:
        f.write("# Test Summary Report\n\n")
        timestamp = subprocess.run(
            ["date"], check=False, capture_output=True, text=True
        ).stdout.strip()
        f.write(f"**Generated at:** {timestamp}\n\n")

        # Combined test results
        total_passed = jest_results["passed"] + playwright_results["passed"]
        total_failed = jest_results["failed"] + playwright_results["failed"]
        total_tests = jest_results["total"] + playwright_results["total"]

        f.write("## Test Results\n\n")
        f.write(
            f"**Summary:** {total_passed} passed, {total_failed} failed, {total_tests} total\n\n"
        )

        # Jest section
        f.write("### Jest (Unit Tests)\n\n")
        if jest_results["total"] > 0:
            f.write(f"- **Test Suites:** {jest_results['suites_passed']} passed, ")
            f.write(
                f"{jest_results['suites_failed']} failed, {jest_results['suites_total']} total\n"
            )
            f.write(f"- **Tests:** {jest_results['passed']} passed, ")
            f.write(f"{jest_results['failed']} failed, {jest_results['total']} total\n")
            if jest_results["duration"]:
                f.write(f"- **Duration:** {jest_results['duration']}\n")
        else:
            f.write("No Jest test results found or tests not configured.\n")
        f.write("\n")

        # Playwright section
        f.write("### Playwright (E2E Tests)\n\n")
        if playwright_results["total"] > 0:
            f.write(f"- **Tests:** {playwright_results['passed']} passed, ")
            f.write(f"{playwright_results['failed']} failed, {playwright_results['total']} total\n")
            if playwright_results["duration"]:
                f.write(f"- **Duration:** {playwright_results['duration']}\n")
        else:
            f.write("No Playwright test results found or tests not configured.\n")
        f.write("\n")

        # Failed tests section
        all_failures = jest_results["failures"] + playwright_results["failures"]
        if all_failures:
            f.write("## Failed Tests\n\n")
            for test, reason in all_failures:
                f.write(f"- `{test}`\n  - {reason}\n")
            f.write("\n")

        f.write("## Full Output\n\n")
        jest_rel = jest_log_file.relative_to(jest_log_file.parent.parent.parent)
        f.write(f"- Jest results: [{jest_log_file.name}](../../{jest_rel})\n")
        pw_rel = playwright_log_file.relative_to(playwright_log_file.parent.parent.parent)
        f.write(f"- Playwright results: [{playwright_log_file.name}](../../{pw_rel})\n")


def _generate_python_coverage_report(markdown_report_file: Path, coverage_dir: Path) -> None:
    """Generate markdown-formatted coverage report using coverage tool.

    Args:
        markdown_report_file: Path where markdown coverage report should be written
        coverage_dir: Path to the coverage data directory
    """
    coverage_cmd = [
        "uv",
        "run",
        "coverage",
        "report",
        "--format=markdown",
        "--show-missing",
        "--skip-covered",
        "--skip-empty",
        "--sort=cover",
    ]
    cov_return, cov_stdout, cov_stderr = run_command(coverage_cmd, capture_output=True)

    if cov_return == 0 and cov_stdout:
        with markdown_report_file.open("w") as f:
            f.write("# Python Coverage Report\n\n")
            timestamp = subprocess.run(
                ["date"], check=False, capture_output=True, text=True
            ).stdout.strip()
            f.write(f"**Generated at:** {timestamp}\n\n")
            f.write("## Coverage by File\n\n")
            f.write(cov_stdout)
            f.write("\n## Report Formats\n\n")
            f.write("- **Markdown**: This file - AI-friendly condensed format\n")
            html_rel = coverage_dir.relative_to(PROJECT_ROOT)
            f.write(
                f"- **HTML**: [Interactive HTML Report](../../{html_rel}/index.html) - "
                "For detailed browsing\n"
            )
            f.write(
                f"- **JSON**: [Machine-readable data](../../{html_rel}/coverage.json) - "
                "For programmatic access\n"
            )
        print(f"Markdown coverage report: {markdown_report_file.relative_to(PROJECT_ROOT)}")
    else:
        print("Warning: Could not generate markdown coverage report")
        if cov_stderr:
            print(f"Error: {cov_stderr}")


def _parse_jest_coverage_data(coverage_data: dict[str, Any]) -> list[tuple[str, float, int, int]]:
    """Parse Jest coverage JSON data into file coverage tuples.

    Args:
        coverage_data: Parsed Jest coverage.json data

    Returns:
        List of (file_path, coverage_pct, total_stmts, missing_stmts) tuples
    """
    files_coverage: list[tuple[str, float, int, int]] = []

    for file_path, file_data in coverage_data.items():
        # Skip summary entries and non-file entries
        if not isinstance(file_data, dict) or "s" not in file_data:
            continue

        # Calculate coverage from statement coverage
        statements = file_data.get("s", {})
        if not statements:
            continue

        total_statements = len(statements)
        covered_statements = sum(1 for count in statements.values() if count > 0)
        missing_statements = total_statements - covered_statements

        if total_statements > 0:
            coverage_pct = (covered_statements / total_statements) * 100
            # Only include files with missing coverage (skip-covered behavior)
            if missing_statements > 0:
                # Get relative path from project root
                rel_path = file_path
                if PROJECT_ROOT.as_posix() in file_path:
                    rel_path = file_path.replace(PROJECT_ROOT.as_posix() + "/", "")
                files_coverage.append(
                    (rel_path, coverage_pct, total_statements, missing_statements)
                )

    return files_coverage


def _write_node_coverage_markdown(
    markdown_file: Path,
    files_coverage: list[tuple[str, float, int, int]],
    html_report_dir: Path,
    coverage_json_path: Path,
) -> None:
    """Write Node.js coverage report in markdown format.

    Args:
        markdown_file: Path where markdown report should be written
        files_coverage: List of (file_path, coverage_pct, total_stmts, missing_stmts)
        html_report_dir: Path to HTML coverage report for linking
        coverage_json_path: Path to coverage JSON file for linking
    """
    # Calculate totals
    total_stmts = sum(f[2] for f in files_coverage)
    total_missing = sum(f[3] for f in files_coverage)
    total_covered = total_stmts - total_missing
    overall_pct = (total_covered / total_stmts * 100) if total_stmts > 0 else 100

    with markdown_file.open("w") as f:
        f.write("# Coverage Report\n\n")
        timestamp = subprocess.run(
            ["date"], check=False, capture_output=True, text=True
        ).stdout.strip()
        f.write(f"**Generated at:** {timestamp}\n\n")

        f.write("## Coverage Summary\n\n")
        f.write(f"- **Total Statements:** {total_stmts}\n")
        f.write(f"- **Covered Statements:** {total_covered}\n")
        f.write(f"- **Missing Statements:** {total_missing}\n")
        f.write(f"- **Overall Coverage:** {overall_pct:.1f}%\n\n")

        if files_coverage:
            f.write("## Coverage by File\n\n")
            f.write("*Files with missing coverage only (sorted by coverage %)*\n\n")
            f.write("| File | Stmts | Miss | Cover |\n")
            f.write("|------|-------|------|-------|\n")
            for file_path, pct, stmts, miss in files_coverage:
                f.write(f"| {file_path} | {stmts} | {miss} | {pct:.1f}% |\n")
        else:
            f.write("## Coverage by File\n\n")
            f.write("All files have 100% coverage!\n")

        f.write("\n## Report Formats\n\n")
        f.write("- **Markdown**: This file (Coverage-Report.md) - ")
        f.write("AI-friendly condensed format\n")
        # Use PROJECT_ROOT-relative paths with ../../ prefix (same pattern as Python coverage)
        html_rel = html_report_dir.relative_to(PROJECT_ROOT)
        f.write(f"- **HTML**: [Interactive HTML Report](../../{html_rel}/index.html) - ")
        f.write("For detailed browsing\n")
        json_rel = coverage_json_path.relative_to(PROJECT_ROOT)
        f.write(f"- **JSON**: [Machine-readable data](../../{json_rel}) - ")
        f.write("For programmatic access\n")


def _generate_node_coverage_report(
    coverage_json_path: Path, markdown_report_file: Path, html_report_dir: Path
) -> bool:
    """Generate markdown-formatted coverage report from Jest coverage JSON.

    Parses the coverage JSON file generated by Jest and creates a markdown
    coverage report matching the Python coverage report format.

    Args:
        coverage_json_path: Path to Jest coverage.json file
        markdown_report_file: Path where markdown coverage report should be written
        html_report_dir: Path to HTML coverage report directory for linking

    Returns:
        True if coverage report generated successfully, False otherwise
    """
    import json

    if not coverage_json_path.exists():
        print(f"Warning: Coverage JSON not found at {coverage_json_path}")
        return False

    try:
        with coverage_json_path.open() as f:
            coverage_data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: Could not parse coverage JSON: {e}")
        return False

    # Parse coverage data from Jest/Istanbul format
    files_coverage = _parse_jest_coverage_data(coverage_data)

    # Sort by coverage percentage (ascending - worst coverage first)
    files_coverage.sort(key=lambda x: x[1])

    # Write markdown report
    _write_node_coverage_markdown(
        markdown_report_file, files_coverage, html_report_dir, coverage_json_path
    )

    print(f"Markdown coverage report: {markdown_report_file.relative_to(PROJECT_ROOT)}")
    return True


class PythonTestResult(TypedDict):
    """Result data from Python test execution for merged summary generation."""

    success: bool
    stdout: str
    raw_log_file: Path
    coverage_dir: Path
    coverage_report_file: Path


def run_python_tests() -> PythonTestResult:
    """Run pytest and save results to report files.

    Returns:
        PythonTestResult containing success status and output data for merging.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DEV_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Language-specific output paths
    coverage_dir = DEV_REPORTS_DIR / "coverage-python"
    raw_output_file = DEV_REPORTS_DIR / "Test-Results-Pytest.log"
    coverage_report_file = REPORTS_DIR / "Python-Coverage-Report.md"

    cmd = [
        "uv",
        "run",
        "pytest",
        "-v",
        "--tb=short",
        "--cov=src",
        "--cov-report=term",
        f"--cov-report=html:{coverage_dir}",
        f"--cov-report=json:{coverage_dir / 'coverage.json'}",
    ]

    print("\nRunning pytest with coverage...")
    returncode, stdout, stderr = run_command(cmd, capture_output=True)

    # Save raw output
    with raw_output_file.open("w") as f:
        f.write(f"Command: {' '.join(cmd)}\n")
        f.write(f"Return code: {returncode}\n\n")
        f.write("--- STDOUT ---\n")
        f.write(stdout)
        f.write("\n--- STDERR ---\n")
        f.write(stderr)

    # Generate markdown coverage report
    print("Generating markdown coverage report...")
    _generate_python_coverage_report(coverage_report_file, coverage_dir)

    # Print summary
    if returncode == 0:
        print("✅ All Python tests passed!")
    else:
        print("❌ Some Python tests failed.")

    print(f"Raw output: {raw_output_file.relative_to(PROJECT_ROOT)}")
    print(f"HTML coverage: {coverage_dir.relative_to(PROJECT_ROOT)}/index.html")
    print(f"Coverage report: {coverage_report_file.relative_to(PROJECT_ROOT)}")

    return PythonTestResult(
        success=returncode == 0,
        stdout=stdout,
        raw_log_file=raw_output_file,
        coverage_dir=coverage_dir,
        coverage_report_file=coverage_report_file,
    )


class NodeTestResult(TypedDict):
    """Result data from Node.js test execution for merged summary generation.

    Attributes:
        success: True if all executed tests passed (skipped tests don't affect this).
        jest_stdout: Captured stdout from Jest execution, empty if skipped.
        playwright_stdout: Captured stdout from Playwright execution, empty if skipped.
        jest_log_file: Path to Jest raw log file.
        playwright_log_file: Path to Playwright raw log file.
        coverage_dir: Path to coverage report directory.
        coverage_report_file: Path to markdown coverage report.
        jest_skipped: True if test script was not available.
        playwright_skipped: True if test:e2e script was not available.
    """

    success: bool
    jest_stdout: str
    playwright_stdout: str
    jest_log_file: Path
    playwright_log_file: Path
    coverage_dir: Path
    coverage_report_file: Path
    jest_skipped: bool
    playwright_skipped: bool


class PythonHealthCheckResult(TypedDict):
    """Result data from Python health check execution for merged summary generation.

    Attributes:
        success: True if all health checks passed, False if any check failed.
        stdout: Captured stdout from health_check.py execution.
        stderr: Captured stderr from health_check.py execution.
        returncode: Process return code from the health check script.
        report_file: Path to the generated health check report file.
    """

    success: bool
    stdout: str
    stderr: str
    returncode: int
    report_file: Path


class NodeHealthCheckResult(TypedDict):
    """Result data from Node.js health check execution for merged summary generation.

    Attributes:
        success: True if all health checks passed, False if any check failed.
        stdout: Captured stdout from health_check.js execution.
        stderr: Captured stderr from health_check.js execution.
        returncode: Process return code from the health check script.
        report_file: Path to the generated health check report file.
    """

    success: bool
    stdout: str
    stderr: str
    returncode: int
    report_file: Path


def run_node_tests(language: str) -> NodeTestResult:
    """Run Jest and Playwright tests and save results to report files.

    Uses detected package manager (pnpm, npm, yarn, or bun) for test commands.
    Falls back to npm if package manager detection returns None.

    Checks script availability before execution: if test or test:e2e scripts
    are not defined in package.json, the corresponding test suite is skipped with
    a clear message rather than marking it as failed.

    Generates the following reports:
    - Raw test logs in dev/reports/ (Test-Results-Jest.log, Test-Results-Playwright.log)
    - Language-specific coverage report in docs/reports/ (e.g., Javascript-Coverage-Report.md)
    - HTML coverage report in dev/reports/coverage-node/ (if Jest coverage is configured)

    Args:
        language: Language identifier ("typescript" or "javascript") for naming outputs

    Returns:
        NodeTestResult containing success status, output data, and skip status for merging.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DEV_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Use detected package manager, fallback to npm if None
    pkg_manager = PKG_MANAGER if PKG_MANAGER is not None else "npm"

    # Language-specific output paths
    display_name = LANGUAGE_CONFIG[language]["display_name"]
    coverage_dir = DEV_REPORTS_DIR / "coverage-node"
    coverage_report_file = REPORTS_DIR / f"{display_name}-Coverage-Report.md"

    # Raw test logs go to dev/reports/
    jest_log_file = DEV_REPORTS_DIR / "Test-Results-Jest.log"
    playwright_log_file = DEV_REPORTS_DIR / "Test-Results-Playwright.log"

    # Track test results
    all_passed = True
    test_outputs: dict[str, str] = {}
    jest_skipped = False
    playwright_skipped = False

    # Check Jest (test) availability and run if available
    if is_script_available("test"):
        jest_cmd = [
            pkg_manager,
            "run",
            "test",
            "--",
            "--coverage",
            "--coverageReporters=json",
            "--coverageReporters=html",
            f"--coverageDirectory={coverage_dir}",
        ]

        print("\nRunning jest tests...")
        returncode, stdout, stderr = run_command(jest_cmd, capture_output=True)

        test_outputs["jest"] = stdout

        log_content = f"Command: {' '.join(jest_cmd)}\n"
        log_content += f"Return code: {returncode}\n\n"
        log_content += f"--- STDOUT ---\n{stdout}\n--- STDERR ---\n{stderr}"

        with jest_log_file.open("w") as f:
            f.write(log_content)
        log_rel = jest_log_file.relative_to(PROJECT_ROOT)
        print(f"Jest test results logged to: {log_rel}")

        if returncode == 0:
            print("Jest tests passed.")
        else:
            all_passed = False
            print(f"Jest tests FAILED (return code: {returncode}). Check log file for details.")
    else:
        jest_skipped = True
        print("\nJest tests SKIPPED (test script not configured)")
        # Write skip status to log file
        with jest_log_file.open("w") as f:
            f.write("Jest tests SKIPPED: test script not configured in package.json\n")

    # Check Playwright (test:e2e) availability and run if available
    if is_script_available("test:e2e"):
        playwright_cmd = [pkg_manager, "run", "test:e2e"]

        print("\nRunning playwright tests...")
        returncode, stdout, stderr = run_command(playwright_cmd, capture_output=True)

        test_outputs["playwright"] = stdout

        log_content = f"Command: {' '.join(playwright_cmd)}\n"
        log_content += f"Return code: {returncode}\n\n"
        log_content += f"--- STDOUT ---\n{stdout}\n--- STDERR ---\n{stderr}"

        with playwright_log_file.open("w") as f:
            f.write(log_content)
        log_rel = playwright_log_file.relative_to(PROJECT_ROOT)
        print(f"Playwright test results logged to: {log_rel}")

        if returncode == 0:
            print("Playwright tests passed.")
        else:
            all_passed = False
            print(
                f"Playwright tests FAILED (return code: {returncode}). Check log file for details."
            )
    else:
        playwright_skipped = True
        print("\nPlaywright tests SKIPPED (test:e2e script not configured)")
        # Write skip status to log file
        with playwright_log_file.open("w") as f:
            f.write("Playwright tests SKIPPED: test:e2e script not configured in package.json\n")

    # Generate coverage report (only if Jest ran and produced coverage)
    print("\nGenerating coverage report...")
    coverage_json_path = coverage_dir / "coverage-final.json"

    if coverage_json_path.exists():
        _generate_node_coverage_report(coverage_json_path, coverage_report_file, coverage_dir)
        print(f"HTML coverage: {coverage_dir.relative_to(PROJECT_ROOT)}/index.html")
    elif jest_skipped:
        print("Note: Coverage data not generated (Jest was skipped).")
    else:
        print("Note: Coverage data not found. Ensure Jest is configured with coverage enabled.")
        print(f"Expected coverage JSON at: {coverage_json_path.relative_to(PROJECT_ROOT)}")

    # Print summary
    if jest_skipped and playwright_skipped:
        print(f"\n⏭️  {display_name} tests skipped (no test scripts configured)")
    elif all_passed:
        print(f"\n✅ All {display_name} tests passed!")
    else:
        print(f"\n❌ Some {display_name} tests failed.")

    return NodeTestResult(
        success=all_passed,
        jest_stdout=test_outputs.get("jest", ""),
        playwright_stdout=test_outputs.get("playwright", ""),
        jest_log_file=jest_log_file,
        playwright_log_file=playwright_log_file,
        coverage_dir=coverage_dir,
        coverage_report_file=coverage_report_file,
        jest_skipped=jest_skipped,
        playwright_skipped=playwright_skipped,
    )


def generate_python_api_docs() -> bool:
    """Generate Python API documentation using codedocs_pdoc.

    Imports and calls generate_python_api_docs() from codedocs_pdoc module,
    passing check_dirs from configuration. The codedocs_pdoc module handles
    hybrid mode selection (package mode vs file mode) internally.

    Returns:
        True if documentation generated successfully, False otherwise
    """
    # Get check_dirs from configuration
    check_dirs = get_check_dirs()
    if not check_dirs:
        print("Skipping Python API docs: no source directories configured.")
        return True

    # Import generate_python_api_docs from codedocs_pdoc
    try:
        from codedocs_pdoc import generate_python_api_docs as pdoc_generate
    except ImportError as e:
        print(f"Warning: Could not import codedocs_pdoc module: {e}")
        return False

    # Define output directory
    output_dir = DEV_REPORTS_DIR / "pydoc-api-docs"

    # Call the function directly with check_dirs
    return pdoc_generate(
        check_dirs=check_dirs,
        output_dir=output_dir,
        project_root=PROJECT_ROOT,
    )


def generate_node_api_docs(project_type: str) -> bool:
    """Generate Node.js API documentation (TypeDoc for TypeScript, JSDoc for JavaScript).

    Executes the appropriate documentation generation script based on project type.
    TypeScript projects use TypeDoc to generate markdown documentation at
    dev/reports/TypeDoc-API-Docs.md. JavaScript projects use JSDoc to generate
    HTML documentation at dev/reports/jsdoc-api-docs/.

    Args:
        project_type: Language type - must be "typescript" or "javascript"

    Returns:
        True if documentation generated successfully, False otherwise

    Raises:
        ValueError: If project_type is not "typescript" or "javascript"
    """
    if project_type not in ("typescript", "javascript"):
        raise ValueError(f"project_type must be 'typescript' or 'javascript', got '{project_type}'")

    if project_type == "typescript":
        script_name = "codedocs_typedoc.js"
        tool_name = "TypeDoc"
        output_desc = "TypeDoc documentation at dev/reports/TypeDoc-API-Docs.md"
    else:  # javascript
        script_name = "codedocs_jsdoc.js"
        tool_name = "JSDoc"
        output_desc = "JSDoc HTML documentation at dev/reports/jsdoc-api-docs/"

    print(f"\nInvoking {tool_name} generation script...")
    script_path = PROJECT_ROOT / "scripts" / script_name

    if not script_path.exists():
        print(f"Warning: {tool_name} script not found at {script_path}")
        return False

    cmd = ["node", str(script_path)]
    returncode, stdout, stderr = run_command(cmd, capture_output=True, cwd=PROJECT_ROOT)

    if stdout:
        print(f"--- {tool_name} Script STDOUT ---\n{stdout.strip()}")
    if stderr:
        print(f"--- {tool_name} Script STDERR ---\n{stderr.strip()}")

    if returncode == 0:
        print(f"{tool_name} generation script completed successfully.")
        print(f"Output: {output_desc}")
        return True
    print(f"{tool_name} generation script FAILED (return code: {returncode}).")
    return False


def generate_python_code_map() -> bool:
    """Generate markdown API documentation summary for Python with metadata and links.

    Executes codedocs_python.py to generate the base code map, then enhances it
    with metadata (generation timestamp, configuration info) and links to related
    documentation resources.

    Returns:
        True if documentation generated successfully, False otherwise
    """
    print("\nGenerating Python code map...")

    code_summary_script = PROJECT_ROOT / "scripts" / "codedocs_python.py"
    output_file = REPORTS_DIR / "Python-Code-Map.md"

    if not code_summary_script.exists():
        print(f"Warning: codedocs_python.py script not found at {code_summary_script}")
        return False

    # Execute codedocs_python.py to generate base code map
    cmd = ["python", str(code_summary_script)]
    returncode, stdout, stderr = run_command(cmd, capture_output=True)

    if stdout:
        print(stdout.strip())
    if stderr and returncode != 0:
        print(f"Error: {stderr.strip()}")

    if returncode != 0:
        print("Failed to generate Python code map.")
        return False

    # Read the generated code map
    if not output_file.exists():
        print(f"Error: Expected output file not found at {output_file}")
        return False

    original_content = output_file.read_text()

    # Add metadata header and links footer
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Extract content after marker, preserving section headers
    if "## Modules" in original_content:
        # Keep "## Modules" header when extracting content
        parts = original_content.split("## Modules", 1)
        content_body = "## Modules" + parts[1]
    elif "# Python API Structure" in original_content:
        # Fallback: extract everything after main title
        parts = original_content.split("# Python API Structure", 1)
        content_body = parts[1].strip() if len(parts) > 1 else ""
    else:
        # Ultimate fallback: use entire content
        content_body = original_content.strip()

    enhanced_content = f"""# Python API Structure

*Generated: {timestamp}*
*Configuration: [tool.wsd].check_dirs from pyproject.toml*

{content_body}

---

## Related Documentation

- [Python Standards](../read-only/standards/Python-Standards.md) - \
Python coding conventions for this project
- [Coding Standards](../read-only/standards/Coding-Standards.md) - \
General coding guidelines
- [Python Document Generator](\
../features/python-document-generator/Python-Document-Generator-Overview.md) - \
Tool specification
"""

    # Write enhanced content
    with output_file.open("w") as f:
        f.write(enhanced_content)

    print("Python code map generated successfully at: docs/reports/Python-Code-Map.md")
    return True


def generate_node_code_map(project_type: str) -> bool:
    """Generate Node.js code map (TypeScript or JavaScript).

    Executes the appropriate code map generation script based on project type.
    TypeScript projects use codedocs_typescript.js to generate a code map at
    docs/reports/TypeScript-Code-Map.md. JavaScript projects use codedocs_javascript.js
    to generate a code map at docs/reports/JavaScript-Code-Map.md.

    Args:
        project_type: Language type - must be "typescript" or "javascript"

    Returns:
        True if code map generated successfully, False otherwise

    Raises:
        ValueError: If project_type is not "typescript" or "javascript"
    """
    if project_type not in ("typescript", "javascript"):
        raise ValueError(f"project_type must be 'typescript' or 'javascript', got '{project_type}'")

    if project_type == "typescript":
        script_name = "codedocs_typescript.js"
        language_name = "TypeScript"
        output_file = "docs/reports/TypeScript-Code-Map.md"
    else:  # javascript
        script_name = "codedocs_javascript.js"
        language_name = "JavaScript"
        output_file = "docs/reports/JavaScript-Code-Map.md"

    print(f"\nInvoking {language_name} code map generation script...")

    script_path = PROJECT_ROOT / "scripts" / script_name

    if not script_path.exists():
        print(f"Warning: {language_name} code map script not found at {script_path}")
        return False

    cmd = ["node", str(script_path)]
    returncode, stdout, stderr = run_command(cmd, capture_output=True, cwd=PROJECT_ROOT)

    if stdout:
        print(f"STDOUT: {stdout.strip()}")
    if stderr and returncode != 0:
        print(f"STDERR: {stderr.strip()}")

    if returncode == 0:
        print(f"{language_name} code map generated successfully at: {output_file}")
        return True
    print(f"{language_name} code map generation FAILED (return code: {returncode}).")
    return False


def archive_claude_sessions() -> bool:
    """Archive Claude Code session files.

    Returns:
        True if archiving completed successfully, False otherwise
    """
    print("\nArchiving Claude Code session files...")

    archive_script = PROJECT_ROOT / "scripts" / "archive_claude_sessions.py"

    if not archive_script.exists():
        print(f"Warning: Archive script not found at {archive_script}")
        return False

    cmd = [sys.executable, str(archive_script)]

    try:
        process = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            cwd=PROJECT_ROOT,
            check=False,
        )

        if process.stdout:
            print(process.stdout)
        if process.stderr:
            print(f"Errors: {process.stderr}", file=sys.stderr)

        if process.returncode == 0:
            print("Claude Code session archiving completed successfully.")
            return True
        print(f"Claude Code session archiving FAILED (return code: {process.returncode}).")
        return False

    except Exception as e:
        print(f"Error running archive script: {e}")
        return False


def _extract_workbench_description(file_path: Path) -> str:
    """Extract first heading or paragraph from a markdown file as description.

    Scans the file for the first non-empty content that is either:
    - A markdown heading (# Title)
    - A paragraph of text (non-heading, non-whitespace content)

    Args:
        file_path: Path to the markdown file to extract description from.

    Returns:
        The extracted description text, truncated to 100 characters if needed.
        Returns "(empty file)" if the file has no extractable content.
    """
    try:
        with file_path.open(encoding="utf-8") as f:
            for line in f:
                stripped_line = line.strip()
                if not stripped_line:
                    continue
                # Check for heading
                if stripped_line.startswith("#"):
                    # Remove heading markers and return text
                    return stripped_line.lstrip("#").strip()[:100]
                # Otherwise, return first non-empty line as paragraph start
                return stripped_line[:100]
        return "(empty file)"
    except (OSError, UnicodeDecodeError) as e:
        return f"(error reading file: {e})"


def generate_workbench_status() -> bool:
    """Generate Workbench Status report listing documents in docs/workbench/.

    Scans the docs/workbench/ directory for markdown files, extracts metadata
    (modification timestamp, first heading or paragraph), and generates a
    markdown table report to assist the Context-Librarian agent.

    The report includes:
    - List of all markdown files in docs/workbench/
    - File modification timestamps
    - First paragraph or heading of each document as description
    - Total count of workbench documents

    Returns:
        True if report generated successfully, False otherwise.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    workbench_dir = PROJECT_ROOT / "docs" / "workbench"
    report_file = REPORTS_DIR / "Workbench-Status.md"

    print("\nGenerating Workbench Status report...")

    if not workbench_dir.exists():
        print(f"Note: Workbench directory not found at {workbench_dir}")
        # Write empty report
        with report_file.open("w", encoding="utf-8") as f:
            f.write("# Workbench Status\n\n")
            f.write("*No workbench directory found.*\n")
        print(f"Workbench Status report: {report_file.relative_to(PROJECT_ROOT)}")
        return True

    # Find all markdown files in workbench
    md_files = sorted(workbench_dir.glob("*.md"))

    if not md_files:
        # Write empty report
        with report_file.open("w", encoding="utf-8") as f:
            f.write("# Workbench Status\n\n")
            f.write("*No documents currently in workbench.*\n")
        print(f"Workbench Status report: {report_file.relative_to(PROJECT_ROOT)}")
        return True

    # Build report content
    from datetime import datetime

    lines: list[str] = []
    lines.append("# Workbench Status\n")
    lines.append("")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"*Generated: {timestamp}*\n")
    lines.append("")
    lines.append(f"**Total Documents:** {len(md_files)}\n")
    lines.append("")
    lines.append("## Documents\n")
    lines.append("")
    lines.append("| File | Modified | Description |")
    lines.append("|------|----------|-------------|")

    for md_file in md_files:
        # Get modification time
        mtime = md_file.stat().st_mtime
        mod_date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")

        # Extract description
        description = _extract_workbench_description(md_file)

        # Escape pipe characters in description for markdown table
        description = description.replace("|", "\\|")

        lines.append(f"| {md_file.name} | {mod_date} | {description} |")

    lines.append("")

    # Write report
    with report_file.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Workbench Status report: {report_file.relative_to(PROJECT_ROOT)}")
    print(f"  Found {len(md_files)} document(s) in workbench")
    return True


def run_python_health_check() -> PythonHealthCheckResult:
    """Run Python health check script and save results to report file.

    Executes health_check.py and generates a language-prefixed report file
    at docs/reports/Python-Health-Check-Report.md. Returns structured result
    for merging with other language health checks.

    Returns:
        PythonHealthCheckResult containing success status and output data for merging.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    health_check_script = PROJECT_ROOT / "scripts" / "health_check.py"
    report_file = REPORTS_DIR / "Python-Health-Check-Report.md"

    print("\nRunning Python health check...")

    if not health_check_script.exists():
        error_message = f"Error: Health check script not found at {health_check_script}"
        print(error_message)
        with report_file.open("w", encoding="utf-8") as f:
            f.write(error_message)
        return PythonHealthCheckResult(
            success=False,
            stdout="",
            stderr=error_message,
            returncode=1,
            report_file=report_file,
        )

    cmd = [sys.executable, str(health_check_script)]

    try:
        process = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            cwd=PROJECT_ROOT,
            check=False,
        )

        full_output = f"--- STDOUT ---\n{process.stdout}\n\n--- STDERR ---\n{process.stderr}"

        with report_file.open("w", encoding="utf-8") as f:
            f.write(full_output)

        if process.returncode == 0:
            print("✅ Python health check passed!")
        else:
            print("❌ Python health check failed.")

        print(f"Report: {report_file.relative_to(PROJECT_ROOT)}")

        return PythonHealthCheckResult(
            success=process.returncode == 0,
            stdout=process.stdout,
            stderr=process.stderr,
            returncode=process.returncode,
            report_file=report_file,
        )

    except Exception as e:
        error_message = f"Error running health check script: {e}"
        print(error_message)
        with report_file.open("w", encoding="utf-8") as f:
            f.write(error_message)
        return PythonHealthCheckResult(
            success=False,
            stdout="",
            stderr=error_message,
            returncode=1,
            report_file=report_file,
        )


def run_node_health_check(language: str) -> NodeHealthCheckResult:
    """Run Node.js health check script and save results to report file.

    Executes health_check.js via node and generates a language-prefixed report
    file (e.g., Javascript-Health-Check-Report.md or TypeScript-Health-Check-Report.md).
    Returns structured result for merging with other language health checks.

    Args:
        language: Language identifier ("typescript" or "javascript") for naming outputs.

    Returns:
        NodeHealthCheckResult containing success status and output data for merging.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Language-specific output paths using display name from registry
    display_name = LANGUAGE_CONFIG[language]["display_name"]
    report_file = REPORTS_DIR / f"{display_name}-Health-Check-Report.md"
    health_check_script = PROJECT_ROOT / "scripts" / "health_check.js"

    print(f"\nRunning {display_name} health check...")

    if not health_check_script.exists():
        error_message = f"Error: Health check script not found at {health_check_script}"
        print(error_message)
        with report_file.open("w", encoding="utf-8") as f:
            f.write(error_message)
        return NodeHealthCheckResult(
            success=False,
            stdout="",
            stderr=error_message,
            returncode=1,
            report_file=report_file,
        )

    cmd = ["node", str(health_check_script)]

    try:
        process = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            cwd=PROJECT_ROOT,
            check=False,
        )

        full_output = f"--- STDOUT ---\n{process.stdout}\n\n--- STDERR ---\n{process.stderr}"

        with report_file.open("w", encoding="utf-8") as f:
            f.write(full_output)

        if process.returncode == 0:
            print(f"✅ {display_name} health check passed!")
        else:
            print(f"❌ {display_name} health check failed.")

        print(f"Report: {report_file.relative_to(PROJECT_ROOT)}")

        return NodeHealthCheckResult(
            success=process.returncode == 0,
            stdout=process.stdout,
            stderr=process.stderr,
            returncode=process.returncode,
            report_file=report_file,
        )

    except Exception as e:
        error_message = f"Error running health check script: {e}"
        print(error_message)
        with report_file.open("w", encoding="utf-8") as f:
            f.write(error_message)
        return NodeHealthCheckResult(
            success=False,
            stdout="",
            stderr=error_message,
            returncode=1,
            report_file=report_file,
        )


def run_health_check_and_save_report() -> bool:
    """Run Python health check and save report.

    Delegates to run_python_health_check() and returns boolean success status.

    Returns:
        True if health check passed, False otherwise.
    """
    result = run_python_health_check()
    return result["success"]


def _calculate_step_count(quick_mode: bool, languages: set[str]) -> int:
    """Calculate total step count for progress display based on mode and languages.

    Determines the number of steps to display in progress messages based on
    the execution mode and detected project languages. Step categories remain
    consistent regardless of language count - language-specific operations
    (tests, API docs, code maps) are grouped under single step numbers with
    per-language sub-operations shown as indented messages.

    Args:
        quick_mode: True for quick documentation mode, False for full mode.
        languages: Set of detected project languages (e.g., {"python", "javascript"}).
            Currently used for validation; step count is category-based.

    Returns:
        Total number of steps for progress display.
    """
    # Validate languages parameter (used for future extensibility)
    _ = [lang for lang in languages if lang in LANGUAGE_CONFIG]

    # Step categories (each shown as [N/total] in progress output):
    # Quick mode (5 steps):
    #   1. File structure update
    #   2. File list generation
    #   3. Code map generation (iterates per language)
    #   4. Workbench status report
    #   5. Claude session archiving
    #
    # Full mode (8 steps):
    #   1. File structure update
    #   2. File list generation
    #   3. Test execution (iterates per language)
    #   4. API documentation (iterates per language)
    #   5. Code map generation (iterates per language)
    #   6. Health check
    #   7. Workbench status report
    #   8. Claude session archiving

    if quick_mode:
        return 5
    return 8


def _execute_quick_mode(languages: set[str], total_steps: int) -> dict[str, bool | str]:
    """Execute quick documentation update mode for all detected languages.

    Iterates over all detected project languages and generates code maps for each.
    Uses the LANGUAGE_CONFIG registry for language-specific dispatch.

    Args:
        languages: Set of detected project languages (e.g., {"python", "javascript"})
        total_steps: Total number of steps in quick mode for progress display

    Returns:
        Dictionary mapping language-prefixed task names to success status. Values are:
            - True: Task passed
            - False: Task failed
            - "skipped": Task was skipped (e.g., no test scripts configured)
        Keys are formatted as "{language}_code_map" (e.g., "python_code_map").
    """
    results: dict[str, bool | str] = {}

    # Generate code maps for each detected language
    print(f"\n[3/{total_steps}] Generating code maps...")
    for lang in sorted(languages):
        if lang not in LANGUAGE_CONFIG:
            continue

        config = LANGUAGE_CONFIG[lang]
        display_name = config["display_name"]
        code_map_func_name = config["code_map_generator"]

        if code_map_func_name == "generate_python_code_map":
            print(f"  Generating {display_name} code map...")
            results[f"{lang}_code_map"] = generate_python_code_map()
        elif code_map_func_name == "generate_node_code_map":
            print(f"  Generating {display_name} code map...")
            results[f"{lang}_code_map"] = generate_node_code_map(lang)

    print(f"\n[4/{total_steps}] Generating Workbench Status report...")
    results["workbench_status"] = generate_workbench_status()

    print(f"\n[5/{total_steps}] Archiving Claude Code sessions...")
    results["sessions_archive"] = archive_claude_sessions()

    return results


def _execute_full_mode(
    languages: set[str], total_steps: int, args: argparse.Namespace
) -> dict[str, bool | str]:
    """Execute full documentation update mode with all checks for all detected languages.

    Iterates over all detected project languages and runs tests, generates API docs,
    and creates code maps for each. Uses the LANGUAGE_CONFIG registry for dispatch.

    Args:
        languages: Set of detected project languages (e.g., {"python", "javascript"})
        total_steps: Total number of steps in full mode for progress display
        args: Parsed command-line arguments containing skip flags

    Returns:
        Dictionary mapping language-prefixed task names to success status. Values are:
            - True: Task passed
            - False: Task failed
            - "skipped": Task was skipped (e.g., no test scripts configured)
        Keys are formatted as "{language}_tests", "{language}_api_docs",
        "{language}_code_map" (e.g., "python_tests", "javascript_api_docs").
    """
    results: dict[str, bool | str] = {}
    step = 3

    # Run tests for each language (unless skipped)
    if not args.skip_tests:
        print(f"\n[{step}/{total_steps}] Running tests and generating reports...")
        test_results: MergedTestInput = {}

        for lang in sorted(languages):
            if lang not in LANGUAGE_CONFIG:
                continue

            config = LANGUAGE_CONFIG[lang]
            display_name = config["display_name"]
            test_func_name = config["test_runner"]

            if test_func_name == "run_python_tests":
                print(f"  Running {display_name} tests...")
                python_result = run_python_tests()
                test_results["python"] = python_result
                results[f"{lang}_tests"] = python_result["success"]
            elif test_func_name == "run_node_tests":
                print(f"  Running {display_name} tests...")
                node_result = run_node_tests(lang)
                test_results["node"] = node_result
                # Distinguish between passed, failed, and all-skipped
                if node_result["jest_skipped"] and node_result["playwright_skipped"]:
                    results[f"{lang}_tests"] = "skipped"
                else:
                    results[f"{lang}_tests"] = node_result["success"]

        # Generate merged test summary after all language test runners complete
        summary_file = REPORTS_DIR / "Test-Summary.md"
        _generate_merged_test_summary(summary_file, test_results)
        print(f"Test summary: {summary_file.relative_to(PROJECT_ROOT)}")
        step += 1
    else:
        print(f"\n[{step}/{total_steps}] Skipping tests (--skip-tests flag)")
        step += 1

    # Generate HTML API documentation for each language (unless skipped)
    if not args.skip_api_docs:
        print(f"\n[{step}/{total_steps}] Generating HTML API documentation...")

        for lang in sorted(languages):
            if lang not in LANGUAGE_CONFIG:
                continue

            config = LANGUAGE_CONFIG[lang]
            display_name = config["display_name"]
            api_doc_func_name = config["api_doc_generator"]

            if api_doc_func_name == "generate_python_api_docs":
                print(f"  Generating {display_name} API docs...")
                results[f"{lang}_api_docs"] = generate_python_api_docs()
            elif api_doc_func_name == "generate_node_api_docs":
                print(f"  Generating {display_name} API docs...")
                results[f"{lang}_api_docs"] = generate_node_api_docs(lang)

        step += 1
    else:
        print(f"\n[{step}/{total_steps}] Skipping HTML API docs (--skip-api-docs flag)")
        step += 1

    # Generate code maps for each language (always in full mode)
    print(f"\n[{step}/{total_steps}] Generating code summary/maps...")

    for lang in sorted(languages):
        if lang not in LANGUAGE_CONFIG:
            continue

        config = LANGUAGE_CONFIG[lang]
        display_name = config["display_name"]
        code_map_func_name = config["code_map_generator"]

        if code_map_func_name == "generate_python_code_map":
            print(f"  Generating {display_name} code map...")
            results[f"{lang}_code_map"] = generate_python_code_map()
        elif code_map_func_name == "generate_node_code_map":
            print(f"  Generating {display_name} code map...")
            results[f"{lang}_code_map"] = generate_node_code_map(lang)

    step += 1

    # Run health checks for each language (unless skipped)
    if not args.skip_health:
        print(f"\n[{step}/{total_steps}] Running project health checks...")
        health_results: HealthCheckMergeInput = {}

        for lang in sorted(languages):
            if lang not in LANGUAGE_CONFIG:
                continue

            config = LANGUAGE_CONFIG[lang]
            display_name = config["display_name"]
            health_func_name = config["health_check_runner"]

            if health_func_name == "run_python_health_check":
                print(f"  Running {display_name} health check...")
                python_health_result: PythonHealthCheckResult = run_python_health_check()
                health_results["python"] = python_health_result
                results[f"{lang}_health_check"] = python_health_result["success"]
            elif health_func_name == "run_node_health_check":
                print(f"  Running {display_name} health check...")
                node_health_result: NodeHealthCheckResult = run_node_health_check(lang)
                health_results["node"] = node_health_result
                results[f"{lang}_health_check"] = node_health_result["success"]

        # Generate merged health check summary after all language health checks complete
        if health_results:
            summary_file = REPORTS_DIR / "Health-Check-Summary.md"
            _generate_merged_health_summary(summary_file, health_results)
            print(f"Health check summary: {summary_file.relative_to(PROJECT_ROOT)}")

        step += 1
    else:
        print(f"\n[{step}/{total_steps}] Skipping health check (--skip-health flag)")
        step += 1

    # Generate Workbench Status report (always in full mode)
    print(f"\n[{step}/{total_steps}] Generating Workbench Status report...")
    results["workbench_status"] = generate_workbench_status()
    step += 1

    # Archive Claude Code sessions (always in full mode)
    print(f"\n[{step}/{total_steps}] Archiving Claude Code sessions...")
    results["sessions_archive"] = archive_claude_sessions()

    return results


def _format_task_name(task_key: str) -> str:
    """Format a result dictionary key into a human-readable task name.

    Handles language-prefixed keys by using display names from LANGUAGE_CONFIG
    when available, ensuring proper capitalization (e.g., "TypeScript" not
    "Typescript"). Falls back to simple title-casing for non-language keys.

    Args:
        task_key: Result dictionary key (e.g., "python_tests", "workbench_status").

    Returns:
        Human-readable task name (e.g., "Python Tests", "Workbench Status").
    """
    # Check if this is a language-prefixed key
    for lang, config in LANGUAGE_CONFIG.items():
        if task_key.startswith(f"{lang}_"):
            # Extract the task type (e.g., "tests", "code_map", "api_docs")
            task_type = task_key[len(lang) + 1 :]  # +1 for the underscore
            display_name = config["display_name"]
            task_type_formatted = task_type.replace("_", " ").title()
            return f"{display_name} {task_type_formatted}"

    # Non-language key: simple title-casing
    return task_key.replace("_", " ").title()


def _print_summary(results: dict[str, bool | str], quick_mode: bool, reports_dir: Path) -> bool:
    """Print documentation update summary and exit with appropriate code.

    Args:
        results: Dictionary mapping task names to success status. Values can be:
            - True: Task passed
            - False: Task failed
            - "skipped": Task was skipped (treated as success)
        quick_mode: Whether quick mode was used
        reports_dir: Path to reports directory for final message

    Returns:
        True if all tasks passed or were skipped, False if any failed
    """
    print("\n" + "=" * 60)
    print("Documentation Update Summary")
    print("=" * 60)

    # "skipped" counts as success (not a failure)
    all_passed = all(v is True or v == "skipped" for v in results.values())

    for task, result in results.items():
        if result == "skipped":
            status = "⏭️  SKIPPED"
        elif result:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        task_name = _format_task_name(task)
        print(f"{task_name:<30} {status}")

    print("=" * 60)

    if all_passed:
        if quick_mode:
            print("\n✅ Quick documentation update completed successfully!")
        else:
            print("\n✅ All documentation tasks completed successfully!")
    else:
        print("\n❌ Some documentation tasks failed. Please review the output above.")
        print("\nFailed tasks:")
        for task, result in results.items():
            if result is False:
                print(f"  - {_format_task_name(task)}")

    # Create docs/reports directory if it doesn't exist
    if not reports_dir.exists():
        reports_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nAll reports saved to: {reports_dir.relative_to(PROJECT_ROOT)}/")

    return all_passed


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description="Update project documentation and run checks for all detected languages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/update_docs.py --quick          # Quick docs update
  python scripts/update_docs.py --full           # Full pre-commit checks (default)
  python scripts/update_docs.py                  # Default: full checks
  python scripts/update_docs.py --project-type python     # Restrict to Python only
  python scripts/update_docs.py --project-type typescript # Restrict to TypeScript only

Language Detection:
  All project languages are detected and processed automatically:
  - Python: pyproject.toml with [project] section
  - TypeScript: package.json with .ts files in check directories
  - JavaScript: package.json without .ts files in check directories

  Multi-language projects (e.g., Python + TypeScript) are fully supported.
  Use --project-type to restrict processing to a single detected language.

Steps executed:
  Quick mode (--quick, -q):
    1. Update file structure
    2. Generate file lists (per language)
    3. Generate code maps (per language)
    4. Generate Workbench Status report
    5. Archive Claude Code sessions

  Full mode (--full, default):
    1. Update file structure
    2. Generate file lists (per language)
    3. Run tests with coverage (per language)
    4. Generate HTML API documentation (per language)
    5. Generate code maps (per language)
    6. Run health check
    7. Generate Workbench Status report
    8. Archive Claude Code sessions
        """,
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--quick",
        "-q",
        action="store_true",
        help="Quick documentation update only (file structure + summaries)",
    )
    mode_group.add_argument(
        "--docs-only",
        action="store_true",
        help="Alias for --quick (documentation only, no tests/checks)",
    )
    mode_group.add_argument(
        "--full",
        "-f",
        action="store_true",
        help="Full pre-commit checks including tests and health check (default)",
    )

    # Project type filter
    parser.add_argument(
        "--project-type",
        choices=["python", "typescript", "javascript"],
        help="Restrict processing to a specific detected language",
    )

    # Individual control flags
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running tests (only with --full)",
    )
    parser.add_argument(
        "--skip-health",
        action="store_true",
        help="Skip health check (only with --full)",
    )
    parser.add_argument(
        "--skip-api-docs",
        action="store_true",
        help="Skip HTML API documentation generation (only with --full)",
    )

    return parser.parse_args()


def main() -> None:
    """Update all documentation files and run tests.

    Detects all project languages and processes documentation for each.
    The --project-type flag can restrict processing to a specific language.

    Returns:
        None (exits with appropriate code)
    """
    args = parse_arguments()

    # Detect all project languages
    languages = detect_project_languages()

    # Validate that at least one language was detected
    if not languages:
        print("Error: No project languages detected.", file=sys.stderr)
        print(
            "No Python project files (pyproject.toml with [project]) "
            "or Node.js files (package.json) found.",
            file=sys.stderr,
        )
        print(
            "Ensure your project has the appropriate configuration files.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Apply --project-type filter if specified
    if args.project_type:
        if args.project_type not in languages:
            print(
                f"Error: Specified language '{args.project_type}' not detected in project.",
                file=sys.stderr,
            )
            detected_list = ", ".join(sorted(languages))
            print(f"Detected languages: {detected_list}", file=sys.stderr)
            print(
                f"Cannot restrict to '{args.project_type}' - it must be in the detected set.",
                file=sys.stderr,
            )
            sys.exit(1)
        # Filter to only the specified language
        languages = {args.project_type}

    # Display detected/filtered languages
    display_names = [LANGUAGE_CONFIG[lang]["display_name"] for lang in sorted(languages)]
    languages_display = ", ".join(display_names)
    print(f"Detected languages: {languages_display}")

    # Validate configuration for Python projects (only if Python is in the language set)
    if "python" in languages:
        validate_python_config()

    # Determine mode
    quick_mode = args.quick or args.docs_only

    # Track all results
    results: dict[str, bool | str] = {}

    print("=" * 60)
    if quick_mode:
        print(f"Starting Documentation Update (Quick Mode) - {languages_display}")
    else:
        print(f"Starting Documentation Update (Full Mode) - {languages_display}")
    print("=" * 60)

    # Calculate total steps based on mode and detected languages
    total_steps = _calculate_step_count(quick_mode, languages)

    print(f"\n[1/{total_steps}] Updating project file structure...")
    results["structure"] = update_file_structure()

    print(f"\n[2/{total_steps}] Generating file list reports...")
    results["file_lists"] = update_file_lists(languages)

    # Execute mode-specific tasks with full language set
    mode_results: dict[str, bool | str]
    if quick_mode:
        mode_results = _execute_quick_mode(languages, total_steps)
    else:
        mode_results = _execute_full_mode(languages, total_steps, args)

    results.update(mode_results)

    # Print summary and exit
    all_passed = _print_summary(results, quick_mode, REPORTS_DIR)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
