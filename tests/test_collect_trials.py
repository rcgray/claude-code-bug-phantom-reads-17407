"""Tests for Collect Trials Script.

This module provides comprehensive test coverage for the Collect Trials Script
(src/collect_trials.py) including argument parsing, path encoding functions,
session directory derivation, session file discovery, progress output, and
summary reporting.

The test architecture uses pytest fixtures for dependency injection, enabling
isolated testing without modifying real directories or relying on actual
Claude Code session structures.

Test Categories:
    - Argument parsing (TestArgumentParsing)
    - Path encoding (TestEncodeProjectPath)
    - Session directory derivation (TestDeriveSessionDirectory)
    - Export scanning (TestExportScanning)
    - Session file discovery (TestSessionFileDiscovery)
    - Copy session files (TestCopySessionFiles)
    - Single trial collection (TestCollectSingleTrial)
    - Idempotency (TestIdempotency)
    - Progress output (TestProgressOutput)
    - Summary report (TestSummaryReport)
"""

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from src.collect_trials import (
    CollectionResult,
    collect_single_trial,
    copy_session_files,
    create_parser,
    derive_session_directory,
    encode_project_path,
    find_session_file,
    main,
    print_summary,
    scan_exports,
    validate_directory,
)

# =============================================================================
# Fixtures
# =============================================================================


# Test constants for integration tests
EXPECTED_FILE_COUNT_FLAT = 4  # export + main session + 2 agent files
EXPECTED_TRIAL_COUNT_PARTIAL_FAILURE = 3  # Three trials with mixed outcomes


@pytest.fixture
def tmp_exports_dir(tmp_path: Path) -> Path:
    """Provide a temporary exports directory for testing.

    Creates a temporary directory structure mimicking an exports directory
    where chat export .txt files would be stored.

    Args:
        tmp_path: Pytest fixture providing temporary directory for test files.

    Returns:
        Path to temporary exports directory (created but empty).
    """
    exports_dir = tmp_path / "exports"
    exports_dir.mkdir(parents=True)
    return exports_dir


@pytest.fixture
def tmp_destination_dir(tmp_path: Path) -> Path:
    """Provide a temporary destination directory for collected trials.

    Creates a temporary directory structure mimicking a destination directory
    where collected trial artifacts would be organized.

    Args:
        tmp_path: Pytest fixture providing temporary directory for test files.

    Returns:
        Path to temporary destination directory (created but empty).
    """
    destination_dir = tmp_path / "destination"
    destination_dir.mkdir(parents=True)
    return destination_dir


@pytest.fixture
def sample_export_content() -> Callable[[str, bool], str]:
    """Provide factory for sample chat export content with Workscope ID.

    Returns a function that generates realistic chat export content containing
    a Workscope ID in various formats for testing export scanning functionality.

    Returns:
        Function that takes workscope_id and optional format flag, returns
        export file content as a string.
    """

    def _create_content(workscope_id: str, use_prefix: bool = False) -> str:
        """Generate sample chat export content.

        Args:
            workscope_id: The Workscope ID to embed in the content.
            use_prefix: If True, uses "Workscope-" prefix format.

        Returns:
            String containing realistic chat export content with embedded ID.
        """
        if use_prefix:
            id_line = f"## Workscope ID: Workscope-{workscope_id}"
        else:
            id_line = f"## Workscope ID: {workscope_id}"

        return f"""# Work Journal - 2026-01-18 15:09
{id_line}

---

## Session Progress Log

This is a sample chat export file used for testing the collect_trials.py
script. It contains a Workscope ID that should be extracted by the
scan_exports() function.

### User Message
Please analyze the codebase for potential issues.

### Assistant Response
I'll examine the code structure and identify any problems.
"""

    return _create_content


@pytest.fixture
def tmp_session_dir(tmp_path: Path) -> Path:
    """Provide a temporary session directory mimicking ~/.claude/projects/.

    Creates a temporary directory structure that simulates the Claude Code
    session directory where .jsonl session files are stored.

    Args:
        tmp_path: Pytest fixture providing temporary directory for test files.

    Returns:
        Path to temporary session directory (created but empty).
    """
    session_dir = tmp_path / "session"
    session_dir.mkdir(parents=True)
    return session_dir


@pytest.fixture
def sample_session_content() -> Callable[[str], str]:
    """Provide factory for sample session .jsonl content with Workscope ID.

    Returns a function that generates realistic session file content containing
    a Workscope ID for testing session file discovery functionality.

    Returns:
        Function that takes workscope_id and returns session file content.
    """

    def _create_content(workscope_id: str) -> str:
        """Generate sample session .jsonl content.

        Args:
            workscope_id: The Workscope ID to embed in the content.

        Returns:
            String containing realistic session .jsonl content with embedded ID.
        """
        # Session files contain JSON lines with various message types
        # The Workscope ID appears in the conversation content
        return f"""{{"type":"system","message":"Starting session"}}
{{"type":"user","message":"Starting workscope initialization"}}
{{"type":"assistant","message":"Workscope ID: {workscope_id}"}}
{{"type":"user","message":"Continue with the task"}}
{{"type":"assistant","message":"Processing the request"}}
"""

    return _create_content


@pytest.fixture
def flat_session_structure(tmp_session_dir: Path) -> dict[str, str | Path | list[Path]]:
    """Create flat session structure files and return paths.

    Creates a flat session structure where agent files are at the root level
    alongside the main session file with no session subdirectory.

    Creates:
        - {SESSION_UUID}.jsonl with Workscope ID
        - agent-{xxx}.jsonl files with sessionId field at root level

    Args:
        tmp_session_dir: Pytest fixture providing temporary session directory.

    Returns:
        Dictionary mapping file types to their paths.
    """
    session_uuid = "flat-uuid-1234-5678-abcd"
    workscope_id = "20260118-100000"

    # Create main session file
    main_session = tmp_session_dir / f"{session_uuid}.jsonl"
    main_session.write_text(
        f'{{"type":"system","sessionId":"{session_uuid}"}}\n'
        f'{{"type":"assistant","message":"Workscope ID: {workscope_id}"}}\n'
    )

    # Create agent files at root level with sessionId field
    agent1 = tmp_session_dir / "agent-abc123.jsonl"
    agent1.write_text(f'{{"sessionId":"{session_uuid}","type":"agent"}}\n')

    agent2 = tmp_session_dir / "agent-def456.jsonl"
    agent2.write_text(f'{{"sessionId":"{session_uuid}","type":"agent"}}\n')

    return {
        "session_uuid": session_uuid,
        "workscope_id": workscope_id,
        "main_session": main_session,
        "agents": [agent1, agent2],
        "session_dir": tmp_session_dir,
    }


@pytest.fixture
def hybrid_session_structure(tmp_session_dir: Path) -> dict[str, str | Path | list[Path]]:
    """Create hybrid session structure files and return paths.

    Creates a hybrid session structure where agent files are at root level
    but a session subdirectory exists containing only tool-results/.

    Creates:
        - {SESSION_UUID}.jsonl with Workscope ID
        - {SESSION_UUID}/ directory with tool-results/ subdirectory
        - agent-{xxx}.jsonl files at root level with sessionId field

    Args:
        tmp_session_dir: Pytest fixture providing temporary session directory.

    Returns:
        Dictionary mapping file types to their paths.
    """
    session_uuid = "hybrid-uuid-1234-5678-abcd"
    workscope_id = "20260118-110000"

    # Create main session file
    main_session = tmp_session_dir / f"{session_uuid}.jsonl"
    main_session.write_text(
        f'{{"type":"system","sessionId":"{session_uuid}"}}\n'
        f'{{"type":"assistant","message":"Workscope ID: {workscope_id}"}}\n'
    )

    # Create session subdirectory with tool-results
    session_subdir = tmp_session_dir / session_uuid
    tool_results_dir = session_subdir / "tool-results"
    tool_results_dir.mkdir(parents=True)

    tool_result = tool_results_dir / "toolu_abc123.txt"
    tool_result.write_text("Tool result content")

    # Create agent files at root level
    agent1 = tmp_session_dir / "agent-ghi789.jsonl"
    agent1.write_text(f'{{"sessionId":"{session_uuid}","type":"agent"}}\n')

    return {
        "session_uuid": session_uuid,
        "workscope_id": workscope_id,
        "main_session": main_session,
        "session_subdir": session_subdir,
        "tool_results": [tool_result],
        "agents": [agent1],
        "session_dir": tmp_session_dir,
    }


@pytest.fixture
def hierarchical_session_structure(tmp_session_dir: Path) -> dict[str, str | Path | list[Path]]:
    """Create hierarchical session structure files and return paths.

    Creates a hierarchical session structure where the session subdirectory
    contains both subagents/ and tool-results/ directories. No agent files
    exist at the root level.

    Creates:
        - {SESSION_UUID}.jsonl with Workscope ID
        - {SESSION_UUID}/ directory with subagents/ and tool-results/
        - Agent files inside subagents/ directory

    Args:
        tmp_session_dir: Pytest fixture providing temporary session directory.

    Returns:
        Dictionary mapping file types to their paths.
    """
    session_uuid = "hier-uuid-1234-5678-abcd"
    workscope_id = "20260118-120000"

    # Create main session file
    main_session = tmp_session_dir / f"{session_uuid}.jsonl"
    main_session.write_text(
        f'{{"type":"system","sessionId":"{session_uuid}"}}\n'
        f'{{"type":"assistant","message":"Workscope ID: {workscope_id}"}}\n'
    )

    # Create session subdirectory with subagents and tool-results
    session_subdir = tmp_session_dir / session_uuid
    subagents_dir = session_subdir / "subagents"
    tool_results_dir = session_subdir / "tool-results"
    subagents_dir.mkdir(parents=True)
    tool_results_dir.mkdir(parents=True)

    # Create agent files inside subagents directory
    agent1 = subagents_dir / "agent-jkl012.jsonl"
    agent1.write_text(f'{{"sessionId":"{session_uuid}","type":"agent"}}\n')

    tool_result = tool_results_dir / "toolu_def456.txt"
    tool_result.write_text("Hierarchical tool result")

    return {
        "session_uuid": session_uuid,
        "workscope_id": workscope_id,
        "main_session": main_session,
        "session_subdir": session_subdir,
        "subagents": [agent1],
        "tool_results": [tool_result],
        "session_dir": tmp_session_dir,
    }


# =============================================================================
# Tests for Argument Parsing (TestArgumentParsing)
# =============================================================================


class TestArgumentParsing:
    """Tests for CLI argument parsing functionality."""

    def test_missing_exports_argument(self, tmp_destination_dir: Path) -> None:
        """Verify parser exits with error when --exports is missing.

        Args:
            tmp_destination_dir: Pytest fixture providing temporary destination directory.
        """
        parser = create_parser()

        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--destination", str(tmp_destination_dir)])

        # argparse exits with code 2 for missing required arguments
        assert exc_info.value.code == 2  # noqa: PLR2004

    def test_missing_destination_argument(self, tmp_exports_dir: Path) -> None:
        """Verify parser exits with error when --destination is missing.

        Args:
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
        """
        parser = create_parser()

        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--exports", str(tmp_exports_dir)])

        # argparse exits with code 2 for missing required arguments
        assert exc_info.value.code == 2  # noqa: PLR2004

    def test_invalid_exports_path_nonexistent(
        self, tmp_path: Path, tmp_destination_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify main exits with error for nonexistent exports directory.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
            tmp_destination_dir: Pytest fixture providing temporary destination directory.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        nonexistent_exports = tmp_path / "nonexistent_exports"

        with patch(
            "sys.argv",
            [
                "collect_trials.py",
                "--exports",
                str(nonexistent_exports),
                "--destination",
                str(tmp_destination_dir),
            ],
        ):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "exports directory does not exist" in captured.err.lower()

    def test_invalid_destination_path_nonexistent(
        self, tmp_path: Path, tmp_exports_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify main exits with error for nonexistent destination directory.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        nonexistent_dest = tmp_path / "nonexistent_dest"

        with patch(
            "sys.argv",
            [
                "collect_trials.py",
                "--exports",
                str(tmp_exports_dir),
                "--destination",
                str(nonexistent_dest),
            ],
        ):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "destination directory does not exist" in captured.err.lower()

    def test_valid_arguments_success(
        self, tmp_exports_dir: Path, tmp_destination_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify main succeeds with valid exports and destination directories.

        With an empty exports directory, main should return 0 and print
        a message indicating no exports to process.

        Args:
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            tmp_destination_dir: Pytest fixture providing temporary destination directory.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        with patch(
            "sys.argv",
            [
                "collect_trials.py",
                "--exports",
                str(tmp_exports_dir),
                "--destination",
                str(tmp_destination_dir),
            ],
        ):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "No exports to process" in captured.out

    def test_verbose_flag_accepted(self, tmp_path: Path) -> None:
        """Verify parser accepts -v and --verbose flags.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        parser = create_parser()
        exports_dir = tmp_path / "exports"
        dest_dir = tmp_path / "dest"

        # Test short flag
        args = parser.parse_args(["-e", str(exports_dir), "-d", str(dest_dir), "-v"])
        assert args.verbose is True

        # Test long flag
        args = parser.parse_args(["-e", str(exports_dir), "-d", str(dest_dir), "--verbose"])
        assert args.verbose is True

        # Test default (no flag)
        args = parser.parse_args(["-e", str(exports_dir), "-d", str(dest_dir)])
        assert args.verbose is False


# =============================================================================
# Tests for encode_project_path() (TestEncodeProjectPath)
# =============================================================================


class TestEncodeProjectPath:
    """Tests for the encode_project_path function."""

    def test_basic_encoding(self) -> None:
        """Verify basic project path encoding replaces slashes with hyphens.

        Tests the standard encoding behavior where forward slashes in absolute
        paths are replaced with hyphens.
        """
        project_path = Path("/Users/gray/Projects/foo")

        result = encode_project_path(project_path)

        assert result == "-Users-gray-Projects-foo"

    def test_encoding_deep_path(self) -> None:
        """Verify encoding works correctly for deeply nested paths.

        Tests that paths with many directory levels are correctly encoded.
        """
        deep_path = Path("/home/user/work/projects/team/feature/submodule")

        result = encode_project_path(deep_path)

        assert result == "-home-user-work-projects-team-feature-submodule"
        assert "/" not in result

    def test_encoding_relative_path(self) -> None:
        """Verify encoding handles relative paths by converting them as-is.

        The function encodes any path by replacing slashes with hyphens,
        regardless of whether it is absolute or relative.
        """
        relative_path = Path("Projects/foo")

        result = encode_project_path(relative_path)

        assert result == "Projects-foo"
        assert "/" not in result


# =============================================================================
# Tests for derive_session_directory() (TestDeriveSessionDirectory)
# =============================================================================


class TestDeriveSessionDirectory:
    """Tests for the derive_session_directory function."""

    def test_with_dependency_injection(self, tmp_path: Path) -> None:
        """Verify derive_session_directory works with injected paths.

        Tests that the function correctly constructs the session directory
        path when both cwd_path and home_path are provided via dependency
        injection.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        mock_cwd = Path("/Users/gray/Projects/test-project")
        mock_home = tmp_path / "home" / "gray"
        mock_home.mkdir(parents=True)

        result = derive_session_directory(cwd_path=mock_cwd, home_path=mock_home)

        expected = mock_home / ".claude" / "projects" / "-Users-gray-Projects-test-project"
        assert result == expected

    def test_path_construction_format(self, tmp_path: Path) -> None:
        """Verify derive_session_directory constructs correct path format.

        Tests that the resulting path follows the expected structure:
        {home}/.claude/projects/{encoded_cwd}

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        mock_cwd = Path("/home/user/workspace/my-project")
        mock_home = tmp_path / "home" / "user"
        mock_home.mkdir(parents=True)

        result = derive_session_directory(cwd_path=mock_cwd, home_path=mock_home)

        # Verify path components
        assert ".claude" in result.parts
        assert "projects" in result.parts
        assert result.name == "-home-user-workspace-my-project"

        # Verify path structure
        assert result.parent.name == "projects"
        assert result.parent.parent.name == ".claude"


# =============================================================================
# Tests for validate_directory()
# =============================================================================


class TestValidateDirectory:
    """Tests for the validate_directory function."""

    def test_valid_directory_returns_none(self, tmp_path: Path) -> None:
        """Verify validate_directory returns None for existing directory.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        valid_dir = tmp_path / "valid"
        valid_dir.mkdir()

        result = validate_directory(valid_dir, "test")

        assert result is None

    def test_nonexistent_directory_returns_error(self, tmp_path: Path) -> None:
        """Verify validate_directory returns error message for nonexistent path.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        nonexistent = tmp_path / "nonexistent"

        result = validate_directory(nonexistent, "test")

        assert result is not None
        assert "does not exist" in result

    def test_file_not_directory_returns_error(self, tmp_path: Path) -> None:
        """Verify validate_directory returns error when path is a file.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        file_path = tmp_path / "a_file.txt"
        file_path.write_text("content")

        result = validate_directory(file_path, "test")

        assert result is not None
        assert "is not a directory" in result


# =============================================================================
# Tests for create_parser()
# =============================================================================


class TestCreateParser:
    """Tests for the create_parser function."""

    def test_short_flags_accepted(self, tmp_path: Path) -> None:
        """Verify parser accepts short flags -e and -d.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        parser = create_parser()
        exports_dir = tmp_path / "exports"
        dest_dir = tmp_path / "dest"

        args = parser.parse_args(["-e", str(exports_dir), "-d", str(dest_dir)])

        assert args.exports == exports_dir
        assert args.destination == dest_dir

    def test_long_flags_accepted(self, tmp_path: Path) -> None:
        """Verify parser accepts long flags --exports and --destination.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        parser = create_parser()
        exports_dir = tmp_path / "exports"
        dest_dir = tmp_path / "dest"

        args = parser.parse_args(["--exports", str(exports_dir), "--destination", str(dest_dir)])

        assert args.exports == exports_dir
        assert args.destination == dest_dir

    def test_paths_converted_to_path_objects(self, tmp_path: Path) -> None:
        """Verify parser converts string paths to Path objects.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        parser = create_parser()

        args = parser.parse_args(
            ["--exports", "/some/exports/path", "--destination", "/some/dest/path"]
        )

        assert isinstance(args.exports, Path)
        assert isinstance(args.destination, Path)


# =============================================================================
# Tests for scan_exports() (TestExportScanning)
# =============================================================================


class TestExportScanning:
    """Tests for the scan_exports function."""

    def test_valid_workscope_id_extraction(
        self, tmp_exports_dir: Path, sample_export_content: Callable[[str, bool], str]
    ) -> None:
        """Verify scan_exports extracts valid Workscope ID from export file.

        Args:
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            sample_export_content: Pytest fixture providing export content factory.
        """
        workscope_id = "20260118-150902"
        export_file = tmp_exports_dir / "trial-export.txt"
        export_file.write_text(sample_export_content(workscope_id, False))

        results, skipped_count = scan_exports(tmp_exports_dir)

        assert len(results) == 1
        assert results[0][0] == workscope_id
        assert results[0][1] == export_file
        assert skipped_count == 0

    def test_both_workscope_id_formats(
        self, tmp_exports_dir: Path, sample_export_content: Callable[[str, bool], str]
    ) -> None:
        """Verify scan_exports handles both Workscope ID format variations.

        Tests extraction works for both "Workscope ID: YYYYMMDD-HHMMSS" and
        "Workscope ID: Workscope-YYYYMMDD-HHMMSS" formats.

        Args:
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            sample_export_content: Pytest fixture providing export content factory.
        """
        # Create file with prefix format
        workscope_id = "20260115-171302"
        export_file = tmp_exports_dir / "prefixed-export.txt"
        export_file.write_text(sample_export_content(workscope_id, True))

        results, skipped_count = scan_exports(tmp_exports_dir)

        assert len(results) == 1
        assert results[0][0] == workscope_id
        assert skipped_count == 0

    def test_no_workscope_id_emits_warning(
        self, tmp_exports_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify scan_exports warns when export file lacks Workscope ID.

        Args:
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        export_file = tmp_exports_dir / "no-id-export.txt"
        export_file.write_text("This export file has no Workscope ID pattern.")

        results, skipped_count = scan_exports(tmp_exports_dir)

        assert len(results) == 0
        assert skipped_count == 1
        captured = capsys.readouterr()
        assert "warning" in captured.err.lower()
        assert "no workscope id found" in captured.err.lower()

    def test_multiple_export_files(
        self, tmp_exports_dir: Path, sample_export_content: Callable[[str, bool], str]
    ) -> None:
        """Verify scan_exports handles multiple export files correctly.

        Args:
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            sample_export_content: Pytest fixture providing export content factory.
        """
        workscope_ids = ["20260118-100000", "20260118-110000", "20260118-120000"]

        for i, wid in enumerate(workscope_ids):
            export_file = tmp_exports_dir / f"export-{i}.txt"
            export_file.write_text(sample_export_content(wid, False))

        results, skipped_count = scan_exports(tmp_exports_dir)

        assert len(results) == len(workscope_ids)
        extracted_ids = {r[0] for r in results}
        assert extracted_ids == set(workscope_ids)
        assert skipped_count == 0

    def test_empty_exports_directory(self, tmp_exports_dir: Path) -> None:
        """Verify scan_exports returns empty list for empty directory.

        Args:
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
        """
        results, skipped_count = scan_exports(tmp_exports_dir)

        assert results == []
        assert skipped_count == 0

    def test_unreadable_file_emits_warning(
        self, tmp_exports_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify scan_exports warns when export file cannot be read.

        Args:
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        # Create a file with invalid UTF-8 bytes
        export_file = tmp_exports_dir / "unreadable-export.txt"
        export_file.write_bytes(b"\x80\x81\x82 Invalid UTF-8 content")

        results, skipped_count = scan_exports(tmp_exports_dir)

        assert len(results) == 0
        assert skipped_count == 1
        captured = capsys.readouterr()
        assert "warning" in captured.err.lower()
        assert "cannot read" in captured.err.lower()

    def test_multiple_ids_in_one_file(
        self, tmp_exports_dir: Path, sample_export_content: Callable[[str, bool], str]
    ) -> None:
        """Verify scan_exports extracts only first Workscope ID from file.

        When a file contains multiple Workscope ID patterns, only the first
        one encountered should be extracted.

        Args:
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            sample_export_content: Pytest fixture providing export content factory.
        """
        first_id = "20260118-100000"
        second_id = "20260118-200000"

        content = sample_export_content(first_id, False)
        content += f"\n\n## Another Section\nWorkscope ID: {second_id}\n"

        export_file = tmp_exports_dir / "multi-id-export.txt"
        export_file.write_text(content)

        results, skipped_count = scan_exports(tmp_exports_dir)

        assert len(results) == 1
        assert results[0][0] == first_id
        assert skipped_count == 0

    def test_non_txt_files_ignored(
        self, tmp_exports_dir: Path, sample_export_content: Callable[[str, bool], str]
    ) -> None:
        """Verify scan_exports ignores non-.txt files in exports directory.

        Args:
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            sample_export_content: Pytest fixture providing export content factory.
        """
        workscope_id = "20260118-150902"

        # Create a .txt file that should be processed
        txt_file = tmp_exports_dir / "valid-export.txt"
        txt_file.write_text(sample_export_content(workscope_id, False))

        # Create non-.txt files that should be ignored
        json_file = tmp_exports_dir / "data.json"
        json_file.write_text(f'{{"workscope_id": "{workscope_id}"}}')

        md_file = tmp_exports_dir / "notes.md"
        md_file.write_text(f"## Workscope ID: {workscope_id}")

        log_file = tmp_exports_dir / "session.log"
        log_file.write_text(f"Workscope ID: {workscope_id}")

        results, skipped_count = scan_exports(tmp_exports_dir)

        assert len(results) == 1
        assert results[0][1] == txt_file
        assert skipped_count == 0


# =============================================================================
# Tests for find_session_file() (TestSessionFileDiscovery)
# =============================================================================


class TestSessionFileDiscovery:
    """Tests for the find_session_file function."""

    def test_session_file_found(
        self, tmp_session_dir: Path, sample_session_content: Callable[[str], str]
    ) -> None:
        """Verify find_session_file returns UUID when session file contains Workscope ID.

        Args:
            tmp_session_dir: Pytest fixture providing temporary session directory.
            sample_session_content: Pytest fixture providing session content factory.
        """
        workscope_id = "20260118-153851"
        session_uuid = "27eaff45-a330-4a88-9213-3725c9f420d0"

        session_file = tmp_session_dir / f"{session_uuid}.jsonl"
        session_file.write_text(sample_session_content(workscope_id))

        result = find_session_file(tmp_session_dir, workscope_id)

        assert result == session_uuid

    def test_session_file_not_found(self, tmp_session_dir: Path) -> None:
        """Verify find_session_file returns None when no session file matches.

        Args:
            tmp_session_dir: Pytest fixture providing temporary session directory.
        """
        # Create session file without the target Workscope ID
        session_file = tmp_session_dir / "some-session-uuid.jsonl"
        session_file.write_text('{"type":"system","message":"No workscope here"}')

        result = find_session_file(tmp_session_dir, "20260118-999999")

        assert result is None

    def test_multiple_files_only_one_matches(
        self, tmp_session_dir: Path, sample_session_content: Callable[[str], str]
    ) -> None:
        """Verify find_session_file finds correct file among multiple session files.

        Args:
            tmp_session_dir: Pytest fixture providing temporary session directory.
            sample_session_content: Pytest fixture providing session content factory.
        """
        target_workscope_id = "20260118-153851"
        other_workscope_id = "20260117-120000"
        target_uuid = "target-uuid-1234-5678-abcd"
        other_uuid = "other-uuid-9999-8888-efgh"

        # Create multiple session files
        target_file = tmp_session_dir / f"{target_uuid}.jsonl"
        target_file.write_text(sample_session_content(target_workscope_id))

        other_file = tmp_session_dir / f"{other_uuid}.jsonl"
        other_file.write_text(sample_session_content(other_workscope_id))

        # Also create a file with no workscope ID
        empty_file = tmp_session_dir / "empty-session.jsonl"
        empty_file.write_text('{"type":"system","message":"Empty session"}')

        result = find_session_file(tmp_session_dir, target_workscope_id)

        assert result == target_uuid

    def test_uuid_extraction_from_filename(
        self, tmp_session_dir: Path, sample_session_content: Callable[[str], str]
    ) -> None:
        """Verify find_session_file correctly extracts UUID from filename stem.

        The Session UUID is the filename without the .jsonl extension. This test
        verifies the extraction handles various UUID formats correctly.

        Args:
            tmp_session_dir: Pytest fixture providing temporary session directory.
            sample_session_content: Pytest fixture providing session content factory.
        """
        workscope_id = "20260118-100000"
        # Use a realistic UUID format
        session_uuid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

        session_file = tmp_session_dir / f"{session_uuid}.jsonl"
        session_file.write_text(sample_session_content(workscope_id))

        result = find_session_file(tmp_session_dir, workscope_id)

        # Verify the full UUID is returned, not truncated or modified
        assert result == session_uuid
        assert ".jsonl" not in result


# =============================================================================
# Tests for copy_session_files() (TestCopySessionFiles)
# =============================================================================


class TestCopySessionFiles:
    """Tests for the copy_session_files function."""

    def test_flat_structure_copies_main_and_agents(
        self, flat_session_structure: dict[str, Any], tmp_path: Path
    ) -> None:
        """Verify copy_session_files handles flat session structure correctly.

        Flat structure has main session and agent files at root level with
        no session subdirectory.

        Args:
            flat_session_structure: Pytest fixture providing flat session files.
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        trial_dir = tmp_path / "trial"
        trial_dir.mkdir()

        files_copied = copy_session_files(
            session_uuid=flat_session_structure["session_uuid"],
            session_dir=flat_session_structure["session_dir"],
            trial_dir=trial_dir,
        )

        # Verify main session was copied
        assert (trial_dir / f"{flat_session_structure['session_uuid']}.jsonl").exists()

        # Verify agent files were copied
        assert (trial_dir / "agent-abc123.jsonl").exists()
        assert (trial_dir / "agent-def456.jsonl").exists()

        # Verify files_copied list contains expected entries
        assert len(files_copied) == 3  # main + 2 agents  # noqa: PLR2004

    def test_hybrid_structure_copies_subdirectory_and_agents(
        self, hybrid_session_structure: dict[str, Any], tmp_path: Path
    ) -> None:
        """Verify copy_session_files handles hybrid session structure correctly.

        Hybrid structure has agent files at root level and session subdirectory
        containing tool-results/.

        Args:
            hybrid_session_structure: Pytest fixture providing hybrid session files.
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        trial_dir = tmp_path / "trial"
        trial_dir.mkdir()

        files_copied = copy_session_files(
            session_uuid=hybrid_session_structure["session_uuid"],
            session_dir=hybrid_session_structure["session_dir"],
            trial_dir=trial_dir,
        )

        # Verify main session was copied
        assert (trial_dir / f"{hybrid_session_structure['session_uuid']}.jsonl").exists()

        # Verify session subdirectory was copied
        copied_subdir = trial_dir / hybrid_session_structure["session_uuid"]
        assert copied_subdir.is_dir()
        assert (copied_subdir / "tool-results" / "toolu_abc123.txt").exists()

        # Verify root-level agent was copied
        assert (trial_dir / "agent-ghi789.jsonl").exists()

        # Verify files_copied list
        assert len(files_copied) == 3  # main + subdir + 1 agent  # noqa: PLR2004

    def test_hierarchical_structure_copies_full_subdirectory(
        self, hierarchical_session_structure: dict[str, Any], tmp_path: Path
    ) -> None:
        """Verify copy_session_files handles hierarchical session structure correctly.

        Hierarchical structure has session subdirectory containing both
        subagents/ and tool-results/ directories.

        Args:
            hierarchical_session_structure: Pytest fixture providing hierarchical session files.
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        trial_dir = tmp_path / "trial"
        trial_dir.mkdir()

        files_copied = copy_session_files(
            session_uuid=hierarchical_session_structure["session_uuid"],
            session_dir=hierarchical_session_structure["session_dir"],
            trial_dir=trial_dir,
        )

        # Verify main session was copied
        assert (trial_dir / f"{hierarchical_session_structure['session_uuid']}.jsonl").exists()

        # Verify session subdirectory structure was copied
        copied_subdir = trial_dir / hierarchical_session_structure["session_uuid"]
        assert copied_subdir.is_dir()
        assert (copied_subdir / "subagents" / "agent-jkl012.jsonl").exists()
        assert (copied_subdir / "tool-results" / "toolu_def456.txt").exists()

        # Verify files_copied list
        assert len(files_copied) == 2  # main + subdir (no root agents)  # noqa: PLR2004

    def test_agent_matching_by_session_id(self, tmp_session_dir: Path, tmp_path: Path) -> None:
        """Verify agent files are matched by sessionId field, not just name pattern.

        Only agent files containing the correct sessionId should be copied.

        Args:
            tmp_session_dir: Pytest fixture providing temporary session directory.
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        session_uuid = "target-uuid-1234"
        other_uuid = "other-uuid-5678"

        # Create main session
        main_session = tmp_session_dir / f"{session_uuid}.jsonl"
        main_session.write_text(f'{{"sessionId":"{session_uuid}","type":"system"}}\n')

        # Create agent file matching target session
        matching_agent = tmp_session_dir / "agent-match.jsonl"
        matching_agent.write_text(f'{{"sessionId":"{session_uuid}","type":"agent"}}\n')

        # Create agent file for different session
        other_agent = tmp_session_dir / "agent-other.jsonl"
        other_agent.write_text(f'{{"sessionId":"{other_uuid}","type":"agent"}}\n')

        trial_dir = tmp_path / "trial"
        trial_dir.mkdir()

        copy_session_files(
            session_uuid=session_uuid,
            session_dir=tmp_session_dir,
            trial_dir=trial_dir,
        )

        # Only matching agent should be copied
        assert (trial_dir / "agent-match.jsonl").exists()
        assert not (trial_dir / "agent-other.jsonl").exists()

    def test_no_subdirectory_copies_main_only(self, tmp_session_dir: Path, tmp_path: Path) -> None:
        """Verify copy_session_files works when no session subdirectory exists.

        Args:
            tmp_session_dir: Pytest fixture providing temporary session directory.
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        session_uuid = "no-subdir-uuid-1234"

        # Create main session only (no subdirectory, no agents)
        main_session = tmp_session_dir / f"{session_uuid}.jsonl"
        main_session.write_text(f'{{"sessionId":"{session_uuid}","type":"system"}}\n')

        trial_dir = tmp_path / "trial"
        trial_dir.mkdir()

        files_copied = copy_session_files(
            session_uuid=session_uuid,
            session_dir=tmp_session_dir,
            trial_dir=trial_dir,
        )

        # Only main session should be copied
        assert (trial_dir / f"{session_uuid}.jsonl").exists()
        # No subdirectory should be created
        assert not (trial_dir / session_uuid).exists()
        assert len(files_copied) == 1

    def test_no_root_agents_only_copies_subdirectory(
        self, tmp_session_dir: Path, tmp_path: Path
    ) -> None:
        """Verify copy_session_files works when no root-level agent files exist.

        Args:
            tmp_session_dir: Pytest fixture providing temporary session directory.
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        session_uuid = "no-agents-uuid-1234"

        # Create main session
        main_session = tmp_session_dir / f"{session_uuid}.jsonl"
        main_session.write_text(f'{{"sessionId":"{session_uuid}","type":"system"}}\n')

        # Create session subdirectory with content but no root agents
        session_subdir = tmp_session_dir / session_uuid
        tool_results = session_subdir / "tool-results"
        tool_results.mkdir(parents=True)
        (tool_results / "toolu_test.txt").write_text("content")

        trial_dir = tmp_path / "trial"
        trial_dir.mkdir()

        copy_session_files(
            session_uuid=session_uuid,
            session_dir=tmp_session_dir,
            trial_dir=trial_dir,
        )

        # Main session and subdirectory should be copied
        assert (trial_dir / f"{session_uuid}.jsonl").exists()
        assert (trial_dir / session_uuid / "tool-results" / "toolu_test.txt").exists()
        # No agent files at root in trial
        assert not list(trial_dir.glob("agent-*.jsonl"))


# =============================================================================
# Tests for collect_single_trial() (TestCollectSingleTrial)
# =============================================================================


class TestCollectSingleTrial:
    """Tests for the collect_single_trial function."""

    def test_successful_collection(
        self,
        flat_session_structure: dict[str, Any],
        tmp_exports_dir: Path,
        tmp_destination_dir: Path,
        sample_export_content: Callable[[str, bool], str],
    ) -> None:
        """Verify collect_single_trial successfully collects all artifacts.

        Args:
            flat_session_structure: Pytest fixture providing flat session files.
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            tmp_destination_dir: Pytest fixture providing temporary destination directory.
            sample_export_content: Pytest fixture providing export content factory.
        """
        workscope_id = flat_session_structure["workscope_id"]

        # Create export file
        export_file = tmp_exports_dir / "trial-export.txt"
        export_file.write_text(sample_export_content(workscope_id, False))

        result = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_file,
            session_dir=flat_session_structure["session_dir"],
            destination_dir=tmp_destination_dir,
        )

        # Should succeed
        assert result.status == "collected"
        assert result.error is None
        assert len(result.files_copied) > 0

        # Trial directory should exist with expected contents
        trial_dir = tmp_destination_dir / workscope_id
        assert trial_dir.is_dir()

    def test_trial_directory_creation(
        self,
        flat_session_structure: dict[str, Any],
        tmp_exports_dir: Path,
        tmp_destination_dir: Path,
        sample_export_content: Callable[[str, bool], str],
    ) -> None:
        """Verify collect_single_trial creates trial directory with workscope ID.

        Args:
            flat_session_structure: Pytest fixture providing flat session files.
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            tmp_destination_dir: Pytest fixture providing temporary destination directory.
            sample_export_content: Pytest fixture providing export content factory.
        """
        workscope_id = flat_session_structure["workscope_id"]

        export_file = tmp_exports_dir / "trial-export.txt"
        export_file.write_text(sample_export_content(workscope_id, False))

        collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_file,
            session_dir=flat_session_structure["session_dir"],
            destination_dir=tmp_destination_dir,
        )

        # Directory named by workscope ID should be created
        trial_dir = tmp_destination_dir / workscope_id
        assert trial_dir.is_dir()
        assert trial_dir.name == workscope_id

    def test_export_renamed_to_workscope_id(
        self,
        flat_session_structure: dict[str, Any],
        tmp_exports_dir: Path,
        tmp_destination_dir: Path,
        sample_export_content: Callable[[str, bool], str],
    ) -> None:
        """Verify chat export is renamed to {WORKSCOPE_ID}.txt in trial directory.

        Args:
            flat_session_structure: Pytest fixture providing flat session files.
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            tmp_destination_dir: Pytest fixture providing temporary destination directory.
            sample_export_content: Pytest fixture providing export content factory.
        """
        workscope_id = flat_session_structure["workscope_id"]

        # Create export with different original name
        export_file = tmp_exports_dir / "original-name-export.txt"
        export_file.write_text(sample_export_content(workscope_id, False))

        collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_file,
            session_dir=flat_session_structure["session_dir"],
            destination_dir=tmp_destination_dir,
        )

        trial_dir = tmp_destination_dir / workscope_id
        # Export should be renamed to workscope ID
        assert (trial_dir / f"{workscope_id}.txt").exists()
        # Original name should not exist
        assert not (trial_dir / "original-name-export.txt").exists()

    def test_export_deleted_after_success(
        self,
        flat_session_structure: dict[str, Any],
        tmp_exports_dir: Path,
        tmp_destination_dir: Path,
        sample_export_content: Callable[[str, bool], str],
    ) -> None:
        """Verify source export is deleted after successful collection.

        Args:
            flat_session_structure: Pytest fixture providing flat session files.
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            tmp_destination_dir: Pytest fixture providing temporary destination directory.
            sample_export_content: Pytest fixture providing export content factory.
        """
        workscope_id = flat_session_structure["workscope_id"]

        export_file = tmp_exports_dir / "trial-export.txt"
        export_file.write_text(sample_export_content(workscope_id, False))

        # Verify export exists before collection
        assert export_file.exists()

        result = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_file,
            session_dir=flat_session_structure["session_dir"],
            destination_dir=tmp_destination_dir,
        )

        # Should succeed
        assert result.status == "collected"
        # Source export should be deleted
        assert not export_file.exists()

    def test_skip_existing_trial_directory(
        self,
        flat_session_structure: dict[str, Any],
        tmp_exports_dir: Path,
        tmp_destination_dir: Path,
        sample_export_content: Callable[[str, bool], str],
    ) -> None:
        """Verify collect_single_trial skips when trial directory already exists.

        Args:
            flat_session_structure: Pytest fixture providing flat session files.
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            tmp_destination_dir: Pytest fixture providing temporary destination directory.
            sample_export_content: Pytest fixture providing export content factory.
        """
        workscope_id = flat_session_structure["workscope_id"]

        # Create trial directory first (simulating previous collection)
        trial_dir = tmp_destination_dir / workscope_id
        trial_dir.mkdir()

        export_file = tmp_exports_dir / "trial-export.txt"
        export_file.write_text(sample_export_content(workscope_id, False))

        result = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_file,
            session_dir=flat_session_structure["session_dir"],
            destination_dir=tmp_destination_dir,
        )

        # Should return skipped status
        assert result.status == "skipped"
        assert result.error is None
        # Export should NOT be deleted when skipped
        assert export_file.exists()

    def test_session_not_found_returns_error(
        self,
        tmp_session_dir: Path,
        tmp_exports_dir: Path,
        tmp_destination_dir: Path,
        sample_export_content: Callable[[str, bool], str],
    ) -> None:
        """Verify collect_single_trial returns error when session file not found.

        Args:
            tmp_session_dir: Pytest fixture providing temporary session directory.
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            tmp_destination_dir: Pytest fixture providing temporary destination directory.
            sample_export_content: Pytest fixture providing export content factory.
        """
        workscope_id = "20260118-999999"

        # Create export but no matching session file
        export_file = tmp_exports_dir / "orphan-export.txt"
        export_file.write_text(sample_export_content(workscope_id, False))

        result = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_file,
            session_dir=tmp_session_dir,
            destination_dir=tmp_destination_dir,
        )

        # Should return failed status with error
        assert result.status == "failed"
        assert result.error is not None
        assert "No session file found" in result.error
        # Trial directory should NOT be created
        assert not (tmp_destination_dir / workscope_id).exists()


# =============================================================================
# Tests for Idempotency (TestIdempotency)
# =============================================================================


class TestIdempotency:
    """Tests for idempotent batch collection behavior."""

    def test_rerun_skips_existing_trials(
        self,
        flat_session_structure: dict[str, Any],
        tmp_exports_dir: Path,
        tmp_destination_dir: Path,
        sample_export_content: Callable[[str, bool], str],
    ) -> None:
        """Verify re-running collection skips already-collected trials.

        Args:
            flat_session_structure: Pytest fixture providing flat session files.
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            tmp_destination_dir: Pytest fixture providing temporary destination directory.
            sample_export_content: Pytest fixture providing export content factory.
        """
        workscope_id = flat_session_structure["workscope_id"]

        # First run: collect trial
        export_file = tmp_exports_dir / "trial-export.txt"
        export_file.write_text(sample_export_content(workscope_id, False))

        result1 = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_file,
            session_dir=flat_session_structure["session_dir"],
            destination_dir=tmp_destination_dir,
        )
        assert result1.status == "collected"

        # Second run: create new export file, should skip
        export_file2 = tmp_exports_dir / "trial-export-2.txt"
        export_file2.write_text(sample_export_content(workscope_id, False))

        result2 = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_file2,
            session_dir=flat_session_structure["session_dir"],
            destination_dir=tmp_destination_dir,
        )

        # Second run should skip
        assert result2.status == "skipped"
        # Second export should NOT be deleted (idempotency preserves source on skip)
        assert export_file2.exists()

    def test_export_cleanup_after_collection(
        self,
        flat_session_structure: dict[str, Any],
        tmp_exports_dir: Path,
        tmp_destination_dir: Path,
        sample_export_content: Callable[[str, bool], str],
    ) -> None:
        """Verify exports are deleted only after successful collection.

        Args:
            flat_session_structure: Pytest fixture providing flat session files.
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            tmp_destination_dir: Pytest fixture providing temporary destination directory.
            sample_export_content: Pytest fixture providing export content factory.
        """
        workscope_id = flat_session_structure["workscope_id"]

        export_file = tmp_exports_dir / "trial-export.txt"
        export_file.write_text(sample_export_content(workscope_id, False))

        # Verify export exists
        assert export_file.exists()

        result = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_file,
            session_dir=flat_session_structure["session_dir"],
            destination_dir=tmp_destination_dir,
        )

        assert result.status == "collected"
        # Export should be deleted after successful collection
        assert not export_file.exists()

        # Collected trial should exist
        assert (tmp_destination_dir / workscope_id).is_dir()

    def test_partial_recovery_continues_remaining(  # noqa: PLR0913
        self,
        flat_session_structure: dict[str, Any],
        tmp_exports_dir: Path,
        tmp_destination_dir: Path,
        tmp_session_dir: Path,
        sample_export_content: Callable[[str, bool], str],
        sample_session_content: Callable[[str], str],
    ) -> None:
        """Verify batch processing continues after some trials are already collected.

        Simulates a partial batch: one trial already collected, one remaining.
        The remaining trial should be collected while the existing one is skipped.

        Args:
            flat_session_structure: Pytest fixture providing flat session files.
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            tmp_destination_dir: Pytest fixture providing temporary destination directory.
            tmp_session_dir: Pytest fixture providing temporary session directory.
            sample_export_content: Pytest fixture providing export content factory.
            sample_session_content: Pytest fixture providing session content factory.
        """
        # First trial - already collected (simulate by creating directory)
        collected_id = flat_session_structure["workscope_id"]
        (tmp_destination_dir / collected_id).mkdir()

        # Second trial - not yet collected
        remaining_id = "20260118-200000"
        remaining_uuid = "remaining-uuid-1234"

        # Create session file for remaining trial
        session_file = flat_session_structure["session_dir"] / f"{remaining_uuid}.jsonl"
        session_file.write_text(sample_session_content(remaining_id))

        # Create exports for both
        export1 = tmp_exports_dir / "collected-export.txt"
        export1.write_text(sample_export_content(collected_id, False))

        export2 = tmp_exports_dir / "remaining-export.txt"
        export2.write_text(sample_export_content(remaining_id, False))

        # Collect both trials
        result1 = collect_single_trial(
            workscope_id=collected_id,
            export_path=export1,
            session_dir=flat_session_structure["session_dir"],
            destination_dir=tmp_destination_dir,
        )

        result2 = collect_single_trial(
            workscope_id=remaining_id,
            export_path=export2,
            session_dir=flat_session_structure["session_dir"],
            destination_dir=tmp_destination_dir,
        )

        # First should be skipped (directory existed)
        assert result1.status == "skipped"
        assert export1.exists()  # Not deleted on skip

        # Second should be collected
        assert result2.status == "collected"
        assert not export2.exists()  # Deleted after collection
        assert (tmp_destination_dir / remaining_id).is_dir()


# =============================================================================
# Tests for Progress Output (TestProgressOutput)
# =============================================================================


class TestProgressOutput:
    """Tests for verbose progress output functionality."""

    def test_verbose_prints_collection_message(
        self,
        flat_session_structure: dict[str, Any],
        tmp_exports_dir: Path,
        tmp_destination_dir: Path,
        sample_export_content: Callable[[str, bool], str],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify verbose mode prints message when collecting a trial.

        Args:
            flat_session_structure: Pytest fixture providing flat session files.
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            tmp_destination_dir: Pytest fixture providing temporary destination directory.
            sample_export_content: Pytest fixture providing export content factory.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        workscope_id = flat_session_structure["workscope_id"]

        export_file = tmp_exports_dir / "trial-export.txt"
        export_file.write_text(sample_export_content(workscope_id, False))

        collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_file,
            session_dir=flat_session_structure["session_dir"],
            destination_dir=tmp_destination_dir,
            verbose=True,
        )

        captured = capsys.readouterr()
        assert f"Collecting {workscope_id}" in captured.out
        assert "trial-export.txt" in captured.out

    def test_verbose_prints_file_copy_messages(
        self,
        flat_session_structure: dict[str, Any],
        tmp_exports_dir: Path,
        tmp_destination_dir: Path,
        sample_export_content: Callable[[str, bool], str],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify verbose mode prints messages for each file copied.

        Args:
            flat_session_structure: Pytest fixture providing flat session files.
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            tmp_destination_dir: Pytest fixture providing temporary destination directory.
            sample_export_content: Pytest fixture providing export content factory.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        workscope_id = flat_session_structure["workscope_id"]

        export_file = tmp_exports_dir / "trial-export.txt"
        export_file.write_text(sample_export_content(workscope_id, False))

        collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_file,
            session_dir=flat_session_structure["session_dir"],
            destination_dir=tmp_destination_dir,
            verbose=True,
        )

        captured = capsys.readouterr()
        # Should see "Copied:" messages for files
        assert "Copied:" in captured.out
        # Should see the chat export mentioned
        assert f"{workscope_id}.txt" in captured.out
        # Should see session file mentioned
        assert ".jsonl" in captured.out

    def test_verbose_prints_skip_message(
        self,
        flat_session_structure: dict[str, Any],
        tmp_exports_dir: Path,
        tmp_destination_dir: Path,
        sample_export_content: Callable[[str, bool], str],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify verbose mode prints message when skipping existing trial.

        Args:
            flat_session_structure: Pytest fixture providing flat session files.
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            tmp_destination_dir: Pytest fixture providing temporary destination directory.
            sample_export_content: Pytest fixture providing export content factory.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        workscope_id = flat_session_structure["workscope_id"]

        # Create trial directory first (simulating previous collection)
        trial_dir = tmp_destination_dir / workscope_id
        trial_dir.mkdir()

        export_file = tmp_exports_dir / "trial-export.txt"
        export_file.write_text(sample_export_content(workscope_id, False))

        collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_file,
            session_dir=flat_session_structure["session_dir"],
            destination_dir=tmp_destination_dir,
            verbose=True,
        )

        captured = capsys.readouterr()
        assert f"Skipping {workscope_id}" in captured.out
        assert "already exists" in captured.out

    def test_quiet_mode_no_progress(
        self,
        flat_session_structure: dict[str, Any],
        tmp_exports_dir: Path,
        tmp_destination_dir: Path,
        sample_export_content: Callable[[str, bool], str],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify quiet mode (verbose=False) does not print progress messages.

        Args:
            flat_session_structure: Pytest fixture providing flat session files.
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            tmp_destination_dir: Pytest fixture providing temporary destination directory.
            sample_export_content: Pytest fixture providing export content factory.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        workscope_id = flat_session_structure["workscope_id"]

        export_file = tmp_exports_dir / "trial-export.txt"
        export_file.write_text(sample_export_content(workscope_id, False))

        collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_file,
            session_dir=flat_session_structure["session_dir"],
            destination_dir=tmp_destination_dir,
            verbose=False,
        )

        captured = capsys.readouterr()
        # Should not see verbose progress messages
        assert "Collecting" not in captured.out
        assert "Copied:" not in captured.out


# =============================================================================
# Tests for Summary Report (TestSummaryReport)
# =============================================================================


class TestSummaryReport:
    """Tests for summary report generation."""

    def test_summary_shows_collected_count(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Verify summary report displays collected count.

        Args:
            capsys: Pytest fixture for capturing stdout/stderr output.
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        print_summary(
            collected_count=5,
            skipped_existing_count=0,
            skipped_no_id_count=0,
            total_files_collected=15,
            destination_dir=tmp_path / "dest",
            errors=[],
        )

        captured = capsys.readouterr()
        assert "Collected:" in captured.out
        assert "5" in captured.out

    def test_summary_shows_skipped_counts(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Verify summary report displays both skipped counts separately.

        Args:
            capsys: Pytest fixture for capturing stdout/stderr output.
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        print_summary(
            collected_count=3,
            skipped_existing_count=2,
            skipped_no_id_count=1,
            total_files_collected=9,
            destination_dir=tmp_path / "dest",
            errors=[],
        )

        captured = capsys.readouterr()
        assert "Skipped (exists):" in captured.out
        assert "2" in captured.out
        assert "Skipped (no ID):" in captured.out
        assert "1" in captured.out

    def test_summary_shows_error_details(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Verify summary report displays error messages.

        Args:
            capsys: Pytest fixture for capturing stdout/stderr output.
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        errors = [
            "No session file found containing Workscope ID 20260118-111111",
            "Failed to collect trial 20260118-222222: Permission denied",
        ]

        print_summary(
            collected_count=1,
            skipped_existing_count=0,
            skipped_no_id_count=0,
            total_files_collected=3,
            destination_dir=tmp_path / "dest",
            errors=errors,
        )

        captured = capsys.readouterr()
        assert "Failed:" in captured.out
        assert "2" in captured.out
        assert "Errors:" in captured.out
        assert "20260118-111111" in captured.out
        assert "20260118-222222" in captured.out

    def test_summary_zero_case(self, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
        """Verify summary report handles all-zero counts correctly.

        Args:
            capsys: Pytest fixture for capturing stdout/stderr output.
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        print_summary(
            collected_count=0,
            skipped_existing_count=0,
            skipped_no_id_count=0,
            total_files_collected=0,
            destination_dir=tmp_path / "dest",
            errors=[],
        )

        captured = capsys.readouterr()
        assert "Collection Summary" in captured.out
        assert "Collected:" in captured.out
        assert "Skipped (exists):" in captured.out
        assert "Skipped (no ID):" in captured.out
        assert "Failed:" in captured.out
        # Should not have Errors section when no errors
        assert "Errors:" not in captured.out

    def test_main_prints_summary(
        self,
        flat_session_structure: dict[str, Any],
        tmp_exports_dir: Path,
        tmp_destination_dir: Path,
        sample_export_content: Callable[[str, bool], str],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify main() prints a summary report at the end.

        Args:
            flat_session_structure: Pytest fixture providing flat session files.
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
            tmp_destination_dir: Pytest fixture providing temporary destination directory.
            sample_export_content: Pytest fixture providing export content factory.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        workscope_id = flat_session_structure["workscope_id"]
        export_file = tmp_exports_dir / "trial-export.txt"
        export_file.write_text(sample_export_content(workscope_id, False))

        with patch(
            "sys.argv",
            [
                "collect_trials.py",
                "--exports",
                str(tmp_exports_dir),
                "--destination",
                str(tmp_destination_dir),
            ],
        ):
            # We need to mock the session directory derivation
            with patch(
                "src.collect_trials.derive_session_directory",
                return_value=flat_session_structure["session_dir"],
            ):
                main()

        captured = capsys.readouterr()
        assert "Collection Summary" in captured.out
        assert "Collected:" in captured.out

    def test_summary_shows_total_trials_processed(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Verify summary report displays total trials processed.

        Total trials processed should be collected + skipped + failed.

        Args:
            capsys: Pytest fixture for capturing stdout/stderr output.
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        print_summary(
            collected_count=5,
            skipped_existing_count=2,
            skipped_no_id_count=1,
            total_files_collected=20,
            destination_dir=tmp_path / "dest",
            errors=["Error 1", "Error 2"],
        )

        captured = capsys.readouterr()
        assert "Total trials processed:" in captured.out
        # 5 collected + 2 skipped + 2 failed = 9 total
        assert "9" in captured.out

    def test_summary_shows_total_files_collected(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Verify summary report displays total files collected.

        Args:
            capsys: Pytest fixture for capturing stdout/stderr output.
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        print_summary(
            collected_count=3,
            skipped_existing_count=0,
            skipped_no_id_count=0,
            total_files_collected=42,
            destination_dir=tmp_path / "dest",
            errors=[],
        )

        captured = capsys.readouterr()
        assert "Total files collected:" in captured.out
        assert "42" in captured.out

    def test_summary_shows_output_directory(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Verify summary report displays output directory location.

        Args:
            capsys: Pytest fixture for capturing stdout/stderr output.
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        dest_dir = tmp_path / "my-trials"

        print_summary(
            collected_count=2,
            skipped_existing_count=0,
            skipped_no_id_count=0,
            total_files_collected=8,
            destination_dir=dest_dir,
            errors=[],
        )

        captured = capsys.readouterr()
        assert "Output directory:" in captured.out
        assert "my-trials" in captured.out

    def test_collection_result_dataclass(self) -> None:
        """Verify CollectionResult dataclass stores expected fields."""
        result = CollectionResult(
            workscope_id="20260118-123456",
            status="collected",
            files_copied=["file1.txt", "file2.jsonl"],
            error=None,
        )

        assert result.workscope_id == "20260118-123456"
        assert result.status == "collected"
        assert result.files_copied == ["file1.txt", "file2.jsonl"]
        assert result.error is None

        # Test failed result
        failed_result = CollectionResult(
            workscope_id="20260118-999999",
            status="failed",
            error="No session file found",
        )

        assert failed_result.status == "failed"
        assert failed_result.error == "No session file found"
        assert failed_result.files_copied == []  # Default empty list


# =============================================================================
# End-to-End Integration Tests
# =============================================================================


@patch.dict("os.environ", {}, clear=True)
class TestIntegrationSingleTrial:
    """Integration tests for end-to-end single trial collection.

    Tests complete workflow from export file to organized trial directory,
    covering all three session storage structures (flat, hybrid, hierarchical).
    """

    def test_collect_single_trial_flat_structure(
        self,
        tmp_path: Path,
        sample_export_content: Callable[[str], str],
        sample_session_content: Callable[[str], str],
    ) -> None:
        """Test end-to-end collection of single trial with flat session structure.

        Verifies complete workflow: export scanning, session discovery, file copying,
        and export cleanup for a trial with flat session structure.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
            sample_export_content: Pytest fixture providing factory for export content.
            sample_session_content: Pytest fixture providing factory for session content.
        """
        # Setup directories
        exports_dir = tmp_path / "exports"
        destination_dir = tmp_path / "trials"
        session_dir = tmp_path / "sessions"
        exports_dir.mkdir()
        destination_dir.mkdir()
        session_dir.mkdir()

        # Create export file with Workscope ID
        workscope_id = "20260119-101500"
        session_uuid = "abc123-flat"
        export_file = exports_dir / "trial-export.txt"
        export_file.write_text(sample_export_content(workscope_id))

        # Create flat session structure
        main_session = session_dir / f"{session_uuid}.jsonl"
        main_session.write_text(sample_session_content(workscope_id))

        agent1 = session_dir / "agent-001.jsonl"
        agent1.write_text(f'{{"sessionId": "{session_uuid}"}}\n')

        agent2 = session_dir / "agent-002.jsonl"
        agent2.write_text(f'{{"sessionId": "{session_uuid}"}}\n')

        # Execute collection
        result = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_file,
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        # Verify result
        assert result.status == "collected"
        assert result.workscope_id == workscope_id
        assert result.error is None
        assert len(result.files_copied) == EXPECTED_FILE_COUNT_FLAT

        # Verify trial directory structure
        trial_dir = destination_dir / workscope_id
        assert trial_dir.exists()
        assert (trial_dir / f"{workscope_id}.txt").exists()
        assert (trial_dir / f"{session_uuid}.jsonl").exists()
        assert (trial_dir / "agent-001.jsonl").exists()
        assert (trial_dir / "agent-002.jsonl").exists()

        # Verify export was deleted
        assert not export_file.exists()

    def test_collect_single_trial_hybrid_structure(
        self,
        tmp_path: Path,
        sample_export_content: Callable[[str], str],
        sample_session_content: Callable[[str], str],
    ) -> None:
        """Test end-to-end collection of single trial with hybrid session structure.

        Verifies collection with session subdirectory containing tool-results
        while agent files remain at root level.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
            sample_export_content: Pytest fixture providing factory for export content.
            sample_session_content: Pytest fixture providing factory for session content.
        """
        # Setup directories
        exports_dir = tmp_path / "exports"
        destination_dir = tmp_path / "trials"
        session_dir = tmp_path / "sessions"
        exports_dir.mkdir()
        destination_dir.mkdir()
        session_dir.mkdir()

        # Create export file
        workscope_id = "20260119-102000"
        session_uuid = "def456-hybrid"
        export_file = exports_dir / "hybrid-trial.txt"
        export_file.write_text(sample_export_content(workscope_id))

        # Create hybrid session structure
        main_session = session_dir / f"{session_uuid}.jsonl"
        main_session.write_text(sample_session_content(workscope_id))

        # Session subdirectory with tool-results
        session_subdir = session_dir / session_uuid
        session_subdir.mkdir()
        tool_results_dir = session_subdir / "tool-results"
        tool_results_dir.mkdir()
        (tool_results_dir / "toolu_001.txt").write_text("Tool output 1")
        (tool_results_dir / "toolu_002.txt").write_text("Tool output 2")

        # Agent files at root level
        agent1 = session_dir / "agent-100.jsonl"
        agent1.write_text(f'{{"sessionId": "{session_uuid}"}}\n')

        # Execute collection
        result = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_file,
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        # Verify result
        assert result.status == "collected"
        assert result.error is None

        # Verify trial directory structure
        trial_dir = destination_dir / workscope_id
        assert trial_dir.exists()
        assert (trial_dir / f"{workscope_id}.txt").exists()
        assert (trial_dir / f"{session_uuid}.jsonl").exists()
        assert (trial_dir / session_uuid / "tool-results" / "toolu_001.txt").exists()
        assert (trial_dir / session_uuid / "tool-results" / "toolu_002.txt").exists()
        assert (trial_dir / "agent-100.jsonl").exists()

        # Verify export was deleted
        assert not export_file.exists()

    def test_collect_single_trial_hierarchical_structure(
        self,
        tmp_path: Path,
        sample_export_content: Callable[[str], str],
        sample_session_content: Callable[[str], str],
    ) -> None:
        """Test end-to-end collection of single trial with hierarchical session structure.

        Verifies collection with all content in session subdirectory including
        both subagents and tool-results.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
            sample_export_content: Pytest fixture providing factory for export content.
            sample_session_content: Pytest fixture providing factory for session content.
        """
        # Setup directories
        exports_dir = tmp_path / "exports"
        destination_dir = tmp_path / "trials"
        session_dir = tmp_path / "sessions"
        exports_dir.mkdir()
        destination_dir.mkdir()
        session_dir.mkdir()

        # Create export file
        workscope_id = "20260119-103000"
        session_uuid = "ghi789-hierarchical"
        export_file = exports_dir / "hierarchical-trial.txt"
        export_file.write_text(sample_export_content(workscope_id))

        # Create hierarchical session structure
        main_session = session_dir / f"{session_uuid}.jsonl"
        main_session.write_text(sample_session_content(workscope_id))

        # Session subdirectory with subagents and tool-results
        session_subdir = session_dir / session_uuid
        session_subdir.mkdir()

        subagents_dir = session_subdir / "subagents"
        subagents_dir.mkdir()
        (subagents_dir / "agent-200.jsonl").write_text("agent content")
        (subagents_dir / "agent-201.jsonl").write_text("agent content")

        tool_results_dir = session_subdir / "tool-results"
        tool_results_dir.mkdir()
        (tool_results_dir / "toolu_010.txt").write_text("Tool output")

        # Execute collection
        result = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_file,
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        # Verify result
        assert result.status == "collected"
        assert result.error is None

        # Verify trial directory structure
        trial_dir = destination_dir / workscope_id
        assert trial_dir.exists()
        assert (trial_dir / f"{workscope_id}.txt").exists()
        assert (trial_dir / f"{session_uuid}.jsonl").exists()
        assert (trial_dir / session_uuid / "subagents" / "agent-200.jsonl").exists()
        assert (trial_dir / session_uuid / "subagents" / "agent-201.jsonl").exists()
        assert (trial_dir / session_uuid / "tool-results" / "toolu_010.txt").exists()

        # Verify no root-level agent files (harmless search in hierarchical)
        assert not (trial_dir / "agent-200.jsonl").exists()

        # Verify export was deleted
        assert not export_file.exists()


@patch.dict("os.environ", {}, clear=True)
class TestIntegrationMultipleTrials:
    """Integration tests for batch collection with mixed outcomes.

    Tests scenarios with multiple trials having different outcomes including
    successful collection, skipped duplicates, and missing session files.
    """

    def test_batch_collection_with_mixed_outcomes(
        self,
        tmp_path: Path,
        sample_export_content: Callable[[str], str],
        sample_session_content: Callable[[str], str],
    ) -> None:
        """Test batch collection with successful, skipped, and failed trials.

        Verifies script continues processing after individual trial failures
        and correctly tracks counts for each outcome type.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
            sample_export_content: Pytest fixture providing factory for export content.
            sample_session_content: Pytest fixture providing factory for session content.
        """
        # Setup directories
        exports_dir = tmp_path / "exports"
        destination_dir = tmp_path / "trials"
        session_dir = tmp_path / "sessions"
        exports_dir.mkdir()
        destination_dir.mkdir()
        session_dir.mkdir()

        # Trial 1: Will succeed
        workscope_1 = "20260119-110000"
        session_1 = "uuid-trial-1"
        (exports_dir / "trial1.txt").write_text(sample_export_content(workscope_1))
        (session_dir / f"{session_1}.jsonl").write_text(sample_session_content(workscope_1))

        # Trial 2: Will skip (already exists)
        workscope_2 = "20260119-111000"
        session_2 = "uuid-trial-2"
        (exports_dir / "trial2.txt").write_text(sample_export_content(workscope_2))
        (session_dir / f"{session_2}.jsonl").write_text(sample_session_content(workscope_2))
        # Pre-create trial directory
        (destination_dir / workscope_2).mkdir()

        # Trial 3: Will fail (no session file)
        workscope_3 = "20260119-112000"
        (exports_dir / "trial3.txt").write_text(sample_export_content(workscope_3))
        # No session file created

        # Execute collections
        result_1 = collect_single_trial(
            workscope_id=workscope_1,
            export_path=exports_dir / "trial1.txt",
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        result_2 = collect_single_trial(
            workscope_id=workscope_2,
            export_path=exports_dir / "trial2.txt",
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        result_3 = collect_single_trial(
            workscope_id=workscope_3,
            export_path=exports_dir / "trial3.txt",
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        # Verify results
        assert result_1.status == "collected"
        assert result_1.error is None

        assert result_2.status == "skipped"
        assert result_2.error is None

        assert result_3.status == "failed"
        assert result_3.error is not None
        assert "No session file found" in result_3.error

        # Verify trial directories
        assert (destination_dir / workscope_1).exists()
        assert (destination_dir / workscope_2).exists()
        assert not (destination_dir / workscope_3).exists()

        # Verify export cleanup
        assert not (exports_dir / "trial1.txt").exists()  # Collected
        assert (exports_dir / "trial2.txt").exists()  # Skipped (not deleted)
        assert (exports_dir / "trial3.txt").exists()  # Failed (not deleted)

    def test_multiple_exports_same_workscope_id(
        self,
        tmp_path: Path,
        sample_export_content: Callable[[str], str],
        sample_session_content: Callable[[str], str],
    ) -> None:
        """Test handling of duplicate Workscope ID in multiple exports.

        Verifies that second export with same Workscope ID is skipped due to
        existing trial directory.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
            sample_export_content: Pytest fixture providing factory for export content.
            sample_session_content: Pytest fixture providing factory for session content.
        """
        # Setup directories
        exports_dir = tmp_path / "exports"
        destination_dir = tmp_path / "trials"
        session_dir = tmp_path / "sessions"
        exports_dir.mkdir()
        destination_dir.mkdir()
        session_dir.mkdir()

        # Same Workscope ID, different export files
        workscope_id = "20260119-120000"
        session_uuid = "uuid-duplicate"

        export_1 = exports_dir / "export-first.txt"
        export_1.write_text(sample_export_content(workscope_id))

        export_2 = exports_dir / "export-second.txt"
        export_2.write_text(sample_export_content(workscope_id))

        # Session file
        (session_dir / f"{session_uuid}.jsonl").write_text(sample_session_content(workscope_id))

        # Collect first export
        result_1 = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_1,
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        # Collect second export (should skip)
        result_2 = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_2,
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        # Verify results
        assert result_1.status == "collected"
        assert result_2.status == "skipped"

        # Verify only one trial directory
        assert (destination_dir / workscope_id).exists()

        # Verify first export deleted, second not deleted (skipped)
        assert not export_1.exists()
        assert export_2.exists()


@patch.dict("os.environ", {}, clear=True)
class TestIntegrationMixedStructures:
    """Integration tests for collecting trials with mixed session structures.

    Tests batch collection where different trials have different session
    storage structures in the same collection run.
    """

    def test_batch_with_flat_hybrid_hierarchical_structures(
        self,
        tmp_path: Path,
        sample_export_content: Callable[[str], str],
        sample_session_content: Callable[[str], str],
    ) -> None:
        """Test batch collection with all three session structures in same run.

        Verifies unified collection algorithm correctly handles flat, hybrid,
        and hierarchical structures without detection logic.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
            sample_export_content: Pytest fixture providing factory for export content.
            sample_session_content: Pytest fixture providing factory for session content.
        """
        # Setup directories
        exports_dir = tmp_path / "exports"
        destination_dir = tmp_path / "trials"
        session_dir = tmp_path / "sessions"
        exports_dir.mkdir()
        destination_dir.mkdir()
        session_dir.mkdir()

        # Flat structure trial
        flat_id = "20260119-130000"
        flat_uuid = "uuid-flat-mixed"
        (exports_dir / "flat.txt").write_text(sample_export_content(flat_id))
        (session_dir / f"{flat_uuid}.jsonl").write_text(sample_session_content(flat_id))
        (session_dir / "agent-flat-1.jsonl").write_text(f'{{"sessionId": "{flat_uuid}"}}\n')

        # Hybrid structure trial
        hybrid_id = "20260119-131000"
        hybrid_uuid = "uuid-hybrid-mixed"
        (exports_dir / "hybrid.txt").write_text(sample_export_content(hybrid_id))
        (session_dir / f"{hybrid_uuid}.jsonl").write_text(sample_session_content(hybrid_id))
        hybrid_subdir = session_dir / hybrid_uuid
        hybrid_subdir.mkdir()
        (hybrid_subdir / "tool-results").mkdir()
        (hybrid_subdir / "tool-results" / "toolu_h1.txt").write_text("tool output")
        (session_dir / "agent-hybrid-1.jsonl").write_text(f'{{"sessionId": "{hybrid_uuid}"}}\n')

        # Hierarchical structure trial
        hier_id = "20260119-132000"
        hier_uuid = "uuid-hier-mixed"
        (exports_dir / "hier.txt").write_text(sample_export_content(hier_id))
        (session_dir / f"{hier_uuid}.jsonl").write_text(sample_session_content(hier_id))
        hier_subdir = session_dir / hier_uuid
        hier_subdir.mkdir()
        (hier_subdir / "subagents").mkdir()
        (hier_subdir / "subagents" / "agent-hier-1.jsonl").write_text("content")
        (hier_subdir / "tool-results").mkdir()
        (hier_subdir / "tool-results" / "toolu_h1.txt").write_text("tool output")

        # Collect all three
        flat_result = collect_single_trial(
            workscope_id=flat_id,
            export_path=exports_dir / "flat.txt",
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        hybrid_result = collect_single_trial(
            workscope_id=hybrid_id,
            export_path=exports_dir / "hybrid.txt",
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        hier_result = collect_single_trial(
            workscope_id=hier_id,
            export_path=exports_dir / "hier.txt",
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        # Verify all succeeded
        assert flat_result.status == "collected"
        assert hybrid_result.status == "collected"
        assert hier_result.status == "collected"

        # Verify flat structure preserved
        flat_dir = destination_dir / flat_id
        assert (flat_dir / "agent-flat-1.jsonl").exists()
        assert not (flat_dir / flat_uuid).exists()  # No subdirectory

        # Verify hybrid structure preserved
        hybrid_dir = destination_dir / hybrid_id
        assert (hybrid_dir / "agent-hybrid-1.jsonl").exists()
        assert (hybrid_dir / hybrid_uuid / "tool-results" / "toolu_h1.txt").exists()

        # Verify hierarchical structure preserved
        hier_dir = destination_dir / hier_id
        assert (hier_dir / hier_uuid / "subagents" / "agent-hier-1.jsonl").exists()
        assert (hier_dir / hier_uuid / "tool-results" / "toolu_h1.txt").exists()
        assert not (hier_dir / "agent-hier-1.jsonl").exists()  # Not at root


@patch.dict("os.environ", {}, clear=True)
class TestIntegrationErrorRecovery:
    """Integration tests for error recovery and idempotent re-runs.

    Tests partial failure scenarios, continuation after errors, and
    idempotent batch processing.
    """

    def test_partial_failure_continuation(
        self,
        tmp_path: Path,
        sample_export_content: Callable[[str], str],
        sample_session_content: Callable[[str], str],
    ) -> None:
        """Test that collection continues after individual trial failures.

        Verifies script processes all exports even when some fail, enabling
        recovery of successful trials from a mixed batch.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
            sample_export_content: Pytest fixture providing factory for export content.
            sample_session_content: Pytest fixture providing factory for session content.
        """
        # Setup directories
        exports_dir = tmp_path / "exports"
        destination_dir = tmp_path / "trials"
        session_dir = tmp_path / "sessions"
        exports_dir.mkdir()
        destination_dir.mkdir()
        session_dir.mkdir()

        # Trial 1: Success
        id_1 = "20260119-140000"
        uuid_1 = "uuid-success-1"
        (exports_dir / "export1.txt").write_text(sample_export_content(id_1))
        (session_dir / f"{uuid_1}.jsonl").write_text(sample_session_content(id_1))

        # Trial 2: Failure (missing session)
        id_2 = "20260119-141000"
        (exports_dir / "export2.txt").write_text(sample_export_content(id_2))

        # Trial 3: Success
        id_3 = "20260119-142000"
        uuid_3 = "uuid-success-3"
        (exports_dir / "export3.txt").write_text(sample_export_content(id_3))
        (session_dir / f"{uuid_3}.jsonl").write_text(sample_session_content(id_3))

        # Collect all three
        results = []
        for export_file in sorted(exports_dir.glob("*.txt")):
            # Extract workscope ID from export
            content = export_file.read_text()
            match = re.search(r"Workscope ID:?\s*(?:Workscope-)?(\d{8}-\d{6})", content)
            if match:
                workscope_id = match.group(1)
                result = collect_single_trial(
                    workscope_id=workscope_id,
                    export_path=export_file,
                    session_dir=session_dir,
                    destination_dir=destination_dir,
                    verbose=False,
                )
                results.append(result)

        # Verify outcomes
        assert len(results) == EXPECTED_TRIAL_COUNT_PARTIAL_FAILURE
        assert results[0].status == "collected"  # Trial 1
        assert results[1].status == "failed"  # Trial 2
        assert results[2].status == "collected"  # Trial 3

        # Verify successful trials collected
        assert (destination_dir / id_1).exists()
        assert (destination_dir / id_3).exists()
        assert not (destination_dir / id_2).exists()

    def test_idempotent_rerun_after_success(
        self,
        tmp_path: Path,
        sample_export_content: Callable[[str], str],
        sample_session_content: Callable[[str], str],
    ) -> None:
        """Test idempotent re-run produces zero collected on second run.

        Verifies that running collection twice with same inputs results in
        all trials being skipped on the second run.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
            sample_export_content: Pytest fixture providing factory for export content.
            sample_session_content: Pytest fixture providing factory for session content.
        """
        # Setup directories
        exports_dir = tmp_path / "exports"
        destination_dir = tmp_path / "trials"
        session_dir = tmp_path / "sessions"
        exports_dir.mkdir()
        destination_dir.mkdir()
        session_dir.mkdir()

        # Create trial
        workscope_id = "20260119-150000"
        session_uuid = "uuid-idempotent"
        export_1 = exports_dir / "export-run1.txt"
        export_1.write_text(sample_export_content(workscope_id))
        (session_dir / f"{session_uuid}.jsonl").write_text(sample_session_content(workscope_id))

        # First run - should collect
        result_1 = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_1,
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        assert result_1.status == "collected"
        assert (destination_dir / workscope_id).exists()

        # Create new export with same Workscope ID for second run
        export_2 = exports_dir / "export-run2.txt"
        export_2.write_text(sample_export_content(workscope_id))

        # Second run - should skip
        result_2 = collect_single_trial(
            workscope_id=workscope_id,
            export_path=export_2,
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        assert result_2.status == "skipped"
        assert len(result_2.files_copied) == 0

    def test_rerun_after_partial_failure_collects_remaining(
        self,
        tmp_path: Path,
        sample_export_content: Callable[[str], str],
        sample_session_content: Callable[[str], str],
    ) -> None:
        """Test that re-run after partial failure collects only remaining trials.

        Verifies recovery workflow where first run has failures, User fixes
        issues, and second run collects previously failed trials.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
            sample_export_content: Pytest fixture providing factory for export content.
            sample_session_content: Pytest fixture providing factory for session content.
        """
        # Setup directories
        exports_dir = tmp_path / "exports"
        destination_dir = tmp_path / "trials"
        session_dir = tmp_path / "sessions"
        exports_dir.mkdir()
        destination_dir.mkdir()
        session_dir.mkdir()

        # Trial 1: Will succeed on first run
        id_1 = "20260119-160000"
        uuid_1 = "uuid-first-success"
        export_1 = exports_dir / "export1.txt"
        export_1.write_text(sample_export_content(id_1))
        (session_dir / f"{uuid_1}.jsonl").write_text(sample_session_content(id_1))

        # Trial 2: Will fail on first run (missing session)
        id_2 = "20260119-161000"
        export_2 = exports_dir / "export2.txt"
        export_2.write_text(sample_export_content(id_2))

        # First run
        result_1_run1 = collect_single_trial(
            workscope_id=id_1,
            export_path=export_1,
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        result_2_run1 = collect_single_trial(
            workscope_id=id_2,
            export_path=export_2,
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        # Verify first run outcomes
        assert result_1_run1.status == "collected"
        assert result_2_run1.status == "failed"

        # Now add missing session file for Trial 2
        uuid_2 = "uuid-second-success"
        (session_dir / f"{uuid_2}.jsonl").write_text(sample_session_content(id_2))

        # Second run (export2 still exists because failed collections don't delete)
        result_2_run2 = collect_single_trial(
            workscope_id=id_2,
            export_path=export_2,
            session_dir=session_dir,
            destination_dir=destination_dir,
            verbose=False,
        )

        # Verify second run collected the previously failed trial
        assert result_2_run2.status == "collected"
        assert (destination_dir / id_2).exists()
