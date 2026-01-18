"""Tests for CC Version Script.

This module provides comprehensive test coverage for the CC Version Script
(src/cc_version.py) including settings file utilities, auto-update management,
version query functions, and command orchestration functions.

The test architecture uses pytest fixtures for dependency injection, enabling
isolated testing without modifying real settings files or executing actual
subprocess commands.

Test Categories:
    - Settings path resolution (get_settings_path)
    - Settings file reading with various error conditions (read_settings)
    - Settings file writing with backup creation (write_settings)
    - Backup file creation and naming (create_backup)
    - Auto-update disable operations (disable_auto_update)
    - Auto-update enable operations (enable_auto_update)
    - Auto-update status queries (get_auto_update_status)
    - Version queries (get_installed_version, get_available_versions,
      get_latest_version, validate_version)
    - Command functions (list_versions, install_version, reset_to_defaults,
      show_status)
    - Prerequisite checking (check_npm_available, check_claude_available,
      validate_prerequisites)
    - CLI argument parsing (create_parser, main)
    - Integration tests (full workflows, backup accumulation, error propagation)
"""

import json
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from src.cc_version import (
    check_claude_available,
    check_npm_available,
    create_backup,
    create_parser,
    disable_auto_update,
    enable_auto_update,
    get_auto_update_status,
    get_available_versions,
    get_installed_version,
    get_latest_version,
    get_settings_path,
    install_version,
    list_versions,
    main,
    read_settings,
    reset_to_defaults,
    show_status,
    validate_prerequisites,
    validate_version,
    write_settings,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def tmp_settings_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory with a settings.json file for testing.

    Creates a temporary directory structure mimicking ~/.claude/ with a valid
    settings.json file containing minimal default content.

    Args:
        tmp_path: Pytest fixture providing temporary directory for test files.

    Returns:
        Path to the temporary settings directory containing settings.json.
    """
    settings_dir = tmp_path / ".claude"
    settings_dir.mkdir(parents=True)
    settings_file = settings_dir / "settings.json"
    settings_file.write_text('{"test": true}\n', encoding="utf-8")
    return settings_dir


@pytest.fixture
def mock_subprocess_run() -> Mock:
    """Create a configurable mock for subprocess.run.

    Factory fixture that returns a Mock object pre-configured to simulate
    subprocess.run behavior. The mock can be customized per-test to return
    specific stdout/stderr content and return codes.

    Returns:
        Mock object configured with default successful subprocess behavior.
        Default configuration:
        - returncode: 0
        - stdout: ""
        - stderr: ""

    Example:
        def test_something(mock_subprocess_run):
            mock_subprocess_run.return_value.stdout = "2.1.6"
            result = function_using_subprocess(run_command=mock_subprocess_run)
    """
    mock = Mock(spec=subprocess.run)
    mock.return_value = Mock(
        returncode=0,
        stdout="",
        stderr="",
    )
    return mock


@pytest.fixture
def sample_settings() -> dict[str, Any]:
    """Provide a factory for creating sample settings dictionaries.

    Returns a dictionary representing a typical Claude Code settings.json
    structure with common configuration options.

    Returns:
        Dictionary containing sample settings with env section.
    """
    return {
        "env": {
            "DISABLE_AUTOUPDATER": "1",
        },
        "theme": "dark",
        "telemetry": False,
    }


@pytest.fixture
def mock_npm_versions() -> list[str]:
    """Provide a standard list of npm version strings for testing.

    Returns a list of version strings representing typical Claude Code
    releases, useful for testing version validation and listing functions.

    Returns:
        List of version strings in ascending order (oldest to newest).
    """
    return [
        "2.0.54",
        "2.0.56",
        "2.0.58",
        "2.0.59",
        "2.0.60",
        "2.0.62",
        "2.0.76",
        "2.1.2",
        "2.1.3",
        "2.1.6",
    ]


# =============================================================================
# Tests for get_settings_path()
# =============================================================================


class TestGetSettingsPath:
    """Tests for the get_settings_path function."""

    def test_returns_correct_path(self) -> None:
        """Verify get_settings_path returns ~/.claude/settings.json path.

        The function should return an absolute path combining the user's
        home directory with .claude/settings.json.
        """
        result = get_settings_path()

        assert result == Path.home() / ".claude" / "settings.json"
        assert result.is_absolute()


# =============================================================================
# Tests for read_settings()
# =============================================================================


class TestReadSettings:
    """Tests for the read_settings function."""

    def test_success_case(self, tmp_settings_dir: Path) -> None:
        """Verify read_settings successfully parses valid JSON settings.

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
        """
        settings_path = tmp_settings_dir / "settings.json"
        settings_path.write_text('{"env": {"KEY": "value"}, "option": true}\n')

        result = read_settings(settings_path=settings_path)

        assert result == {"env": {"KEY": "value"}, "option": True}
        assert isinstance(result, dict)

    def test_file_not_found_error(self, tmp_path: Path) -> None:
        """Verify read_settings raises FileNotFoundError for missing file.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
        """
        nonexistent_path = tmp_path / "nonexistent" / "settings.json"

        with pytest.raises(FileNotFoundError) as exc_info:
            read_settings(settings_path=nonexistent_path)

        assert "Settings file not found" in str(exc_info.value)
        assert str(nonexistent_path) in str(exc_info.value)

    def test_empty_file_error(self, tmp_settings_dir: Path) -> None:
        """Verify read_settings raises ValueError for empty settings file.

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
        """
        settings_path = tmp_settings_dir / "settings.json"
        settings_path.write_text("")

        with pytest.raises(ValueError) as exc_info:
            read_settings(settings_path=settings_path)

        assert "Settings file is empty" in str(exc_info.value)

    def test_invalid_json_error(self, tmp_settings_dir: Path) -> None:
        """Verify read_settings raises ValueError for malformed JSON.

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
        """
        settings_path = tmp_settings_dir / "settings.json"
        settings_path.write_text('{"invalid": json, missing quotes}')

        with pytest.raises(ValueError) as exc_info:
            read_settings(settings_path=settings_path)

        assert "invalid JSON" in str(exc_info.value)

    def test_non_dict_root_error(self, tmp_settings_dir: Path) -> None:
        """Verify read_settings raises TypeError when JSON root is not a dict.

        Settings must be a JSON object (dict), not an array or primitive.

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
        """
        settings_path = tmp_settings_dir / "settings.json"
        settings_path.write_text('["array", "not", "dict"]')

        with pytest.raises(TypeError) as exc_info:
            read_settings(settings_path=settings_path)

        assert "must contain a JSON object" in str(exc_info.value)
        assert "list" in str(exc_info.value)


# =============================================================================
# Tests for write_settings()
# =============================================================================


class TestWriteSettings:
    """Tests for the write_settings function."""

    def test_creates_backup(self, tmp_settings_dir: Path) -> None:
        """Verify write_settings creates a backup before writing.

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
        """
        settings_path = tmp_settings_dir / "settings.json"
        original_content = settings_path.read_text()

        write_settings({"new": "settings"}, settings_path=settings_path)

        # Check backup was created
        backup_files = list(tmp_settings_dir.glob("*.cc_version_backup"))
        assert len(backup_files) == 1

        # Verify backup contains original content
        backup_content = backup_files[0].read_text()
        assert backup_content == original_content

    def test_formats_json_correctly(self, tmp_settings_dir: Path) -> None:
        """Verify write_settings formats JSON with indent=2 and trailing newline.

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
        """
        settings_path = tmp_settings_dir / "settings.json"
        test_settings = {"env": {"KEY": "value"}, "option": True}

        write_settings(test_settings, settings_path=settings_path)

        content = settings_path.read_text()

        # Verify indent=2 formatting
        expected = json.dumps(test_settings, indent=2) + "\n"
        assert content == expected

        # Verify trailing newline
        assert content.endswith("\n")

    def test_invalid_env_type_error(self, tmp_settings_dir: Path) -> None:
        """Verify write_settings raises TypeError when env is not a dict.

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
        """
        settings_path = tmp_settings_dir / "settings.json"
        invalid_settings = {"env": "not_a_dict"}

        with pytest.raises(TypeError) as exc_info:
            write_settings(invalid_settings, settings_path=settings_path)

        assert "'env' is not a dictionary" in str(exc_info.value)


# =============================================================================
# Tests for create_backup()
# =============================================================================


class TestCreateBackup:
    """Tests for the create_backup function."""

    def test_timestamp_format(self, tmp_settings_dir: Path) -> None:
        """Verify create_backup uses injected timestamp in filename.

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
        """
        settings_path = tmp_settings_dir / "settings.json"
        test_timestamp = "20260116_103045"

        backup_path = create_backup(settings_path, timestamp=test_timestamp)

        assert test_timestamp in backup_path.name

    def test_naming_pattern(self, tmp_settings_dir: Path) -> None:
        """Verify create_backup follows correct naming pattern.

        Expected pattern: settings.json.YYYYMMDD_HHMMSS.cc_version_backup

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
        """
        settings_path = tmp_settings_dir / "settings.json"
        test_timestamp = "20260116_103045"

        backup_path = create_backup(settings_path, timestamp=test_timestamp)

        expected_name = f"settings.json.{test_timestamp}.cc_version_backup"
        assert backup_path.name == expected_name
        assert backup_path.parent == settings_path.parent
        assert backup_path.exists()

        # Verify content was copied
        original_content = settings_path.read_text()
        backup_content = backup_path.read_text()
        assert backup_content == original_content


# =============================================================================
# Tests for disable_auto_update()
# =============================================================================


class TestDisableAutoUpdate:
    """Tests for the disable_auto_update function."""

    def test_creates_env_key(self, tmp_settings_dir: Path) -> None:
        """Verify disable_auto_update creates the env key when missing.

        When settings.json has no env section, disable_auto_update should
        create the env dict and add the DISABLE_AUTOUPDATER key.

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
        """
        settings_path = tmp_settings_dir / "settings.json"
        # Start with settings that have no env key
        settings_path.write_text('{"theme": "dark"}', encoding="utf-8")

        disable_auto_update(settings_path=settings_path)

        # Verify env key was created
        result = json.loads(settings_path.read_text())
        assert "env" in result
        assert "DISABLE_AUTOUPDATER" in result["env"]

    def test_sets_correct_value(self, tmp_settings_dir: Path) -> None:
        """Verify disable_auto_update sets DISABLE_AUTOUPDATER to "1".

        The value must be the string "1", not a boolean or integer.

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
        """
        settings_path = tmp_settings_dir / "settings.json"
        settings_path.write_text('{"theme": "dark"}', encoding="utf-8")

        disable_auto_update(settings_path=settings_path)

        result = json.loads(settings_path.read_text())
        assert result["env"]["DISABLE_AUTOUPDATER"] == "1"
        assert isinstance(result["env"]["DISABLE_AUTOUPDATER"], str)

    def test_idempotent_behavior(self, tmp_settings_dir: Path) -> None:
        """Verify disable_auto_update is idempotent when already disabled.

        When auto-update is already disabled, the function should exit
        successfully with code 0 without modifying the file.

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
        """
        settings_path = tmp_settings_dir / "settings.json"
        # Settings already have auto-update disabled
        settings_path.write_text(
            '{"env": {"DISABLE_AUTOUPDATER": "1"}, "theme": "dark"}',
            encoding="utf-8",
        )
        original_content = settings_path.read_text()

        with pytest.raises(SystemExit) as exc_info:
            disable_auto_update(settings_path=settings_path)

        # Should exit with code 0 (success)
        assert exc_info.value.code == 0

        # File should not be modified (no backup created)
        backup_files = list(tmp_settings_dir.glob("*.cc_version_backup"))
        assert len(backup_files) == 0

        # Content should be unchanged
        assert settings_path.read_text() == original_content


# =============================================================================
# Tests for enable_auto_update()
# =============================================================================


class TestEnableAutoUpdate:
    """Tests for the enable_auto_update function."""

    def test_removes_key(self, tmp_settings_dir: Path) -> None:
        """Verify enable_auto_update removes the DISABLE_AUTOUPDATER key.

        When auto-update is disabled, enable_auto_update should remove
        the DISABLE_AUTOUPDATER key from the env section.

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
        """
        settings_path = tmp_settings_dir / "settings.json"
        settings_path.write_text(
            '{"env": {"DISABLE_AUTOUPDATER": "1", "OTHER_KEY": "value"}, "theme": "dark"}',
            encoding="utf-8",
        )

        enable_auto_update(settings_path=settings_path)

        result = json.loads(settings_path.read_text())
        assert "DISABLE_AUTOUPDATER" not in result["env"]

    def test_cleans_empty_env_dict(self, tmp_settings_dir: Path) -> None:
        """Verify enable_auto_update removes empty env dict after key removal.

        When DISABLE_AUTOUPDATER is the only key in the env section,
        removing it should also remove the entire env dict.

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
        """
        settings_path = tmp_settings_dir / "settings.json"
        settings_path.write_text(
            '{"env": {"DISABLE_AUTOUPDATER": "1"}, "theme": "dark"}',
            encoding="utf-8",
        )

        enable_auto_update(settings_path=settings_path)

        result = json.loads(settings_path.read_text())
        assert "env" not in result
        assert result == {"theme": "dark"}

    def test_idempotent_behavior(self, tmp_settings_dir: Path) -> None:
        """Verify enable_auto_update is idempotent when already enabled.

        When auto-update is already enabled (no DISABLE_AUTOUPDATER key),
        the function should exit successfully with code 0 without modifying
        the file.

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
        """
        settings_path = tmp_settings_dir / "settings.json"
        # Settings with no env section (auto-update enabled by default)
        settings_path.write_text('{"theme": "dark"}', encoding="utf-8")
        original_content = settings_path.read_text()

        with pytest.raises(SystemExit) as exc_info:
            enable_auto_update(settings_path=settings_path)

        # Should exit with code 0 (success)
        assert exc_info.value.code == 0

        # File should not be modified (no backup created)
        backup_files = list(tmp_settings_dir.glob("*.cc_version_backup"))
        assert len(backup_files) == 0

        # Content should be unchanged
        assert settings_path.read_text() == original_content

    def test_preserves_other_env_keys(self, tmp_settings_dir: Path) -> None:
        """Verify enable_auto_update preserves other keys in the env section.

        When removing DISABLE_AUTOUPDATER, other keys in the env section
        should remain unchanged.

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
        """
        settings_path = tmp_settings_dir / "settings.json"
        settings_path.write_text(
            '{"env": {"DISABLE_AUTOUPDATER": "1", "API_KEY": "secret", "DEBUG": "true"}, "theme": "dark"}',
            encoding="utf-8",
        )

        enable_auto_update(settings_path=settings_path)

        result = json.loads(settings_path.read_text())
        assert "env" in result
        assert "DISABLE_AUTOUPDATER" not in result["env"]
        assert result["env"]["API_KEY"] == "secret"
        assert result["env"]["DEBUG"] == "true"
        assert result["theme"] == "dark"


# =============================================================================
# Tests for get_auto_update_status()
# =============================================================================


class TestGetAutoUpdateStatus:
    """Tests for the get_auto_update_status function."""

    def test_returns_disabled_when_set(self, tmp_settings_dir: Path) -> None:
        """Verify get_auto_update_status returns 'Disabled' when DISABLE_AUTOUPDATER is set.

        When the settings file contains env.DISABLE_AUTOUPDATER set to "1",
        the function should return the string "Disabled".

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
        """
        settings_path = tmp_settings_dir / "settings.json"
        settings_path.write_text(
            '{"env": {"DISABLE_AUTOUPDATER": "1"}, "theme": "dark"}',
            encoding="utf-8",
        )

        result = get_auto_update_status(settings_path=settings_path)

        assert result == "Disabled"

    def test_returns_enabled_when_unset(self, tmp_settings_dir: Path) -> None:
        """Verify get_auto_update_status returns 'Enabled' when DISABLE_AUTOUPDATER is not set.

        When the settings file does not contain env.DISABLE_AUTOUPDATER,
        the function should return the string "Enabled".

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
        """
        settings_path = tmp_settings_dir / "settings.json"
        settings_path.write_text(
            '{"theme": "dark", "other": "setting"}',
            encoding="utf-8",
        )

        result = get_auto_update_status(settings_path=settings_path)

        assert result == "Enabled"


# =============================================================================
# Tests for get_installed_version()
# =============================================================================


class TestGetInstalledVersion:
    """Tests for the get_installed_version function."""

    def test_parses_output_correctly(self, mock_subprocess_run: Mock) -> None:
        """Verify get_installed_version parses claude --version output correctly.

        The function should extract the version number from output in the
        format "2.1.3 (Claude Code)" and return just the version string.

        Args:
            mock_subprocess_run: Pytest fixture providing mock subprocess.run.
        """
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "2.1.3 (Claude Code)\n"

        result = get_installed_version(run_command=mock_subprocess_run)

        assert result == "2.1.3"
        mock_subprocess_run.assert_called_once_with(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_command_failure_error(self, mock_subprocess_run: Mock) -> None:
        """Verify get_installed_version raises RuntimeError on command failure.

        When the claude command fails (non-zero exit code), the function
        should raise RuntimeError with details about the failure.

        Args:
            mock_subprocess_run: Pytest fixture providing mock subprocess.run.
        """
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stderr = "Command not found"

        with pytest.raises(RuntimeError) as exc_info:
            get_installed_version(run_command=mock_subprocess_run)

        assert "Failed to get Claude Code version" in str(exc_info.value)
        assert "Exit code: 1" in str(exc_info.value)

    def test_empty_output_error(self, mock_subprocess_run: Mock) -> None:
        """Verify get_installed_version raises RuntimeError on empty output.

        When the claude command succeeds but returns empty output, the
        function should raise RuntimeError indicating the issue.

        Args:
            mock_subprocess_run: Pytest fixture providing mock subprocess.run.
        """
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = ""

        with pytest.raises(RuntimeError) as exc_info:
            get_installed_version(run_command=mock_subprocess_run)

        assert "empty output" in str(exc_info.value).lower()


# =============================================================================
# Tests for get_available_versions()
# =============================================================================


class TestGetAvailableVersions:
    """Tests for the get_available_versions function."""

    def test_parses_json_array(
        self, mock_subprocess_run: Mock, mock_npm_versions: list[str]
    ) -> None:
        """Verify get_available_versions parses npm JSON array correctly.

        The function should parse the JSON array returned by npm and return
        a list of version strings.

        Args:
            mock_subprocess_run: Pytest fixture providing mock subprocess.run.
            mock_npm_versions: Pytest fixture providing sample version list.
        """
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = json.dumps(mock_npm_versions)

        result = get_available_versions(run_command=mock_subprocess_run)

        assert result == mock_npm_versions
        assert len(result) == len(mock_npm_versions)
        assert result[0] == "2.0.54"
        assert result[-1] == "2.1.6"
        mock_subprocess_run.assert_called_once_with(
            ["npm", "view", "@anthropic-ai/claude-code", "versions", "--json"],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_npm_failure_error(self, mock_subprocess_run: Mock) -> None:
        """Verify get_available_versions raises RuntimeError on npm failure.

        When the npm command fails (non-zero exit code), the function
        should raise RuntimeError with details about the failure.

        Args:
            mock_subprocess_run: Pytest fixture providing mock subprocess.run.
        """
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stderr = "npm ERR! code E404"

        with pytest.raises(RuntimeError) as exc_info:
            get_available_versions(run_command=mock_subprocess_run)

        assert "Failed to fetch versions from npm" in str(exc_info.value)
        assert "Exit code: 1" in str(exc_info.value)

    def test_invalid_json_error(self, mock_subprocess_run: Mock) -> None:
        """Verify get_available_versions raises RuntimeError on invalid JSON.

        When the npm command returns invalid JSON, the function should
        raise RuntimeError indicating the parsing failure.

        Args:
            mock_subprocess_run: Pytest fixture providing mock subprocess.run.
        """
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "not valid json {["

        with pytest.raises(RuntimeError) as exc_info:
            get_available_versions(run_command=mock_subprocess_run)

        assert "Failed to parse npm JSON output" in str(exc_info.value)


# =============================================================================
# Tests for get_latest_version()
# =============================================================================


class TestGetLatestVersion:
    """Tests for the get_latest_version function."""

    def test_returns_last_element(
        self, mock_subprocess_run: Mock, mock_npm_versions: list[str]
    ) -> None:
        """Verify get_latest_version returns the last element from versions list.

        The function should call get_available_versions and return the last
        element, which represents the most recent release.

        Args:
            mock_subprocess_run: Pytest fixture providing mock subprocess.run.
            mock_npm_versions: Pytest fixture providing sample version list.
        """
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = json.dumps(mock_npm_versions)

        result = get_latest_version(run_command=mock_subprocess_run)

        assert result == "2.1.6"
        assert result == mock_npm_versions[-1]


# =============================================================================
# Tests for validate_version()
# =============================================================================


class TestValidateVersion:
    """Tests for the validate_version function."""

    def test_returns_true_for_valid(
        self, mock_subprocess_run: Mock, mock_npm_versions: list[str]
    ) -> None:
        """Verify validate_version returns True for a valid version.

        When the requested version exists in the available versions list,
        the function should return True.

        Args:
            mock_subprocess_run: Pytest fixture providing mock subprocess.run.
            mock_npm_versions: Pytest fixture providing sample version list.
        """
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = json.dumps(mock_npm_versions)

        result = validate_version("2.0.58", run_command=mock_subprocess_run)

        assert result is True

    def test_returns_false_for_invalid(
        self, mock_subprocess_run: Mock, mock_npm_versions: list[str]
    ) -> None:
        """Verify validate_version returns False for an invalid version.

        When the requested version does not exist in the available versions
        list, the function should return False.

        Args:
            mock_subprocess_run: Pytest fixture providing mock subprocess.run.
            mock_npm_versions: Pytest fixture providing sample version list.
        """
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = json.dumps(mock_npm_versions)

        result = validate_version("9.9.9", run_command=mock_subprocess_run)

        assert result is False


# =============================================================================
# Tests for list_versions()
# =============================================================================


class TestListVersions:
    """Tests for the list_versions function."""

    def test_passes_through_npm_output(
        self, mock_subprocess_run: Mock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify list_versions passes npm output directly to stdout.

        The function should execute npm view without --json flag and print
        the human-readable output directly to stdout without modification.

        Args:
            mock_subprocess_run: Mock for subprocess.run to simulate npm command.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        npm_output = "[ '2.0.54', '2.0.56', '2.0.58', '2.1.6' ]\n"
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = npm_output

        list_versions(run_command=mock_subprocess_run)

        captured = capsys.readouterr()
        assert captured.out == npm_output
        mock_subprocess_run.assert_called_once_with(
            ["npm", "view", "@anthropic-ai/claude-code", "versions"],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_npm_error_handling(
        self, mock_subprocess_run: Mock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify list_versions exits with code 1 on npm failure.

        When npm command fails, the function should print an error message
        to stderr and exit with code 1.

        Args:
            mock_subprocess_run: Mock for subprocess.run to simulate npm failure.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stderr = "npm ERR! network error"

        with pytest.raises(SystemExit) as exc_info:
            list_versions(run_command=mock_subprocess_run)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "npm command failed" in captured.err.lower()


# =============================================================================
# Tests for install_version()
# =============================================================================


class TestInstallVersion:
    """Tests for the install_version function."""

    def test_validates_version_first(
        self,
        mock_subprocess_run: Mock,
        mock_npm_versions: list[str],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify install_version validates the version before installation.

        The function should call npm view to validate that the requested
        version exists before attempting any installation commands.

        Args:
            mock_subprocess_run: Mock for subprocess.run to simulate commands.
            mock_npm_versions: Pytest fixture providing sample version list.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = json.dumps(mock_npm_versions)

        # Configure mock to return success for all npm commands
        def side_effect(*args: Any, **kwargs: Any) -> Mock:
            result = Mock()
            result.returncode = 0
            if args and len(args[0]) > 0:
                cmd = args[0]
                if cmd == ["npm", "view", "@anthropic-ai/claude-code", "versions", "--json"]:
                    result.stdout = json.dumps(mock_npm_versions)
                elif cmd == ["claude", "--version"]:
                    result.stdout = "2.0.58 (Claude Code)\n"
                else:
                    result.stdout = ""
            result.stderr = ""
            return result

        mock_subprocess_run.side_effect = side_effect

        install_version("2.0.58", run_command=mock_subprocess_run)

        captured = capsys.readouterr()
        assert "Validating version 2.0.58" in captured.out

    def test_invalid_version_exits(
        self,
        mock_subprocess_run: Mock,
        mock_npm_versions: list[str],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify install_version exits with code 1 for invalid version.

        When the requested version does not exist in the available versions,
        the function should print an error message and exit with code 1.

        Args:
            mock_subprocess_run: Mock for subprocess.run to simulate commands.
            mock_npm_versions: Pytest fixture providing sample version list.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = json.dumps(mock_npm_versions)

        with pytest.raises(SystemExit) as exc_info:
            install_version("9.9.9", run_command=mock_subprocess_run)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Version '9.9.9' not found" in captured.err
        assert "--list" in captured.err

    def test_executes_npm_sequence(
        self,
        mock_subprocess_run: Mock,
        mock_npm_versions: list[str],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify install_version executes the correct npm command sequence.

        The function should execute: npm uninstall, npm cache clean, npm install
        in that exact order for a valid version.

        Args:
            mock_subprocess_run: Mock for subprocess.run to simulate commands.
            mock_npm_versions: Pytest fixture providing sample version list.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        call_sequence: list[list[str]] = []

        def side_effect(*args: Any, **kwargs: Any) -> Mock:
            result = Mock()
            result.returncode = 0
            result.stderr = ""
            if args and len(args[0]) > 0:
                cmd = args[0]
                call_sequence.append(list(cmd))
                if cmd == ["npm", "view", "@anthropic-ai/claude-code", "versions", "--json"]:
                    result.stdout = json.dumps(mock_npm_versions)
                elif cmd == ["claude", "--version"]:
                    result.stdout = "2.0.58 (Claude Code)\n"
                else:
                    result.stdout = ""
            return result

        mock_subprocess_run.side_effect = side_effect

        install_version("2.0.58", run_command=mock_subprocess_run)

        # Verify the npm sequence was executed in order
        assert ["npm", "uninstall", "-g", "@anthropic-ai/claude-code"] in call_sequence
        assert ["npm", "cache", "clean", "--force"] in call_sequence
        assert ["npm", "install", "-g", "@anthropic-ai/claude-code@2.0.58"] in call_sequence

        # Verify order: uninstall before cache clean before install
        uninstall_idx = call_sequence.index(["npm", "uninstall", "-g", "@anthropic-ai/claude-code"])
        cache_idx = call_sequence.index(["npm", "cache", "clean", "--force"])
        install_idx = call_sequence.index(
            ["npm", "install", "-g", "@anthropic-ai/claude-code@2.0.58"]
        )
        assert uninstall_idx < cache_idx < install_idx

    def test_verifies_installation(
        self,
        mock_subprocess_run: Mock,
        mock_npm_versions: list[str],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify install_version checks installed version after installation.

        After installing, the function should run claude --version to verify
        the correct version was installed and report success.

        Args:
            mock_subprocess_run: Mock for subprocess.run to simulate commands.
            mock_npm_versions: Pytest fixture providing sample version list.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """

        def side_effect(*args: Any, **kwargs: Any) -> Mock:
            result = Mock()
            result.returncode = 0
            result.stderr = ""
            if args and len(args[0]) > 0:
                cmd = args[0]
                if cmd == ["npm", "view", "@anthropic-ai/claude-code", "versions", "--json"]:
                    result.stdout = json.dumps(mock_npm_versions)
                elif cmd == ["claude", "--version"]:
                    result.stdout = "2.0.58 (Claude Code)\n"
                else:
                    result.stdout = ""
            return result

        mock_subprocess_run.side_effect = side_effect

        install_version("2.0.58", run_command=mock_subprocess_run)

        captured = capsys.readouterr()
        assert "Successfully installed Claude Code version 2.0.58" in captured.out


# =============================================================================
# Tests for reset_to_defaults()
# =============================================================================


class TestResetToDefaults:
    """Tests for the reset_to_defaults function."""

    def test_enables_auto_update(
        self,
        tmp_settings_dir: Path,
        mock_subprocess_run: Mock,
        mock_npm_versions: list[str],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify reset_to_defaults enables auto-update when disabled.

        The function should remove env.DISABLE_AUTOUPDATER from settings
        as part of resetting to defaults.

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
            mock_subprocess_run: Mock for subprocess.run to simulate commands.
            mock_npm_versions: Pytest fixture providing sample version list.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        settings_path = tmp_settings_dir / "settings.json"
        settings_path.write_text(
            '{"env": {"DISABLE_AUTOUPDATER": "1"}, "theme": "dark"}',
            encoding="utf-8",
        )

        def side_effect(*args: Any, **kwargs: Any) -> Mock:
            result = Mock()
            result.returncode = 0
            result.stderr = ""
            if args and len(args[0]) > 0:
                cmd = args[0]
                if cmd == ["npm", "view", "@anthropic-ai/claude-code", "versions", "--json"]:
                    result.stdout = json.dumps(mock_npm_versions)
                elif cmd == ["claude", "--version"]:
                    result.stdout = "2.1.6 (Claude Code)\n"
                else:
                    result.stdout = ""
            return result

        mock_subprocess_run.side_effect = side_effect

        reset_to_defaults(run_command=mock_subprocess_run, settings_path=settings_path)

        # Verify auto-update is enabled (DISABLE_AUTOUPDATER removed)
        result = json.loads(settings_path.read_text())
        assert "env" not in result or "DISABLE_AUTOUPDATER" not in result.get("env", {})

        captured = capsys.readouterr()
        assert "Auto-update enabled" in captured.out

    def test_installs_latest(
        self,
        tmp_settings_dir: Path,
        mock_subprocess_run: Mock,
        mock_npm_versions: list[str],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify reset_to_defaults installs the latest version.

        The function should fetch the latest version from npm and install it.

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
            mock_subprocess_run: Mock for subprocess.run to simulate commands.
            mock_npm_versions: Pytest fixture providing sample version list.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        settings_path = tmp_settings_dir / "settings.json"
        settings_path.write_text('{"theme": "dark"}', encoding="utf-8")

        call_sequence: list[list[str]] = []

        def side_effect(*args: Any, **kwargs: Any) -> Mock:
            result = Mock()
            result.returncode = 0
            result.stderr = ""
            if args and len(args[0]) > 0:
                cmd = args[0]
                call_sequence.append(list(cmd))
                if cmd == ["npm", "view", "@anthropic-ai/claude-code", "versions", "--json"]:
                    result.stdout = json.dumps(mock_npm_versions)
                elif cmd == ["claude", "--version"]:
                    result.stdout = "2.1.6 (Claude Code)\n"
                else:
                    result.stdout = ""
            return result

        mock_subprocess_run.side_effect = side_effect

        reset_to_defaults(run_command=mock_subprocess_run, settings_path=settings_path)

        # Verify latest version (2.1.6) was installed
        assert ["npm", "install", "-g", "@anthropic-ai/claude-code@2.1.6"] in call_sequence

        captured = capsys.readouterr()
        assert "Latest version is 2.1.6" in captured.out
        assert "Reset to defaults complete" in captured.out


# =============================================================================
# Tests for show_status()
# =============================================================================


class TestShowStatus:
    """Tests for the show_status function."""

    def test_displays_all_info(
        self,
        tmp_settings_dir: Path,
        mock_subprocess_run: Mock,
        mock_npm_versions: list[str],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify show_status displays auto-update status, installed and latest versions.

        The function should print three lines of information: auto-update state,
        currently installed version, and latest available version.

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
            mock_subprocess_run: Mock for subprocess.run to simulate commands.
            mock_npm_versions: Pytest fixture providing sample version list.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        settings_path = tmp_settings_dir / "settings.json"
        settings_path.write_text(
            '{"env": {"DISABLE_AUTOUPDATER": "1"}, "theme": "dark"}',
            encoding="utf-8",
        )

        def side_effect(*args: Any, **kwargs: Any) -> Mock:
            result = Mock()
            result.returncode = 0
            result.stderr = ""
            if args and len(args[0]) > 0:
                cmd = args[0]
                if cmd == ["npm", "view", "@anthropic-ai/claude-code", "versions", "--json"]:
                    result.stdout = json.dumps(mock_npm_versions)
                elif cmd == ["claude", "--version"]:
                    result.stdout = "2.0.58 (Claude Code)\n"
                else:
                    result.stdout = ""
            return result

        mock_subprocess_run.side_effect = side_effect

        show_status(run_command=mock_subprocess_run, settings_path=settings_path)

        captured = capsys.readouterr()
        assert "Auto-update: Disabled" in captured.out
        assert "Installed version: 2.0.58" in captured.out
        assert "Latest version: 2.1.6" in captured.out


# =============================================================================
# Tests for check_npm_available()
# =============================================================================


class TestCheckNpmAvailable:
    """Tests for the check_npm_available function."""

    def test_returns_true_when_npm_succeeds(self, mock_subprocess_run: Mock) -> None:
        """Verify check_npm_available returns True when npm command succeeds.

        When npm --version executes successfully with return code 0,
        the function should return True.

        Args:
            mock_subprocess_run: Mock for subprocess.run to simulate npm command.
        """
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "8.5.0\n"

        result = check_npm_available(run_command=mock_subprocess_run)

        assert result is True
        mock_subprocess_run.assert_called_once_with(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_returns_false_when_npm_fails(self, mock_subprocess_run: Mock) -> None:
        """Verify check_npm_available returns False when npm command fails.

        When npm --version fails with a non-zero return code, the function
        should return False.

        Args:
            mock_subprocess_run: Mock for subprocess.run to simulate npm failure.
        """
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stderr = "command not found"

        result = check_npm_available(run_command=mock_subprocess_run)

        assert result is False

    def test_returns_false_when_file_not_found(self, mock_subprocess_run: Mock) -> None:
        """Verify check_npm_available returns False when npm command not found.

        When subprocess.run raises FileNotFoundError (npm not in PATH),
        the function should catch the exception and return False.

        Args:
            mock_subprocess_run: Mock for subprocess.run to simulate missing npm.
        """
        mock_subprocess_run.side_effect = FileNotFoundError("npm not found")

        result = check_npm_available(run_command=mock_subprocess_run)

        assert result is False


# =============================================================================
# Tests for check_claude_available()
# =============================================================================


class TestCheckClaudeAvailable:
    """Tests for the check_claude_available function."""

    def test_returns_true_when_claude_succeeds(self, mock_subprocess_run: Mock) -> None:
        """Verify check_claude_available returns True when claude command succeeds.

        When claude --version executes successfully with return code 0,
        the function should return True.

        Args:
            mock_subprocess_run: Mock for subprocess.run to simulate claude command.
        """
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "2.1.6 (Claude Code)\n"

        result = check_claude_available(run_command=mock_subprocess_run)

        assert result is True
        mock_subprocess_run.assert_called_once_with(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_returns_false_when_claude_fails(self, mock_subprocess_run: Mock) -> None:
        """Verify check_claude_available returns False when claude command fails.

        When claude --version fails with a non-zero return code, the function
        should return False.

        Args:
            mock_subprocess_run: Mock for subprocess.run to simulate claude failure.
        """
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stderr = "command not found"

        result = check_claude_available(run_command=mock_subprocess_run)

        assert result is False

    def test_returns_false_when_file_not_found(self, mock_subprocess_run: Mock) -> None:
        """Verify check_claude_available returns False when claude command not found.

        When subprocess.run raises FileNotFoundError (claude not in PATH),
        the function should catch the exception and return False.

        Args:
            mock_subprocess_run: Mock for subprocess.run to simulate missing claude.
        """
        mock_subprocess_run.side_effect = FileNotFoundError("claude not found")

        result = check_claude_available(run_command=mock_subprocess_run)

        assert result is False


# =============================================================================
# Tests for validate_prerequisites()
# =============================================================================


class TestValidatePrerequisites:
    """Tests for the validate_prerequisites function."""

    def test_returns_true_when_all_pass(
        self, mock_subprocess_run: Mock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify validate_prerequisites returns True when all tools are available.

        When both npm and claude commands succeed, the function should
        return True without printing any error messages.

        Args:
            mock_subprocess_run: Mock for subprocess.run to simulate commands.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """

        def side_effect(*args: Any, **kwargs: Any) -> Mock:
            result = Mock()
            result.returncode = 0
            result.stderr = ""
            if args and args[0] == ["npm", "--version"]:
                result.stdout = "8.5.0\n"
            elif args and args[0] == ["claude", "--version"]:
                result.stdout = "2.1.6 (Claude Code)\n"
            return result

        mock_subprocess_run.side_effect = side_effect

        result = validate_prerequisites(run_command=mock_subprocess_run)

        assert result is True
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_returns_false_when_npm_missing(
        self, mock_subprocess_run: Mock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify validate_prerequisites returns False when npm is missing.

        When npm command fails but claude succeeds, the function should
        return False and print an error message for npm.

        Args:
            mock_subprocess_run: Mock for subprocess.run to simulate commands.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """

        def side_effect(*args: Any, **kwargs: Any) -> Mock:
            result = Mock()
            result.stderr = ""
            if args and args[0] == ["npm", "--version"]:
                result.returncode = 1
                result.stdout = ""
            elif args and args[0] == ["claude", "--version"]:
                result.returncode = 0
                result.stdout = "2.1.6 (Claude Code)\n"
            return result

        mock_subprocess_run.side_effect = side_effect

        result = validate_prerequisites(run_command=mock_subprocess_run)

        assert result is False
        captured = capsys.readouterr()
        assert "npm is not installed" in captured.err

    def test_returns_false_when_claude_missing(
        self, mock_subprocess_run: Mock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify validate_prerequisites returns False when claude is missing.

        When npm succeeds but claude command fails, the function should
        return False and print an error message for claude.

        Args:
            mock_subprocess_run: Mock for subprocess.run to simulate commands.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """

        def side_effect(*args: Any, **kwargs: Any) -> Mock:
            result = Mock()
            result.stderr = ""
            if args and args[0] == ["npm", "--version"]:
                result.returncode = 0
                result.stdout = "8.5.0\n"
            elif args and args[0] == ["claude", "--version"]:
                result.returncode = 1
                result.stdout = ""
            return result

        mock_subprocess_run.side_effect = side_effect

        result = validate_prerequisites(run_command=mock_subprocess_run)

        assert result is False
        captured = capsys.readouterr()
        assert "Claude Code is not installed" in captured.err


# =============================================================================
# Tests for create_parser()
# =============================================================================


class TestCreateParser:
    """Tests for the create_parser function."""

    def test_mutual_exclusivity(self) -> None:
        """Verify create_parser enforces mutual exclusivity of commands.

        When multiple command flags are provided, argparse should raise
        an error indicating that only one command can be specified.
        """
        parser = create_parser()

        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--disable-auto-update", "--enable-auto-update"])

        # argparse exits with code 2 for argument errors
        assert exc_info.value.code == 2  # noqa: PLR2004

    def test_requires_command(self) -> None:
        """Verify create_parser requires at least one command to be specified.

        When no command flags are provided, argparse should raise an error
        indicating that a command is required.
        """
        parser = create_parser()

        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args([])

        # argparse exits with code 2 for missing required arguments
        assert exc_info.value.code == 2  # noqa: PLR2004

    def test_install_accepts_version(self) -> None:
        """Verify create_parser correctly parses --install with version argument.

        The --install flag should accept a version string argument and
        store it in the parsed args.
        """
        parser = create_parser()

        args = parser.parse_args(["--install", "2.0.58"])

        assert args.install == "2.0.58"

    def test_status_flag_parsed(self) -> None:
        """Verify create_parser correctly parses --status flag.

        The --status flag should be recognized and set to True in parsed args.
        """
        parser = create_parser()

        args = parser.parse_args(["--status"])

        assert args.status is True

    def test_reset_flag_parsed(self) -> None:
        """Verify create_parser correctly parses --reset flag.

        The --reset flag should be recognized and set to True in parsed args.
        """
        parser = create_parser()

        args = parser.parse_args(["--reset"])

        assert args.reset is True

    def test_list_flag_parsed(self) -> None:
        """Verify create_parser correctly parses --list flag.

        The --list flag should be recognized and stored as list_versions
        in parsed args (due to dest parameter).
        """
        parser = create_parser()

        args = parser.parse_args(["--list"])

        assert args.list_versions is True


# =============================================================================
# Tests for main()
# =============================================================================


class TestMain:
    """Tests for the main function."""

    def test_validates_prerequisites_first(
        self, mock_subprocess_run: Mock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify main validates prerequisites before processing commands.

        The main function should check prerequisites first and return 1
        if they fail, before attempting to parse or execute any commands.

        Args:
            mock_subprocess_run: Mock for subprocess.run to simulate commands.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        # Mock prerequisites to fail
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stderr = ""

        with patch("src.cc_version.validate_prerequisites") as mock_validate:
            mock_validate.return_value = False

            result = main()

        assert result == 1

    def test_dispatches_to_status_handler(
        self,
        tmp_settings_dir: Path,
        mock_subprocess_run: Mock,
        mock_npm_versions: list[str],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify main dispatches --status to show_status handler.

        When --status is provided, main should call show_status and display
        the current status information.

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
            mock_subprocess_run: Mock for subprocess.run to simulate commands.
            mock_npm_versions: Pytest fixture providing sample version list.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """

        def run_side_effect(*args: Any, **kwargs: Any) -> Mock:
            result = Mock()
            result.returncode = 0
            result.stderr = ""
            if args and args[0] == ["npm", "--version"]:
                result.stdout = "8.5.0\n"
            elif args and args[0] == ["claude", "--version"]:
                result.stdout = "2.1.6 (Claude Code)\n"
            elif args and args[0] == [
                "npm",
                "view",
                "@anthropic-ai/claude-code",
                "versions",
                "--json",
            ]:
                result.stdout = json.dumps(mock_npm_versions)
            return result

        settings_path = tmp_settings_dir / "settings.json"
        settings_path.write_text('{"theme": "dark"}', encoding="utf-8")

        with patch("sys.argv", ["cc_version.py", "--status"]):
            with patch("src.cc_version.subprocess.run", side_effect=run_side_effect):
                with patch("src.cc_version.get_settings_path", return_value=settings_path):
                    result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "Auto-update:" in captured.out

    def test_dispatches_to_list_handler(
        self,
        mock_subprocess_run: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify main dispatches --list to list_versions handler.

        When --list is provided, main should call list_versions and display
        available versions from npm.

        Args:
            mock_subprocess_run: Mock for subprocess.run to simulate commands.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        npm_output = "[ '2.0.54', '2.0.56', '2.1.6' ]\n"

        def run_side_effect(*args: Any, **kwargs: Any) -> Mock:
            result = Mock()
            result.returncode = 0
            result.stderr = ""
            if args and args[0] == ["npm", "--version"]:
                result.stdout = "8.5.0\n"
            elif args and args[0] == ["claude", "--version"]:
                result.stdout = "2.1.6 (Claude Code)\n"
            elif args and args[0] == ["npm", "view", "@anthropic-ai/claude-code", "versions"]:
                result.stdout = npm_output
            return result

        with patch("sys.argv", ["cc_version.py", "--list"]):
            with patch("src.cc_version.subprocess.run", side_effect=run_side_effect):
                result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert npm_output in captured.out


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for full workflows and error propagation."""

    def test_full_workflow_disable_install_status_reset(
        self,
        tmp_settings_dir: Path,
        mock_subprocess_run: Mock,
        mock_npm_versions: list[str],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify full workflow: disable auto-update, install, status, reset.

        This integration test exercises the recommended trial workflow:
        1. Disable auto-updates
        2. Install a specific version
        3. Check status
        4. Reset to defaults

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
            mock_subprocess_run: Mock for subprocess.run to simulate commands.
            mock_npm_versions: Pytest fixture providing sample version list.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        settings_path = tmp_settings_dir / "settings.json"
        settings_path.write_text('{"theme": "dark"}', encoding="utf-8")

        def run_side_effect(*args: Any, **kwargs: Any) -> Mock:
            result = Mock()
            result.returncode = 0
            result.stderr = ""
            if args and args[0] == [
                "npm",
                "view",
                "@anthropic-ai/claude-code",
                "versions",
                "--json",
            ]:
                result.stdout = json.dumps(mock_npm_versions)
            elif args and args[0] == ["claude", "--version"]:
                # Return the version that should be installed at this point
                result.stdout = "2.0.58 (Claude Code)\n"
            else:
                result.stdout = ""
            return result

        mock_subprocess_run.side_effect = run_side_effect

        # Step 1: Disable auto-update
        disable_auto_update(settings_path=settings_path)
        settings = json.loads(settings_path.read_text())
        assert settings.get("env", {}).get("DISABLE_AUTOUPDATER") == "1"

        # Step 2: Install specific version
        install_version("2.0.58", run_command=mock_subprocess_run, settings_path=settings_path)

        # Step 3: Check status
        show_status(run_command=mock_subprocess_run, settings_path=settings_path)
        captured = capsys.readouterr()
        assert "Auto-update: Disabled" in captured.out
        assert "Installed version: 2.0.58" in captured.out

        # Step 4: Reset to defaults
        def reset_side_effect(*args: Any, **kwargs: Any) -> Mock:
            result = Mock()
            result.returncode = 0
            result.stderr = ""
            if args and args[0] == [
                "npm",
                "view",
                "@anthropic-ai/claude-code",
                "versions",
                "--json",
            ]:
                result.stdout = json.dumps(mock_npm_versions)
            elif args and args[0] == ["claude", "--version"]:
                result.stdout = "2.1.6 (Claude Code)\n"
            else:
                result.stdout = ""
            return result

        mock_subprocess_run.side_effect = reset_side_effect
        reset_to_defaults(run_command=mock_subprocess_run, settings_path=settings_path)

        # Verify reset state
        settings = json.loads(settings_path.read_text())
        assert "env" not in settings or "DISABLE_AUTOUPDATER" not in settings.get("env", {})

    def test_backup_accumulation_across_operations(self, tmp_settings_dir: Path) -> None:
        """Verify backups accumulate across multiple operations.

        Each settings modification should create a new timestamped backup,
        and all backups should be preserved with unique names.

        Args:
            tmp_settings_dir: Pytest fixture providing temporary settings directory.
        """
        settings_path = tmp_settings_dir / "settings.json"
        settings_path.write_text('{"theme": "dark"}', encoding="utf-8")

        # Create backups with different timestamps
        create_backup(settings_path, timestamp="20260118_100000")
        create_backup(settings_path, timestamp="20260118_100100")
        create_backup(settings_path, timestamp="20260118_100200")

        # Verify all backups exist
        backup_files = list(tmp_settings_dir.glob("*.cc_version_backup"))
        assert len(backup_files) == 3  # noqa: PLR2004

        # Verify unique names
        backup_names = [f.name for f in backup_files]
        assert len(set(backup_names)) == 3  # noqa: PLR2004
        assert "settings.json.20260118_100000.cc_version_backup" in backup_names
        assert "settings.json.20260118_100100.cc_version_backup" in backup_names
        assert "settings.json.20260118_100200.cc_version_backup" in backup_names

    def test_error_propagation_from_settings(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify errors from settings operations propagate correctly.

        When settings file operations fail (e.g., file not found, invalid JSON),
        the error should propagate up through the calling functions.

        Args:
            tmp_path: Pytest fixture providing temporary directory for test files.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        nonexistent_path = tmp_path / "nonexistent" / "settings.json"

        # Test disable_auto_update with missing settings file
        with pytest.raises(FileNotFoundError) as fnf_exc:
            disable_auto_update(settings_path=nonexistent_path)

        assert "Settings file not found" in str(fnf_exc.value)

        # Test show_status with missing settings file
        with pytest.raises(SystemExit) as exit_exc:
            show_status(settings_path=nonexistent_path)

        assert exit_exc.value.code == 1

    def test_error_propagation_from_npm(
        self, mock_subprocess_run: Mock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify errors from npm operations propagate correctly.

        When npm commands fail (e.g., network error, package not found),
        the error should be reported clearly to the user.

        Args:
            mock_subprocess_run: Mock for subprocess.run to simulate npm failure.
            capsys: Pytest fixture for capturing stdout/stderr output.
        """
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stderr = "npm ERR! code E404"

        # Test list_versions with npm failure
        with pytest.raises(SystemExit) as exc_info:
            list_versions(run_command=mock_subprocess_run)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "npm command failed" in captured.err.lower()

        # Test get_available_versions with npm failure
        with pytest.raises(RuntimeError) as runtime_exc:
            get_available_versions(run_command=mock_subprocess_run)

        assert "Failed to fetch versions from npm" in str(runtime_exc.value)
