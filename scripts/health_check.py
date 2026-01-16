"""Health check script for Python projects.

This script is specifically for Python projects only. For Node.js projects
(TypeScript or JavaScript), use health_check.js instead.

Runs code quality checks including formatting, linting, type checking, security scanning,
and documentation completeness validation for dataclasses and public methods.
Designed to be run before git commits to ensure code quality.

Requires pyproject.toml to be present in the project root. The script will exit
with a helpful error message if pyproject.toml is not found. Directory configuration
for quality checks is read from the [tool.wsd] section.

Flags:
    --aggressive: Enable unsafe auto-fixes during linting (more fixes, higher risk).
    --clean: Clear type checker cache (.mypy_cache/) before running checks. Use this
        flag for quality gates (pre-commit, CI/CD) to ensure deterministic results.
        Incremental caching is faster but may mask configuration errors when imports
        or paths change.
    --commands: Display all commands used by each check without running them.

Usage Examples:
    # Standard development check (uses cached type information for speed)
    python scripts/health_check.py

    # Quality gate check (fresh analysis, no cached state)
    python scripts/health_check.py --clean

    # Aggressive fixes with clean analysis
    python scripts/health_check.py --aggressive --clean

    # Show available commands
    python scripts/health_check.py --commands
"""

import argparse
import ast
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Add scripts directory to path for wsd_utils import
_scripts_dir = Path(__file__).parent
sys.path.insert(0, str(_scripts_dir))
from wsd_utils import get_check_dirs  # noqa: E402

# Get the project root directory (this script is in scripts/ subdirectory)
project_root = Path(__file__).parent.parent.resolve()


def _validate_dataclass_docstring(
    node: ast.ClassDef, field_names: list[str], py_file: Path
) -> list[str]:
    """Validate dataclass docstring completeness.

    Args:
        node: ClassDef AST node representing the dataclass
        field_names: List of field names to validate documentation for
        py_file: Path to the Python file being checked

    Returns:
        List of issue strings describing documentation problems
    """
    issues = []
    docstring = ast.get_docstring(node)

    if not docstring:
        issues.append(f"{py_file}:{node.lineno}: {node.name} - No docstring found for dataclass")
    elif "Attributes:" not in docstring:
        issues.append(
            f"{py_file}:{node.lineno}: {node.name} - "
            f"No 'Attributes:' section in dataclass docstring"
        )
    else:
        # Check each field is documented
        missing_fields = [f for f in field_names if f not in docstring]
        if missing_fields:
            issues.append(
                f"{py_file}:{node.lineno}: {node.name} - "
                f"Missing field documentation for: {', '.join(missing_fields)}"
            )

    return issues


def validate_dataclass_documentation(dirs: list[str]) -> tuple[bool, list[str], int]:
    """Validate that all dataclass fields are documented in their docstrings.

    This fills an industry gap - no existing tool validates dataclass field
    documentation completeness. Uses AST parsing to check:
    1. All dataclasses have docstrings
    2. Docstrings include an "Attributes:" section
    3. Every field is documented in the Attributes section

    Args:
        dirs: List of directory paths to check (relative to project root)

    Returns:
        Tuple of (all_valid, issues_list, issue_count)
    """
    issues = []

    # Check Python files in all specified directories
    for dir_name in dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            continue

        for py_file in dir_path.rglob("*.py"):
            try:
                with py_file.open() as f:
                    tree = ast.parse(f.read())
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it has @dataclass decorator
                    is_dataclass = any(
                        (isinstance(d, ast.Name) and d.id == "dataclass")
                        or (isinstance(d, ast.Attribute) and d.attr == "dataclass")
                        for d in node.decorator_list
                    )

                    if is_dataclass:
                        # Get field names from class body
                        field_names = []
                        for item in node.body:
                            if isinstance(item, ast.AnnAssign) and isinstance(
                                item.target, ast.Name
                            ):
                                field_names.append(item.target.id)

                        issues.extend(_validate_dataclass_docstring(node, field_names, py_file))

    return (len(issues) == 0, issues, len(issues))


def _validate_parameter_docs(
    node: ast.FunctionDef | ast.AsyncFunctionDef, docstring: str, py_file: Path
) -> list[str]:
    """Validate that all function parameters are documented.

    Args:
        node: FunctionDef or AsyncFunctionDef node to validate
        docstring: Function's docstring
        py_file: Path to the Python file being checked

    Returns:
        List of issue strings for missing parameter documentation
    """
    issues = []
    params = [arg.arg for arg in node.args.args if arg.arg not in {"self", "cls"}]

    if params:
        if (
            "Args:" not in docstring
            and "Arguments:" not in docstring
            and "Parameters:" not in docstring
        ):
            issues.append(
                f"{py_file}:{node.lineno}: {node.name} - "
                f"Missing Args/Arguments/Parameters section for parameters: "
                f"{', '.join(params)}"
            )
        else:
            # Check each parameter is documented
            missing_params = [p for p in params if p not in docstring]
            if missing_params:
                params_str = ", ".join(missing_params)
                issues.append(
                    f"{py_file}:{node.lineno}: {node.name} - "
                    f"Missing documentation for parameters: {params_str}"
                )

    return issues


def _validate_return_docs(
    node: ast.FunctionDef | ast.AsyncFunctionDef, docstring: str, py_file: Path
) -> list[str]:
    """Validate that return value is documented if function returns.

    Args:
        node: FunctionDef or AsyncFunctionDef node to validate
        docstring: Function's docstring
        py_file: Path to the Python file being checked

    Returns:
        List of issue strings for missing return documentation
    """
    issues = []

    # Check for Returns documentation if function returns non-None
    # Only check returns in the function's direct body, not nested functions
    def has_return_in_body(
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> bool:
        """Check if function has return statements with values in its direct body.

        Recursively walks the function body but stops at nested function boundaries.

        Args:
            func_node: The function AST node to check

        Returns:
            True if function body contains return statements with non-None values
        """

        def walk_excluding_nested_functions(
            node: ast.AST,
        ) -> list[ast.AST]:
            """Walk AST excluding nested function definitions.

            Args:
                node: AST node to walk

            Returns:
                List of AST nodes excluding those inside nested functions
            """
            nodes = []
            for child in ast.iter_child_nodes(node):
                # Don't walk into nested function/class definitions
                if isinstance(
                    child,
                    (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
                ):
                    continue
                nodes.append(child)
                nodes.extend(walk_excluding_nested_functions(child))
            return nodes

        # Check direct returns in function body
        for ast_node in walk_excluding_nested_functions(func_node):
            if isinstance(ast_node, ast.Return):
                # Bare return or return None don't require documentation
                if ast_node.value is None:
                    continue
                # return None (as ast.Constant) doesn't require documentation
                if isinstance(ast_node.value, ast.Constant) and ast_node.value.value is None:
                    continue
                # Any other return requires documentation
                return True
        return False

    has_return = has_return_in_body(node)
    if has_return and "Returns:" not in docstring and "Return:" not in docstring:
        issues.append(f"{py_file}:{node.lineno}: {node.name} - Missing Returns/Return section")

    return issues


def _walk_functions_at_module_level(
    tree: ast.Module,
) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    """Walk AST and return only top-level and class-level functions.

    Skips functions nested inside other functions, as these are not
    public and don't require docstrings per Python documentation standards.

    Args:
        tree: The parsed AST module

    Returns:
        List of function nodes that are at module or class level (not nested)
    """
    functions: list[ast.FunctionDef | ast.AsyncFunctionDef] = []

    def visit(node: ast.AST, inside_function: bool = False) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not inside_function:
                functions.append(node)
            for child in ast.iter_child_nodes(node):
                visit(child, inside_function=True)
        elif isinstance(node, ast.ClassDef):
            for child in ast.iter_child_nodes(node):
                visit(child, inside_function=False)
        else:
            for child in ast.iter_child_nodes(node):
                visit(child, inside_function=inside_function)

    visit(tree)
    return functions


def validate_public_method_documentation(dirs: list[str]) -> tuple[bool, list[str], int]:
    """Validate that public methods and functions have complete documentation.

    Checks:
    1. All public functions/methods have docstrings
    2. Docstrings document all parameters in Args section
    3. Return types are documented in Returns section (if not None)

    Args:
        dirs: List of directory paths to check (relative to project root)

    Returns:
        Tuple of (all_valid, issues_list, issue_count)
    """
    issues = []

    # Check Python files in all specified directories
    for dir_name in dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            continue

        for py_file in dir_path.rglob("*.py"):
            try:
                with py_file.open() as f:
                    content = f.read()
                    tree = ast.parse(content)
            except SyntaxError:
                continue

            for node in _walk_functions_at_module_level(tree):
                # Skip private methods (starting with _)
                if node.name.startswith("_") and not node.name.startswith("__init__"):
                    continue

                # Get docstring
                docstring = ast.get_docstring(node)

                if not docstring:
                    # Skip methods that are property setters/deleters (they inherit docs)
                    is_property_method = any(
                        isinstance(d, ast.Name) and d.id in ("setter", "deleter")
                        for d in node.decorator_list
                    )
                    if not is_property_method:
                        issues.append(
                            f"{py_file}:{node.lineno}: {node.name} - "
                            f"No docstring found for public method"
                        )
                    continue

                # Validate parameter documentation
                issues.extend(_validate_parameter_docs(node, docstring, py_file))

                # Validate return documentation
                issues.extend(_validate_return_docs(node, docstring, py_file))

    return (len(issues) == 0, issues, len(issues))


def test_pydoc_generation() -> tuple[bool, str]:
    """Test that pydoc can generate documentation without errors.

    This is a simple smoke test to ensure documentation generation
    would work for API documentation tools. Tests the project's main
    module if available, otherwise tests a known stdlib module.

    Returns:
        Tuple of (success, error_message)
    """
    import contextlib  # noqa: PLC0415
    import io  # noqa: PLC0415
    import pydoc  # noqa: PLC0415

    try:
        import tomllib  # type: ignore[import-not-found]  # noqa: PLC0415
    except ModuleNotFoundError:
        import tomli as tomllib  # noqa: PLC0415

    try:
        # First try to add src to path to find project module
        import sys  # noqa: PLC0415

        src_path = project_root / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        # Attempt to get project name from pyproject.toml
        module_name = None
        pyproject_path = project_root / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with pyproject_path.open("rb") as f:
                    config = tomllib.load(f)
                    if "project" in config and "name" in config["project"]:
                        module_name = config["project"]["name"]
            except Exception:
                pass  # Fall back to stdlib module

        # Capture output to avoid printing to console
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            # Try to get documentation for the main module
            try:
                if module_name:
                    doc = pydoc.render_doc(module_name, renderer=pydoc.plaintext)  # type: ignore
                    if doc:
                        return (True, "")
                    return (False, "Failed to generate documentation")
            except ImportError:
                pass  # Fall through to stdlib module test

            # If project module not importable, test with a known module as smoke test
            doc = pydoc.render_doc("pathlib", renderer=pydoc.plaintext)  # type: ignore
            if doc:
                return (True, "")
            return (False, "Failed to generate documentation")
    except Exception as e:
        return (False, f"Documentation generation error: {e!s}")


def analyze_mypy_output(stdout: str, stderr: str = "") -> tuple[int, list[str], int]:
    """Analyze mypy output to distinguish real errors from known false positives.

    Args:
        stdout: Raw mypy output string
        stderr: Raw mypy stderr output (for detecting crashes)

    Returns:
        Tuple of (real_error_count, real_error_lines, false_positive_count)
    """
    # First check if mypy crashed (traceback in stderr)
    if stderr and ("Traceback" in stderr or "KeyError" in stderr or "Exception" in stderr):
        # Mypy crashed - this is a critical error
        return (
            1,
            [
                "Mypy crashed with an internal error. "
                "Try clearing the cache with: rm -rf .mypy_cache"
            ],
            0,
        )

    lines = stdout.split("\n")
    real_errors = []
    false_positive_count = 0

    # Known false positive patterns
    # NOTE: When adding new patterns, document the reason and ensure they are
    # legitimate false positives, not real issues being masked
    # ALL patterns must be explicitly approved via Process Integrity Standards
    known_false_positives: list[str] = [
        # Add other known false positive patterns here as they are discovered
        # Example: "Some specific mypy issue that is confirmed to be false positive"
        # Each pattern MUST include approval reference: "Pattern approved in ticket #XXX"
    ]

    for line in lines:
        if "error:" in line:
            # Check if this line matches any known false positive pattern
            is_false_positive = any(fp in line for fp in known_false_positives)

            if is_false_positive:
                false_positive_count += 1
            else:
                real_errors.append(line.strip())

    return len(real_errors), real_errors, false_positive_count


def run_command(
    command: list[str],
    step_name: str,
    allow_failure: bool = False,
    auto_fix: bool = False,
) -> tuple[bool, str, str]:
    """Run a command and report results.

    Args:
        command: Command as list of strings
        step_name: Description of the step
        allow_failure: If True, don't exit on failure
        auto_fix: If True, this is an auto-fix operation

    Returns:
        Tuple of (success, stdout, stderr)
    """
    prefix = "Health Check" if not auto_fix else "Auto-fixing"
    print(f"{prefix}: Running {step_name}...")

    try:
        # Run with uv if it's a uv-compatible command
        if command[0] in ["ruff", "mypy", "pytest", "bandit", "pip-audit"]:
            command = ["uv", "run", *command]

        process = subprocess.run(
            command,
            cwd=project_root,
            check=not allow_failure,
            text=True,
            capture_output=True,
        )

        if process.returncode == 0:
            print(f"{prefix}: {step_name} completed successfully.")
            if process.stdout and not auto_fix:
                print("Output:\n", process.stdout)
        else:
            print(f"{prefix}: {step_name} found issues (exit code: {process.returncode})")
            if process.stdout:
                print("Output:\n", process.stdout)
            if process.stderr:
                print("Errors:\n", process.stderr)

        return (process.returncode == 0, process.stdout, process.stderr)

    except subprocess.CalledProcessError as e:
        if not allow_failure:
            print(f"{prefix}: ERROR during {step_name}!")
            print("Command:", " ".join(e.cmd))
            print("Return code:", e.returncode)
            if e.stdout:
                print("Output (stdout):\n", e.stdout)
            if e.stderr:
                print("Output (stderr):\n", e.stderr)
            sys.exit(1)
        return (False, e.stdout or "", e.stderr or "")

    except FileNotFoundError:
        print(f"{prefix}: ERROR: Command '{command[0]}' not found.")
        print("Please ensure all development dependencies are installed with: uv sync --extra dev")
        sys.exit(1)


def check_dependencies() -> None:
    """Check if required dependencies are available."""
    print("\nHealth Check: Verifying development dependencies...")

    # Check if uv is available
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: 'uv' is not available. Please install it first.")
        print("See: https://github.com/astral-sh/uv")
        sys.exit(1)

    # Verify dependencies are synced
    success, _stdout, _stderr = run_command(
        ["uv", "sync", "--dry-run"], "Dependency verification", allow_failure=True
    )

    if not success:
        print("\nDependencies are not properly synced. Running 'uv sync --extra dev'...")
        run_command(["uv", "sync", "--extra", "dev"], "Dependency installation")


def show_commands(dirs: list[str]) -> None:
    """Display all commands used in the health check.

    Args:
        dirs: List of directory paths being checked
    """
    dirs_str = " ".join(dirs)
    print("=" * 60)
    print("HEALTH CHECK COMMANDS REFERENCE")
    print("=" * 60)

    commands = [
        ("Build Validation", "uv build"),
        ("Type Checking", f"uv run mypy {dirs_str}"),
        ("Security Scan", f"uv run bandit -r {dirs[0]} -f screen -ll"),
        ("Dependency Audit", "uv run pip-audit"),
        ("Linting Check", f"uv run ruff check {dirs_str}"),
        ("Linting Fix (safe)", f"uv run ruff check {dirs_str} --fix"),
        (
            "Linting Fix (aggressive)",
            f"uv run ruff check {dirs_str} --fix --unsafe-fixes",
        ),
        ("Code Formatting Check", f"uv run ruff format --check {dirs_str}"),
        ("Code Formatting Fix", f"uv run ruff format {dirs_str}"),
    ]
    # Note: Docstring rules (D) are included in linting via convention
    # configured in pyproject.toml [tool.ruff.lint.pydocstyle]

    print(f"{'Check':<28} {'Command':<50}")
    print("-" * 78)

    for check_name, command in commands:
        print(f"{check_name:<28} {command:<50}")

    print("=" * 60)
    print("\nNote: All commands should be run from the project root directory.")
    print("      The health check script automatically adds 'uv run' prefix.")
    print(f"      Directories checked: {dirs_str}")


def _scan_security(dirs: list[str]) -> tuple[bool, list[tuple[str, str, str]]]:
    """Run security scanning with bandit.

    Args:
        dirs: List of directory paths to check (uses first directory)

    Returns:
        Tuple of (all_passed_flag, check_results_list)
        where check_results_list contains tuples of (name, status, notes)

    Raises:
        None
    """
    print("\n" + "-" * 40)

    # First check if bandit is available
    try:
        subprocess.run(
            ["uv", "run", "bandit", "--version"],
            capture_output=True,
            check=True,
            cwd=project_root,
        )

        # Use first directory for bandit scan
        success, stdout, _ = run_command(
            ["bandit", "-r", f"{dirs[0]}/", "-f", "screen", "-ll"],
            "Security scanning (bandit)",
            allow_failure=True,
        )

        if not success:
            print("\nSecurity issues detected. Please review.")
            # Count security issues
            issue_count = stdout.count("Issue:")
            return (False, [("Security Scan", "❌ FAILED", f"{issue_count} issues")])
        return (True, [("Security Scan", "✅ PASSED", "")])

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Skipping bandit security scan (not installed).")
        print("To enable, add 'bandit' to dev dependencies.")
        return (True, [("Security Scan", "⏭️  SKIPPED", "bandit not installed")])


def _check_types_with_mypy(
    dirs: list[str], clean: bool = False
) -> tuple[bool, list[tuple[str, str, str]]]:
    """Run type checking with mypy and analyze output.

    Args:
        dirs: List of directory paths to check
        clean: If True, clear mypy cache before checking for fresh analysis

    Returns:
        Tuple of (all_passed_flag, check_results_list)
        where check_results_list contains tuples of (name, status, notes)
    """
    print("\n" + "-" * 40)

    # Clear mypy cache if --clean flag is set
    if clean:
        cache_dir = project_root / ".mypy_cache"
        if cache_dir.exists():
            print("  Clearing mypy cache for fresh analysis...")
            try:
                shutil.rmtree(cache_dir)
            except OSError as e:
                print(f"  Warning: Failed to clear mypy cache: {e}")

    success, stdout, stderr = run_command(
        ["mypy"] + [f"{d}/" for d in dirs], "Type checking (mypy)", allow_failure=True
    )

    if not success:
        # Analyze mypy output to distinguish real errors from known false positives
        error_count, real_errors, false_positive_count = analyze_mypy_output(stdout, stderr)

        if error_count > 0:
            print(f"\nType checking failed with {error_count} real error(s):")
            # Show first 5 real errors for clarity
            for error in real_errors[:5]:
                print(f"  {error}")
            if len(real_errors) > 5:
                print(f"  ... and {len(real_errors) - 5} more error(s)")

            details = f"{error_count} error(s)"
            if false_positive_count > 0:
                details += f", {false_positive_count} false positive(s) ignored"
            return (False, [("Type Checking", "❌ FAILED", details)])
        if false_positive_count > 0:
            print(f"\nType checking passed ({false_positive_count} false positive(s) ignored).")
            return (
                True,
                [
                    (
                        "Type Checking",
                        "✅ PASSED",
                        f"{false_positive_count} false positive(s) ignored",
                    )
                ],
            )
        print("\nType checking passed with no issues.")
        return (True, [("Type Checking", "✅ PASSED", "")])
    return (True, [("Type Checking", "✅ PASSED", "")])


def _validate_build() -> tuple[bool, list[tuple[str, str, str]]]:
    """Validate that the build completes successfully.

    Args:
        None

    Returns:
        Tuple of (all_passed_flag, check_results_list)
        where check_results_list contains tuples of (name, status, notes)

    Raises:
        None
    """
    print("\n" + "-" * 40)
    success, _, _ = run_command(["uv", "build"], "Build validation", allow_failure=True)

    if not success:
        print("\nBuild validation failed. Check pyproject.toml configuration.")
        return (False, [("Build Validation", "❌ FAILED", "Check pyproject.toml")])
    return (True, [("Build Validation", "✅ PASSED", "")])


def _run_dependency_audit() -> tuple[bool, list[tuple[str, str, str]]]:
    """Run dependency security audit with pip-audit.

    Args:
        None

    Returns:
        Tuple of (all_passed_flag, check_results_list)
        where check_results_list contains tuples of (name, status, notes)

    Raises:
        None
    """
    print("\n" + "-" * 40)

    # Check if pip-audit is available
    try:
        subprocess.run(
            ["uv", "run", "pip-audit", "--version"],
            capture_output=True,
            check=True,
            cwd=project_root,
        )

        success, stdout, _stderr = run_command(
            ["pip-audit"], "Dependency security audit (pip-audit)", allow_failure=True
        )

        if not success:
            print("\nVulnerable dependencies detected. Please review.")
            # Count vulnerabilities with robust parsing and multiple fallbacks
            # Try multiple patterns to match vulnerability counts
            vuln_count = 0
            parsing_method = "unknown"

            # Primary pattern: handles singular/plural forms correctly
            vuln_match = re.search(r"Found (\d+) known vulnerabilit(y|ies)", stdout)
            if vuln_match:
                vuln_count = int(vuln_match.group(1))
                parsing_method = "primary pattern"
            else:
                # Secondary pattern: alternative phrasing
                vuln_match = re.search(
                    r"(\d+) known vulnerabilit(y|ies) found", stdout, re.IGNORECASE
                )
                if vuln_match:
                    vuln_count = int(vuln_match.group(1))
                    parsing_method = "secondary pattern"
                else:
                    # Tertiary pattern: package-focused phrasing
                    vuln_match = re.search(
                        r"(\d+) package\(s\)? with known vulnerabilities", stdout, re.IGNORECASE
                    )
                    if vuln_match:
                        vuln_count = int(vuln_match.group(1))
                        parsing_method = "tertiary pattern"
                    else:
                        # Final fallback: count GHSA/PYSEC IDs
                        ghsa_count = len(re.findall(r"GHSA-\w+-\w+-\w+", stdout))
                        pysec_count = len(re.findall(r"PYSEC-\d{4}-\d+", stdout))
                        vuln_count = ghsa_count + pysec_count
                        parsing_method = f"ID counting (GHSA: {ghsa_count}, PYSEC: {pysec_count})"

            # Self-validation: detect contradictory output
            if vuln_count == 0 and (
                "vulnerability" in stdout.lower() or "vulnerabilities" in stdout.lower()
            ):
                # Log warning about potential parsing issue
                print(
                    f"⚠️  Warning: Detected vulnerability text but count is 0 "
                    f"(parsing method: {parsing_method})"
                )
                # Try to extract any number near "vulnerability" as last resort
                numbers_near_vuln = re.findall(r"(\d+)[^0-9]*vulnerabilit", stdout, re.IGNORECASE)
                if numbers_near_vuln:
                    vuln_count = int(numbers_near_vuln[0])
                    parsing_method = "proximity extraction"

            return (
                False,
                [
                    (
                        "Dependency Audit",
                        "❌ FAILED",
                        f"{vuln_count} {'vulnerability' if vuln_count == 1 else 'vulnerabilities'}",
                    )
                ],
            )
        return (True, [("Dependency Audit", "✅ PASSED", "")])

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Skipping pip-audit dependency scan (not installed).")
        print("To enable, add 'pip-audit' to dev dependencies.")
        return (True, [("Dependency Audit", "⏭️  SKIPPED", "pip-audit not installed")])


def _check_enhanced_documentation(dirs: list[str]) -> tuple[str, str, str]:
    """Run enhanced documentation validation including dataclass and method checks.

    Args:
        dirs: List of directory paths to check

    Returns:
        Tuple of (name, status, notes) for the check result

    Raises:
        None
    """
    print("\n" + "-" * 40)

    # First run our custom dataclass documentation validation
    dataclass_valid, dataclass_issues, dataclass_count = validate_dataclass_documentation(dirs)

    if not dataclass_valid:
        print(f"\nDataclass documentation issues detected ({dataclass_count} issues):")
        for issue in dataclass_issues[:5]:
            print(f"  {issue}")
        if len(dataclass_issues) > 5:
            print(f"  ... and {len(dataclass_issues) - 5} more issue(s)")

    # Run public method documentation validation
    method_valid, method_issues, method_count = validate_public_method_documentation(dirs)

    if not method_valid:
        print(f"\nPublic method documentation issues detected ({method_count} issues):")
        for issue in method_issues[:5]:
            print(f"  {issue}")
        if len(method_issues) > 5:
            print(f"  ... and {len(method_issues) - 5} more issue(s)")

    # Test pydoc generation
    pydoc_success, pydoc_error = test_pydoc_generation()
    if not pydoc_success:
        print(f"\nPydoc generation test failed: {pydoc_error}")

    # Generate result based on all checks
    if not dataclass_valid or not method_valid or not pydoc_success:
        doc_details: list[str] = []
        if dataclass_count > 0:
            doc_details.append(f"{dataclass_count} dataclass")
        if method_count > 0:
            doc_details.append(f"{method_count} method")
        if not pydoc_success:
            doc_details.append("pydoc generation failed")

        if doc_details:
            return (
                "Doc Completeness",
                "⚠️ WARNING",
                f"{' + '.join(doc_details)} issues (non-blocking)",
            )
    return ("Doc Completeness", "✅ PASSED", "")


def _check_documentation(dirs: list[str]) -> tuple[bool, list[tuple[str, str, str]]]:
    """Run documentation completeness checks for dataclasses and public methods.

    This check validates that dataclass fields and public method parameters are
    properly documented. Standard docstring style rules (pydocstyle D rules) are
    enforced via the main linting check configured in pyproject.toml.

    Args:
        dirs: List of directory paths to check

    Returns:
        Tuple of (all_passed_flag, check_results_list)
        where check_results_list contains tuples of (name, status, notes)
    """
    results: list[tuple[str, str, str]] = []

    # Enhanced Documentation Check - dataclass field and method parameter validation
    enhanced_doc_result = _check_enhanced_documentation(dirs)
    results.append(enhanced_doc_result)

    # Note: Standard docstring style rules (D rules) are now part of the main
    # linting check, using convention specified in pyproject.toml. This ensures
    # consistent behavior across ./wsd.py lint and ./wsd.py health.

    # All checks passed if we have PASSED/FIXED/WARNING results (WARNING is non-blocking)
    all_passed = all(status in ["✅ PASSED", "✅ FIXED", "⚠️ WARNING"] for _, status, _ in results)
    return (all_passed, results)


def _check_linting(dirs: list[str], aggressive: bool) -> tuple[bool, list[tuple[str, str, str]]]:
    """Run linting checks with auto-fix capabilities.

    Args:
        dirs: List of directory paths to check
        aggressive: Whether to use unsafe fixes

    Returns:
        Tuple of (all_passed_flag, check_results_list)
        where check_results_list contains tuples of (name, status, notes)

    Raises:
        None
    """
    print("\n" + "-" * 40)

    # First check without fix to see if there are any issues
    dirs_with_slash = [f"{d}/" for d in dirs]
    check_success, _check_stdout, _check_stderr = run_command(
        ["ruff", "check", *dirs_with_slash],
        "Linting check (ruff)",
        allow_failure=True,
    )

    if not check_success:
        # There are linting issues, try to fix them
        print("\nLinting issues detected. Attempting auto-fix...")

        if aggressive:
            # Run with unsafe fixes
            fix_success, fix_stdout, _fix_stderr = run_command(
                [
                    "ruff",
                    "check",
                    *dirs_with_slash,
                    "--fix",
                    "--unsafe-fixes",
                ],
                "Aggressive linting auto-fix (with unsafe fixes)",
                allow_failure=True,
                auto_fix=True,
            )
        else:
            # Run with only safe fixes
            fix_success, fix_stdout, _fix_stderr = run_command(
                ["ruff", "check", *dirs_with_slash, "--fix"],
                "Linting auto-fix (safe fixes only)",
                allow_failure=True,
                auto_fix=True,
            )

        if not fix_success:
            # Count remaining errors
            error_match = re.search(r"Found (\d+) error", fix_stdout)
            if error_match:
                error_count = int(error_match.group(1))
            else:
                # Fallback: count lines with error codes
                error_count = len(
                    [
                        line
                        for line in fix_stdout.split("\n")
                        if re.match(r"^\S+\.py:\d+:\d+:", line)
                    ]
                )

            # If not in aggressive mode, check how many could be fixed with unsafe fixes
            unsafe_fixable_count = 0
            if not aggressive:
                unsafe_match = re.search(
                    r"(\d+) hidden fixes can be enabled with the `--unsafe-fixes` option",
                    fix_stdout,
                )
                if not unsafe_match:
                    unsafe_match = re.search(
                        r"(\d+) fixes available with `--unsafe-fixes`", fix_stdout
                    )
                if not unsafe_match:
                    unsafe_match = re.search(r"(\d+) fixable with the --fix option", fix_stdout)

                if unsafe_match:
                    unsafe_fixable_count = int(unsafe_match.group(1))

            # Format the result message
            if unsafe_fixable_count > 0 and not aggressive:
                details = (
                    f"{error_count} unfixable issues "
                    f"({unsafe_fixable_count} more fixable with --aggressive)"
                )
            else:
                details = f"{error_count} unfixable issues"

            return (False, [("Linting", "❌ FAILED", details)])
        # All issues were fixed
        message = (
            "All issues auto-fixed (aggressive mode)" if aggressive else "All issues auto-fixed"
        )
        return (True, [("Linting", "✅ FIXED", message)])
    # No issues found
    return (True, [("Linting", "✅ PASSED", "")])


def _check_formatting(dirs: list[str]) -> tuple[bool, list[tuple[str, str, str]]]:
    """Run code formatting checks with auto-fix capabilities.

    Args:
        dirs: List of directory paths to check

    Returns:
        Tuple of (all_passed_flag, check_results_list)
        where check_results_list contains tuples of (name, status, notes)

    Raises:
        None
    """
    print("\n" + "-" * 40)
    dirs_with_slash = [f"{d}/" for d in dirs]
    success, _, _ = run_command(
        ["ruff", "format", "--check", *dirs_with_slash],
        "Code formatting check (ruff format)",
        allow_failure=True,
    )

    if not success:
        print("\nCode formatting issues detected. Running auto-fix...")
        run_command(
            ["ruff", "format", *dirs_with_slash],
            "Code formatting",
            auto_fix=True,
        )
        return (True, [("Code Formatting", "✅ FIXED", "Auto-formatted")])
    return (True, [("Code Formatting", "✅ PASSED", "")])


def _generate_summary(check_results: list[tuple[str, str, str]]) -> None:
    """Print summary table of all health check results.

    Args:
        check_results: List of check results, each containing (name, status, details)

    Returns:
        None

    Raises:
        None
    """
    print("\n" + "=" * 60)
    print("HEALTH CHECK SUMMARY")
    print("=" * 60)
    print(f"{'Check':<20} {'Status':<15} {'Details':<25}")
    print("-" * 60)

    for check_name, status, details in check_results:
        print(f"{check_name:<20} {status:<15} {details:<25}")

    print("=" * 60)


def _parse_arguments_and_setup() -> tuple[argparse.Namespace, list[str]]:
    """Parse command-line arguments and load configuration.

    Args:
        None

    Returns:
        Tuple of (parsed_arguments, check_directories)

    Raises:
        SystemExit: If --commands flag is set (exits after displaying commands)
    """
    parser = argparse.ArgumentParser(
        description="Health Check Script - Run code quality checks on your project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/health_check.py
  python scripts/health_check.py --aggressive
  python scripts/health_check.py --commands

Directories are read from pyproject.toml [tool.wsd] configuration.
Requires [tool.wsd] section with check_dirs defined.
        """,
    )
    parser.add_argument(
        "--aggressive",
        action="store_true",
        help="Enable unsafe fixes during linting",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clear type checker cache before running checks for fresh analysis",
    )
    parser.add_argument(
        "--commands",
        action="store_true",
        help="Show all commands used by each check",
    )

    args = parser.parse_args()

    # Early validation: Check for pyproject.toml existence
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        print(
            "This is a Python health check script. "
            "No pyproject.toml found. For Node.js projects, use health_check.js."
        )
        sys.exit(1)

    dirs = get_check_dirs()

    # Check for --commands flag
    if args.commands:
        if not dirs:
            print("Note: No check_dirs configured. Commands shown are for reference only.")
            print(
                "Configure [tool.wsd].check_dirs in pyproject.toml to enable code quality checks."
            )
            dirs = ["<source_dir>"]  # Placeholder for command display
        show_commands(dirs)
        sys.exit(0)

    print("=" * 60)
    print("Starting Health Check...")
    if dirs:
        print(f"Checking directories: {' '.join(dirs)}")
    else:
        print("Note: No check_dirs configured. Directory-dependent checks will be skipped.")
    if args.aggressive:
        print("Running in AGGRESSIVE mode (unsafe fixes enabled)")
    else:
        print("Running in SAFE mode (use --aggressive for more fixes)")
    print("=" * 60)

    return args, dirs


def main() -> None:
    """Run all health checks for the project."""
    args, dirs = _parse_arguments_and_setup()

    # Check dependencies
    check_dependencies()

    # Track overall success and individual results
    all_passed = True
    check_results: list[tuple[str, str, str]] = []

    # Determine if directory-dependent checks should run
    dirs_configured = len(dirs) > 0

    # 1. Build/Package Check
    build_passed, build_results = _validate_build()
    if not build_passed:
        all_passed = False
    check_results.extend(build_results)

    # 2. Type Checking - requires check_dirs
    if dirs_configured:
        type_check_passed, type_check_results = _check_types_with_mypy(dirs, clean=args.clean)
        if not type_check_passed:
            all_passed = False
        check_results.extend(type_check_results)
    else:
        check_results.append(("Type Checking", "⏭️  SKIPPED", "no check_dirs configured"))

    # 3. Security Scanning - requires check_dirs
    if dirs_configured:
        security_passed, security_results = _scan_security(dirs)
        if not security_passed:
            all_passed = False
        check_results.extend(security_results)
    else:
        check_results.append(("Security Scan", "⏭️  SKIPPED", "no check_dirs configured"))

    # 4. Dependency Security Audit
    audit_passed, audit_results = _run_dependency_audit()
    if not audit_passed:
        all_passed = False
    check_results.extend(audit_results)

    # 5. Documentation Completeness Check - requires check_dirs
    if dirs_configured:
        docs_passed, docs_results = _check_documentation(dirs)
        if not docs_passed:
            all_passed = False
        check_results.extend(docs_results)
    else:
        check_results.append(("Doc Completeness", "⏭️  SKIPPED", "no check_dirs configured"))

    # 6. Linting Check with auto-fix - requires check_dirs
    if dirs_configured:
        lint_passed, lint_results = _check_linting(dirs, args.aggressive)
        if not lint_passed:
            all_passed = False
        check_results.extend(lint_results)
    else:
        check_results.append(("Linting", "⏭️  SKIPPED", "no check_dirs configured"))

    # 7. Code Formatting Check - requires check_dirs
    if dirs_configured:
        format_passed, format_results = _check_formatting(dirs)
        if not format_passed:
            all_passed = False
        check_results.extend(format_results)
    else:
        check_results.append(("Code Formatting", "⏭️  SKIPPED", "no check_dirs configured"))

    # Print summary table
    _generate_summary(check_results)

    # Final summary
    if all_passed:
        print("\n✅ Project Health Check completed successfully!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n❌ Project Health Check found issues that need attention.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nHealth check interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error during health check: {e}")
        sys.exit(1)
