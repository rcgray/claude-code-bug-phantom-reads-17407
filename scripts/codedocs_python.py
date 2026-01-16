"""Generate markdown API summary from Python source files.

This script analyzes Python source code using AST parsing to extract
module, class, and function information, then generates a markdown
summary suitable for AI-friendly documentation.

Configuration is read from pyproject.toml:
- Source directory: [tool.wsd].check_dirs[0]
- Output location: docs/reports/Python-Code-Map.md (hardcoded)
"""

import ast
import sys
from pathlib import Path
from typing import Any

# Add scripts directory to path for wsd_utils import
_scripts_dir = Path(__file__).parent
sys.path.insert(0, str(_scripts_dir))
from wsd_utils import get_check_dirs  # noqa: E402


def get_docstring_summary(docstring: str | None) -> str:
    """Extract the first paragraph of a docstring.

    Args:
        docstring: The docstring to summarize, or None

    Returns:
        First paragraph of docstring, or default message if None
    """
    if not docstring:
        return "No description available."
    return docstring.strip().split("\n\n")[0].strip()


def analyze_module(file_path: Path) -> dict[str, Any] | None:
    """Analyze a Python file and extract its structure using AST parsing.

    This function performs static analysis without importing or executing the code,
    making it safe to use on files with broken imports or side effects.

    The algorithm:
    1. Read and parse the file into an Abstract Syntax Tree (AST)
    2. Extract the module-level docstring
    3. Walk the AST to find class and function definitions
    4. For classes, also extract their method definitions
    5. Distinguish module-level functions from class methods using col_offset

    Args:
        file_path: Path to the Python file to analyze

    Returns:
        Dictionary containing module info with keys:
        - docstring: Module-level docstring
        - classes: List of class info dicts
        - functions: List of function info dicts
        Returns None if file cannot be parsed (e.g., syntax errors)
    """
    with file_path.open("r") as f:
        try:
            # Parse file content into AST without executing the code
            # This allows analysis of files with broken imports
            tree = ast.parse(f.read())
        except SyntaxError:
            # Silently skip files with syntax errors to allow documentation
            # of valid modules even when some files are broken
            return None

    # Initialize module structure with the module-level docstring
    module_info: dict[str, Any] = {
        "docstring": ast.get_docstring(tree),
        "classes": [],
        "functions": [],
    }

    # Walk the entire AST to find all class and function definitions
    # ast.walk performs a breadth-first traversal of all nodes
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Extract class information including its methods
            class_info: dict[str, Any] = {
                "name": node.name,
                "docstring": ast.get_docstring(node),
                "methods": [],
            }
            # Iterate through class body to find method definitions
            # Note: We check node.body directly, not ast.walk, to get only
            # direct methods (not nested class methods)
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_info: dict[str, Any] = {
                        "name": item.name,
                        "docstring": ast.get_docstring(item),
                    }
                    class_info["methods"].append(method_info)
            module_info["classes"].append(class_info)
        elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
            # Only capture module-level functions (col_offset == 0)
            # This distinguishes top-level functions from methods (which have col_offset > 0)
            # and from nested functions defined inside other functions
            func_info: dict[str, Any] = {"name": node.name, "docstring": ast.get_docstring(node)}
            module_info["functions"].append(func_info)

    return module_info


def _validate_source_path(src_path: Path) -> None:
    """Validate that the source path exists and is a directory.

    Args:
        src_path: Path to validate

    Raises:
        SystemExit: If path doesn't exist or isn't a directory
    """
    if not src_path.exists():
        print(f"Error: Source path '{src_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if not src_path.is_dir():
        print(f"Error: Source path '{src_path}' is not a directory.", file=sys.stderr)
        sys.exit(1)


def _format_class_info(cls: dict[str, Any]) -> str:
    """Format information about a class as markdown.

    Args:
        cls: Dictionary containing class information with keys 'name', 'docstring', 'methods'

    Returns:
        Formatted markdown string for the class
    """
    cls_desc = get_docstring_summary(cls["docstring"]) if cls["docstring"] else "No description"
    lines = [f"- `{cls['name']}`: {cls_desc}"]
    if cls["methods"]:
        method_names = ", ".join(
            [f"`{m['name']}()`" for m in cls["methods"] if not m["name"].startswith("_")]
        )
        if method_names:
            lines.append(f"  - Methods: {method_names}")
    return "\n".join(lines)


def _format_function_info(func: dict[str, Any]) -> str | None:
    """Format information about a function as markdown.

    Args:
        func: Dictionary containing function information with keys 'name', 'docstring'

    Returns:
        Formatted markdown string for the function, or None if private
    """
    if func["name"].startswith("_"):
        return None
    func_desc = get_docstring_summary(func["docstring"]) if func["docstring"] else "No description"
    return f"- `{func['name']}()`: {func_desc}"


def _generate_markdown(modules: dict[str, dict[str, Any]]) -> str:
    """Generate markdown content from analyzed modules.

    This function transforms the analyzed module data into a structured markdown
    document suitable for AI-friendly consumption. The output is designed to be
    token-conscious while providing a comprehensive structural overview.

    The markdown structure:
    - H1: Document title ("Python API Structure")
    - H2: "Modules" section header
    - H3: Individual module names in backticks
    - Bold labels: "Classes:" and "Functions:" subsections
    - Bullet lists: Class/function names with docstring summaries
    - Nested bullets: Method lists for classes (comma-separated)

    Args:
        modules: Dictionary mapping module names to their analysis info

    Returns:
        Complete markdown document as a string
    """
    lines: list[str] = []

    # Document header structure
    lines.append("# Python API Structure\n")
    lines.append("## Modules\n")

    # Process modules in alphabetical order for consistent, predictable output
    for module_name, info in sorted(modules.items()):
        # H3 header for each module with name in backticks for code formatting
        lines.append(f"### `{module_name}`\n")

        # Module description: use first paragraph of docstring or fallback message
        if info["docstring"]:
            lines.append(f"{get_docstring_summary(info['docstring'])}\n")
        else:
            lines.append("No module description.\n")

        # Classes section: only included if module has classes
        if info["classes"]:
            lines.append("**Classes:**\n")
            for cls in info["classes"]:
                # _format_class_info handles private method filtering
                lines.append(_format_class_info(cls))
            lines.append("")  # Blank line after section

        # Functions section: only included if module has public functions
        if info["functions"]:
            lines.append("**Functions:**\n")
            for func in info["functions"]:
                # _format_function_info returns None for private functions (underscore prefix)
                formatted = _format_function_info(func)
                if formatted:
                    lines.append(formatted)
            lines.append("")  # Blank line after section

    return "\n".join(lines)


def main() -> None:
    """Generate Python code documentation summary.

    Reads configuration from pyproject.toml and generates a markdown code map
    at docs/reports/Python-Code-Map.md.
    """
    # Check for configured source directories first
    check_dirs = get_check_dirs()
    if not check_dirs:
        print("Skipping Python code map: no source directories configured.")
        return

    # Resolve paths relative to project root
    # Project root is one directory up from script location (scripts/ → project root)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Get the source directory from check_dirs
    source_dir_name = check_dirs[0]

    # Build paths
    src_path = project_root / source_dir_name
    output_path = project_root / "docs" / "reports" / "Python-Code-Map.md"

    # Validate source directory exists
    _validate_source_path(src_path)

    # Analyze all Python files
    modules: dict[str, dict[str, Any]] = {}

    for py_file in src_path.rglob("*.py"):
        if "__pycache__" not in str(py_file):
            rel_path = py_file.relative_to(src_path.parent)
            module_name = str(rel_path).replace("/", ".").replace(".py", "")
            info = analyze_module(py_file)
            if info:
                modules[module_name] = info

    # Generate markdown content
    content = _generate_markdown(modules)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to file
    with output_path.open("w") as f:
        f.write(content)

    # Success message
    print(f"Python code map generated: {output_path.relative_to(project_root)}")


if __name__ == "__main__":
    main()
