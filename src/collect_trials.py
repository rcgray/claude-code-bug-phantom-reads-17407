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
    - Session file discovery by searching for Workscope ID within .jsonl files
    - Support for all Claude Code session storage structures (flat, hybrid, hierarchical)
    - Idempotent batch processing with progress reporting
    - Verbose mode for detailed progress output

Usage:
    ./src/collect_trials.py -e <exports-dir> -d <destination-dir> [-v]

Functions:
    encode_project_path: Encodes project paths to Claude Code directory format
    derive_session_directory: Derives session directory from current working directory
    scan_exports: Scans exports directory for chat export files and extracts Workscope IDs
    find_session_file: Searches session files for Workscope ID and returns Session UUID
    file_contains_session_id: Checks if an agent file belongs to a session
    copy_session_files: Copies session files using unified algorithm for all structures
    collect_single_trial: Collects all artifacts for a single trial
    main: CLI entry point with argument parsing and validation
"""

import argparse
import json
import re
import shutil
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

# Pattern for extracting Workscope ID from chat export content.
# Matches both "Workscope ID: 20260115-171302" and "Workscope ID: Workscope-20260115-171302"
WORKSCOPE_ID_PATTERN = re.compile(r"Workscope ID:?\s*(?:Workscope-)?(\d{8}-\d{6})")


@dataclass
class CollectionResult:
    """Results from collecting a single trial.

    Tracks the outcome of a trial collection attempt including success status,
    files copied, and any error messages.

    Attributes:
        workscope_id: The Workscope ID of the trial.
        status: Collection outcome - 'collected', 'skipped', or 'failed'.
        files_copied: List of file paths that were copied during collection.
        error: Error message if collection failed, None otherwise.
    """

    workscope_id: str
    status: str  # 'collected', 'skipped', or 'failed'
    files_copied: list[str] = field(default_factory=list)
    error: str | None = None


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


def scan_exports(exports_dir: Path, verbose: bool = False) -> tuple[list[tuple[str, Path]], int]:
    """Scan exports directory for chat export files and extract Workscope IDs.

    Searches for all .txt files in the exports directory and attempts to extract
    a Workscope ID from each file's contents. Files without a valid Workscope ID
    are skipped with a warning printed to stderr.

    Args:
        exports_dir: Path to the directory containing chat export .txt files.
        verbose: If True, print detailed progress messages.

    Returns:
        Tuple containing:
            - List of tuples containing (workscope_id, export_path) for each export
              file that contains a valid Workscope ID.
            - Count of exports skipped due to missing Workscope ID.
    """
    results: list[tuple[str, Path]] = []
    skipped_no_id_count = 0

    for export_path in exports_dir.glob("*.txt"):
        try:
            content = export_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            print(f"Warning: Cannot read export file: {export_path} ({e})", file=sys.stderr)
            skipped_no_id_count += 1
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
            skipped_no_id_count += 1

    return results, skipped_no_id_count


def find_session_file(session_dir: Path, workscope_id: str) -> str | None:
    """Search session files for Workscope ID and return the Session UUID.

    Searches all .jsonl files in the session directory for the given Workscope ID
    string. When a match is found, extracts the Session UUID from the matching
    file's filename (the filename without the .jsonl extension IS the UUID).

    Args:
        session_dir: Path to the Claude Code session directory to search.
        workscope_id: The Workscope ID (YYYYMMDD-HHMMSS format) to search for.

    Returns:
        The Session UUID string if a matching session file is found, or None if
        no session file contains the Workscope ID.
    """
    for session_file in session_dir.glob("*.jsonl"):
        try:
            content = session_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # Skip files that cannot be read
            continue

        if workscope_id in content:
            # The filename (without extension) is the Session UUID
            return session_file.stem

    return None


def file_contains_session_id(agent_file: Path, session_uuid: str) -> bool:
    """Check if an agent file belongs to a specific session.

    Agent files in flat and hybrid structures contain a sessionId field in their
    JSON lines that references the parent session UUID. This function reads the
    first line of the agent file and checks for a matching sessionId.

    Args:
        agent_file: Path to the agent .jsonl file to check.
        session_uuid: The Session UUID to match against.

    Returns:
        True if the agent file contains the session UUID, False otherwise.
    """
    try:
        with agent_file.open(encoding="utf-8") as f:
            first_line = f.readline()
            if not first_line:
                return False
            data = json.loads(first_line)
            return bool(data.get("sessionId") == session_uuid)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return False


def copy_session_files(  # noqa: PLR0913
    session_uuid: str,
    session_dir: Path,
    trial_dir: Path,
    copy_file: Callable[[Path, Path], None] | None = None,
    copy_tree: Callable[[Path, Path], None] | None = None,
    verbose: bool = False,
) -> list[str]:
    """Copy session files using unified algorithm for all structures.

    Handles flat, hybrid, and hierarchical session structures transparently
    by checking for session subdirectory and root-level agent files. The unified
    approach eliminates the need for structure detection logic.

    Args:
        session_uuid: The Session UUID identifying files to copy.
        session_dir: Root session directory to search for files.
        trial_dir: Destination trial directory for collected files.
        copy_file: Function to copy individual files. If None, uses shutil.copy2
            which preserves file metadata during copy.
        copy_tree: Function to recursively copy directories. If None, uses
            shutil.copytree.
        verbose: If True, print file copy progress messages.

    Returns:
        List of file paths that were copied.

    Raises:
        FileNotFoundError: If main session file doesn't exist.
    """
    copy_file_fn = copy_file if copy_file is not None else shutil.copy2
    copy_tree_fn = copy_tree if copy_tree is not None else shutil.copytree
    files_copied: list[str] = []

    # Step 1: Copy main session .jsonl (always exists)
    main_session = session_dir / f"{session_uuid}.jsonl"
    if not main_session.exists():
        raise FileNotFoundError(f"Main session file not found: {main_session}")
    copy_file_fn(main_session, trial_dir / main_session.name)
    files_copied.append(main_session.name)
    if verbose:
        print(f"  Copied: {main_session.name}")

    # Step 2: If session subdirectory exists, copy it entirely
    # This handles tool-results/ and/or subagents/ in hybrid and hierarchical structures
    session_subdir = session_dir / session_uuid
    if session_subdir.is_dir():
        copy_tree_fn(session_subdir, trial_dir / session_uuid)
        files_copied.append(f"{session_uuid}/")
        if verbose:
            print(f"  Copied: {session_uuid}/ (directory)")

    # Step 3: ALWAYS search for root-level agent files
    # They exist in flat and hybrid structures, not in hierarchical - but searching is harmless
    for agent_file in session_dir.glob("agent-*.jsonl"):
        if file_contains_session_id(agent_file, session_uuid):
            copy_file_fn(agent_file, trial_dir / agent_file.name)
            files_copied.append(agent_file.name)
            if verbose:
                print(f"  Copied: {agent_file.name}")

    return files_copied


def collect_single_trial(  # noqa: PLR0913
    workscope_id: str,
    export_path: Path,
    session_dir: Path,
    destination_dir: Path,
    copy_file: Callable[[Path, Path], None] | None = None,
    copy_tree: Callable[[Path, Path], None] | None = None,
    remove_file: Callable[[Path], None] | None = None,
    verbose: bool = False,
) -> CollectionResult:
    """Collect all artifacts for a single trial.

    Orchestrates the collection of trial artifacts by creating the trial directory,
    copying the chat export, locating and copying session files, and cleaning up
    the source export after successful collection.

    Args:
        workscope_id: The Workscope ID (YYYYMMDD-HHMMSS format) for this trial.
        export_path: Path to the chat export .txt file.
        session_dir: Path to the Claude Code session directory.
        destination_dir: Path to the destination directory for collected trials.
        copy_file: Function to copy individual files. If None, uses shutil.copy2.
        copy_tree: Function to recursively copy directories. If None, uses
            shutil.copytree.
        remove_file: Function to delete files. If None, uses Path.unlink.
        verbose: If True, print detailed progress messages.

    Returns:
        CollectionResult containing status, files copied, and any error message.
    """
    copy_file_fn = copy_file if copy_file is not None else shutil.copy2
    remove_file_fn = remove_file if remove_file is not None else Path.unlink

    # Step 1: Create trial directory
    trial_dir = destination_dir / workscope_id

    # Step 2: Skip if trial directory already exists (idempotency)
    if trial_dir.exists():
        if verbose:
            print(f"Skipping {workscope_id} (already exists)")
        return CollectionResult(workscope_id=workscope_id, status="skipped")

    # Find the Session UUID for this Workscope ID
    session_uuid = find_session_file(session_dir, workscope_id)
    if session_uuid is None:
        error_msg = f"No session file found containing Workscope ID {workscope_id}"
        return CollectionResult(workscope_id=workscope_id, status="failed", error=error_msg)

    if verbose:
        print(f"Collecting {workscope_id} (from {export_path.name})")

    # Create the trial directory
    trial_dir.mkdir(parents=True)
    files_copied: list[str] = []

    try:
        # Step 3: Copy chat export as {WORKSCOPE_ID}.txt
        export_dest = trial_dir / f"{workscope_id}.txt"
        copy_file_fn(export_path, export_dest)
        files_copied.append(f"{workscope_id}.txt")
        if verbose:
            print(f"  Copied: {workscope_id}.txt (chat export)")

        # Steps 4-7: Copy session files using unified algorithm
        session_files = copy_session_files(
            session_uuid=session_uuid,
            session_dir=session_dir,
            trial_dir=trial_dir,
            copy_file=copy_file,
            copy_tree=copy_tree,
            verbose=verbose,
        )
        files_copied.extend(session_files)

        # Step 8: Delete source export only after successful copy
        remove_file_fn(export_path)

        return CollectionResult(
            workscope_id=workscope_id, status="collected", files_copied=files_copied
        )

    except (OSError, shutil.Error) as e:
        # Clean up partial trial directory on failure
        if trial_dir.exists():
            shutil.rmtree(trial_dir)
        error_msg = f"Failed to collect trial {workscope_id}: {e}"
        return CollectionResult(workscope_id=workscope_id, status="failed", error=error_msg)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for the CLI.

    Builds an ArgumentParser with required arguments for exports and
    destination directories, plus optional verbose flag.

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

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print detailed progress during collection",
    )

    return parser


def print_summary(  # noqa: PLR0913
    collected_count: int,
    skipped_existing_count: int,
    skipped_no_id_count: int,
    total_files_collected: int,
    destination_dir: Path,
    errors: list[str],
) -> None:
    """Print collection summary report.

    Outputs a summary of the collection results including counts for each
    outcome type and any error details.

    Args:
        collected_count: Number of trials successfully collected.
        skipped_existing_count: Number of trials skipped (already exist).
        skipped_no_id_count: Number of exports skipped (no Workscope ID).
        total_files_collected: Total number of files copied across all trials.
        destination_dir: Destination directory where trials were collected.
        errors: List of error messages from failed collections.
    """
    total_trials = collected_count + skipped_existing_count + len(errors)

    print()
    print("=" * 50)
    print("Collection Summary")
    print("=" * 50)
    print(f"Total trials processed: {total_trials}")
    print(f"Total files collected:  {total_files_collected}")
    print()
    print(f"Collected:              {collected_count}")
    print(f"Skipped (exists):       {skipped_existing_count}")
    print(f"Skipped (no ID):        {skipped_no_id_count}")
    print(f"Failed:                 {len(errors)}")
    print()
    print(f"Output directory:       {destination_dir}")

    if errors:
        print()
        print("Errors:")
        for error in errors:
            print(f"  - {error}")


def main(
    cwd_path: Path | None = None,
    home_path: Path | None = None,
) -> int:
    """Main entry point for the collect_trials CLI.

    Parses command-line arguments, validates directory paths, and orchestrates
    the trial collection process. Scans the exports directory for chat export
    files, derives the session directory, and collects each trial.

    Args:
        cwd_path: Optional current working directory path for testing. If None,
            uses Path.cwd() to get the actual current working directory.
        home_path: Optional home directory path for testing. If None,
            uses Path.home() to get the actual home directory.

    Returns:
        Exit code (0 for success, 1 for any error).
    """
    parser = create_parser()
    args = parser.parse_args()

    verbose: bool = args.verbose

    # Stage 1: Validate that both directories exist
    error = validate_directory(args.exports, "exports")
    if error:
        print(error, file=sys.stderr)
        return 1

    error = validate_directory(args.destination, "destination")
    if error:
        print(error, file=sys.stderr)
        return 1

    # Stage 2: Scan exports and extract Workscope IDs
    exports, skipped_no_id_count = scan_exports(args.exports, verbose=verbose)

    if not exports and skipped_no_id_count == 0:
        print("No exports to process.")
        return 0

    # Stage 3: Derive project session directory
    session_dir = derive_session_directory(cwd_path=cwd_path, home_path=home_path)

    # Stage 4: Collect each trial, tracking results
    collected_count = 0
    skipped_existing_count = 0
    total_files_collected = 0
    errors: list[str] = []

    for workscope_id, export_path in exports:
        result = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_path,
            session_dir=session_dir,
            destination_dir=args.destination,
            verbose=verbose,
        )

        if result.status == "collected":
            collected_count += 1
            total_files_collected += len(result.files_copied)
        elif result.status == "skipped":
            skipped_existing_count += 1
        elif result.status == "failed":
            if result.error:
                errors.append(result.error)
                print(f"Error: {result.error}", file=sys.stderr)

    # Stage 5: Report summary
    print_summary(
        collected_count,
        skipped_existing_count,
        skipped_no_id_count,
        total_files_collected,
        args.destination,
        errors,
    )

    # Return 1 if any failures occurred, 0 otherwise
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
