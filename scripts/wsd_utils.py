"""WSD utility functions for language detection, configuration, and file operations.

Provides centralized utility functions for detecting project language type
based on actual source file presence rather than configuration files alone.
These functions are used by wsd.py and other WSD tools to adapt their
behavior appropriately for each project type.

Public Functions:
    calculate_file_hash: Calculate SHA-256 content hash for a file
    get_check_dirs: Read configured check directories from pyproject.toml (for Python)
    get_node_check_dirs: Read configured check directories from package.json (for Node.js)
    has_typescript_files: Scan directories for .ts files
    collect_python_files: Collect all documentable Python files from check directories
    detect_project_languages: Detect all programming languages present in a project
    detect_package_manager: Detect which Node.js package manager is in use
    is_tool_available: Check if a Python package is available for import
    is_script_available: Check if a script is defined in package.json
    collect_wsd_files: Validate and collect WSD Runtime files from a directory

Public Classes:
    WsdCollectionError: Exception raised when WSD file collection encounters invalid content

Internal Functions (private):
    _find_package_json_root: Find directory containing package.json for Node.js detection
    _find_python_project_root: Find directory containing pyproject.toml for Python detection
    _is_python_project: Determine if project is Python vs just having WSD installed
    _detect_node_language: Determine if project is TypeScript or JavaScript
    _is_binary_file: Detect if file is binary (not text)
    _parse_wsdignore: Parse .wsdignore file and return list of patterns
    _is_safe_filename: Check if filename contains only safe characters
"""

import fnmatch
import hashlib
import json
import re
import sys
from pathlib import Path


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 content hash for a file.

    Reads the file in binary mode for cross-platform consistency and returns
    the hash in a prefixed format suitable for storage in wsd.json.

    Args:
        file_path: Absolute or relative path to the file to hash.

    Returns:
        Hash string in format 'sha256:<64_lowercase_hex_chars>'.

    Raises:
        FileNotFoundError: If file_path does not exist.
        IOError: If file cannot be read.
    """
    hasher = hashlib.sha256()

    with file_path.open("rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)

    return f"sha256:{hasher.hexdigest()}"


def get_check_dirs(project_root: Path | None = None) -> list[str]:
    """Read check directories from pyproject.toml [tool.wsd].check_dirs configuration.

    Reads the configured directories that WSD tools should check for source files.
    This is the primary function for Python scripts to retrieve directory configuration.

    The function searches for pyproject.toml starting from the current working directory
    (or provided project_root) and walking up the directory tree. If found, it reads
    the [tool.wsd].check_dirs configuration. If the configuration is missing or not
    found, returns an empty list.

    Args:
        project_root: Root directory of the project. If None, searches from
            current working directory up the tree for pyproject.toml.

    Returns:
        List of directory paths relative to project root, or empty list if not configured.
    """
    # Import tomllib conditionally for Python 3.10 compatibility
    try:
        import tomllib  # type: ignore[import-not-found]  # noqa: PLC0415
    except ModuleNotFoundError:
        import tomli as tomllib  # noqa: PLC0415

    # Find project root by searching for pyproject.toml
    pyproject_path: Path | None = None
    if project_root is not None:
        candidate = project_root / "pyproject.toml"
        if candidate.exists():
            pyproject_path = candidate
    else:
        current_dir = Path.cwd()
        while current_dir != current_dir.parent:
            candidate = current_dir / "pyproject.toml"
            if candidate.exists():
                pyproject_path = candidate
                break
            current_dir = current_dir.parent

    if pyproject_path is None:
        print(
            "Note: [tool.wsd].check_dirs not configured. Code quality tools will be skipped.",
            file=sys.stderr,
        )
        return []

    try:
        with pyproject_path.open("rb") as f:
            config = tomllib.load(f)
    except Exception as e:
        print(f"Warning: Failed to parse pyproject.toml: {e}", file=sys.stderr)
        return []

    wsd_config = config.get("tool", {}).get("wsd", {})
    check_dirs = wsd_config.get("check_dirs")

    if check_dirs is None:
        print(
            "Note: [tool.wsd].check_dirs not configured. Code quality tools will be skipped.",
            file=sys.stderr,
        )
        return []

    if not isinstance(check_dirs, list):
        print(
            "Warning: [tool.wsd].check_dirs must be a list in pyproject.toml.",
            file=sys.stderr,
        )
        return []

    # Filter and validate entries
    valid_dirs = [str(d) for d in check_dirs if isinstance(d, str)]
    if not valid_dirs:
        print(
            "Note: [tool.wsd].check_dirs not configured. Code quality tools will be skipped.",
            file=sys.stderr,
        )
        return []

    return valid_dirs


def _print_node_config_help() -> None:
    """Print helpful configuration message for Node.js projects."""
    print(
        "Note: wsd.checkDirs not configured in package.json.",
        file=sys.stderr,
    )
    print(
        "Add this to your package.json:",
        file=sys.stderr,
    )
    print(
        '  "wsd": { "checkDirs": ["src", "tests"] }',
        file=sys.stderr,
    )


def get_node_check_dirs(project_root: Path | None = None) -> list[str]:
    """Read check directories from package.json wsd.checkDirs configuration.

    Reads the configured directories that WSD tools should check for source files
    in Node.js (TypeScript/JavaScript) projects. This is the Node.js equivalent
    of get_check_dirs() for Python projects.

    The function searches for package.json starting from the current working directory
    (or provided project_root) and walking up the directory tree. If found, it reads
    the wsd.checkDirs configuration. If the configuration is missing or not found,
    returns an empty list.

    Args:
        project_root: Root directory of the project. If None, searches from
            current working directory up the tree for package.json.

    Returns:
        List of directory paths relative to project root, or empty list if not configured.
    """
    # Find project root by searching for package.json
    package_json_path: Path | None = None
    if project_root is not None:
        candidate = project_root / "package.json"
        if candidate.exists():
            package_json_path = candidate
    else:
        search_root = _find_package_json_root()
        candidate = search_root / "package.json"
        if candidate.exists():
            package_json_path = candidate

    if package_json_path is None:
        print(
            "Note: wsd.checkDirs not configured. Code quality tools will be skipped.",
            file=sys.stderr,
        )
        return []

    # Try to parse package.json
    try:
        with package_json_path.open(encoding="utf-8") as f:
            package_json = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: Failed to read/parse package.json: {e}", file=sys.stderr)
        return []

    # Validate wsd config structure and extract checkDirs
    wsd_config = package_json.get("wsd", {})
    if not isinstance(wsd_config, dict):
        print(
            "Warning: wsd field in package.json must be an object.",
            file=sys.stderr,
        )
        return []

    check_dirs = wsd_config.get("checkDirs")
    if check_dirs is None:
        _print_node_config_help()
        return []

    if not isinstance(check_dirs, list):
        print(
            "Warning: wsd.checkDirs must be an array in package.json.",
            file=sys.stderr,
        )
        return []

    # Filter and validate entries - return valid strings or empty list with help
    valid_dirs = [str(d) for d in check_dirs if isinstance(d, str)]
    if not valid_dirs:
        _print_node_config_help()
    return valid_dirs


def _find_package_json_root() -> Path:
    """Find the directory containing package.json for Node.js language detection.

    Internal helper function used by Node.js detection functions to locate
    the package.json file. Walks up the directory tree from the current
    working directory until it finds a directory containing package.json.

    This function specifically searches for package.json, not the general
    project root (which could be indicated by pyproject.toml for Python).

    Returns:
        Path to directory containing package.json, or current directory if not found.
    """
    current_dir = Path.cwd()
    while current_dir != current_dir.parent:
        if (current_dir / "package.json").exists():
            return current_dir
        current_dir = current_dir.parent
    # Fallback: return current working directory
    return Path.cwd()


def _has_files_with_extension(directory: Path, extension: str, exclude_dirs: set[str]) -> bool:
    """Recursively scan a directory for files matching an extension.

    Args:
        directory: Directory path to scan (absolute path).
        extension: File extension to match (e.g., '.ts').
        exclude_dirs: Set of directory names to exclude from scanning.

    Returns:
        True if any matching files found, False otherwise.
    """
    if not directory.exists():
        return False

    try:
        for entry in directory.iterdir():
            if entry.is_dir():
                if entry.name in exclude_dirs:
                    continue
                if _has_files_with_extension(entry, extension, exclude_dirs):
                    return True
            elif entry.is_file() and entry.name.endswith(extension):
                return True
    except OSError:
        return False

    return False


def has_typescript_files(check_dirs: list[str]) -> bool:
    """Scan directories for TypeScript files (.ts).

    Recursively scans the provided directories looking for any .ts files.
    Excludes node_modules/ and dist/ directories from scanning.
    Type declaration files (.d.ts) are included in the scan.

    Args:
        check_dirs: Directories to scan (relative to project root).

    Returns:
        True if any .ts files found, False otherwise.
    """
    project_root = _find_package_json_root()
    exclude_dirs = {"node_modules", "dist"}

    for dir_name in check_dirs:
        full_path = project_root / dir_name
        if _has_files_with_extension(full_path, ".ts", exclude_dirs):
            return True

    return False


def collect_python_files(
    check_dirs: list[str],
    project_root: Path | None = None,
) -> list[Path]:
    """Collect all documentable Python files from check directories.

    Recursively searches each directory in check_dirs for .py files,
    filtering out non-documentable files like __pycache__, test files,
    and build artifacts. This function is the Python equivalent of the
    directory-based pattern used in codedocs_typedoc.js and codedocs_jsdoc.js.

    Args:
        check_dirs: List of directory paths to search (relative to project root).
        project_root: Optional explicit project root. If None, searches from
            current working directory up the tree for pyproject.toml.

    Returns:
        List of Path objects for all documentable Python files found, sorted
        alphabetically by path for deterministic ordering.
    """
    if project_root is None:
        project_root = _find_python_project_root()

    # Directories to exclude from scanning
    exclude_dirs = {
        "__pycache__",
        ".eggs",
        "dist",
        "build",
        "node_modules",
        ".git",
        ".venv",
        "venv",
        "env",
    }

    # File patterns to exclude (test files)
    def _is_test_file(file_path: Path) -> bool:
        """Check if a file is a test file based on naming conventions."""
        name = file_path.name
        # Exclude test_*.py and *_test.py patterns
        if name.startswith("test_") or name.endswith("_test.py"):
            return True
        # Exclude conftest.py (pytest configuration)
        return name == "conftest.py"

    def _is_in_excluded_dir(file_path: Path) -> bool:
        """Check if a file is in an excluded directory."""
        for part in file_path.parts:
            if part in exclude_dirs:
                return True
            # Exclude .egg-info directories
            if part.endswith(".egg-info"):
                return True
        return False

    def _is_in_test_directory(file_path: Path, base_dir: Path) -> bool:
        """Check if a file is in a test directory."""
        # Get the relative path from base_dir
        try:
            rel_path = file_path.relative_to(base_dir)
        except ValueError:
            return False
        # Check if any parent directory is named 'test' or 'tests'
        return any(part in ("test", "tests") for part in rel_path.parts[:-1])

    python_files: list[Path] = []

    for dir_name in check_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            continue

        for py_file in dir_path.rglob("*.py"):
            # Skip if in excluded directory
            if _is_in_excluded_dir(py_file):
                continue
            # Skip test files
            if _is_test_file(py_file):
                continue
            # Skip files in test directories
            if _is_in_test_directory(py_file, dir_path):
                continue
            python_files.append(py_file)

    # Sort for deterministic ordering
    return sorted(python_files)


def _find_python_project_root() -> Path:
    """Find the directory containing pyproject.toml for Python project detection.

    Internal helper function used by Python detection functions to locate
    the pyproject.toml file. Walks up the directory tree from the current
    working directory until it finds a directory containing pyproject.toml.

    Returns:
        Path to directory containing pyproject.toml, or current directory if not found.
    """
    current_dir = Path.cwd()
    while current_dir != current_dir.parent:
        if (current_dir / "pyproject.toml").exists():
            return current_dir
        current_dir = current_dir.parent
    # Fallback: return current working directory
    return Path.cwd()


def _detect_node_language(project_root: Path | None = None) -> str | None:
    """Detect whether the project is TypeScript or JavaScript.

    Internal helper function - use detect_project_languages() for public API.

    Determines the project's language type based on the presence of .ts files
    in the configured check directories from package.json wsd.checkDirs.

    If wsd.checkDirs is not configured, no directories are scanned and the
    project defaults to JavaScript (no .ts files found in empty directory set).

    A project is classified as TypeScript if ANY .ts files exist in the check
    directories. Otherwise, it is classified as JavaScript.

    Args:
        project_root: Root directory of the project. If None, uses _find_package_json_root()
            to locate the directory containing package.json.

    Returns:
        'typescript', 'javascript', or None if no package.json exists.
    """
    if project_root is None:
        project_root = _find_package_json_root()
    package_json_path = project_root / "package.json"

    if not package_json_path.exists():
        return None

    # Try to read wsd.checkDirs from package.json
    check_dirs: list[str] = []
    try:
        with package_json_path.open(encoding="utf-8") as f:
            package_json = json.load(f)
        wsd_config: dict[str, object] = package_json.get("wsd", {})
        configured_dirs = wsd_config.get("checkDirs", [])
        if isinstance(configured_dirs, list):
            check_dirs = [str(d) for d in configured_dirs if isinstance(d, str)]
    except (json.JSONDecodeError, OSError):
        pass

    # Scan for TypeScript files in configured directories only
    if has_typescript_files(check_dirs):
        return "typescript"

    return "javascript"


def _is_python_project(project_root: Path | None = None) -> bool:
    """Determine if this is a Python project vs just having WSD installed.

    Internal helper function - use detect_project_languages() for public API.

    A project is considered a Python project if:
    1. pyproject.toml has a [project] section (PEP 621 metadata), OR
    2. There are .py files in the configured check_dirs

    The mere presence of pyproject.toml does NOT make it a Python project,
    since WSD requires pyproject.toml for its own dependencies.

    Args:
        project_root: Root directory of the project. If None, searches from
            current working directory up the tree for pyproject.toml.

    Returns:
        True if this is a Python project, False otherwise.
    """
    # Import tomllib conditionally for Python 3.10 compatibility
    # Note: type ignore includes unused-ignore for mypy quirk with duplicate imports
    try:
        import tomllib  # type: ignore[import-not-found,unused-ignore]  # noqa: PLC0415
    except ModuleNotFoundError:
        import tomli as tomllib  # noqa: PLC0415

    # Find project root by searching for pyproject.toml
    if project_root is None:
        current_dir = Path.cwd()
        while current_dir != current_dir.parent:
            if (current_dir / "pyproject.toml").exists():
                project_root = current_dir
                break
            current_dir = current_dir.parent

    if project_root is None:
        return False

    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        return False

    try:
        with pyproject_path.open("rb") as f:
            pyproject = tomllib.load(f)
    except Exception:
        return False

    # Check 1: Has [project] section = actual Python project (PEP 621)
    if "project" in pyproject:
        return True

    # Check 2: Has Python source files in check_dirs
    check_dirs = pyproject.get("tool", {}).get("wsd", {}).get("check_dirs", [])
    for dir_name in check_dirs:
        dir_path = project_root / dir_name
        # Check for any .py files (not exhaustive, just existence check)
        if dir_path.exists() and any(dir_path.rglob("*.py")):
            return True

    return False


def detect_project_languages(project_root: Path | None = None) -> set[str]:
    """Detect all programming languages present in the project.

    Returns set of detected languages: {"python", "typescript", "javascript"}
    Returns empty set for codeless projects.

    Detection logic:
    - Python: Has [project] section in pyproject.toml OR .py files in check_dirs
    - TypeScript: Has .ts files in configured check directories
    - JavaScript: Has package.json but no .ts files in check directories

    Args:
        project_root: Root directory of the project. If None, searches from
            current working directory up the tree for configuration files.

    Returns:
        Set of detected language identifiers, empty set if codeless project.
    """
    languages: set[str] = set()

    # Use _is_python_project() to distinguish actual Python projects from
    # projects that just have pyproject.toml for WSD dependencies
    if _is_python_project(project_root):
        languages.add("python")

    # Use file-based detection to distinguish TypeScript from JavaScript
    node_language = _detect_node_language(project_root)
    if node_language is not None:
        languages.add(node_language)

    return languages


def detect_package_manager() -> str | None:
    """Detect which Node.js package manager is in use.

    Checks for lock files in this order:
    1. pnpm-lock.yaml → pnpm
    2. package-lock.json → npm
    3. yarn.lock → yarn
    4. bun.lockb → bun

    Returns:
        Package manager command ("pnpm", "npm", "yarn", or "bun"),
        or None if no lock file is found.
    """
    project_root = _find_package_json_root()

    if (project_root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (project_root / "package-lock.json").exists():
        return "npm"
    if (project_root / "yarn.lock").exists():
        return "yarn"
    if (project_root / "bun.lockb").exists():
        return "bun"

    return None


def is_tool_available(package_name: str) -> bool:
    """Check if a Python package is available for import.

    Determines whether a package can be imported in the current Python
    environment. This is the Python equivalent of isToolAvailable() in
    wsd_utils.js, enabling consistent tool availability checking across
    both ecosystems.

    Args:
        package_name: Name of the package to check (e.g., 'pdoc', 'sphinx').

    Returns:
        True if the package can be imported, False otherwise.
    """
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


def is_script_available(script_name: str) -> bool:
    """Check if a script is defined in the project's package.json.

    Examines the scripts section of package.json to determine if a specific
    script name is available for execution via the package manager.

    Args:
        script_name: Name of the script to check (e.g., 'build', 'test', 'typedoc').

    Returns:
        True if the script exists in package.json scripts, False otherwise.

    Remarks:
        Returns False if package.json doesn't exist or cannot be parsed.
    """
    package_json_path = _find_package_json_root() / "package.json"

    if not package_json_path.exists():
        return False

    try:
        with package_json_path.open(encoding="utf-8") as f:
            package_json = json.load(f)
        return bool(package_json.get("scripts", {}).get(script_name))
    except Exception:
        return False


# ==============================================================================
# WSD FILE COLLECTION
# ==============================================================================

# VCS directories that are silently skipped during file collection.
# These directories contain version control metadata and are never part of
# the WSD Runtime distribution.
VCS_DIRECTORIES: set[str] = {".git", ".svn", ".hg", ".bzr", "CVS"}

# Suspicious directory patterns that indicate build artifacts or development
# pollution that should never exist in WSD Runtime directories.
SUSPICIOUS_DIRECTORY_PATTERNS: set[str] = {
    "node_modules",
    "dist",
    "build",
}

# Suspicious directory suffix patterns that indicate build artifacts.
SUSPICIOUS_DIRECTORY_SUFFIXES: tuple[str, ...] = (".egg-info",)

# Suspicious file patterns that indicate OS artifacts, editor artifacts,
# or development pollution that should never exist in WSD Runtime directories.
# These use glob-style matching against the filename.
SUSPICIOUS_FILE_PATTERNS: tuple[str, ...] = (
    ".DS_Store",
    "desktop.ini",
    "Thumbs.db",
    "*~",
    ".*.swp",
    ".*.swo",
    "*.pyc",
    "*.pyo",
    "package-lock.json",
    ".package-lock.json",
)

# Pattern for detecting special characters in filenames that could cause
# cross-platform issues. Allows: alphanumeric, dash, underscore, dot.
SAFE_FILENAME_PATTERN: re.Pattern[str] = re.compile(r"^[a-zA-Z0-9._-]+$")


class WsdCollectionError(Exception):
    """Exception raised when WSD file collection encounters invalid content.

    This exception indicates a structural violation or safeguard failure in
    the WSD Runtime directory. Unlike items that are silently skipped (VCS
    directories, .wsdignore matches), these conditions should never occur
    and indicate a problem that needs to be resolved.

    Attributes:
        message: Description of the error.
        path: Path that caused the error.
    """

    def __init__(self, message: str, path: Path) -> None:
        """Initialize the collection error.

        Args:
            message: Description of the error.
            path: Path that caused the error.
        """
        self.message = message
        self.path = path
        super().__init__(f"{message}: {path}")


def _is_binary_file(path: Path) -> bool:
    """Detect if file is binary (not text).

    Uses heuristic approach: reads first 8KB of file and checks for null bytes
    or high proportion of non-text characters. WSD Runtime files should be
    text-only, so binary files indicate invalid content.

    Args:
        path: File path to check.

    Returns:
        True if file appears to be binary, False if appears to be text.
    """
    try:
        # Read first 8KB for detection
        chunk_size = 8192
        with path.open("rb") as f:
            chunk = f.read(chunk_size)

        if not chunk:
            # Empty file treated as text
            return False

        # Check for null bytes (strong binary indicator)
        if b"\x00" in chunk:
            return True

        # Count non-text bytes
        # Text files should be mostly printable ASCII + common whitespace
        text_chars = bytes(range(32, 127)) + b"\n\r\t\b"
        non_text_count = sum(1 for byte in chunk if byte not in text_chars)

        # If more than 30% non-text characters, likely binary
        return non_text_count / len(chunk) > 0.30

    except (OSError, UnicodeDecodeError):
        # If we can't read it, assume binary
        return True


def _parse_wsdignore(directory: Path) -> list[str]:
    """Parse .wsdignore file and return list of patterns to skip.

    The .wsdignore file lists files that legitimately exist in a WSD Runtime
    directory but should not be included in file collection. Each line
    contains a file path relative to the directory root.

    Args:
        directory: Root directory containing .wsdignore.

    Returns:
        List of file paths to ignore (relative to directory). Returns empty
        list if .wsdignore does not exist.
    """
    wsdignore_path = directory / ".wsdignore"

    if not wsdignore_path.exists():
        return []

    entries: list[str] = []
    try:
        with wsdignore_path.open(encoding="utf-8") as f:
            for raw_line in f:
                # Strip whitespace
                line = raw_line.strip()
                # Skip empty lines
                if not line:
                    continue
                # Skip comments
                if line.startswith("#"):
                    continue
                entries.append(line)
    except OSError:
        # If we can't read .wsdignore, treat as empty
        return []

    return entries


def _is_safe_filename(filename: str) -> bool:
    """Check if filename contains only safe characters.

    Safe filenames contain only alphanumeric characters, dashes, underscores,
    and dots. This ensures cross-platform compatibility and prevents issues
    with special characters in file paths.

    Args:
        filename: Filename to check (not full path, just the name).

    Returns:
        True if filename is safe, False if it contains unsafe characters.
    """
    return bool(SAFE_FILENAME_PATTERN.match(filename))


def _is_suspicious_directory(dirname: str) -> bool:
    """Check if a directory name matches suspicious patterns.

    Suspicious directories are development artifacts that should never exist
    in WSD Runtime directories.

    Args:
        dirname: Name of the directory (not full path, just the name).

    Returns:
        True if directory matches suspicious patterns, False otherwise.
    """
    if dirname in SUSPICIOUS_DIRECTORY_PATTERNS:
        return True
    return any(dirname.endswith(suffix) for suffix in SUSPICIOUS_DIRECTORY_SUFFIXES)


def _is_suspicious_file(filename: str) -> bool:
    """Check if a filename matches suspicious file patterns.

    Suspicious files are OS artifacts, editor artifacts, or development
    pollution that should never exist in WSD Runtime directories.

    Args:
        filename: Name of the file (not full path, just the name).

    Returns:
        True if filename matches suspicious patterns, False otherwise.
    """
    return any(fnmatch.fnmatch(filename, pattern) for pattern in SUSPICIOUS_FILE_PATTERNS)


def _validate_directory_entry(entry: Path, entry_name: str) -> bool:
    """Validate a directory entry for WSD Runtime compliance.

    Args:
        entry: Full path to directory entry.
        entry_name: Name of the directory.

    Returns:
        True if directory should be processed, False if it should be skipped.

    Raises:
        WsdCollectionError: Directory violates WSD Runtime rules.
    """
    # Skip Python cache directories silently
    if entry_name == "__pycache__":
        return False

    # Error on suspicious directories
    if _is_suspicious_directory(entry_name):
        raise WsdCollectionError(
            "Development artifact directory detected",
            entry,
        )

    # Check for empty directories (error - should have .wsdkeep)
    try:
        contents = list(entry.iterdir())
    except OSError as e:
        raise WsdCollectionError(
            f"Cannot read directory: {e}",
            entry,
        ) from e

    if len(contents) == 0:
        raise WsdCollectionError(
            "Empty directory without .wsdkeep placeholder",
            entry,
        )

    return True


def _validate_file_entry(entry: Path, entry_name: str) -> None:
    """Validate a file entry for WSD Runtime compliance.

    Args:
        entry: Full path to file entry.
        entry_name: Name of the file.

    Raises:
        WsdCollectionError: File violates WSD Runtime rules.
    """
    # Error on suspicious files
    if _is_suspicious_file(entry_name):
        raise WsdCollectionError(
            "Development artifact file detected",
            entry,
        )

    # Error on unsafe filenames
    if not _is_safe_filename(entry_name):
        raise WsdCollectionError(
            "Unsafe filename with special characters",
            entry,
        )

    # Error on binary files
    if _is_binary_file(entry):
        raise WsdCollectionError(
            "Binary file detected (WSD Runtime is text-only)",
            entry,
        )


def collect_wsd_files(directory: Path) -> list[Path]:
    """Validate and collect WSD Runtime files from a directory.

    Recursively scans a directory and returns a sorted list of valid file
    paths relative to the directory root. This function enforces the universal
    rules for what constitutes valid WSD Runtime content.

    The function distinguishes between two types of exclusions:

    **Silently skipped** (legitimately expected, not part of WSD Runtime):
        - VCS directories (.git, .svn, .hg, .bzr, CVS) and their contents
        - Python bytecode cache directories (__pycache__)
        - Files matching patterns in .wsdignore (if present)
        - The .wsdignore file itself

    **Raises WsdCollectionError** (safeguard failures / structural violations):
        - OS artifacts (.DS_Store, Thumbs.db, desktop.ini)
        - Editor artifacts (*~, .*.swp, .*.swo)
        - Build artifacts (node_modules, dist, build, *.egg-info)
        - Python bytecode files (*.pyc, *.pyo)
        - Package locks (package-lock.json)
        - Symlinks (never valid in WSD Runtime)
        - Empty directories without .wsdkeep placeholder
        - Binary files (WSD Runtime is text-only)
        - Unsafe filenames (special characters that cause cross-platform issues)

    Args:
        directory: Root directory to scan.

    Returns:
        Sorted list of Path objects relative to the directory root.

    Raises:
        WsdCollectionError: Invalid content found (structural violation).
        FileNotFoundError: Directory does not exist.
        NotADirectoryError: Path exists but is not a directory.
    """
    if not directory.exists():
        error_msg = f"Directory does not exist: {directory}"
        raise FileNotFoundError(error_msg)

    if not directory.is_dir():
        error_msg = f"Path is not a directory: {directory}"
        raise NotADirectoryError(error_msg)

    # Load .wsdignore patterns
    wsdignore_entries = _parse_wsdignore(directory)

    # Build set of .wsdignore patterns for efficient lookup
    wsdignore_set = set(wsdignore_entries)

    files: list[Path] = []

    def process_directory(dir_path: Path, relative_prefix: str) -> None:
        """Recursively process a directory.

        Args:
            dir_path: Absolute path to directory to process.
            relative_prefix: Path prefix relative to root (e.g., "scripts/").
        """
        try:
            entries = sorted(dir_path.iterdir())
        except OSError as e:
            raise WsdCollectionError(f"Cannot read directory: {e}", dir_path) from e

        for entry in entries:
            entry_name = entry.name
            relative_path = f"{relative_prefix}{entry_name}" if relative_prefix else entry_name

            # Check for symlinks first (error - never valid)
            if entry.is_symlink():
                raise WsdCollectionError(
                    "Symlinks are not allowed in WSD Runtime",
                    entry,
                )

            if entry.is_dir():
                # Skip VCS directories silently
                if entry_name in VCS_DIRECTORIES:
                    continue

                # Validate directory entry (returns False if should be skipped)
                if not _validate_directory_entry(entry, entry_name):
                    continue

                # Recurse into directory
                process_directory(entry, f"{relative_path}/")
            elif entry.is_file():
                # Skip .wsdignore file itself
                if entry_name == ".wsdignore":
                    continue

                # Skip files matching .wsdignore patterns
                if relative_path in wsdignore_set:
                    continue

                # Validate file entry
                _validate_file_entry(entry, entry_name)

                # Valid file - add to results
                files.append(Path(relative_path))

    # Start recursive processing from root
    process_directory(directory, "")

    # Return sorted list for deterministic ordering
    return sorted(files)
