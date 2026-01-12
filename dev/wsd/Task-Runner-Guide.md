# Workscope-Dev Task Runner Guide

**Version:** 1.0.0
**Audience:** Developers using WSD in their projects

## Introduction

The WSD Task Runner (wsd.py) provides a unified command interface for common development tasks across Python and TypeScript projects. Instead of remembering different commands for each language's tooling (pytest vs jest, ruff vs eslint), you use consistent commands like `wsd test`, `wsd lint`, and `wsd format` that automatically run the appropriate tools for your project.

## Quick Start

### Using the Task Runner

The task runner is the `wsd.py` file in your project root. You can run it directly:

```bash
./wsd.py test
python wsd.py lint
```

### Shell Alias (Recommended)

For convenience, create a shell alias to type `wsd` instead of `./wsd.py`:

**Bash/Zsh** (add to `~/.bashrc` or `~/.zshrc`):
```bash
alias wsd='./wsd.py'
```

**Fish** (add to `~/.config/fish/config.fish`):
```fish
alias wsd './wsd.py'
```

After adding the alias and reloading your shell, you can use the shorter command:

```bash
wsd test
wsd lint
wsd format
```

All examples in this guide use the `wsd` alias format.

## Multi-Language Projects

### How Language Detection Works

The task runner automatically detects which languages your project uses based on source file presence:

- **Python detected** when `pyproject.toml` has a `[project]` section OR `.py` files exist in configured check directories
- **TypeScript detected** when `package.json` exists AND `.ts` files are found in configured check directories
- **JavaScript detected** when `package.json` exists but NO `.ts` files are found in check directories
- **Codeless** when none of the above conditions are met

TypeScript and JavaScript are mutually exclusive - a project with any `.ts` files is classified as TypeScript. However, a project can be both Python AND TypeScript/JavaScript (e.g., a Python backend with a React frontend).

### Multi-Language Command Execution

In projects with multiple languages, commands run for ALL detected languages:

```bash
# In a Python + TypeScript project
$ wsd test

🚀 Running: uv run pytest
=============== test session starts ===============
collected 42 items
...
42 passed in 2.1s

🚀 Running: pnpm test
> my-app@1.0.0 test
> jest
...
PASS  src/components/App.test.tsx
Test Suites: 8 passed, 8 total
Tests:       54 passed, 54 total
```

The task runner executes commands sequentially (Python first, then Node.js) with fail-fast behavior - if Python tests fail, Node.js tests won't run. This ensures all parts of your codebase pass before considering the task successful.

### Single-Language Projects

For projects with only one language, commands run only the relevant tools:

**Python-only project:**
```bash
$ wsd test
🚀 Running: uv run pytest
```

**TypeScript project:**
```bash
$ wsd test
🚀 Running: pnpm test
```

**JavaScript project:**
```bash
$ wsd test
🚀 Running: npm test
```

## Command Reference

The task runner provides 29 commands organized into 4 categories.

### Workscope-Dev Core Commands

These commands support WSD-specific operations:

| Command             | Description                  | Example                 |
| ------------------- | ---------------------------- | ----------------------- |
| `install`           | Install WSD to a project     | `wsd install .`         |
| `update`            | Update WSD installation      | `wsd update .`          |
| `prompt`            | Create new prompt session    | `wsd prompt`            |
| `health`            | Run health diagnostics       | `wsd health`            |
| `health:aggressive` | Run aggressive health checks | `wsd health:aggressive` |
| `archive`           | Archive Claude sessions      | `wsd archive`           |
| `docs:update`       | Update WSD documentation     | `wsd docs:update`       |
| `docs:full`         | Full documentation rebuild   | `wsd docs:full`         |

The `install` and `update` commands are the primary mechanisms for distributing WSD to projects. For detailed usage, see `Integration-Guide.md` (installation) and `Update-Guide.md` (updates).

The `health` command runs for both Python and Node.js languages when detected, checking language-specific health metrics.

### Testing & Quality Commands

These commands help maintain code quality:

| Command           | Multi-Lang  | Description                      | Example               |
| ----------------- | ----------- | -------------------------------- | --------------------- |
| `test`            | Yes         | Run test suite                   | `wsd test`            |
| `test:watch`      | Yes         | Auto-rerun tests on changes      | `wsd test:watch`      |
| `test:coverage`   | Yes         | Run tests with coverage          | `wsd test:coverage`   |
| `lint`            | Yes         | Check code for issues            | `wsd lint`            |
| `lint:fix`        | Yes         | Auto-fix linting issues          | `wsd lint:fix`        |
| `lint:aggressive` | Yes         | Fix with unsafe transformations  | `wsd lint:aggressive` |
| `lint:docs`       | Python-only | Check docstring compliance       | `wsd lint:docs`       |
| `lint:docs:fix`   | Python-only | Fix docstring issues             | `wsd lint:docs:fix`   |
| `format`          | Yes         | Format code                      | `wsd format`          |
| `format:check`    | Yes         | Check formatting without changes | `wsd format:check`    |
| `type`            | Yes         | Run type checker                 | `wsd type`            |
| `validate`        | Yes         | Run lint + type + format:check   | `wsd validate`        |
| `security`        | Yes         | Security vulnerability scan      | `wsd security`        |

**Multi-Language Behavior:**
- Commands marked "Yes" run for all detected languages
- Python-only commands (like `lint:docs`) only execute for Python projects
- In multi-language projects, tools for each language run sequentially

**What Each Command Does:**

**Python:**
- `test` → `uv run pytest`
- `lint` → `uv run ruff check [directories]`
- `format` → `uv run ruff format [directories]`
- `type` → `uv run mypy [directories]`
- `security` → `uv run bandit -r [directories] -f screen -ll`

**Node.js (TypeScript/JavaScript):**
- `test` → `{pm} test` (where `{pm}` is pnpm/npm/yarn/bun based on your lock file)
- `lint` → `{pm} run lint`
- `format` → `{pm} run format`
- `type` → `{pm} run typecheck`
- `security` → `{pm} audit`

### Build & Development Commands

These commands support development workflows:

| Command | Multi-Lang | Description              | Example     |
| ------- | ---------- | ------------------------ | ----------- |
| `build` | Yes        | Build project            | `wsd build` |
| `dev`   | Yes        | Start development server | `wsd dev`   |
| `serve` | Yes        | Serve built project      | `wsd serve` |
| `watch` | Yes        | Watch files and rebuild  | `wsd watch` |
| `clean` | Yes        | Clean build artifacts    | `wsd clean` |

### Dependencies & Security Commands

These commands manage project dependencies:

| Command     | Multi-Lang | Description                          | Example         |
| ----------- | ---------- | ------------------------------------ | --------------- |
| `sync`      | Yes        | Install and synchronize dependencies | `wsd sync`      |
| `audit`     | Yes        | Check for vulnerabilities            | `wsd audit`     |
| `audit:fix` | Yes        | Fix vulnerable dependencies          | `wsd audit:fix` |

**Package Manager Detection:**

For Node.js projects (TypeScript and JavaScript), the task runner detects your package manager from lock files:
- `pnpm-lock.yaml` → uses `pnpm`
- `package-lock.json` → uses `npm`
- `yarn.lock` → uses `yarn`
- `bun.lockb` → uses `bun`

A lock file is required. If no lock file exists, the task runner will prompt you to initialize your package manager by running its install command (e.g., `pnpm install`, `npm install`).

## Configuration

### Universal Commands (No Configuration Required)

These commands work immediately without any setup:
- All WSD core commands (`prompt`, `health`, `archive`, etc.)
- Testing commands (`test`, `test:watch`, `test:coverage`)
- Build commands (`build`, `dev`, `serve`, `watch`, `clean`)
- Dependency commands (`sync`, `update`, `audit`, `audit:fix`)

### Configuration-Dependent Commands

Some Python commands require configuration to specify which directories to check:

**Commands needing configuration:**
- `lint`, `lint:fix`, `lint:aggressive`
- `lint:docs`, `lint:docs:fix`
- `format`, `format:check`
- `type`
- `security`

**How to configure:**

Add a `[tool.wsd]` section to your `pyproject.toml`:

```toml
[tool.wsd]
check_dirs = ["src", "tests"]
```

The `check_dirs` array specifies which directories these tools should analyze. Typical values:
- `["src", "tests"]` for projects with a `src/` directory
- `["myproject", "tests"]` for projects with a package directory
- `["source", "tests"]` (as used in the WSD Development project itself)

**What happens without configuration:**

If you run a configuration-dependent command without `[tool.wsd]` configuration, you'll see:

```
ERROR: [tool.wsd] configuration missing or incomplete in pyproject.toml.

Add this to your pyproject.toml:

[tool.wsd]
check_dirs = ["src", "tests"]
```

### Node.js Configuration (TypeScript/JavaScript)

Node.js commands delegate to scripts defined in your `package.json`. You should define these scripts for the commands you want to use:

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "lint:aggressive": "eslint . --fix",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "typecheck": "tsc --noEmit",
    "build": "tsc",
    "dev": "vite dev"
  }
}
```

You can customize these scripts to match your project's tooling choices (e.g., using Biome instead of ESLint + Prettier, or Vitest instead of Jest).

## Command Examples

### Running Tests

```bash
# Run all tests
wsd test

# Run tests in watch mode (auto-rerun on changes)
wsd test:watch

# Run tests with coverage report
wsd test:coverage

# Pass additional arguments to test command
wsd test -k test_auth  # Python: runs pytest -k test_auth
wsd test --verbose     # Forwards --verbose to pytest/jest
```

### Linting and Formatting

```bash
# Check for linting issues (does not modify files)
wsd lint

# Automatically fix linting issues
wsd lint:fix

# Format code (modifies files)
wsd format

# Check if code is formatted correctly (does not modify)
wsd format:check

# Run all quality checks without modifying files
wsd validate  # Runs lint + type + format:check
```

### Python Docstring Linting

Python projects can use specialized docstring linting:

```bash
# Check docstring compliance (Google-style, NumPy-style, etc.)
wsd lint:docs

# Automatically fix docstring issues
wsd lint:docs:fix
```

These commands use Ruff's docstring rules (D-selector) to ensure consistent documentation.

### Security Scanning

```bash
# Scan for security vulnerabilities
wsd security

# In Python projects: runs bandit on source code
# In TypeScript projects: runs npm/pnpm/yarn audit
# In multi-language projects: runs both
```

### Working with Dependencies

```bash
# Install and synchronize dependencies
wsd sync

# Check for known vulnerabilities
wsd audit

# Automatically fix vulnerable dependencies
wsd audit:fix
```

## Viewing Available Commands

Run the task runner without arguments to see all available commands for your project:

```bash
$ wsd

Workscope Runner - Available Commands
Project Languages: PYTHON, TYPESCRIPT
Package Manager: pnpm
======================================================================

Workscope-Dev Core:
  install              → wsd.py install [--dry-run] [--force] <target-path>
  update               → wsd.py update [--dry-run] <target-path>
  prompt               → python scripts/new_prompt.py
  health               → python scripts/health_check.py
                         node scripts/health_check.js
  ...

Testing & Quality:
  test                 → uv run pytest
                         pnpm test
  lint                 → uv run ruff check src/ tests/
                         pnpm run lint
  ...
```

The help display shows:
- Which languages are detected in your project
- Which package manager is detected (for Node.js projects)
- What actual command will run for each task
- Multi-language commands display all commands that will execute

## API Documentation Generation

The task runner does not include built-in commands for API documentation generation (like pdoc for Python or TypeDoc for TypeScript). This is intentional - API documentation tools are project-specific and better suited for custom project scripts.

**Why API documentation commands were removed:**

Not all projects need API documentation. Web applications, CLI tools, and internal services often don't publish API docs. Projects that do need API docs can add their own scripts:

**For Python projects** (add to `scripts/` directory):
```bash
#!/usr/bin/env bash
# scripts/generate_api_docs.sh
uv run pdoc src/ -o docs/api/
```

**For TypeScript projects** (add to package.json):
```json
{
  "scripts": {
    "docs:api": "typedoc src/ --out docs/api/"
  }
}
```

This approach keeps the task runner focused on universal development commands while allowing each project to customize documentation generation for their specific needs.

## Troubleshooting

### Command Not Found

**Problem:** Shell says `wsd: command not found`

**Solutions:**
1. Ensure you created the shell alias (see Shell Alias section above)
2. Reload your shell configuration: `source ~/.bashrc` or `source ~/.zshrc`
3. Or use the direct invocation: `./wsd.py` or `python wsd.py`

### No Languages Detected

**Problem:** Task runner says "No languages detected"

**Solution:** Add appropriate project markers and source files:
- For Python: create `pyproject.toml` with a `[project]` section, OR add `.py` files to your configured check directories
- For TypeScript: create `package.json` and add `.ts` files to your configured check directories
- For JavaScript: create `package.json` (JavaScript is detected when no `.ts` files exist)

### Missing Package Manager Lock File

**Problem:** Node.js commands fail with "No package manager lock file found"

**Solution:** Initialize your preferred package manager to create a lock file:
```bash
pnpm install   # Creates pnpm-lock.yaml
# or
npm install    # Creates package-lock.json
# or
yarn install   # Creates yarn.lock
# or
bun install    # Creates bun.lockb
```

The task runner requires an explicit lock file to determine which package manager to use. This follows the explicit configuration principle - WSD does not assume a default package manager.

### Configuration Required Error

**Problem:** Command fails with "ERROR: [tool.wsd] configuration missing"

**Solution:** Add `[tool.wsd]` section to `pyproject.toml` (see Configuration section above)

### Tests Failing in Multi-Language Projects

**Problem:** Python tests pass but Node.js tests fail, and you don't see Node.js test output

**Explanation:** This is expected fail-fast behavior. When the first language fails, subsequent languages don't run. Fix the Python tests first, then Node.js tests will run.

**Workaround:** Run language-specific tests directly:
```bash
uv run pytest          # Python only
pnpm test              # Node.js only (or npm/yarn/bun based on your lock file)
```

## Related Documentation

- **Task-Runner-Overview.md**: Technical specification of the task runner architecture
- **Integration-Guide.md**: Installing WSD into your project
- **Python-Standards.md**: Python tooling standards and configuration
- **TypeScript-Standards.md**: TypeScript tooling standards and configuration

---

*This guide covers the WSD Task Runner for end users. For technical implementation details, see the Task-Runner-Overview.md specification.*
