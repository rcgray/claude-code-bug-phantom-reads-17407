#!/usr/bin/env python
"""Collect Trials Script.

Automates the collection and organization of phantom read trial artifacts from
Claude Code sessions. Provides CLI interface for specifying export directories
and destination paths for collected trial data.

This script serves as a convenience tool for investigators running phantom read
reproduction trials. It scans an exports directory for chat export files,
extracts Workscope IDs, locates associated session files, and organizes all
artifacts into trial directories.

Features:
    - CLI argument parsing with validation for exports and destination directories
    - Path encoding for Claude Code session directory derivation
    - Support for all Claude Code session storage structures (flat, hybrid, hierarchical)
    - Idempotent batch processing with progress reporting

Usage:
    ./src/collect_trials.py -e <exports-dir> -d <destination-dir>

Functions:
    encode_project_path: Encodes project paths to Claude Code directory format
    derive_session_directory: Derives session directory from current working directory
    scan_exports: Scans exports directory for chat export files and extracts Workscope IDs
    main: CLI entry point with argument parsing and validation
"""

import argparse
import re
import sys
from pathlib import Path

# Pattern for extracting Workscope ID from chat export content.
# Matches both "Workscope ID: 20260115-171302" and "Workscope ID: Workscope-20260115-171302"
WORKSCOPE_ID_PATTERN = re.compile(r"Workscope ID:?\s*(?:Workscope-)?(\d{8}-\d{6})")


def encode_project_path(project_path: Path) -> str:
    """Convert project path to Claude Code's directory naming convention.

    Args:
        project_path: Absolute path to the project directory.

    Returns:
        String with forward slashes replaced by hyphens.
        Example: /Users/gray/Projects/foo -> -Users-gray-Projects-foo
    """
    return str(project_path).replace("/", "-")


def derive_session_directory(
    cwd_path: Path | None = None,
    home_path: Path | None = None,
) -> Path:
    """Derive Claude Code session directory from current working directory.

    Constructs the path to Claude Code's project-specific session directory
    based on the current working directory. Claude Code stores session files
    in ~/.claude/projects/{encoded_cwd}/.

    Args:
        cwd_path: Optional current working directory path for testing. If None,
            uses Path.cwd() to get the actual current working directory.
        home_path: Optional home directory path for testing. If None,
            uses Path.home() to get the actual home directory.

    Returns:
        Path to the Claude Code session directory for the specified project.
    """
    cwd = cwd_path if cwd_path is not None else Path.cwd()
    home = home_path if home_path is not None else Path.home()

    encoded_cwd = encode_project_path(cwd)
    return home / ".claude" / "projects" / encoded_cwd


def validate_directory(path: Path, name: str) -> str | None:
    """Validate that a directory exists and is accessible.

    Args:
        path: Path to the directory to validate.
        name: Human-readable name for error messages (e.g., "exports", "destination").

    Returns:
        None if validation passes, or an error message string if validation fails.
    """
    if not path.exists():
        return f"Error: {name.capitalize()} directory does not exist: {path}"

    if not path.is_dir():
        return f"Error: {name.capitalize()} path is not a directory: {path}"

    return None


def scan_exports(exports_dir: Path) -> list[tuple[str, Path]]:
    """Scan exports directory for chat export files and extract Workscope IDs.

    Searches for all .txt files in the exports directory and attempts to extract
    a Workscope ID from each file's contents. Files without a valid Workscope ID
    are skipped with a warning printed to stderr.

    Args:
        exports_dir: Path to the directory containing chat export .txt files.

    Returns:
        List of tuples containing (workscope_id, export_path) for each export
        file that contains a valid Workscope ID. The workscope_id is the
        timestamp portion (YYYYMMDD-HHMMSS) extracted from the file.
    """
    results: list[tuple[str, Path]] = []

    for export_path in exports_dir.glob("*.txt"):
        try:
            content = export_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            print(f"Warning: Cannot read export file: {export_path} ({e})", file=sys.stderr)
            continue

        match = WORKSCOPE_ID_PATTERN.search(content)
        if match:
            workscope_id = match.group(1)
            results.append((workscope_id, export_path))
        else:
            print(
                f"Warning: Skipping export (no Workscope ID found): {export_path.name}",
                file=sys.stderr,
            )

    return results


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for the CLI.

    Builds an ArgumentParser with required arguments for exports and
    destination directories.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Collect and organize phantom read trial artifacts from Claude Code sessions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-e",
        "--exports",
        required=True,
        type=Path,
        metavar="DIR",
        help="Path to directory containing chat export .txt files",
    )

    parser.add_argument(
        "-d",
        "--destination",
        required=True,
        type=Path,
        metavar="DIR",
        help="Path to destination directory for collected trials",
    )

    return parser


def main() -> int:
    """Main entry point for the collect_trials CLI.

    Parses command-line arguments, validates directory paths, and orchestrates
    the trial collection process.

    Returns:
        Exit code (0 for success, 1 for any error).
    """
    parser = create_parser()
    args = parser.parse_args()

    # Validate that both directories exist
    error = validate_directory(args.exports, "exports")
    if error:
        print(error, file=sys.stderr)
        return 1

    error = validate_directory(args.destination, "destination")
    if error:
        print(error, file=sys.stderr)
        return 1

    # Validation passed - print directories for confirmation
    print(f"Exports directory: {args.exports}")
    print(f"Destination directory: {args.destination}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
