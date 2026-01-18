"""Tests for Collect Trials Script.

This module provides comprehensive test coverage for the Collect Trials Script
(src/collect_trials.py) including argument parsing, path encoding functions,
and session directory derivation.

The test architecture uses pytest fixtures for dependency injection, enabling
isolated testing without modifying real directories or relying on actual
Claude Code session structures.

Test Categories:
    - Argument parsing (TestArgumentParsing)
    - Path encoding (TestEncodeProjectPath)
    - Session directory derivation (TestDeriveSessionDirectory)
    - Export scanning (TestExportScanning)
"""

from collections.abc import Callable
from pathlib import Path
from unittest.mock import patch

import pytest

from src.collect_trials import (
    create_parser,
    derive_session_directory,
    encode_project_path,
    main,
    scan_exports,
    validate_directory,
)

# =============================================================================
# Fixtures
# =============================================================================


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
        assert str(tmp_exports_dir) in captured.out
        assert str(tmp_destination_dir) in captured.out


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

        results = scan_exports(tmp_exports_dir)

        assert len(results) == 1
        assert results[0][0] == workscope_id
        assert results[0][1] == export_file

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

        results = scan_exports(tmp_exports_dir)

        assert len(results) == 1
        assert results[0][0] == workscope_id

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

        results = scan_exports(tmp_exports_dir)

        assert len(results) == 0
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

        results = scan_exports(tmp_exports_dir)

        assert len(results) == len(workscope_ids)
        extracted_ids = {r[0] for r in results}
        assert extracted_ids == set(workscope_ids)

    def test_empty_exports_directory(self, tmp_exports_dir: Path) -> None:
        """Verify scan_exports returns empty list for empty directory.

        Args:
            tmp_exports_dir: Pytest fixture providing temporary exports directory.
        """
        results = scan_exports(tmp_exports_dir)

        assert results == []

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

        results = scan_exports(tmp_exports_dir)

        assert len(results) == 0
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

        results = scan_exports(tmp_exports_dir)

        assert len(results) == 1
        assert results[0][0] == first_id

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

        results = scan_exports(tmp_exports_dir)

        assert len(results) == 1
        assert results[0][1] == txt_file
