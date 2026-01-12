# Environment and Configuration Variable Standards

## Overview

This document establishes the architectural principles and decision framework for determining whether a setting belongs as an environment variable or in a configuration file. These standards apply to any software project that must choose between these two fundamental configuration mechanisms.

The principles codified here emerged from practical experience managing configuration across diverse deployment environments, security contexts, testing infrastructure, and user requirements. They provide deterministic guidance that ensures settings are placed where they naturally belong, avoiding the confusion and maintenance burden that arises from arbitrary placement decisions.

## Core Philosophy: Practical Minimalism

The guiding principle for configuration architecture is **practical minimalism**: use the simplest approach that satisfies genuine technical requirements. For most applications, especially CLI tools and developer utilities, this means:

1. **Configuration files for user preferences** - Settings users actively manage
2. **Environment variables only when technically required** - Security, testing, or tooling constraints
3. **Minimal `.env` files** - Only what cannot reasonably go elsewhere
4. **Clear separation of concerns** - Internal vs external variables

## The Two Configuration Mechanisms

### Configuration Files (`.appirc`, `.config`, `settings.yml`, etc.)

Configuration files excel at:
- **User preferences** that users actively manage and modify
- **Complex structures** like aliases, mappings, and nested settings
- **Settings with defaults** that work for most users
- **Self-documenting options** with comments and examples
- **Version control** for non-sensitive settings

### Environment Variables

Environment variables are necessary for:
- **Secrets and credentials** that must stay out of version control
- **Testing infrastructure** that relies on environment injection
- **Bootstrap configuration** needed before config files can be found
- **Process-level overrides** for temporary configuration changes
- **External tool integration** where other tools expect specific variables

## Decision Criteria

### Primary Criteria (In Order of Priority)

#### 1. Security Requirement (Absolute)

**Principle:** Settings containing secrets, credentials, or sensitive information MUST be environment variables and NEVER appear in configuration files.

This principle is absolute and overrides all other considerations. Security always wins.

**Examples that MUST be environment variables:**
- API keys and tokens
- Database passwords
- Encryption keys
- OAuth credentials
- Any value that could compromise security or incur costs if exposed

#### 2. Testing Infrastructure Requirement

**Principle:** Settings that testing frameworks need to mock or inject should be environment variables.

Modern testing practices rely heavily on environment variable manipulation for test isolation and dependency injection. This is particularly true in Python, JavaScript, and other dynamic languages.

**Why this matters:**
```python
# This pattern is ubiquitous in testing:
@patch.dict(os.environ, {"API_KEY": "test-key"}, clear=True)
def test_api_authentication():
    # Test can control the environment cleanly
    pass
```

**Examples that should be environment variables:**
- API keys (even fake ones for testing)
- Test data paths
- Feature flags for test scenarios
- Mock service endpoints

#### 3. Bootstrap and Override Requirement

**Principle:** Settings needed to locate configuration files or temporarily override configuration should be environment variables.

Some settings must exist before configuration files can be found or need to override file-based configuration for specific invocations.

**Examples:**
- Config file location override (`CONFIG_PATH=/tmp/special.conf myapp`)
- Temporary debug flags (`DEBUG=1 myapp`)
- Bootstrap paths needed to find config files

#### 4. External Tool Integration

**Principle:** When integrating with external tools or following industry standards, respect their conventions.

Don't reinvent patterns that the ecosystem already expects. However, distinguish between:
- **External variables you READ** (like `NO_COLOR` from the shell)
- **Internal variables you SET** (in your own `.env` file)

Reading external variables doesn't require having your own `.env` file.

**Examples of external standards to respect:**
- `NO_COLOR` - Disables color output (industry standard)
- `DEBUG` - Debug mode (common convention)
- `HOME`, `USER` - System variables
- Tool-specific vars (`EDITOR`, `PAGER`, `BROWSER`)

#### 5. User Preference Test

**Principle:** Settings that represent user preferences or application behavior should go in configuration files.

If users will want to customize it, see it documented, and understand available options, it belongs in a configuration file.

**Examples for configuration files:**
- Default models or providers
- Output formatting preferences
- Feature toggles
- Behavioral settings (timeouts, retries)
- UI customization

### Secondary Considerations

#### Default Value Test

**Question:** Does this setting have a meaningful default that works for most users?

- **Has good default** → Configuration file (can document the default)
- **No reasonable default** → Environment variable (deployment-specific)

#### Complexity Test

**Question:** Is this setting part of a complex structure?

- **Simple key-value** → Could be either
- **Nested structure, lists, mappings** → Configuration file (better format support)

## Application Context Matters

### CLI Tools and Developer Utilities

CLI tools have different needs than deployed services:

- **Single user context** - Not dealing with multiple deployments
- **Local execution** - Running on developer machines, not servers
- **Direct invocation** - Users run commands directly
- **Testing patterns** - Heavy use of environment injection in tests

For CLI tools, lean toward configuration files except where environment variables are technically required.

### Web Services and Deployed Applications

Services following 12-factor app principles need more environment variables:

- **Multiple deployments** - Dev, staging, production
- **Container orchestration** - Kubernetes, Docker configs
- **Secret management** - Vault, AWS Secrets Manager
- **Infrastructure as code** - Terraform, CloudFormation

For services, environment variables for deployment configuration are standard.

### Libraries and Frameworks

Libraries should generally:
- Read from environment variables for common conventions
- Allow configuration objects to be passed by the consuming application
- Avoid requiring their own configuration files
- Document which environment variables they respect

## Implementation Guidelines

### Environment Variable Practices

#### Naming Conventions
- Use `UPPER_SNAKE_CASE` for environment variables
- Prefix with application name to avoid collisions (e.g., `MYAPP_API_KEY`)
- Follow platform conventions for standard variables

#### Loading Behavior
**Use defensive loading** - `.env` files should only set variables that aren't already set:

```python
# CORRECT: Defensive loading (respect existing environment)
if "API_KEY" not in os.environ:
    os.environ["API_KEY"] = dotenv_value

# WRONG: Aggressive loading (overwrites existing values)
os.environ["API_KEY"] = dotenv_value  # Don't do this
```

This allows:
- Shell overrides: `API_KEY=test myapp`
- CI/CD injection to work properly
- Testing frameworks to control environment
- User expectations to be met

#### Documentation Requirements
- Document all recognized environment variables
- Distinguish between required and optional
- Provide `.env.example` with safe examples (never real secrets)
- Explain precedence and override behavior

### Configuration File Practices

#### File Formats
- Use established formats (TOML, YAML, JSON, INI)
- Choose formats that support comments for documentation
- Consider human readability and editing ease

#### File Locations
Establish a clear search order:
1. Explicit path (via `--config` flag or env var)
2. Current directory
3. User config directory
4. System config directory

#### Default Behavior
- Applications should work with zero configuration when possible
- Provide complete defaults in code
- Ship example configuration files
- Document all available options

## Common Patterns and Anti-Patterns

### Correct Patterns

#### Minimal `.env` File
```bash
# .env - Only what MUST be environment variables

# Secrets (security requirement)
API_KEY=sk-1234...

# Test infrastructure (testing requirement)
TEST_DATA_PATH=tests/fixtures

# Override mechanism (bootstrap requirement)
# CONFIG_PATH=/tmp/special-config.yml
```

#### Rich Configuration File
```yaml
# config.yml - User preferences and behavior

display:
  format: json
  colors: auto
  verbose: false

behavior:
  timeout: 30
  retries: 3

features:
  experimental_mode: false
```

### Anti-Patterns to Avoid

#### Putting Secrets in Config Files
```yaml
# WRONG - Never put secrets in config files
api:
  key: sk-1234...  # Security vulnerability!
```

#### Duplicating Everything
```bash
# WRONG - Don't mirror config file options in env vars
MYAPP_OUTPUT_FORMAT=json
MYAPP_OUTPUT_COLOR=true
MYAPP_OUTPUT_VERBOSE=false
MYAPP_BEHAVIOR_TIMEOUT=30
MYAPP_BEHAVIOR_RETRIES=3
# Just use a config file for these!
```

#### Aggressive Environment Loading
```python
# WRONG - Don't overwrite existing environment
load_dotenv(override=True)  # This breaks shell overrides
```

#### Test-Only Settings in User Config
```yaml
# WRONG - Test infrastructure doesn't belong in user config
testing:
  mock_api: true
  test_data_dir: /tests/data
```

## Testing Considerations

### Why Testing Drives Environment Variable Usage

Testing infrastructure, particularly in dynamic languages, relies heavily on environment variable manipulation:

1. **Isolation** - Each test can have its own environment
2. **Injection** - Mock values easily injected
3. **Cleanup** - Environment automatically restored after test
4. **Framework Support** - Built-in support in test frameworks

### Testing Patterns

```python
# Environment variables are easy to mock
@patch.dict(os.environ, {"API_KEY": "test"}, clear=True)
def test_with_api_key():
    assert get_api_key() == "test"

# Config files require more complex mocking
def test_with_config(tmp_path):
    config = tmp_path / "config.yml"
    config.write_text("api_key: test")
    # How do we tell the app where this config is?
    # We need an environment variable anyway!
```

## Precedence and Override Behavior

### Standard Precedence Order (Highest to Lowest)

1. **Command-line arguments** - Most specific, immediate override
2. **Environment variables** - Deployment or session level
3. **Configuration files** - User preferences
4. **Built-in defaults** - Fallback values

### Override Philosophy

- Command-line arguments always win (most specific)
- Environment variables override files (deployment overrides preferences)
- `.env` files use defensive loading (don't overwrite existing)
- Document precedence clearly for users

## Migration and Evolution

### Adding New Settings

Ask these questions in order:
1. Is it a secret? → Environment variable
2. Is it needed for testing? → Environment variable
3. Is it needed for bootstrap? → Environment variable
4. Is it a user preference? → Configuration file
5. Does it have complex structure? → Configuration file
6. Default to configuration file if unsure

### Migrating Existing Settings

When moving settings between mechanisms:
1. Support both locations temporarily
2. Document the migration
3. Use deprecation warnings
4. Provide migration tools if needed
5. Clean up after suitable notice period

## Summary

The choice between environment variables and configuration files is not arbitrary but driven by practical requirements:

**Use environment variables when required by:**
- Security (secrets must not be in files)
- Testing infrastructure (framework expectations)
- Bootstrap needs (finding config files)
- External standards (respecting conventions)

**Use configuration files for:**
- User preferences
- Complex structures
- Self-documenting settings
- Anything with good defaults

**Key principles:**
- Maintain a minimal `.env` file
- Use defensive loading (don't overwrite existing environment)
- Respect external standards without unnecessary duplication
- Let practical requirements drive decisions, not theoretical purity
- Different application types have different needs

By following these standards, applications achieve the right balance of security, usability, testability, and maintainability without unnecessary complexity.
