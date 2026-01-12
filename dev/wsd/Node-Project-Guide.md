# JavaScript/TypeScript Project Setup Guide

**Version:** 1.0.0
**Audience:** Developers integrating WSD into JavaScript or TypeScript projects

## Introduction

This guide covers the specific setup requirements for using Workscope-Dev (WSD) with JavaScript and TypeScript projects. WSD provides tools for health checks, code documentation, and quality validation that adapt their behavior based on your project's language type.

For general WSD installation instructions, see the Integration-Guide.md first, then return here for JavaScript/TypeScript-specific configuration.

**Related Documentation:**
- **`package.json.md`** - Authoritative reference for scripts and dependencies. Use this file as your copy-paste source.
- **`tsconfig.json.md`** - Authoritative reference for TypeScript compiler configuration (TypeScript projects only).
- **`typedoc.json.md`** - Authoritative reference for TypeDoc API documentation configuration (TypeScript projects only).
- **`jsdoc.json.md`** - Authoritative reference for JSDoc API documentation configuration (JavaScript projects only).
- **`eslintrc.md`** - Authoritative reference for ESLint configuration. Covers TypeScript vs JavaScript parser settings, security scanning, and TSDoc validation.
- **`prettierrc.md`** - Authoritative reference for Prettier configuration. Covers formatting options, ignore patterns, and editor integration.
- **Integration-Guide.md** - General WSD installation instructions
- **Python-Project-Guide.md** - Setup guide for Python projects

## Prerequisites

Before configuring WSD for JavaScript or TypeScript, ensure you have:

- **WSD installed**: Follow Integration-Guide.md to install WSD into your project
- **Node.js 18+**: Required for all JavaScript/TypeScript tooling
- **npm, pnpm, or yarn**: Package manager (WSD auto-detects which you use)
- **Python 3.10+**: Required for WSD core scripts (including `update_docs.py`)

## Quick Start

If you're integrating WSD into an **existing project** that already has ESLint and Prettier configured, the minimum setup is:

```bash
# 1. Install WSD (if not already done)
python /path/to/wsd-source/wsd.py install .

# 2. Verify your package.json has the required scripts (see package.json.md)

# 3. Test the health check
./wsd.py health
```

If starting from scratch or missing dependencies, follow the complete setup below.

## Project Detection

WSD automatically detects and distinguishes between JavaScript and TypeScript projects by examining both configuration files and actual source files:

| Detection Criteria                                     | Classification |
| ------------------------------------------------------ | -------------- |
| `package.json` exists AND `.ts` files in check dirs    | TypeScript     |
| `package.json` exists AND NO `.ts` files in check dirs | JavaScript     |
| No `package.json`                                      | Not detected   |

**How Language Detection Works:**

WSD scans your configured check directories for `.ts` files to determine whether your project is TypeScript or JavaScript. The detection uses the `wsd.checkDirs` field in `package.json` (see Configuration section below), falling back to conventional directories (`src`, `lib`, `source`, `tests`, `test`) if not configured.

- **TypeScript projects**: Contain at least one `.ts` file in check directories
- **JavaScript projects**: Contain `package.json` but no `.ts` files in check directories
- **Mixed projects**: Projects with both `.ts` and `.js` files are classified as TypeScript

The `update_docs.py` script and task runner use this detection to run the appropriate tools and skip checks that don't apply to your project type.

## Required Dependencies

The required packages depend on whether your project uses JavaScript or TypeScript.

### JavaScript Projects

| Package                  | Purpose             | Required | WSD Feature                                  |
| ------------------------ | ------------------- | -------- | -------------------------------------------- |
| `eslint`                 | Linting             | **Yes**  | `./wsd.py lint`, health check                |
| `prettier`               | Code formatting     | **Yes**  | `./wsd.py format`, health check              |
| `eslint-plugin-security` | Security scanning   | Optional | Health check (skips if missing)              |
| `jsdoc`                  | HTML API docs       | Optional | codedocs_jsdoc.js (required for script)      |
| `@babel/parser`          | Code map generation | Optional | codedocs_javascript.js (required for script) |
| `jest`                   | Testing framework   | Optional | `./wsd.py test`                              |

**Quick Install (JavaScript):**

```bash
npm install --save-dev eslint prettier
```

**With Documentation Tools:**

```bash
npm install --save-dev eslint prettier jsdoc @babel/parser
```

### TypeScript Projects

> **TypeScript projects only**: The following packages are in addition to the JavaScript requirements above.

| Package                            | Purpose                     | Required    | WSD Feature                               |
| ---------------------------------- | --------------------------- | ----------- | ----------------------------------------- |
| `typescript`                       | Type checking & compilation | **Yes**     | All TS commands, codedocs_typescript.js   |
| `@types/node`                      | Node.js type definitions    | **Yes**     | TypeScript compilation                    |
| `@typescript-eslint/parser`        | ESLint TS support           | Recommended | ESLint for TypeScript                     |
| `@typescript-eslint/eslint-plugin` | ESLint TS rules             | Recommended | ESLint for TypeScript                     |
| `eslint-plugin-tsdoc`              | TSDoc validation            | Optional    | Health check (skips if missing)           |
| `typedoc`                          | HTML API doc generation     | Optional    | codedocs_typedoc.js (required for script) |
| `@types/jest`                      | Jest type definitions       | Optional    | Jest with TypeScript                      |
| `ts-jest`                          | Jest TS transformer         | Optional    | Jest with TypeScript                      |

**Quick Install (TypeScript):**

```bash
npm install --save-dev eslint prettier typescript @types/node
```

For a fully-featured TypeScript installation with all optional packages:

```bash
npm install --save-dev \
  typescript \
  @types/node \
  eslint \
  @typescript-eslint/parser \
  @typescript-eslint/eslint-plugin \
  prettier \
  typedoc \
  jest \
  @types/jest \
  ts-jest \
  eslint-plugin-security \
  eslint-plugin-tsdoc
```

### Graceful Degradation

Optional packages enable additional WSD features. When missing, the health check **gracefully skips** these checks rather than failing - they appear with "⏭️ SKIPPED" status in the summary. Install them when you want those specific quality checks enabled.

**See `package.json.md`** for complete dependency documentation and alternative tool choices (Vitest instead of Jest, Biome instead of ESLint/Prettier, etc.).

## Required Scripts

WSD's task runner (`wsd.py`) delegates to your package.json scripts. It doesn't run tools directly - it calls `npm run <script>` (or pnpm/yarn equivalent).

### JavaScript Projects

These scripts are required for JavaScript projects:

```json
{
  "scripts": {
    "lint": "eslint .",
    "format": "prettier --write .",
    "format:check": "prettier --check ."
  }
}
```

> **JavaScript projects**: No `build` script is required since JavaScript doesn't need compilation. The health check will skip build validation automatically.

### TypeScript Projects

> **TypeScript projects only**: These scripts include build and type-checking, which are not applicable to JavaScript projects.

```json
{
  "scripts": {
    "lint": "eslint .",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "build": "tsc",
    "typecheck": "tsc --noEmit"
  }
}
```

### Recommended Scripts (Full WSD Support)

```json
{
  "scripts": {
    "test": "jest",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "lint:json": "eslint . --format json",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "typecheck": "tsc --noEmit",
    "validate": "npm run lint && npm run typecheck && npm run format:check",
    "build": "tsc"
  }
}
```

**Important:** Script names are fixed (must be `lint`, not `eslint-check`), but implementations are flexible (use your preferred tools).

### Optional Scripts (Project-Type Dependent)

Some scripts are only needed for specific project types:

```json
{
  "scripts": {
    "dev": "vite",
    "serve": "vite preview"
  }
}
```

| Script  | Purpose                   | Needed For                       |
| ------- | ------------------------- | -------------------------------- |
| `dev`   | Development server        | Web apps (React, Vue, Angular)   |
| `serve` | Production preview server | Web apps requiring local preview |

**Note:** CLI tools, libraries, and backend services typically don't need `dev` or `serve` scripts. The health check does not require these scripts.

**See `package.json.md`** for the complete script reference with all WSD commands and customization examples.

## Configuration Files

### Check Directories Configuration (package.json)

WSD uses the `wsd.checkDirs` field in `package.json` to determine which directories to scan for language detection and tool execution. This applies to both JavaScript and TypeScript projects.

```json
{
  "name": "my-project",
  "wsd": {
    "checkDirs": ["src", "tests"]
  }
}
```

**Why This Matters:**

- WSD scans these directories to detect whether your project is TypeScript or JavaScript
- Health check tools (ESLint, Prettier, security scans) target these directories
- Provides a single source of truth for project structure

**Fallback Behavior:** If `wsd.checkDirs` is not configured, WSD falls back to:
1. Parsing `tsconfig.json` include patterns (if present)
2. Conventional directories: `src`, `lib`, `source`, `tests`, `test`

**Recommendation:** Explicitly configure `wsd.checkDirs` for reliable detection. See `package.json.md` for complete documentation.

### TypeScript Compiler (tsconfig.json)

> **TypeScript projects only**: JavaScript projects do not need a `tsconfig.json` file.

Minimum configuration for TypeScript projects:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "strict": true,
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

**See `tsconfig.json.md`** for complete configuration examples by project type (Node.js backend, React app, library package) and detailed explanations of all compiler options.

### ESLint Configuration

ESLint configuration differs between JavaScript and TypeScript projects.

**JavaScript Projects:**

```javascript
module.exports = {
  extends: ['eslint:recommended'],
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module'
  },
  env: {
    node: true,
    es2020: true
  }
};
```

**TypeScript Projects:**

> **TypeScript projects only**: The `project` field enables type-aware linting rules but requires `.ts` files.

```javascript
module.exports = {
  parser: '@typescript-eslint/parser',
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended'
  ],
  plugins: ['@typescript-eslint'],
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
    project: './tsconfig.json'
  }
};
```

**Key Difference:** The `project` field in `parserOptions` enables TypeScript type-aware linting rules. When absent (JavaScript projects), the parser handles `.js` files without type checking.

### Prettier Configuration

Create `.prettierrc`:

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

And `.prettierignore`:

```
dist/
node_modules/
*.min.js
docs/reports/
```

### TypeDoc Configuration

> **TypeScript projects only**: TypeDoc generates API documentation from TypeScript source code. JavaScript projects should use JSDoc with a tool like `jsdoc` or `documentation.js` instead.

WSD provides a default `typedoc.json` for generating HTML API documentation. Place it in your project root or `scripts/` directory.

**See `typedoc.json.md`** for the complete TypeDoc configuration, customization examples, and explanations of all options.

### JavaScript Documentation (JSDoc)

JavaScript projects use JSDoc comments for API documentation. WSD includes two documentation generation scripts for JavaScript projects:

**codedocs_jsdoc.js** - Generates comprehensive HTML API documentation using JSDoc:
```bash
node scripts/codedocs_jsdoc.js
```
Output: `dev/reports/jsdoc-api-docs/` (HTML directory with navigation and search)

**codedocs_javascript.js** - Generates lightweight AI-friendly code maps using Babel parser:
```bash
node scripts/codedocs_javascript.js
```
Output: `docs/reports/JavaScript-Code-Map.md` (markdown for AI consumption)

**Required Setup:**

1. Install dependencies:
```bash
npm install --save-dev jsdoc @babel/parser
```

2. Add a `jsdoc` script to your package.json (required for codedocs_jsdoc.js):
```json
{
  "scripts": {
    "jsdoc": "jsdoc -c jsdoc.json -d dev/reports/jsdoc-api-docs -r"
  }
}
```

3. Configure source directories in package.json:
```json
{
  "wsd": {
    "checkDirs": ["src"]
  }
}
```

If the required packages or scripts are not configured, the scripts will exit with a clear error message explaining how to set them up.

**Example JSDoc comment:**

```javascript
/**
 * Calculates the sum of two numbers.
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} The sum of a and b
 */
function add(a, b) {
  return a + b;
}
```

Unlike TypeScript's type annotations, JSDoc provides documentation without requiring a compilation step.

**JSDoc Configuration (jsdoc.json):**

For optimal JSDoc output, create a `jsdoc.json` configuration file in your project root:

```json
{
  "source": {
    "include": ["src"],
    "exclude": ["node_modules", "dist"]
  },
  "opts": {
    "destination": "dev/reports/jsdoc-api-docs",
    "recurse": true
  },
  "plugins": ["plugins/markdown"],
  "templates": {
    "cleverLinks": true,
    "monospaceLinks": true
  }
}
```

Key configuration options:
- `source.include`: Directories containing source files to document
- `source.exclude`: Directories to skip (dependencies, build output)
- `opts.destination`: Output location for HTML documentation
- `plugins`: Enable markdown support in JSDoc comments (recommended)

**See `jsdoc.json.md`** for the complete JSDoc configuration reference, customization examples, and explanations of all options.

**See `Code-Doc-Guide.md`** for complete documentation generation instructions.

## WSD Command Reference

### Task Runner Commands

WSD's task runner (`wsd.py`) provides these commands for TypeScript projects:

| WSD Command              | Delegates To            | Description                     |
| ------------------------ | ----------------------- | ------------------------------- |
| `./wsd.py health`        | Multiple scripts        | Runs comprehensive health check |
| `./wsd.py test`          | `npm run test`          | Run test suite                  |
| `./wsd.py test:watch`    | `npm run test:watch`    | Run tests in watch mode         |
| `./wsd.py test:coverage` | `npm run test:coverage` | Run tests with coverage         |
| `./wsd.py lint`          | `npm run lint`          | Check for lint errors           |
| `./wsd.py lint:fix`      | `npm run lint:fix`      | Auto-fix lint errors            |
| `./wsd.py format`        | `npm run format`        | Format code                     |
| `./wsd.py format:check`  | `npm run format:check`  | Check formatting                |
| `./wsd.py type`          | `npm run typecheck`     | Type check code                 |
| `./wsd.py validate`      | `npm run validate`      | Lint + type + format check      |
| `./wsd.py build`         | `npm run build`         | Build project                   |
| `./wsd.py sync`          | `npm install`           | Install dependencies            |
| `./wsd.py audit`         | `npm audit`             | Audit dependencies              |

**Note:** Replace `npm` with `pnpm` or `yarn` based on your lock file. WSD auto-detects your package manager.

### Health Check (`./wsd.py health`)

Runs comprehensive code quality checks, adapting automatically based on whether your project is JavaScript or TypeScript:

**TypeScript Projects:**
1. **Build Validation**: Runs `npm run build` to verify TypeScript compiles successfully
2. **Security Scan**: Runs `npm run lint:security` if configured (skips otherwise)
3. **Dependency Audit**: Runs `npm audit` to check for vulnerabilities
4. **Documentation Validation**: Runs `npm run lint:tsdoc` and `npm run typedoc:validate` if configured (skips otherwise)
5. **Linting (ESLint)**: Runs `npm run lint`, attempts auto-fix on failure
6. **Code Formatting (Prettier)**: Runs `npm run format:check`, auto-formats if needed

**JavaScript Projects:**
1. **Build Validation**: SKIPPED (JavaScript doesn't require compilation)
2. **Security Scan**: Runs `npm run lint:security` if configured (skips otherwise)
3. **Dependency Audit**: Runs `npm audit` to check for vulnerabilities
4. **Documentation Validation**: SKIPPED (TypeDoc requires TypeScript)
5. **Linting (ESLint)**: Runs `npm run lint`, attempts auto-fix on failure
6. **Code Formatting (Prettier)**: Runs `npm run format:check`, auto-formats if needed

**Rationale for Sequence:** Build validation runs first because structural failures (type errors, import issues) block meaningful analysis. Security and dependency checks follow to identify vulnerabilities early. Documentation validates content completeness. Linting identifies code quality issues. Formatting runs last as pure style changes never affect functionality.

**Optional Scripts:** Security scan and documentation validation require both the package AND the corresponding script to be defined. See `package.json.md` for the optional scripts (`lint:security`, `lint:tsdoc`, `typedoc:validate`).

**Flags:**
- `--aggressive`: Treat warnings as errors during linting (adds `--max-warnings 0`)
- `--commands`: Show all commands used by each check

**Note on Aggressive Mode:** Unlike Python's ruff which has distinct safe and unsafe fix categories (`--fix` vs `--unsafe-fixes`), ESLint does not distinguish between safe and unsafe auto-fixes. The `--aggressive` flag for TypeScript makes the linter stricter by treating warnings as errors, but it does not enable any additional or potentially behavior-changing fixes.

**Example Output (TypeScript Project):**
```
============================================================
HEALTH CHECK SUMMARY
============================================================
Check                Status          Details
------------------------------------------------------------
Build Validation     ✅ PASSED
Security Scan        ✅ PASSED
Dependency Audit     ✅ PASSED
Documentation        ⏭️  SKIPPED     TSDoc not configured
Linting              ✅ PASSED
Code Formatting      ✅ PASSED
============================================================
```

**Example Output (JavaScript Project):**
```
============================================================
HEALTH CHECK SUMMARY
============================================================
Check                Status          Details
------------------------------------------------------------
Build Validation     ⏭️  SKIPPED     JavaScript project
Security Scan        ✅ PASSED
Dependency Audit     ✅ PASSED
Documentation        ⏭️  SKIPPED     TypeDoc requires TypeScript
Linting              ✅ PASSED
Code Formatting      ✅ PASSED
============================================================
```

### Documentation Scripts

WSD provides documentation generation scripts for both TypeScript and JavaScript projects. All scripts use zero-argument interfaces, reading configuration from `package.json` and project-specific configuration files.

**TypeScript Documentation:**

**Code Map (`codedocs_typescript.js`):**
Generates a markdown code map from TypeScript source using the TS Compiler API:

```bash
node scripts/codedocs_typescript.js
```

Reads source directories from `package.json` `wsd.checkDirs` and compiler options from `tsconfig.json`. Output goes to `docs/reports/TypeScript-Code-Map.md`.

**TypeDoc HTML Generation (`codedocs_typedoc.js`):**
Generates TypeDoc API documentation in HTML format:

```bash
node scripts/codedocs_typedoc.js
```

Uses `typedoc.json` configuration (see `typedoc.json.md`). Output goes to `dev/reports/typedoc-api-docs/` (HTML directory).

**Required dependency:** `typedoc` (HTML is the native output format - no plugins needed)

**Viewing documentation:** Open `dev/reports/typedoc-api-docs/index.html` in your browser or serve locally with `python -m http.server -d dev/reports/typedoc-api-docs`

**JavaScript Documentation:**

**JSDoc HTML (`codedocs_jsdoc.js`):**
Generates HTML API documentation using JSDoc:

```bash
node scripts/codedocs_jsdoc.js
```

Reads source directories from `package.json` `wsd.checkDirs`. Output goes to `dev/reports/jsdoc-api-docs/`.

**Required dependency:** `jsdoc`

**Code Map (`codedocs_javascript.js`):**
Generates a markdown code map from JavaScript source using Babel parser:

```bash
node scripts/codedocs_javascript.js
```

Reads source directories from `package.json` `wsd.checkDirs`. Output goes to `docs/reports/JavaScript-Code-Map.md`.

**Required dependency:** `@babel/parser`

**Note:** If required dependencies are not installed, the scripts will exit with a clear error message.

**Consistency Across Languages:** All three ecosystem tools (pdoc, JSDoc, TypeDoc) generate HTML by default, providing navigable documentation with search and cross-references for human developers.

**Update Docs (`update_docs.py`):**
Unified documentation script that auto-detects TypeScript projects:

```bash
python scripts/update_docs.py          # Full mode (tests, docs, health check)
python scripts/update_docs.py --quick  # Quick mode (structure, file lists, code maps)
```

## Integration Scenarios

### Scenario 1: New JavaScript Project

Starting from scratch with WSD and JavaScript:

```bash
# Create project
mkdir my-js-project && cd my-js-project
npm init -y

# Install linting and formatting tools
npm install --save-dev eslint prettier

# Configure wsd.checkDirs in package.json
# Add: "wsd": { "checkDirs": ["src"] }

# Install WSD
python /path/to/wsd-source/wsd.py install .

# Add required scripts to package.json (see package.json.md)

# Initialize git and test
git init
./wsd.py health
git add . && git commit -m "Initialize JavaScript project with WSD"
```

### Scenario 2: New TypeScript Project

Starting from scratch with WSD and TypeScript:

```bash
# Create project
mkdir my-ts-project && cd my-ts-project
npm init -y

# Install TypeScript and dependencies
npm install --save-dev typescript @types/node eslint prettier

# Create tsconfig.json
npx tsc --init

# Configure wsd.checkDirs in package.json
# Add: "wsd": { "checkDirs": ["src"] }

# Install WSD
python /path/to/wsd-source/wsd.py install .

# Add required scripts to package.json (see package.json.md)

# Initialize git and test
git init
./wsd.py health
git add . && git commit -m "Initialize TypeScript project with WSD"
```

### Scenario 3: Existing TypeScript Project

Adding WSD to a project with existing TypeScript setup:

```bash
cd my-existing-ts-project

# Checkpoint
git add -A && git commit -m "Checkpoint before WSD"

# Install WSD
python /path/to/wsd-source/wsd.py install .

# Verify package.json scripts exist (see package.json.md)
# If missing, add lint, format, build scripts

# Test health check
./wsd.py health

# Commit WSD
git add -A && git commit -m "Add Workscope-Dev framework"
```

### Scenario 4: React/Vue/Angular Project

Frontend frameworks typically come with ESLint and build tooling pre-configured. WSD integrates smoothly:

```bash
# React (Create React App)
npx create-react-app my-app --template typescript
cd my-app
python /path/to/wsd-source/wsd.py install .
# CRA already has lint, build scripts configured

# Vue
npm create vue@latest
cd my-vue-app
python /path/to/wsd-source/wsd.py install .
# Add any missing scripts to package.json

# Angular
ng new my-angular-app
cd my-angular-app
python /path/to/wsd-source/wsd.py install .
# Angular CLI provides lint, build, test scripts
```

### Scenario 5: Node.js Backend

For Express, NestJS, or other Node.js backends (JavaScript or TypeScript):

```bash
cd my-backend-project

# Ensure ESLint/Prettier are installed
npm install --save-dev eslint prettier @typescript-eslint/parser @typescript-eslint/eslint-plugin

# Add .eslintrc.js (see Configuration Files section)
# Add .prettierrc (see Configuration Files section)

# Install WSD
python /path/to/wsd-source/wsd.py install .

# Verify scripts in package.json
./wsd.py health
```

### Scenario 6: Mixed Python/JavaScript or Python/TypeScript Project

For projects with both Python and JavaScript/TypeScript:

```bash
cd my-mixed-project

# Install WSD
python /path/to/wsd-source/wsd.py install .

# Add Python configuration to pyproject.toml (see Python-Project-Guide.md)
# Add TypeScript configuration to package.json (see package.json.md)

# WSD commands will run for BOTH languages
./wsd.py health   # Runs both Python and TypeScript health checks
./wsd.py test     # Runs pytest AND jest
./wsd.py lint     # Runs ruff AND eslint
```

## Troubleshooting

### Health Check Fails Immediately

**Symptom:** `./wsd.py health` fails with "command not found"

**Solution:** Ensure Node.js 18+ is installed and in PATH:
```bash
node --version  # Should be 18.x or higher
```

### ESLint Script Missing

**Symptom:** Health check fails with "npm run lint" error

**Solution:** Add the lint script to package.json (see `package.json.md`):
```json
{
  "scripts": {
    "lint": "eslint ."
  }
}
```

### Prettier Script Missing

**Symptom:** Health check fails on formatting step

**Solution:** Add the format script to package.json:
```json
{
  "scripts": {
    "format": "prettier --write ."
  }
}
```

### Build Script Fails

**Symptom:** Health check passes lint/format but fails on build

**Solution:** Verify your build script works standalone:
```bash
npm run build
```

Common issues:
- Missing `outDir` in tsconfig.json (see `tsconfig.json.md`)
- TypeScript errors in source code
- Missing dependencies

### TypeScript Import Error

**Symptom:** `codedocs_typescript.js` fails with "Cannot find module 'typescript'"

**Solution:** Install TypeScript as a dev dependency:
```bash
npm install --save-dev typescript
```

### Package Manager Detection

**Symptom:** Wrong package manager being used

**Solution:** WSD detects package manager from lock files. Ensure only one exists:
- `pnpm-lock.yaml` → pnpm
- `yarn.lock` → yarn
- `package-lock.json` → npm

Delete extra lock files if needed.

### Security Scan Skipped

**Symptom:** Health check shows "Security Scan SKIPPED"

**Solution:** Install eslint-plugin-security:
```bash
npm install --save-dev eslint-plugin-security
```

Then add to your ESLint config:
```javascript
module.exports = {
  extends: ['plugin:security/recommended'],
  plugins: ['security']
};
```

### JSDoc Script Not Found

**Symptom:** `codedocs_jsdoc.js` fails with "jsdoc script not found in package.json"

**Solution:** Install JSDoc and add the script to package.json:
```bash
npm install --save-dev jsdoc
```

Then add the script:
```json
{
  "scripts": {
    "jsdoc": "jsdoc -c jsdoc.json -d dev/reports/jsdoc-api-docs -r"
  }
}
```

### JavaScript Parse Errors

**Symptom:** `codedocs_javascript.js` shows "Warning: Could not parse file.js"

**Solution:** The file contains syntax errors. Fix the syntax errors in your JavaScript source files. The code mapper uses Babel parser with ES2024+ syntax support, so ensure your code is valid JavaScript.

Common causes:
- Unclosed brackets or parentheses
- Invalid ES module/CommonJS mixing
- Unsupported experimental syntax

### No JavaScript Files Found

**Symptom:** Code mapper completes but output is empty or minimal

**Solution:** Verify your `wsd.checkDirs` configuration points to directories containing `.js` files:
```json
{
  "wsd": {
    "checkDirs": ["src", "lib"]
  }
}
```

The code mapper excludes these patterns:
- `node_modules/`, `dist/`, `build/`, `coverage/`, `__tests__/` directories
- `*.min.js`, `*.bundle.js`, `*.test.js`, `*.spec.js`, `*.config.js` files

### Babel Parser Not Found

**Symptom:** `codedocs_javascript.js` fails with "Cannot find module '@babel/parser'"

**Solution:** Install the Babel parser:
```bash
npm install --save-dev @babel/parser
```

### TypeScript Project Detected

**Symptom:** JavaScript documentation scripts skip with "TypeScript project detected"

**Solution:** This is expected behavior. JavaScript documentation tools are designed for JavaScript-only projects. If your project contains `.ts` files in the check directories, use the TypeScript tools instead:
```bash
node scripts/codedocs_typedoc.js    # For HTML docs
node scripts/codedocs_typescript.js  # For code maps
```

## Next Steps

After completing TypeScript setup:

1. **Run health check**: `./wsd.py health` to verify everything works
2. **Generate documentation**: `python scripts/update_docs.py --quick` to test doc generation
3. **Customize WORKSCOPE-DEV tags**: Fill in project-specific content in WSD files
4. **Set up Action Plan**: Add your project phases and tasks
5. **Start your first session**: Run `/wsd:init` in Claude Code

For updates and maintenance, see Update-Guide.md.

---

*This guide covers JavaScript and TypeScript-specific WSD configuration. For general installation, see Integration-Guide.md. For the task runner, see Task-Runner-Guide.md.*
