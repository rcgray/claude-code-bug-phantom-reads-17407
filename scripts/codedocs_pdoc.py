"""Generate Python API documentation using pdoc.

This script generates comprehensive HTML documentation using pdoc with support
for both traditional packages and script collections (hybrid mode). The mode is
automatically selected based on project structure, aligning with the directory-based
approach used by the TypeScript and JavaScript documentation generators.

Hybrid Mode Operation:
    Package Mode:
        - Activated when [project].name exists AND matching package directory found
        - Uses module discovery to find all Python modules within the package
        - Generates documentation with full package hierarchy and cross-references
        - Ideal for traditional Python packages with __init__.py files

    File Mode:
        - Activated when no package structure exists (name missing or directory not found)
        - Uses collect_python_files() from wsd_utils.py to find all .py files
        - Documents individual Python files directly via pdoc
        - Ideal for script collections without formal package structure

Mode Selection Logic:
    use_package_mode = package_name is not None and (source_dir / package_name).exists()

Configuration (read from pyproject.toml):
    - Package name: [project].name (optional - enables package mode if present)
    - Source directories: [tool.wsd].check_dirs
    - Output directory: dev/reports/pydoc-api-docs/ (hardcoded)

Example Output Messages:
    - Package mode: "Generating Python API documentation (package mode: 'mypackage')..."
    - File mode: "Generating Python API documentation (file mode)..."
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


# Add scripts directory to path for wsd_utils import
_scripts_dir = Path(__file__).parent
sys.path.insert(0, str(_scripts_dir))
from wsd_utils import collect_python_files, get_check_dirs, is_tool_available  # noqa: E402


def read_pyproject_config(project_root: Path, check_dirs: list[str]) -> tuple[str | None, str]:
    """Read configuration from pyproject.toml.

    Reads package name from [project].name if available. The source directory
    is taken from the first entry in check_dirs (already validated by caller).

    The package name is optional - if not present, the caller should use file
    mode instead of package mode for documentation generation.

    Args:
        project_root: Path to the project root directory containing pyproject.toml
        check_dirs: List of configured check directories (must not be empty)

    Returns:
        Tuple of (package_name, source_dir) where package_name may be None
        if [project].name is not configured.

    Raises:
        SystemExit: If pyproject.toml is missing or malformed
    """
    try:
        import tomllib  # type: ignore[import-not-found]  # noqa: PLC0415
    except ModuleNotFoundError:
        import tomli as tomllib  # noqa: PLC0415

    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        print("Error: pyproject.toml not found in project root.", file=sys.stderr)
        print(
            "\nThis script requires pyproject.toml with [tool.wsd].check_dirs configuration.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        with pyproject_path.open("rb") as f:
            config = tomllib.load(f)
    except Exception as e:
        print(f"Error: Failed to parse pyproject.toml: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract package name from [project].name (optional)
    project_config = config.get("project", {})
    package_name = project_config.get("name")

    source_dir = check_dirs[0]

    return package_name, source_dir


def run_command(
    cmd: list[str],
    capture_output: bool = False,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    """Run a command and return its results.

    Args:
        cmd: Command and arguments to run
        capture_output: Whether to capture command output
        cwd: Working directory for the command
        env: Environment variables for the command

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


def discover_python_modules(src_path: Path, package_name: str) -> list[str]:
    """Automatically discover all Python modules in a package.

    This function performs a recursive directory scan to find all documentable
    Python modules within a package. It handles both regular .py files and
    __init__.py files, converting filesystem paths to Python module notation.

    The algorithm:
    1. Start with the package root as the first module
    2. Recursively scan for all .py files using rglob
    3. Filter out non-documentable files (tests, cache, data, entry points)
    4. Convert each file path to dot-notation module name
    5. Handle __init__.py specially (represents parent directory as module)
    6. Deduplicate and sort for consistent output

    Args:
        src_path: Path to the source directory containing the package
        package_name: Name of the Python package to document

    Returns:
        List of module names in dot notation (e.g., 'mypackage.cli')
    """
    modules: list[str] = []
    package_path = src_path / package_name

    if not package_path.exists():
        print(f"Error: Package path {package_path} does not exist")
        return modules

    # Start with the main package itself as the first module entry
    # This ensures the package root is always documented
    modules.append(package_name)

    # Recursively find all Python files in the package tree
    for py_file in package_path.rglob("*.py"):
        # Apply exclusion filters to skip non-documentable files:
        # - __pycache__: Bytecode cache directories (not source)
        # - /data/: Data directories containing non-library files
        # - test_*.py: Test files following pytest naming convention
        # - *_test.py: Test files following alternative convention
        path_str = str(py_file)
        if (
            "__pycache__" in path_str
            or "/data/" in path_str
            or "test_" in py_file.name
            or "_test.py" in py_file.name
        ):
            continue

        # Compute path relative to package root for module name conversion
        rel_path = py_file.relative_to(package_path)

        # Convert filesystem path to Python module notation (dots instead of slashes)
        if rel_path.name == "__init__.py":
            # __init__.py represents its parent directory as a module
            # e.g., mypackage/utils/__init__.py -> mypackage.utils
            # Skip if it's the root __init__.py (already added as package_name)
            if rel_path.parent != Path():
                module_name = f"{package_name}." + str(rel_path.parent).replace(os.sep, ".")
                # Deduplicate: subpackages may be discovered via __init__.py and other files
                if module_name not in modules:
                    modules.append(module_name)
        else:
            # Regular .py files: strip .py extension and convert path separators
            # e.g., mypackage/cli/commands.py -> mypackage.cli.commands
            module_name = f"{package_name}." + str(rel_path).replace(os.sep, ".")[:-3]
            # Exclude __main__.py files - these are entry point scripts, not API modules
            if not module_name.endswith(".__main__"):
                modules.append(module_name)

    # Sort alphabetically for deterministic output across runs
    modules.sort()
    return modules


def _prepare_package_mode(source_dir: Path, package_name: str) -> tuple[list[str], dict[str, str]]:
    """Prepare documentation targets for package mode.

    Args:
        source_dir: Directory containing the package source code
        package_name: Name of the Python package to document

    Returns:
        Tuple of (doc_targets, env) where doc_targets is a list of module names
        and env is the environment with PYTHONPATH set.
    """
    print(f"\nGenerating Python API documentation (package mode: '{package_name}')...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(source_dir)

    modules = discover_python_modules(source_dir, package_name)
    print(f"Discovered {len(modules)} modules to document")

    if os.environ.get("DEBUG_DOCS"):
        print("Modules to document:")
        for module in modules:
            print(f"  - {module}")

    return modules, env


def _prepare_file_mode(
    check_dirs: list[str], project_root: Path
) -> tuple[list[str], dict[str, str]] | None:
    """Prepare documentation targets for file mode.

    Args:
        check_dirs: List of directories to check for Python files
        project_root: Root directory of the project

    Returns:
        Tuple of (doc_targets, env) where doc_targets is a list of file paths,
        or None if no Python files were found.
    """
    print("\nGenerating Python API documentation (file mode)...")
    python_files = collect_python_files(check_dirs, project_root)

    if not python_files:
        print("No Python files found to document.")
        return None

    print(f"Discovered {len(python_files)} Python files to document")

    if os.environ.get("DEBUG_DOCS"):
        print("Files to document:")
        for py_file in python_files:
            print(f"  - {py_file}")

    return [str(f) for f in python_files], os.environ.copy()


def generate_python_api_docs(
    check_dirs: list[str],
    output_dir: Path,
    project_root: Path,
    package_name: str | None = None,
) -> bool:
    """Generate Python API documentation using pdoc.

    Supports two modes of operation:
    - Package mode: If package_name is provided and the package directory exists,
      uses module discovery to document the package structure.
    - File mode: If package_name is None or the package doesn't exist, documents
      individual Python files found in check_dirs using collect_python_files().

    Args:
        check_dirs: List of directories to check for Python files (relative to project_root)
        output_dir: Directory where documentation should be generated
        project_root: Root directory of the project
        package_name: Optional name of the Python package. If None, uses file mode.

    Returns:
        True if documentation generated successfully, False otherwise
    """
    if not is_tool_available("pdoc"):
        print("Error: pdoc is not installed.", file=sys.stderr)
        print("", file=sys.stderr)
        print("To fix this issue, install pdoc as a dev dependency:", file=sys.stderr)
        print("  uv add --dev pdoc", file=sys.stderr)
        sys.exit(1)

    # Handle empty check_dirs - skip gracefully
    if not check_dirs:
        print("No Python files found to document.")
        return True

    # Determine source directory from first check_dir
    source_dir = project_root / check_dirs[0]

    # Determine which mode to use and prepare targets
    use_package_mode = package_name is not None and (source_dir / package_name).exists()

    if use_package_mode:
        doc_targets, env = _prepare_package_mode(source_dir, package_name)  # type: ignore[arg-type]
    else:
        result = _prepare_file_mode(check_dirs, project_root)
        if result is None:
            return True
        doc_targets, env = result

    # Prepare output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # Run pdoc
    cmd = [
        "uv",
        "run",
        "pdoc",
        "-o",
        str(output_dir),
        "-d",
        "google",
        "--search",
        "--show-source",
        *doc_targets,
    ]

    print(f"Generating API documentation to: {output_dir.relative_to(project_root)}")
    returncode, stdout, stderr = run_command(cmd, capture_output=True, cwd=project_root, env=env)

    if stdout:
        print(f"pdoc output:\n{stdout.strip()}")
    if stderr and returncode != 0:
        print(f"pdoc errors:\n{stderr.strip()}")

    if returncode == 0:
        print(
            f"API documentation generated successfully at: {output_dir.relative_to(project_root)}"
        )
        return True
    print(f"API documentation generation FAILED (return code: {returncode}).")
    return False


def main() -> None:
    """Generate Python API documentation using pdoc.

    Reads configuration from pyproject.toml and generates HTML documentation
    using hybrid mode (package mode if package exists, file mode otherwise).
    """
    # Check for configured source directories first
    check_dirs = get_check_dirs()
    if not check_dirs:
        print("Skipping pdoc documentation: no source directories configured.")
        return

    # Resolve paths relative to project root
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Read configuration from pyproject.toml
    package_name, source_dir_name = read_pyproject_config(project_root, check_dirs)

    # Build paths
    source_dir = project_root / source_dir_name
    output_dir = project_root / "dev" / "reports" / "pydoc-api-docs"

    # Validate source directory exists
    if not source_dir.exists():
        print(f"Error: Source directory '{source_dir_name}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Pass to generate_python_api_docs which handles package vs file mode
    success = generate_python_api_docs(
        check_dirs=check_dirs,
        output_dir=output_dir,
        project_root=project_root,
        package_name=package_name,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
