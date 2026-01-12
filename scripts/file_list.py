"""Generates a Markdown file listing files in a specified directory.

Filtered by include/exclude patterns, and includes an ASCII-like tree structure.
"""

import argparse
import fnmatch
import os
import sys
from pathlib import Path
from typing import Any


def setup_parser() -> argparse.ArgumentParser:
    """Set up the argument parser for the script.

    Returns:
        Configured ArgumentParser for the file list generation script.
    """
    parser = argparse.ArgumentParser(
        description="Generates a Markdown file listing files in a directory, with an ASCII tree.",
        add_help=False,  # Allows custom -h for header argument
    )

    # Required Arguments
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="The path to the output Markdown file.",
    )

    # Optional Arguments with Defaults
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        default=None,
        help="The root directory to scan. Defaults to the current working directory. "
        "Multiple directories can be specified as a comma-separated list.",
    )
    parser.add_argument(
        "-h",
        "--header",
        type=str,
        default="File List",
        help="The H1 header for the Markdown output file.",
    )

    # Filter Arguments (no longer mutually exclusive)
    parser.add_argument(
        "-i",
        "--include",
        dest="include_patterns_str",
        type=str,
        help=(
            "Comma-separated list of wildcard patterns to include. "
            "Can be combined with -e/--exclude."
        ),
    )
    parser.add_argument(
        "-e",
        "--exclude",
        dest="exclude_patterns_str",
        type=str,
        help=(
            "Comma-separated list of wildcard patterns or directory names to exclude. "
            "Can be combined with -i/--include."
        ),
    )

    # Custom Help Argument
    parser.add_argument("--help", action="help", help="Show this help message and exit.")
    return parser


def collect_and_filter_files_multi_dir(
    target_scan_dirs: list[Path],
    tree_base_dir: Path,
    include_patterns: list[str],
    exclude_patterns: list[str],
) -> list[Path]:
    """Collect files from multiple directories and filter them.

    Args:
        target_scan_dirs: List of directories to scan recursively.
        tree_base_dir: Base directory for relative path calculation.
        include_patterns: List of wildcard patterns to include (empty = include all).
        exclude_patterns: List of wildcard patterns to exclude.

    Returns:
        Sorted list of Path objects relative to tree_base_dir.
    """
    unique_relative_paths: set[Path] = set()
    auto_excluded_dirs = {".venv", "venv", "__pycache__", "node_modules", "dist", "build"}

    for scan_dir in target_scan_dirs:
        for item_path in scan_dir.rglob("*"):
            if item_path.is_file():
                # Step 4: Apply auto-exclusion rules DURING discovery (before filtering)
                # Check path components relative to scan_dir for auto-excluded directories
                rel_to_scan = item_path.relative_to(scan_dir)
                if any(part in auto_excluded_dirs for part in rel_to_scan.parts):
                    continue

                file_name = item_path.name
                include_file = True  # Default if no filters

                # Step 5: Apply include patterns (if any)
                if include_patterns:
                    include_file = any(
                        fnmatch.fnmatch(file_name, pattern) for pattern in include_patterns
                    )

                # Step 6: Apply exclude patterns (if any)
                if include_file and exclude_patterns:
                    # Check both filename and path components for exclusion
                    path_parts = rel_to_scan.parts
                    exclude_by_path = any(part in exclude_patterns for part in path_parts)
                    exclude_by_name = any(
                        fnmatch.fnmatch(file_name, pattern) for pattern in exclude_patterns
                    )
                    include_file = not (exclude_by_path or exclude_by_name)

                if include_file:
                    try:
                        # Step 7: Calculate relative path from common base
                        relative_path_for_tree = item_path.relative_to(tree_base_dir)
                        unique_relative_paths.add(relative_path_for_tree)
                    except ValueError:
                        # Step 7 edge case: symlink points outside tree_base_dir
                        print(
                            f"Warning: Could not make path {item_path.resolve()} relative to "
                            f"base {tree_base_dir.resolve()}. Skipping.",
                            file=sys.stderr,
                        )

    return sorted(unique_relative_paths)


def process_directory_arguments(directory_arg: str | None) -> tuple[list[Path], Path, str]:
    """Process and validate directory arguments from command line.

    Args:
        directory_arg: Raw directory argument (None or comma-separated paths).

    Returns:
        Tuple of (resolved_scan_dirs, common_base_for_tree, tree_root_name_display).

    Raises:
        SystemExit: If directory validation fails.
    """
    resolved_scan_dirs: list[Path] = []
    common_base_for_tree: Path

    if directory_arg is None:  # -d not provided
        current_dir = Path.cwd().resolve()
        resolved_scan_dirs.append(current_dir)
        common_base_for_tree = current_dir
    else:  # -d was provided
        dir_strings_from_arg = [p.strip() for p in directory_arg.split(",") if p.strip()]
        if not dir_strings_from_arg:
            print(
                f"Error: The -d argument was provided but contained no valid directory "
                f"paths after parsing: '{directory_arg}'",
                file=sys.stderr,
            )
            sys.exit(1)

        for path_str in dir_strings_from_arg:
            p = Path(path_str).resolve()
            if not p.exists():
                print(
                    f"Error: Input directory '{path_str}' (resolved to '{p}') does not exist.",
                    file=sys.stderr,
                )
                sys.exit(1)
            if not p.is_dir():
                print(
                    f"Error: Input path '{path_str}' (resolved to '{p}') is not a directory.",
                    file=sys.stderr,
                )
                sys.exit(1)
            resolved_scan_dirs.append(p)

        if not resolved_scan_dirs:  # Should be caught by earlier check, but for safety
            print(
                "Error: No valid directories found to scan after processing -d argument.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Determine common base for the tree structure
        try:
            common_base_for_tree = Path(os.path.commonpath([str(p) for p in resolved_scan_dirs]))
        except ValueError as e:
            # This can happen if paths are on different drives on Windows
            print(
                f"Error: Could not determine a common base path for the provided "
                f"directories (possibly on different drives?): {e}",
                file=sys.stderr,
            )
            sys.exit(1)

    # Determine tree_root_name_display based on common_base_for_tree
    tree_root_name_display = common_base_for_tree.name
    if not tree_root_name_display:  # If common_base_for_tree is a root like '/' or 'C:/'
        tree_root_name_display = str(common_base_for_tree.resolve())  # Show '/' or 'C:\\'

    return resolved_scan_dirs, common_base_for_tree, tree_root_name_display


def build_file_tree_dict(relative_paths: list[Path]) -> dict[str, Any]:
    """Build a nested dictionary representing the file tree structure.

    Args:
        relative_paths: List of relative file paths to organize into tree structure.

    Returns:
        Nested dictionary with structure:
        {'_files_': [], '_dirs_': {'dirname': {'_files_': [], '_dirs_': {}}}}
    """
    tree_root: dict[str, Any] = {"_files_": [], "_dirs_": {}}

    for path_obj in relative_paths:
        current_level = tree_root
        parts = path_obj.parts
        for i, part_name in enumerate(parts):
            if i == len(parts) - 1:  # It's a file
                if part_name not in current_level["_files_"]:
                    current_level["_files_"].append(part_name)
            else:  # It's a directory
                current_level = current_level["_dirs_"].setdefault(
                    part_name, {"_files_": [], "_dirs_": {}}
                )

    def sort_tree_recursively(node: dict[str, Any]) -> None:
        """Sort files and directory keys at each level of the tree.

        Args:
            node: Tree dictionary node to sort recursively.
        """
        node["_files_"].sort()
        # Sort directory keys for consistent iteration order
        sorted_dir_keys = sorted(node["_dirs_"].keys())
        sorted_dirs = {key: node["_dirs_"][key] for key in sorted_dir_keys}
        node["_dirs_"] = sorted_dirs
        for dir_name in node["_dirs_"]:
            sort_tree_recursively(node["_dirs_"][dir_name])

    sort_tree_recursively(tree_root)
    return tree_root


def generate_tree_lines_recursive(node: dict[str, Any], prefix: str = "") -> list[str]:
    """Recursively generates the ASCII-like tree string representation.

    Args:
        node: File tree dictionary node to process.
        prefix: String prefix for indentation (default: "").

    Returns:
        List of formatted tree lines for display.
    """
    output_lines: list[str] = []

    # Ensure directories are processed before files if listed separately,
    # or maintain a combined sorted order if that's the visual goal.
    # The examples show dirs and files at the same level sorted alphabetically together.

    dir_items = sorted(node["_dirs_"].keys())
    file_items = sorted(node["_files_"])  # Already sorted by build_file_tree_dict

    items_to_process: list[tuple[str, bool]] = []
    items_to_process.extend([(item_name, True) for item_name in dir_items])  # True for is_dir
    items_to_process.extend([(item_name, False) for item_name in file_items])  # False for is_dir

    # Sort combined list by name
    items_to_process.sort(key=lambda x: x[0])

    for i, (name, is_dir) in enumerate(items_to_process):
        is_last = i == len(items_to_process) - 1
        connector = "└── " if is_last else "├── "
        output_lines.append(f"{prefix}{connector}{name}")

        if is_dir:
            new_prefix = prefix + ("    " if is_last else "│   ")
            output_lines.extend(generate_tree_lines_recursive(node["_dirs_"][name], new_prefix))
    return output_lines


def generate_markdown_output(
    header_text: str,
    root_display_name: str,
    tree_data: dict[str, Any],
    final_file_list: list[Path],
) -> str:
    """Assembles the final Markdown content.

    Args:
        header_text: H1 header text for the Markdown document.
        root_display_name: Display name for the tree root directory.
        tree_data: File tree dictionary structure.
        final_file_list: List of file paths to include in file list section.

    Returns:
        Complete Markdown content as a string.
    """
    content: list[str] = [f"# {header_text}\n", "```"]

    # Check if tree_data represents an empty structure (no files, no dirs under root)
    # and if final_file_list is also empty.
    # This condition means no files matched the filters or the directory was empty.
    is_empty_result = not final_file_list and not tree_data["_dirs_"] and not tree_data["_files_"]

    content.append(root_display_name)
    if not is_empty_result:  # Only generate tree lines if there's something to show
        content.extend(generate_tree_lines_recursive(tree_data))

    content.append("```\n")

    if final_file_list:
        for rel_path in final_file_list:  # Assumes final_file_list is sorted
            # Construct display path: root_name/relative_path
            full_display_path = Path(root_display_name) / rel_path
            content.append(f"- `{full_display_path.as_posix()}`")

    # Ensure a blank line after the ``` if there's a list, or just one newline if not.
    if final_file_list:
        return "\n".join(content) + "\n"
    return "\n".join(content)


def main() -> None:
    """Execute the file list generation script."""
    parser = setup_parser()
    args = parser.parse_args()

    # --- Directory Processing & Validation ---
    resolved_scan_dirs, common_base_for_tree, tree_root_name_display = process_directory_arguments(
        args.directory
    )

    # --- Output File Path Processing & Validation ---
    output_file_path = Path(args.output).resolve()
    if output_file_path.is_dir():
        print(
            f"Error: Output path '{output_file_path}' is a directory. Please specify a file path.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Check parent directory of output file
    try:
        if not output_file_path.parent.exists():
            print(
                f"Error: Parent directory for output file '{output_file_path.parent}' "
                f"does not exist.",
                file=sys.stderr,
            )
            sys.exit(1)
        if not output_file_path.parent.is_dir():
            print(
                f"Error: Parent path for output file '{output_file_path.parent}' "
                f"is not a directory.",
                file=sys.stderr,
            )
            sys.exit(1)
    except Exception as e:  # Broad exception for unexpected path issues
        print(
            f"Error validating output file path '{output_file_path}': {e}",
            file=sys.stderr,
        )
        sys.exit(1)

    # --- Filter Patterns Processing ---
    include_patterns = (
        [p.strip() for p in args.include_patterns_str.split(",") if p.strip()]
        if args.include_patterns_str
        else []
    )
    exclude_patterns = (
        [p.strip() for p in args.exclude_patterns_str.split(",") if p.strip()]
        if args.exclude_patterns_str
        else []
    )

    # --- Core Logic ---
    try:
        relative_file_paths = collect_and_filter_files_multi_dir(
            resolved_scan_dirs, common_base_for_tree, include_patterns, exclude_patterns
        )
        file_tree_data = build_file_tree_dict(relative_file_paths)

        markdown_string = generate_markdown_output(
            args.header,
            tree_root_name_display,  # Use the calculated display name for the tree root
            file_tree_data,
            relative_file_paths,
        )
    except Exception as e:
        print(f"Error during file processing or Markdown generation: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Writing Output ---
    try:
        with output_file_path.open("w", encoding="utf-8") as f:
            f.write(markdown_string)
        print(f"Successfully generated file list: {output_file_path}")
    except OSError as e:
        print(f"Error writing to output file '{output_file_path}': {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        # Argparse errors or explicit sys.exit already handled (printed message)
        # or help message was displayed.
        pass
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
