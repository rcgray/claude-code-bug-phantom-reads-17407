# Test Environment Isolation Standards

## Overview

This document establishes mandatory standards for test environment isolation in Python projects using pytest. These standards ensure that tests are deterministic, reproducible, and independent of developer machine configuration.

### Core Principle

**Tests must pass identically on any machine, regardless of local environment configuration.**

A test suite that depends on a developer's specific setup is not truly automated—it's a source of false failures, CI/CD instability, and developer friction.

## Why Test Isolation Matters

### Problems Caused by Poor Isolation

1. **Non-deterministic failures**: Tests pass on one machine, fail on another
2. **CI/CD brittleness**: Build servers require special configuration to match developer environments
3. **Onboarding friction**: New developers encounter mysterious test failures
4. **Hidden bugs**: Tests may pass due to "lucky" local config, hiding real issues
5. **Debugging overhead**: Hours wasted investigating environment-dependent failures

### Benefits of Proper Isolation

1. **Confidence**: Green tests mean the code works, red tests mean it doesn't
2. **Portability**: Tests run anywhere—local machines, CI/CD, containers
3. **Maintainability**: Tests explicitly declare their dependencies
4. **Debugging**: Failures are reproducible and clearly caused by code changes

## Standard 1: Environment Variable Isolation

### Mandatory Practice

**Every test must explicitly control its environment variables.**

Tests fall into two categories:

#### 1A: Tests of Default Behavior (No Environment Variables Set)

These tests verify behavior when environment variables are NOT set. They must clear the environment:

```python
from unittest.mock import patch
import pytest

@patch.dict(os.environ, {}, clear=True)
def test_default_cache_directory():
    """Test default behavior when SERVICE_CACHE_DIR is not set."""
    client = ExternalServiceClient("resource-id")
    cache_dir = client.get_cache_directory()

    # Now we KNOW SERVICE_CACHE_DIR was not set
    assert cache_dir == Path.home() / ".cache" / "external_service"
```

**Why**: Without `clear=True`, the test inherits the developer's shell environment, making it non-deterministic.

#### 1B: Tests of Environment-Dependent Behavior

These tests verify behavior when specific environment variables ARE set. They must explicitly set only what's needed:

```python
@patch.dict(os.environ, {"SERVICE_CACHE_DIR": "/custom/path"})
def test_custom_cache_directory():
    """Test behavior when SERVICE_CACHE_DIR is explicitly set."""
    client = ExternalServiceClient("resource-id")
    cache_dir = client.get_cache_directory()

    # Now we KNOW exactly what SERVICE_CACHE_DIR is
    assert cache_dir == Path("/custom/path")
```

### Common Environment Variables in Python Projects

When testing code that reads these variables, always use `@patch.dict`:

- **API credentials**: `API_KEY`, `SERVICE_TOKEN`, `DATABASE_URL` - Must be mocked unless in opt-in integration tests
- **Service endpoints**: `API_ENDPOINT`, `DATABASE_HOST`, `REDIS_URL` - Must be controlled
- **Directory paths**: `HOME`, `CACHE_DIR`, `DATA_PATH`, `LOG_DIR` - Must be explicitly set or cleared
- **Configuration files**: `CONFIG_FILE`, `SETTINGS_PATH` - Must be controlled, typically with `tmp_path`
- **Feature flags**: `ENABLE_FEATURE_X`, `DEBUG_MODE`, `EXPERIMENTAL` - Must be explicitly set
- **Runtime environment**: `ENVIRONMENT`, `STAGE`, `NODE_ENV` - Must be controlled for deterministic behavior

### Anti-Pattern Example

```python
# ❌ BAD: This test will fail if developer has SERVICE_CACHE_DIR set
def test_default_cache_directory():
    client = ExternalServiceClient("resource-id")
    cache_dir = client.get_cache_directory()
    assert cache_dir == Path.home() / ".cache" / "external_service"
```

### Correct Pattern

```python
# ✅ GOOD: Environment is explicitly controlled
@patch.dict(os.environ, {}, clear=True)
def test_default_cache_directory():
    client = ExternalServiceClient("resource-id")
    cache_dir = client.get_cache_directory()
    assert cache_dir == Path.home() / ".cache" / "external_service"
```

## Standard 2: File System Isolation

### Mandatory Practice

**Tests must never read from or write to actual user directories.**

### Use pytest tmp_path Fixture

All file operations should use temporary directories:

```python
def test_config_file_loading(tmp_path: Path):
    """Test configuration file loading."""
    # Create temporary config file
    config_file = tmp_path / "config.toml"
    config_file.write_text("[settings]\ntheme = dark\nlog_level = info")

    # Test with temporary file
    config = AppConfig.load(config_file)
    assert config.get("theme") == "dark"
```

### Never Access Real User Directories

```python
# ❌ BAD: Reads from actual user config directory
def test_config_loading():
    config_path = Path.home() / ".config" / "myapp" / "config.toml"
    config = AppConfig.load(config_path)
    # What if user doesn't have this file? Or has different settings?

# ✅ GOOD: Uses temporary directory
@patch.dict(os.environ, {"CONFIG_HOME": str(tmp_path)})
def test_config_loading(tmp_path: Path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("[settings]\ntheme = dark\nlog_level = info")
    config = AppConfig.load(config_file)
```

### Test Fixtures Location

Permanent test data files belong in `tests/test_data/`:

```
tests/
├── test_data/
│   ├── sample_config.toml
│   ├── external_model_data.json
│   └── gguf/
│       └── minimal_test.gguf
```

These are **version-controlled fixtures**, not developer configuration files.

## Standard 3: Configuration File Isolation

### Mandatory Practice

**Tests must never depend on developer's actual configuration files.**

### Pattern: Mock Config Loading

```python
from unittest.mock import Mock, patch

def test_cli_with_config():
    """Test CLI behavior with configuration."""
    # Create mock config in memory
    mock_config = Mock()
    mock_config.get = Mock(side_effect=lambda k: {"theme": "dark", "debug": True}.get(k))

    with patch('myapp.config.AppConfig.load', return_value=mock_config):
        result = runner.invoke(cli, ["process", "--verbose"])
        assert result.exit_code == 0
```

### Pattern: Temporary Config Files

```python
def test_config_manager_platform_specific(tmp_path: Path):
    """Test platform-specific config paths."""
    with patch.dict(os.environ, {"CONFIG_HOME": str(tmp_path)}, clear=True):
        config_path = tmp_path / "config.toml"
        config_path.write_text("[aliases]\nshortcut = full-command --with-args")

        config = AppConfig.load()
        assert config.get_aliases() == {"shortcut": "full-command --with-args"}
```

### Never Test Against Real User Files

```python
# ❌ BAD: Depends on developer's actual .env file
def test_api_key_discovery():
    keys = discover_api_keys()
    assert "API_KEY" in keys
    # What if developer doesn't have this key? Or has a different one?

# ✅ GOOD: Creates controlled test environment
def test_api_key_discovery(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("API_KEY=test-key-12345")

    with patch.dict(os.environ, {"CONFIG_HOME": str(tmp_path)}, clear=True):
        keys = discover_api_keys()
        assert keys["API_KEY"] == "test-key-12345"
```

## Standard 4: Network Isolation

### Mandatory Practice

**Unit tests must mock all network calls. Integration tests requiring network must be opt-in.**

### Unit Tests: Always Mock Network

```python
from unittest.mock import Mock, patch

def test_anthropic_tokenization():
    """Test Anthropic tokenization (mocked)."""
    # Mock the API response
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = {
            "token_count": 42
        }

        tokenizer = AnthropicTokenizer("claude-3-opus-20240229")
        count = tokenizer.count_tokens("Hello world")

        assert count == 42
        # Verify API was called correctly
        mock_post.assert_called_once()
```

### Integration Tests: Opt-in with Markers

For tests that genuinely need network access:

```python
@pytest.mark.network
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="API key required")
def test_anthropic_api_integration():
    """Integration test with real Anthropic API."""
    tokenizer = AnthropicTokenizer("claude-3-opus-20240229")
    count = tokenizer.count_tokens("Hello world")
    assert count > 0
```

Run these explicitly:
```bash
# Skip by default
pytest  # Network tests skipped

# Run explicitly
pytest --network  # Or custom marker setup
pytest -m network
```

### Example Pattern: --with-api-keys Flag

Example implementation of this pattern:

```python
# tests/conftest.py
def pytest_addoption(parser):
    parser.addoption(
        "--with-api-keys",
        action="store_true",
        default=False,
        help="Run tests requiring real API keys"
    )

@pytest.fixture
def api_keys_available(request):
    if not request.config.getoption("--with-api-keys"):
        pytest.skip("Test requires --with-api-keys flag")
```

This is the correct pattern. **Extend it to all network-dependent tests.**

## Standard 5: Test Categories and Isolation Levels

### Unit Tests (Default)

**Characteristics:**
- No network access (mock all external APIs)
- No file system access to user directories (use `tmp_path`)
- No environment variable dependencies (use `@patch.dict`)
- Fast execution (milliseconds)
- No external dependencies

**Isolation Requirements:**
- ✅ Environment variables cleared or explicitly set
- ✅ File system isolated to temporary directories
- ✅ Network calls mocked
- ✅ No reading from actual config files

**Run by default:**
```bash
pytest  # Runs all unit tests
```

### Integration Tests (Opt-in)

**Characteristics:**
- May use real network calls to test actual API integration
- Still use controlled environments (not developer's personal config)
- May require API keys or other credentials
- Slower execution (seconds)

**Isolation Requirements:**
- ✅ API keys provided via test fixtures or temporary env vars
- ✅ File system still isolated to temporary directories
- ✅ Network calls allowed but to real endpoints
- ❌ No mocking of core functionality being tested

**Run explicitly:**
```bash
pytest --with-api-keys
pytest -m integration
```

### End-to-End Tests (Rare, Opt-in)

**Characteristics:**
- Test complete user workflows
- May read from actual installed configuration (if testing installation)
- Much slower execution (seconds to minutes)

**Isolation Requirements:**
- ⚠️ May use some real environment, but document requirements
- ✅ Should not assume any particular user configuration
- ✅ Should clean up after themselves

**Run explicitly:**
```bash
pytest --e2e
pytest -m e2e
```

## Standard 6: Common Patterns and Fixtures

### Standard Fixture: Isolated Environment

Create reusable fixtures for common isolation needs:

```python
# tests/conftest.py

@pytest.fixture
def clean_env():
    """Provide a completely clean environment."""
    with patch.dict(os.environ, {}, clear=True):
        yield

@pytest.fixture
def isolated_app_env(tmp_path):
    """Provide isolated application environment with temp directories."""
    env = {
        "CONFIG_HOME": str(tmp_path / "config"),
        "CACHE_HOME": str(tmp_path / "cache"),
        "DATA_HOME": str(tmp_path / "data"),
    }

    # Create directories
    for path_str in env.values():
        Path(path_str).mkdir(parents=True, exist_ok=True)

    with patch.dict(os.environ, env, clear=True):
        yield tmp_path
```

Usage:
```python
def test_config_isolation(isolated_app_env):
    """Test runs in completely isolated application environment."""
    config_file = isolated_app_env / "config" / "config.toml"
    config_file.write_text("[settings]\nmode = test")

    # Config will be loaded from isolated environment
    config = AppConfig.load()
    assert config.get("mode") == "test"
```

### Standard Fixture: Mock API Keys

```python
@pytest.fixture
def mock_api_keys(monkeypatch):
    """Provide mock API credentials for testing."""
    keys = {
        "API_KEY": "test-api-key-12345",
        "SERVICE_TOKEN": "test-token-67890",
        "DATABASE_URL": "sqlite:///:memory:",
    }
    for key, value in keys.items():
        monkeypatch.setenv(key, value)
    yield keys
```

## Standard 7: Anti-Patterns to Avoid

### ❌ Assuming Clean Environment

```python
# BAD: Assumes HF_HOME is not set
def test_default_behavior():
    result = get_cache_dir()
    assert result == Path.home() / ".cache" / "huggingface"
```

### ✅ Explicitly Ensuring Clean Environment

```python
# GOOD: Guarantees HF_HOME is not set
@patch.dict(os.environ, {}, clear=True)
def test_default_behavior():
    result = get_cache_dir()
    assert result == Path.home() / ".cache" / "huggingface"
```

### ❌ Reading Real User Files

```python
# BAD: Reads from actual user directory
def test_config_loading():
    config = load_config(Path.home() / ".config" / "myapp" / "config.toml")
    assert config.get("theme") == "dark"
```

### ✅ Using Temporary Files

```python
# GOOD: Creates temporary config
def test_config_loading(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("[settings]\ntheme = dark\nlog_level = info")
    config = load_config(config_file)
    assert config.get("theme") == "dark"
```

### ❌ Unmocked Network Calls in Unit Tests

```python
# BAD: Makes real network call
def test_fetch_models():
    models = fetch_models_from_api()
    assert len(models) > 0
```

### ✅ Mocked Network Calls

```python
# GOOD: Mocks network call
@patch('requests.get')
def test_fetch_models(mock_get):
    mock_get.return_value.json.return_value = {"models": ["gpt-4", "gpt-3.5"]}
    models = fetch_models_from_api()
    assert models == ["gpt-4", "gpt-3.5"]
```

### ❌ Partial Environment Patching

```python
# BAD: Only patches one variable, leaves others from shell
@patch.dict(os.environ, {"CONFIG_FILE": "/tmp/config.toml"})
def test_with_config():
    # SERVICE_CACHE_DIR, API_KEY, etc. still leak from shell!
    ...
```

### ✅ Complete Environment Control

```python
# GOOD: Clears everything, sets only what's needed
@patch.dict(os.environ, {"CONFIG_FILE": "/tmp/config.toml"}, clear=True)
def test_with_config():
    # Only CONFIG_FILE is set, everything else is clean
    ...
```

## Standard 8: Case Study - Environment Variable Isolation

> **Note**: This case study uses a real example involving an external service's cache directory environment variable. While the specific variable name is from one project, the isolation pattern demonstrated here applies to any environment-dependent behavior in your code.

### The Problem

Test: `tests/test_huggingface_coverage.py::test_get_cache_dir_default`

```python
# Original test (WRONG)
def test_get_cache_dir_default(self, mock_auto_tokenizer):
    """Test default cache directory."""
    tokenizer = HuggingFaceTokenizer("meta-llama/Llama-2-7b-hf")
    cache_dir = tokenizer._get_cache_dir()
    assert cache_dir == Path.home() / ".cache" / "huggingface" / "hub"
```

**Failure**: When developer runs `HF_HOME=env/hf_home pytest`, test fails because:
1. Test assumes `HF_HOME` is not set
2. Test doesn't isolate environment
3. Code correctly reads `HF_HOME` from shell
4. Test gets `env/hf_home/hub` instead of default path

**This is a test isolation bug, not a code bug.** The code correctly reads the environment variable; the test incorrectly assumed it wasn't set.

### The Fix

```python
# Corrected test
@patch.dict(os.environ, {}, clear=True)
def test_get_cache_dir_default(self, mock_auto_tokenizer):
    """Test default cache directory when HF_HOME is not set."""
    tokenizer = HuggingFaceTokenizer("meta-llama/Llama-2-7b-hf")
    cache_dir = tokenizer._get_cache_dir()
    assert cache_dir == Path.home() / ".cache" / "huggingface" / "hub"
```

Now the test:
- Explicitly clears environment, ensuring `HF_HOME` is not set
- Tests exactly what it claims to test (default behavior)
- Passes regardless of developer's shell environment

### Comparison: The Custom Path Test

The sibling test already does this correctly:

```python
@patch.dict(os.environ, {"HF_HOME": "/custom/hf/home"})
def test_get_cache_dir_custom(self, mock_auto_tokenizer):
    """Test custom cache directory from environment."""
    tokenizer = HuggingFaceTokenizer("meta-llama/Llama-2-7b-hf")
    cache_dir = tokenizer._get_cache_dir()
    assert cache_dir == Path("/custom/hf/home") / "hub"
```

This test works because it explicitly sets `HF_HOME` to a known value.

## Standard 9: Cache State Isolation

### Mandatory Practice

**Tests must not depend on existing cache state and must clean up after execution.**

Cache pollution is a common source of test interdependence. One test populates the cache, and subsequent tests unexpectedly find cached data instead of exercising fresh code paths.

### The Problem

Python applications commonly have multiple caches that can affect test behavior:
- **External data cache** - Downloaded resources, API responses, computed results
- **Session cache** - User sessions, authentication tokens, temporary state
- **Build cache** - Compiled artifacts, processed assets, generated files
- **Application cache** - Business logic caching, memoization, computed values

### Pattern: Isolated Cache Directories

Use temporary cache directories for each test:

```python
def test_resource_download(tmp_path: Path):
    """Test resource download with isolated cache."""
    cache_dir = tmp_path / "service_cache"

    with patch.dict(os.environ, {"SERVICE_CACHE_DIR": str(cache_dir)}, clear=True):
        client = ExternalServiceClient("resource-identifier")
        # This test has its own cache, won't interfere with others
        assert client.is_cached() is False
```

### Pattern: Clear Cache Before Test

For tests that must use a specific cache location:

```python
def test_cache_loading(tmp_path: Path):
    """Test loading from cache."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    # Explicitly populate cache with known data
    cache_file = cache_dir / "test_model.cache"
    cache_file.write_text('{"tokens": 100}')

    # Test uses only the cache we created
    result = load_from_cache(cache_file)
    assert result["tokens"] == 100
```

### Anti-Pattern Examples

```python
# ❌ BAD: Assumes cache is empty
def test_cache_miss():
    client = ExternalServiceClient("resource-identifier")
    # Fails if another test or developer has this resource cached!
    assert client.is_cached() is False

# ❌ BAD: Pollutes shared cache
def test_cache_writing():
    # Uses default cache location
    client = ExternalServiceClient("resource-identifier")
    client.download()
    # Leaves cache in modified state for other tests!

# ❌ BAD: Depends on cache from previous test
def test_cache_hit():
    # Assumes test_cache_writing ran first
    client = ExternalServiceClient("resource-identifier")
    assert client.is_cached() is True
```

### Correct Patterns

```python
# ✅ GOOD: Isolated cache
@patch.dict(os.environ, {"SERVICE_CACHE_DIR": str(tmp_path / "cache")}, clear=True)
def test_cache_miss(tmp_path: Path):
    client = ExternalServiceClient("resource-identifier")
    # Fresh cache, known state
    assert client.is_cached() is False

# ✅ GOOD: Explicit cache setup
def test_cache_hit(tmp_path: Path):
    cache_dir = tmp_path / "cache" / "resources"
    cache_dir.mkdir(parents=True)

    # Explicitly create cache state
    resource_dir = cache_dir / "resource-identifier"
    resource_dir.mkdir()
    # ... populate with known cached data

    with patch.dict(os.environ, {"SERVICE_CACHE_DIR": str(tmp_path / "cache")}, clear=True):
        client = ExternalServiceClient("resource-identifier")
        assert client.is_cached() is True
```

### Common Cache Patterns

When testing cache-related functionality, isolate these:

```python
@pytest.fixture
def isolated_caches(tmp_path: Path):
    """Provide isolated cache directories for testing."""
    env = {
        "CACHE_HOME": str(tmp_path / "cache"),
        "DATA_CACHE_DIR": str(tmp_path / "data_cache"),
        "SESSION_CACHE_DIR": str(tmp_path / "session_cache"),
    }

    # Create directories
    for path_str in env.values():
        Path(path_str).mkdir(parents=True, exist_ok=True)

    with patch.dict(os.environ, env, clear=True):
        yield tmp_path
```

## Standard 10: Global State and Singleton Isolation

### Mandatory Practice

**Tests must reset global state and singletons before/after execution.**

Global state creates hidden dependencies between tests. One test modifies a singleton, and subsequent tests inherit that modified state.

### Common Problems in Python Applications

Python applications commonly have global state concerns:

1. **Provider Registry** - Singleton that registers available providers
2. **Tokenizer Instances** - May be cached/reused
3. **Module-level Configuration** - Settings loaded at import time

### Pattern: Reset Singletons

```python
def test_service_registration():
    """Test service registration in isolation."""
    # Reset registry to known state
    from myapp.services import ServiceRegistry

    # Save original state
    original_services = ServiceRegistry._services.copy()

    try:
        # Test with clean registry
        ServiceRegistry._services.clear()
        ServiceRegistry.register("custom", CustomService)
        assert "custom" in ServiceRegistry.list_services()
    finally:
        # Restore original state
        ServiceRegistry._services = original_services
```

### Pattern: Fixture for State Cleanup

```python
@pytest.fixture
def clean_service_registry():
    """Ensure clean service registry for test."""
    from myapp.services import ServiceRegistry

    original = ServiceRegistry._services.copy()
    yield
    ServiceRegistry._services = original

def test_with_clean_registry(clean_service_registry):
    """Test runs with isolated registry state."""
    # Registry is cleaned before and after this test
    ...
```

### Anti-Pattern Examples

```python
# ❌ BAD: Modifies global registry
def test_add_service():
    ServiceRegistry.register("test", TestService)
    # Leaves registry in modified state!

# ❌ BAD: Depends on global state from other test
def test_service_exists():
    # Assumes test_add_service ran first
    assert "test" in ServiceRegistry.list_services()

# ❌ BAD: Module-level side effects
import myapp.config
myapp.config.DEFAULT_MODE = "custom"  # Affects all tests!

def test_something():
    # This test and all subsequent tests see modified default
    ...
```

### Correct Patterns

```python
# ✅ GOOD: Isolated registry modification
def test_add_service(clean_service_registry):
    ServiceRegistry.register("test", TestService)
    assert "test" in ServiceRegistry.list_services()
    # Fixture cleans up after

# ✅ GOOD: Mock global config
def test_with_custom_default():
    with patch('myapp.config.DEFAULT_MODE', 'custom'):
        # Only this test sees modified default
        assert get_default_mode() == 'custom'
```

### Important: Module Import Side Effects

Be aware of code that executes at import time:

```python
# In module code (BAD pattern to avoid):
DEFAULT_CONFIG = load_config()  # Runs at import!

# Tests will inherit whatever state this creates
```

If such code exists, tests must account for it:

```python
def test_something():
    # Reset module-level state
    import myapp.some_module
    importlib.reload(myapp.some_module)  # Careful: expensive!

    # Or better: refactor module to avoid import-time side effects
```

## Standard 11: Working Directory Isolation

### Mandatory Practice

**Tests must not assume they run from a specific working directory.**

Tests that use relative paths fail when run from different directories (IDE, CI/CD, different developer setups).

### The Problem

```python
# ❌ BAD: Assumes running from project root
def test_load_fixture():
    data = load_json("tests/test_data/sample.json")
    # Fails if run from tests/ directory or elsewhere
```

### Pattern: Use `__file__` for Paths

```python
# ✅ GOOD: Path relative to test file location
def test_load_fixture():
    test_dir = Path(__file__).parent
    fixture_path = test_dir / "test_data" / "sample.json"
    data = load_json(fixture_path)
```

### Pattern: Use Fixtures for Test Data Paths

```python
# tests/conftest.py
@pytest.fixture
def test_data_dir():
    """Provide path to test data directory."""
    return Path(__file__).parent / "test_data"

# tests/test_something.py
def test_load_sample(test_data_dir: Path):
    """Test loading sample data."""
    data = load_json(test_data_dir / "sample.json")
    assert data["version"] == 1
```

### Anti-Pattern Examples

```python
# ❌ BAD: Relative path from unknown location
def test_data_loading():
    data = load_data("tests/test_data/fixtures/sample_data.json")

# ❌ BAD: Assumes CWD is project root
def test_config_loading():
    with open("src/myapp/data/metadata.json") as f:
        data = json.load(f)

# ❌ BAD: Changes working directory without cleanup
def test_something():
    os.chdir("tests")
    # Other tests now run from wrong directory!
    ...
```

### Correct Patterns

```python
# ✅ GOOD: Absolute path from test location
def test_data_loading():
    test_dir = Path(__file__).parent
    data_path = test_dir / "test_data" / "fixtures" / "sample_data.json"
    data = load_data(data_path)

# ✅ GOOD: Use package resources for package data
from importlib.resources import files
def test_metadata_loading():
    metadata = files("myapp.data").joinpath("metadata.json")
    with metadata.open() as f:
        data = json.load(f)

# ✅ GOOD: Change directory with cleanup
def test_with_different_cwd(tmp_path: Path):
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        # Test that needs specific CWD
        ...
    finally:
        os.chdir(original_cwd)
```

### Example Test Data Organization

Example test data organization in `tests/test_data/`:

```
tests/
├── test_data/
│   ├── fixtures/          # Version-controlled test inputs
│   │   ├── sample_data.json
│   │   ├── test_config.toml
│   │   └── valid_input.csv
│   ├── expected/          # Expected outputs for verification
│   │   ├── processed_result.json
│   │   └── formatted_output.txt
│   └── mocks/             # Mock API responses
│       ├── api_success.json
│       └── api_error.json
└── test_*.py
```

Access these with path relative to test file:

```python
@pytest.fixture
def sample_data_file():
    """Provide path to sample data fixture."""
    tests_dir = Path(__file__).parent
    return tests_dir / "test_data" / "fixtures" / "sample_data.json"
```

## Standard 12: Standard Stream Isolation (CLI Testing)

### Mandatory Practice

**CLI tests must properly capture and isolate stdout/stderr output.**

CLI applications write to stdout/stderr. Tests must capture this output without interference between tests.

### The Problem

```python
# ❌ BAD: Output goes to console
def test_cli_help():
    cli_main(["--help"])
    # How do we verify what was printed?
    # Output visible in test runner, pollutes output
```

### Pattern: Use pytest's capsys

```python
# ✅ GOOD: Capture output with capsys
def test_cli_help(capsys):
    """Test CLI help output."""
    with pytest.raises(SystemExit):  # --help exits
        cli_main(["--help"])

    captured = capsys.readouterr()
    assert "usage:" in captured.out.lower()
    assert "show this help message" in captured.out.lower()
```

### Pattern: Use Typer's CliRunner (Recommended for Typer apps)

For Python CLIs using Typer, which provides a testing utility:

```python
from typer.testing import CliRunner
from myapp.cli import app

runner = CliRunner()

def test_version_command():
    """Test version command output."""
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "version" in result.stdout.lower()
```

### Pattern: Mixing Output Capture

```python
def test_cli_with_file_output(tmp_path: Path, capsys):
    """Test CLI that writes to both file and stdout."""
    output_file = tmp_path / "output.txt"

    result = runner.invoke(app, [
        "hello world",
        "--output", str(output_file)
    ])

    # Verify CLI output
    assert result.exit_code == 0

    # Verify file was written
    assert output_file.exists()
    assert "token" in output_file.read_text()

    # Verify nothing leaked to stderr
    assert result.stderr == ""
```

### Anti-Pattern Examples

```python
# ❌ BAD: Doesn't capture output
def test_cli_output():
    cli_main(["hello"])
    # No way to verify output!

# ❌ BAD: Manual stdout redirection (fragile)
def test_cli_manual_capture():
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        cli_main(["hello"])
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout
    # Fragile, doesn't handle stderr, can leave stdout corrupted

# ❌ BAD: Output interference
def test_something():
    print("Debug info")  # Pollutes test output!
```

### Correct Patterns

```python
# ✅ GOOD: CliRunner captures everything
def test_error_messages():
    """Test that errors are properly reported."""
    result = runner.invoke(app, ["--model", "nonexistent"])

    assert result.exit_code != 0
    assert "error" in result.stdout.lower()

# ✅ GOOD: Use pytest's capsys for non-CLI code
def test_formatter_output(capsys):
    """Test formatter writes to stdout."""
    formatter = OutputFormatter()
    formatter.print_result({"tokens": 42})

    captured = capsys.readouterr()
    assert "42" in captured.out

# ✅ GOOD: Suppress output when not testing it
def test_cli_exit_code():
    """Test only exit code, ignore output."""
    result = runner.invoke(app, ["hello"], catch_exceptions=False)
    assert result.exit_code == 0
    # Don't check output, just success/failure
```

### Python CLI Testing Best Practices

```python
# Standard test setup for Python CLI tests
from typer.testing import CliRunner
from myapp.cli import app

runner = CliRunner()

def test_basic_tokenization():
    """Test basic token counting."""
    result = runner.invoke(app, [
        "Hello, world!",
        "--provider", "openai",
        "--model", "gpt-4"
    ])

    assert result.exit_code == 0
    assert "tokens" in result.stdout.lower()

def test_cli_with_config(tmp_path: Path):
    """Test CLI with custom config."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("[settings]\nlog_level = debug")

    with patch.dict(os.environ, {"CONFIG_FILE": str(config_file)}, clear=True):
        result = runner.invoke(app, ["run"])
        assert result.exit_code == 0
```

## Standard 13: Module-Level Derived Constant Patching

### Mandatory Practice

**Tests that patch module-level constants must patch all derived constants in the dependency chain.**

Python evaluates module-level expressions once at import time. Constants derived from other constants capture a snapshot of their base value—patching the base constant later does not update derived constants.

### The Problem

```python
# In module code:
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "docs" / "reports"      # Evaluated ONCE at import
DEV_REPORTS_DIR = PROJECT_ROOT / "dev" / "reports"   # Evaluated ONCE at import
```

When you patch `PROJECT_ROOT`, `REPORTS_DIR` and `DEV_REPORTS_DIR` still point to their original computed values. Tests using these derived constants will write to real directories.

### Anti-Pattern: Patching Only the Base Constant

```python
# ❌ BAD: Only patches base constant
def test_generate_docs(tmp_path: Path):
    with patch.object(my_module, "PROJECT_ROOT", tmp_path):
        # REPORTS_DIR still points to real directory!
        result = my_module.generate_report()
```

### Correct Pattern: Patch All Constants in the Chain

```python
# ✅ GOOD: Patches base AND all derived constants
def test_generate_docs(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(my_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(my_module, "REPORTS_DIR", tmp_path / "docs" / "reports")
    monkeypatch.setattr(my_module, "DEV_REPORTS_DIR", tmp_path / "dev" / "reports")

    result = my_module.generate_report()
    # Now writes to tmp_path, not real directories
```

### Finding Constants to Patch

Before writing a test that patches any path constant:

1. **Identify the base constant** you need to patch (e.g., `PROJECT_ROOT`)
2. **Search the module** for constants that reference it:
   ```bash
   grep "PROJECT_ROOT" source/scripts/my_module.py
   ```
3. **Patch every constant** in the dependency chain

### Common Patterns

```python
@pytest.fixture
def isolated_project_paths(tmp_path: Path, monkeypatch):
    """Provide isolated project paths for testing."""
    monkeypatch.setattr(my_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(my_module, "REPORTS_DIR", tmp_path / "docs" / "reports")
    monkeypatch.setattr(my_module, "DEV_REPORTS_DIR", tmp_path / "dev" / "reports")

    # Create directories
    (tmp_path / "docs" / "reports").mkdir(parents=True)
    (tmp_path / "dev" / "reports").mkdir(parents=True)

    return tmp_path

def test_with_isolated_paths(isolated_project_paths):
    """Test runs with fully isolated path constants."""
    result = my_module.generate_all_reports()
    assert result.success
```

### Troubleshooting

If a test unexpectedly writes to real directories:

1. **Check which constant the function uses** - It may use a derived constant, not the base
2. **Verify all derived constants are patched** - Missing even one breaks isolation
3. **Create directories in tmp_path** - Derived paths may need their directories created

## Future Considerations

These isolation concerns are lower priority in simpler projects but may become relevant as complexity grows:

### Time and Date Dependencies

If time-based features are implemented (e.g., timestamped logs, time-sensitive operations):

```python
# Mock time for deterministic tests
from unittest.mock import patch
from datetime import datetime

@patch('datetime.datetime')
def test_timestamp_generation(mock_datetime):
    mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
    # Test runs with frozen time
    result = generate_report_with_timestamp()
    assert "2024-01-01" in result
```

### Random Number Generation

If randomness is introduced (sampling, fuzzing, etc.):

```python
import random

def test_with_randomness():
    random.seed(42)  # Deterministic "random" behavior
    result = generate_random_test_cases()
    assert len(result) == 10  # Always generates same 10
```

### System Properties (Locale, Timezone)

For locale-sensitive features:

```python
import locale

def test_number_formatting():
    with patch.object(locale, 'getlocale', return_value=('en_US', 'UTF-8')):
        # Test with known locale
        ...
```

### Platform-Specific Behavior

Example implementation of cross-platform testing with pytest markers:

```python
@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only test")
def test_windows_paths():
    # Test Windows-specific path handling
    ...
```

## Enforcement and Compliance

### Required for All New Tests

Starting immediately, all new tests must comply with these standards. Code reviews must verify:

- [ ] Environment variables are explicitly controlled with `@patch.dict`
- [ ] File operations use `tmp_path` or controlled fixtures
- [ ] Network calls are mocked in unit tests
- [ ] Integration tests are marked and opt-in
- [ ] Tests do not depend on developer's personal configuration
- [ ] Cache directories are isolated with temporary paths
- [ ] Global state and singletons are reset before/after tests
- [ ] Paths use `__file__` or fixtures, not relative to CWD
- [ ] CLI tests properly capture stdout/stderr output
- [ ] Module-level derived constants are fully patched

### Existing Test Audit

A separate audit will be conducted to identify non-compliant tests in the existing suite. Violations will be addressed through:

1. Identification phase: Scan all tests for anti-patterns
2. Prioritization: Fix critical failures first
3. Systematic remediation: Fix all violations
4. Verification: Confirm tests pass in various environments

## Summary: The Golden Rules

1. **Default Behavior Tests**: Always use `@patch.dict(os.environ, {}, clear=True)`
2. **Environment-Dependent Tests**: Always use `@patch.dict(os.environ, {...})` with explicit values
3. **File Operations**: Always use `tmp_path` fixture
4. **Network Calls**: Always mock in unit tests; opt-in for integration tests
5. **Configuration Files**: Never read from actual user directories
6. **Test Categories**: Clearly separate unit/integration/e2e tests
7. **Cache Isolation**: Use temporary cache directories, never assume cache state
8. **Global State**: Reset singletons and global variables before/after tests
9. **Working Directory**: Use `__file__` or fixtures, never assume CWD
10. **CLI Output**: Use `CliRunner` or `capsys` to capture stdout/stderr
11. **Documentation**: Tests must document what environment they assume
12. **Derived Constants**: Patch all constants in the dependency chain, not just the base

**When in doubt, ask**: "Would this test pass on a colleague's machine with different environment variables, configuration, cache state, and working directory?"

If the answer is no, the test needs better isolation.
