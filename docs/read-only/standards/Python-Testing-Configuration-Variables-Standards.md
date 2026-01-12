# Testing Configuration and Environment Variables: Standards

## Overview

This document establishes mandatory standards for testing **both configuration variables and environment variables** in Python projects. These standards prevent the critical failure mode where options are defined, documented, and "tested" without actually verifying they work.

**The Core Failure Mode**: Configuration options can be declared ✓, implementation mechanisms can exist ✓, tests can pass ✓, **but the config values are never actually read and used** ✗. This creates a silent failure where documented features don't work, eroding user trust.

### Scope: Two Types of Variables

This standard applies to:

1. **Configuration Variables** (config files)
   - Defined in: `docs/core/Config-Spec.md`
   - Examples: `cache.max_size`, `defaults.provider`, `security.trust_remote_code`
   - Location: `~/.config/myapp/.apprc` (or platform-specific)
   - Format: TOML/JSON/YAML sections and keys

2. **Environment Variables** (`.env` files or shell)
   - Defined in: `docs/core/Environment-Variables-Spec.md`
   - Examples: `ANTHROPIC_API_KEY`, `APP_CONFIG_HOME`, `HF_HOME`
   - Location: `.env` files, shell environment, or system environment
   - Format: `KEY=value` pairs

**When adding or modifying either type**, you must follow the testing standards in this document.

### Core Principle

**Testing the mechanism ≠ Testing the feature**

When the feature is "configuration controls behavior X," you must test that configuration actually controls behavior X, not just that behavior X works when manually configured.

## Why Configuration Testing Matters

### The Failure Mode

A test that verifies a mechanism works is not the same as a test that verifies configuration controls that mechanism.

**Example scenario**:
- `cache.max_size` configuration option exists
- Cache has `max_size_bytes` parameter
- Test exists: `cache.max_size_bytes = 1024; verify_eviction()`
- Test passes ✓
- **But**: Config value is never read, hardcoded 100 MB always used
- **Result**: Users setting `max_size = 50` silently get 100 MB

**The problem**: Test verified LRU eviction mechanism works (by directly setting size), but never verified that configuration controls the size.

### Problems Caused by Inadequate Config Testing

1. **Silent failures**: Config options silently ignored, no errors or warnings
2. **False confidence**: "All tests pass" doesn't mean features work
3. **User confusion**: Documented features don't work as described
4. **Maintenance burden**: Unused config options clutter codebase
5. **Trust erosion**: Can't trust that documented config actually does anything

### Benefits of Proper Config Testing

1. **Verification**: Config options proven to work, not assumed
2. **Early detection**: Disconnections caught before reaching users
3. **Documentation accuracy**: Config docs match actual behavior
4. **Maintainability**: Unused config detected automatically
5. **Confidence**: Green tests mean features actually work

## Alignment with Specification Documents

### The Three-Way Contract

Every configurable feature involves a three-way contract:

1. **Specification** (`docs/core/Config-Spec.md` or `docs/core/Environment-Variables-Spec.md`)
   - Documents what options exist
   - Describes expected behavior
   - Defines default values
   - User-facing documentation

2. **Implementation** (`config_manager.py`, component code)
   - `get_default_config()` defines schema
   - Components read and use config values
   - Factories create components with config

3. **Tests** (this document's focus)
   - Verify spec ↔ implementation alignment
   - Prove config actually controls behavior
   - Document through executable contracts

**All three must stay synchronized**. When you add/modify/remove a variable:

- ✅ Update specification document (`docs/core/Config-Spec.md` or `docs/core/Environment-Variables-Spec.md`)
- ✅ Update implementation (`config_manager.py`, component)
- ✅ Update tests (integration test proving connection)
- ✅ Update examples (`.apprc.example` or `.env.example`)

**This document focuses on #3 (tests)**, ensuring they properly verify the contract between specs and implementation.

## Standard 1: Two Types of Tests Required

### Mandatory Practice

**Every configurable feature requires BOTH mechanism tests AND integration tests.**

### Type 1: Mechanism Tests (Unit Tests)

**Purpose**: Verify the underlying component works correctly

**Example** (cache size limiting):
```python
def test_cache_eviction_mechanism(cache: Cache) -> None:
    """Verify that cache evicts entries when size limit reached."""
    cache.max_size_bytes = 1024  # Direct manipulation for unit testing

    # Fill cache beyond limit
    for i in range(10):
        cache.save(f"file_{i}", large_data)

    # Assert oldest entries evicted
    assert cache.contains("file_0") is False  # Evicted
    assert cache.contains("file_9") is True   # Retained
```

**Characteristics**:
- Direct manipulation of component state
- Isolated from configuration system
- Fast, focused, repeatable
- Tests "does the mechanism work?"

**✅ Necessary but NOT sufficient**

### Type 2: Integration Tests (Config Contract Tests)

**Purpose**: Verify configuration/environment variables actually control behavior

**Example** (cache size limiting):
```python
@pytest.mark.config_contract
def test_cache_max_size_config_is_respected(tmp_path: Path) -> None:
    """CONTRACT: cache.max_size from .apprc must control cache size."""
    # Create config file with specific value
    config_file = tmp_path / ".apprc"
    config_file.write_text("""
    [cache]
    max_size = 50
    """)

    # Load through normal configuration path
    with patch.dict(os.environ, {"APP_CONFIG": str(config_file)}, clear=True):
        cache = get_component()  # Factory function, not direct instantiation

    # Verify config value is actually used
    assert cache.max_size_bytes == 50 * 1024 * 1024
```

**Characteristics**:
- Loads real configuration files
- Uses factory functions, not direct instantiation
- Tests "does the config option work?"
- Should test multiple config values

**✅ Required for all configuration features**

### The Critical Distinction

**Mechanism test**: "Does component X work when I set parameter Y?"
**Config test**: "Does config option control parameter Y in component X?"

You need both. Mechanism test alone creates false confidence.

## Standard 2: Mandatory Requirements for Configuration Variables (.apprc)

### Applies To

All configuration options in config files as defined in `docs/core/Config-Spec.md`.

Common configuration sections in Python applications:
- `[defaults]` section: Application defaults (provider, model, format, etc.)
- `[output]` section: Output formatting (color, verbosity, progress indicators)
- `[network]` section: Network and timeout settings
- `[cache]` section: Cache behavior (size limits, expiration, cleanup)
- `[security]` section: Security-related options (trust levels, validation)
- `[logging]` section: Logging configuration
- `[aliases]` section: User-defined shortcuts or aliases

### When Adding a Configuration Option

Every configuration option added to `config_manager.py` and documented in `docs/core/Config-Spec.md` MUST have:

1. **At least one integration test** that:
   - Creates a `.apprc` file (or sets environment variable)
   - Loads config through ConfigManager
   - Creates component through factory/normal path
   - Asserts config value affects behavior
   - Tests minimum 2-3 different values

2. **Test marker**: Use `@pytest.mark.config_contract` for discoverability

3. **Factory usage**: Test must use `get_component()` / `get_component()`, NOT `ComponentClass()`

4. **No mocking ConfigManager**: Integration tests must load real config

5. **Clear contract statement**: Docstring must state what contract is verified

### Template for Config Contract Tests

```python
@pytest.mark.config_contract
def test_<feature>_<config_option>_is_respected(tmp_path: Path) -> None:
    """CONTRACT: config.section.option must control feature behavior.

    Verifies that setting section.option=value in config file results
    in component using that value correctly.
    """
    # 1. Create config file
    config_file = tmp_path / ".apprc"
    config_file.write_text(f"""
    [section]
    option = value1
    """)

    # 2. Load config through normal path (no mocking)
    with patch.dict(os.environ, {"APP_CONFIG": str(config_file)}, clear=True):
        component = get_component()  # Use factory, not ComponentClass()

    # 3. Verify config value controls behavior
    assert component.setting == expected_value1

    # 4. Test with different value
    config_file.write_text(f"""
    [section]
    option = value2
    """)
    with patch.dict(os.environ, {"APP_CONFIG": str(config_file)}, clear=True):
        component = get_component()
    assert component.setting == expected_value2
```

## Standard 3: Mandatory Requirements for Environment Variables (.env)

### Applies To

All environment variables as defined in `docs/core/Environment-Variables-Spec.md`:

**API Keys:**
- `ANTHROPIC_API_KEY` - Anthropic API authentication
- `GOOGLE_API_KEY` - Google API authentication
- `HUGGINGFACE_API_KEY` - HuggingFace authentication
- `OPENAI_API_KEY` - OpenAI API authentication

**Directory Overrides:**
- `APP_CONFIG_HOME` - Override configuration directory
- `APP_DATA_HOME` - Override data directory
- `APP_CACHE_HOME` - Override cache directory

**Configuration:**
- `APP_CONFIG` - Custom config file path
- `APP_TEST_DATA` - Test data directory (testing only)

**External Tool Integration:**
- `HF_HOME` - HuggingFace cache directory (example of third-party integration)

**Platform-Specific:**
- `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME` (Linux/Unix)
- `APPDATA`, `LOCALAPPDATA` (Windows)

### When Adding an Environment Variable

Every environment variable added to the codebase and documented in `docs/core/Environment-Variables-Spec.md` MUST have:

1. **Test with variable set**:
```python
def test_feature_respects_env_var(tmp_path: Path) -> None:
    """Test that APP_FEATURE_FLAG enables feature."""
    with patch.dict(os.environ, {"APP_FEATURE_FLAG": "true"}, clear=True):
        result = get_feature_status()
        assert result is True
```

2. **Test with variable unset** (default behavior):
```python
def test_feature_default_when_env_unset() -> None:
    """Test feature defaults correctly when APP_FEATURE_FLAG not set."""
    with patch.dict(os.environ, {}, clear=True):
        result = get_feature_status()
        assert result is False  # Or whatever default should be
```

3. **Test precedence** (if multiple sources):
```python
def test_env_var_overrides_config(tmp_path: Path) -> None:
    """Test that APP_X env var overrides config.x value."""
    config_file = tmp_path / ".apprc"
    config_file.write_text("[section]\nx = from_config")

    with patch.dict(os.environ, {"APP_X": "from_env"}, clear=True):
        with patch_config_file(config_file):
            result = get_x()
            assert result == "from_env"  # Env wins
```

### Environment Variable Test Requirements

- **Always use** `clear=True` with `@patch.dict`
- **Always test** both set and unset states
- **Document precedence**: CLI > Env > Config > Default
- **Test multiple values**: Not just "works", but "uses correct value"

## Standard 4: Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Testing Only the Mechanism

**Wrong**:
```python
def test_cache_size_limiting(cache: Cache) -> None:
    cache.max_size_bytes = 1024  # Direct manipulation
    # Test eviction works...
```

**Why wrong**: Never verifies config controls `max_size_bytes`

**Right**: Have both mechanism test AND config integration test

---

### ❌ Anti-Pattern 2: Mocking Config in Integration Tests

**Wrong**:
```python
def test_config_max_size() -> None:
    with patch("ConfigManager.get_effective_config") as mock:
        mock.return_value = {"cache": {"max_size": 50}}
        # ... test ...
```

**Why wrong**: Mocking the thing you're trying to test

**Right**: Create actual config file, load through real ConfigManager

---

### ❌ Anti-Pattern 3: Testing Default Only

**Wrong**:
```python
def test_default_timeout() -> None:
    config = {}  # Empty
    timeout = get_timeout(config)
    assert timeout == 30
```

**Why wrong**: Only tests default, doesn't verify config override works

**Right**: Test default AND test with config value set

---

### ❌ Anti-Pattern 4: Direct Instantiation

**Wrong**:
```python
def test_cache_config() -> None:
    cache = Cache(max_size_mb=50)  # Direct instantiation
    assert cache.max_size_bytes == 50 * 1024 * 1024
```

**Why wrong**: Bypasses `get_component()` which should read config

**Right**: Use `cache = get_component()` to test real initialization path

---

### ❌ Anti-Pattern 5: Fixture That Bypasses Config

**Wrong**:
```python
@pytest.fixture
def cache(tmp_path: Path):
    with patch("ConfigManager.get_cache_dir"):
        cache = Cache()  # Bypasses get_component()
        yield cache
```

**Why wrong**: Every test using this fixture bypasses config loading

**Right**: Have separate fixtures for unit tests vs. integration tests

## Standard 5: Configuration Precedence Testing

### Required Precedence Tests

Standard configuration precedence (highest to lowest):
1. CLI arguments
2. Environment variables
3. Config file values
4. Default values

**Each override level must be tested**:

```python
def test_cli_arg_overrides_all(tmp_path: Path) -> None:
    """Test CLI argument takes precedence over env, config, defaults."""
    config_file = tmp_path / ".apprc"
    config_file.write_text("[feature]\nsetting = from_config")

    with patch.dict(os.environ, {"APP_SETTING": "from_env"}):
        with patch_config_file(config_file):
            result = get_setting(cli_arg="from_cli")
            assert result == "from_cli"

def test_env_overrides_config_and_defaults(tmp_path: Path) -> None:
    """Test env var overrides config file and defaults."""
    config_file = tmp_path / ".apprc"
    config_file.write_text("[feature]\nsetting = from_config")

    with patch.dict(os.environ, {"APP_SETTING": "from_env"}):
        with patch_config_file(config_file):
            result = get_setting()
            assert result == "from_env"

def test_config_overrides_defaults(tmp_path: Path) -> None:
    """Test config file value overrides default."""
    config_file = tmp_path / ".apprc"
    config_file.write_text("[feature]\nsetting = from_config")

    with patch.dict(os.environ, {}, clear=True):
        with patch_config_file(config_file):
            result = get_setting()
            assert result == "from_config"

def test_defaults_when_nothing_set() -> None:
    """Test default value used when no other source provides value."""
    with patch.dict(os.environ, {}, clear=True):
        result = get_setting()
        assert result == "default_value"
```

## Standard 6: Test Organization and Markers

### Suggested Test File Structure

```python
# tests/test_feature_config.py

class TestFeatureMechanism:
    """Unit tests for feature mechanism (direct manipulation)."""

    def test_mechanism_works_correctly(self) -> None:
        component = FeatureComponent(setting=value)
        # Test mechanism...

class TestFeatureConfigIntegration:
    """Integration tests for config → feature flow."""

    @pytest.mark.config_contract
    def test_config_controls_feature(self, tmp_path: Path) -> None:
        # Load real config, verify it controls behavior
        pass

    @pytest.mark.config_contract
    def test_env_var_controls_feature(self) -> None:
        # Set env var, verify it controls behavior
        pass

    @pytest.mark.config_contract
    def test_config_precedence(self, tmp_path: Path) -> None:
        # Test CLI > Env > Config > Default precedence
        pass
```

### Marker Usage

Use `@pytest.mark.config_contract` for integration tests:

```bash
# Run only config contract tests
pytest -m config_contract

# Verify all config options have contract tests
pytest -m config_contract --collect-only
```

## Standard 7: Test Naming Conventions

### Format

`test_<what>_<source>_<result>`

### Examples

- `test_cache_max_size_config_controls_cache_bytes()`
- `test_timeout_env_var_overrides_config_default()`
- `test_api_key_missing_raises_clear_error()`
- `test_trust_flag_from_cli_overrides_config_file()`

### Docstring Format

```python
def test_cache_max_size_config_controls_cache_bytes(tmp_path: Path) -> None:
    """CONTRACT: cache.max_size from .apprc must control Cache size.

    Verifies that setting cache.max_size=50 in config file results in
    Cache with max_size_bytes=50*1024*1024.
    """
```

**Required elements**:
- Start with "CONTRACT:" to identify contract tests
- State what config option controls
- State expected behavior clearly

## Standard 8: Common Pitfalls and Solutions

### Pitfall 1: Singleton State Pollution

**Problem**: Global cache instance retains state between tests

**Solution**:
```python
@pytest.fixture(autouse=True)
def reset_cache_singleton() -> None:
    """Reset global cache instance before each test."""
    from myapp.cache import reset_cache
    reset_cache()
```

### Pitfall 2: Environment Variable Leakage

**Problem**: Env vars set in one test affect others

**Solution**: Always use `clear=True`
```python
with patch.dict(os.environ, {"APP_X": "value"}, clear=True):
    # Test with only APP_X set
    pass
```

### Pitfall 3: Config File Persistence

**Problem**: Test config files remain on disk

**Solution**: Use `tmp_path` fixture
```python
def test_config(tmp_path: Path) -> None:
    config_file = tmp_path / ".apprc"  # Auto-cleaned
    config_file.write_text("...")
```

### Pitfall 4: Unclear Test Failures

**Problem**: Test fails but doesn't explain what config was expected

**Solution**: Include config in assertion message
```python
assert result == 50, (
    f"Expected config setting=50 to be used, got {result}. "
    f"Config file: {config_file.read_text()}"
)
```

## Standard 9: Red Flags in Test Review

When reviewing tests for configuration features, these are red flags that indicate inadequate testing:

1. **No integration test**: Only unit tests that manipulate state directly
2. **All fixtures mock config**: No test uses real config loading
3. **No factory usage**: Tests instantiate components directly instead of using `get_component()`
4. **Single value tested**: Only tests default, not custom values
5. **No precedence test**: Doesn't verify CLI > Env > Config > Default
6. **Env vars not cleared**: Tests don't use `patch.dict(os.environ, {}, clear=True)`
7. **No edge cases**: Doesn't test empty strings, missing values, invalid values
8. **Mocking ConfigManager**: Integration tests mock the config system they're meant to test
9. **No unset tests**: Environment variable tests don't check behavior when variable is unset
10. **Direct parameter setting**: Tests set parameters directly instead of through config

If you see any of these patterns, the configuration feature is not adequately tested.

## Standard 10: Integration with Existing Standards

This standard complements:

- **`docs/read-only/standards/Python-Test-Environment-Isolation-Standards.md`**: Config tests must also follow environment isolation rules (use `@patch.dict`, `tmp_path`, etc.)
- **`docs/read-only/standards/Python-Standards.md`**: Type hints, return annotations required
- **`docs/read-only/standards/Coding-Standards.md`**: General code quality principles

**Combined requirements**:
- Config integration tests must use `@patch.dict(os.environ, {...}, clear=True)`
- Must use `tmp_path` for config files
- Must not read from actual user directories
- Must follow Python type hint standards

## Standard 11: Enforcement and Compliance

### Rule-Enforcer Will Verify

- Every config option in `get_default_config()` has integration test
- Every environment variable has tests for set/unset states
- Integration tests use real config loading (no mocking ConfigManager)
- Tests use factory functions, not direct instantiation
- Tests follow naming conventions

### Test-Guardian Will Verify

- Config contract tests exist and pass
- Multiple values tested for each config option
- Precedence tests exist where applicable
- Edge cases covered (empty strings, None, invalid values)

### Required for All New Config Options

Starting immediately, adding a config option without integration tests is a **blocking violation**. Code reviews must verify:

- [ ] Integration test exists with `@pytest.mark.config_contract`
- [ ] Test loads real config file (no mocking ConfigManager)
- [ ] Test uses factory function (e.g., `get_component()`)
- [ ] Test verifies config value affects behavior
- [ ] Test tries multiple different values
- [ ] Test follows naming convention
- [ ] Docstring includes CONTRACT statement

## Summary: The Golden Rules

1. **Two types required**: Mechanism tests + Config integration tests
2. **Two sources covered**: Configuration variables (`.apprc`) AND environment variables (`.env`)
3. **Update specs first**: Add to `Config-Spec.md` or `Environment-Variables-Spec.md` before implementing
4. **No mocking config**: Integration tests load real `.apprc` files or set real env vars
5. **Use factories**: `get_component()`, not `ComponentClass()`
6. **Test precedence**: CLI > Env > Config > Default
7. **Test multiple values**: Not just default, test overrides
8. **Mark clearly**: `@pytest.mark.config_contract` for discoverability
9. **Clear environment**: Always use `clear=True` with `@patch.dict`
10. **Name descriptively**: `test_<what>_<source>_<result>`
11. **Document contracts**: Docstring must state what's being verified
12. **Both types necessary**: Mechanism test alone is insufficient

### The Core Questions

Before marking a configurable feature complete, ask:

1. **"If I change the config default value, will any test fail?"** (for `.apprc` options)
2. **"If I change the environment variable, will any test fail?"** (for `.env` variables)
3. **"Is this documented in the appropriate spec file?"** (`docs/core/Config-Spec.md` or `docs/core/Environment-Variables-Spec.md`)

If the answer to any of these is no, you don't have adequate config testing.

### Required Workflow for New Variables

When adding a new configuration option or environment variable:

1. **Document in spec FIRST**:
   - Configuration variables → `docs/core/Config-Spec.md`
   - Environment variables → `docs/core/Environment-Variables-Spec.md`

2. **Write integration test** (following standards in this document)

3. **Implement the feature** (config reading + behavior)

4. **Verify test passes** (config actually controls behavior)

5. **Update `.apprc.example` or `.env.example`** if appropriate

This order ensures features are specified before implementation and tested before declaring complete.

## See Also

### Specification Documents

- **`docs/core/Config-Spec.md`**: Complete reference for configuration options
- **`docs/core/Environment-Variables-Spec.md`**: Complete reference for environment variables
- **`.apprc.example`** (or `.config.toml`): Example configuration file in project root
- **`.env.example`**: Example environment variables in project root

### Related Standards

- **`docs/read-only/standards/Test-Environment-Isolation-Standards.md`**: Environment isolation requirements (complements this document)
- **`docs/read-only/standards/Python-Standards.md`**: Type hints and code style
- **`docs/read-only/standards/Coding-Standards.md`**: General code quality principles
