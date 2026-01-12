# Health Check Guide

This guide explains how to use the WSD health check system to maintain code quality in your TypeScript and Python projects.

## Overview

WSD provides comprehensive health checks that validate code quality across multiple dimensions: build validation, security scanning, dependency auditing, documentation completeness, linting, and code formatting. The health check system automatically detects your project type and runs the appropriate checks.

## Quick Start

Run the health check from your project root:

```bash
# Using the WSD task runner
wsd health

# Or run directly for TypeScript projects
node scripts/health_check.js

# Or run directly for Python projects
python scripts/health_check.py
```

## TypeScript Health Check

### Basic Usage

```bash
# Run health check in safe mode (default)
node scripts/health_check.js

# Run with aggressive auto-fixes
node scripts/health_check.js --aggressive

# Show all commands used by each check
node scripts/health_check.js --commands

# Display help
node scripts/health_check.js --help
```

### What Gets Checked

The TypeScript health check runs these checks in sequence:

| Check | Description | Auto-Fix |
|-------|-------------|----------|
| Build Validation | TypeScript compilation and bundling | No |
| Security Scan | Static code analysis for vulnerabilities | No |
| Dependency Audit | npm audit for vulnerable packages | No |
| Documentation | TSDoc/TypeDoc validation | No |
| Linting | ESLint code quality rules | Yes |
| Code Formatting | Prettier style enforcement | Yes |

### Package Manager Support

The health check automatically detects your package manager based on lock files:

1. **pnpm** (highest priority) - Detected by `pnpm-lock.yaml`
2. **yarn** (medium priority) - Detected by `yarn.lock`
3. **npm** (default) - Used if no other lock files found

### Safe vs Aggressive Mode

**Safe Mode** (default): Applies only transformations guaranteed not to change code behavior.

```bash
node scripts/health_check.js
```

**Aggressive Mode**: Applies all auto-fixes and treats warnings as errors.

```bash
node scripts/health_check.js --aggressive
```

### Required package.json Scripts

The health check expects these scripts in your `package.json`:

```json
{
  "scripts": {
    "build": "tsc && vite build",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "lint:json": "eslint . --format json",
    "format": "prettier --write .",
    "format:check": "prettier --check ."
  }
}
```

### Optional Tools

Install these for comprehensive checking:

```bash
# Security scanning
npm install --save-dev eslint-plugin-security

# Documentation validation
npm install --save-dev eslint-plugin-tsdoc typedoc
```

### Understanding Results

The health check produces a summary table:

```
============================================================
HEALTH CHECK SUMMARY
============================================================
Check                Status          Details
------------------------------------------------------------
Build Validation     PASSED
Security Scan        PASSED
Dependency Audit     PASSED
Documentation        WARNING         TSDoc: 3 issue(s) (non-blocking)
Linting              FIXED           All issues auto-fixed
Code Formatting      PASSED
============================================================
```

**Status meanings:**
- **PASSED**: Check completed with no issues
- **FIXED**: Issues detected and automatically fixed
- **FAILED**: Issues detected that require manual attention
- **WARNING**: Non-blocking issues detected
- **SKIPPED**: Check not run (optional tool not installed)

### Exit Codes

- **0**: All checks passed or were auto-fixed
- **1**: One or more checks failed

## Python Health Check

### Basic Usage

```bash
# Run health check in safe mode (default)
python scripts/health_check.py

# Run with aggressive auto-fixes
python scripts/health_check.py --aggressive

# Show all commands used by each check
python scripts/health_check.py --commands
```

### What Gets Checked

The Python health check runs these checks in sequence:

| Check | Description | Auto-Fix |
|-------|-------------|----------|
| Build Validation | Package build verification | No |
| Type Checking | mypy static type analysis | No |
| Security Scan | bandit vulnerability detection | No |
| Dependency Audit | pip-audit for vulnerable packages | No |
| Documentation | Docstring completeness | No |
| Linting | ruff code quality rules | Yes |
| Code Formatting | ruff format style enforcement | Yes |

### Safe vs Aggressive Mode

**Safe Mode** (default): Applies only safe transformations.

```bash
python scripts/health_check.py
```

**Aggressive Mode**: Applies unsafe fixes (may change code behavior).

```bash
python scripts/health_check.py --aggressive
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Health Check

on: [push, pull_request]

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run health check
        run: node scripts/health_check.js
```

### GitLab CI

```yaml
health-check:
  image: node:20
  stage: test
  script:
    - npm ci
    - node scripts/health_check.js
  only:
    - merge_requests
    - main
```

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
node scripts/health_check.js
if [ $? -ne 0 ]; then
    echo "Health check failed. Please fix issues before committing."
    exit 1
fi
```

Or use husky:

```json
{
  "husky": {
    "hooks": {
      "pre-commit": "node scripts/health_check.js"
    }
  }
}
```

## Recommended Workflow

1. **Run health check** before committing:
   ```bash
   node scripts/health_check.js
   ```

2. **Review auto-fixes** to understand changes:
   ```bash
   git diff
   ```

3. **Manually fix** remaining issues based on error messages

4. **Re-run** to verify all checks pass:
   ```bash
   node scripts/health_check.js
   ```

5. **Commit** your clean code:
   ```bash
   git commit -m "Feature with quality checks passed"
   ```

## Troubleshooting

### "Command not found" errors

Ensure dependencies are installed:
```bash
npm install
```

### Build failures

Check your `tsconfig.json` configuration. Common issues:
- Missing type definitions
- Incorrect module resolution
- Path alias configuration

### Security scan skipped

Install the security plugin:
```bash
npm install --save-dev eslint-plugin-security
```

### Dependency vulnerabilities

Update vulnerable packages:
```bash
npm audit fix
```

For breaking changes:
```bash
npm audit fix --force
```

## Related Documentation

- [TypeScript Standards](../read-only/standards/TypeScript-Standards.md) - Coding standards enforced by health checks
- [Python Standards](../read-only/standards/Python-Standards.md) - Python coding standards
- [System Architecture](../core/System-Architecture.md) - WSD Runtime architecture overview
