# Code Documentation Guide

This guide explains how to use the WSD code documentation system to generate API documentation and code maps for your projects.

## Overview

WSD provides automated code documentation generation through two types of tools that serve different audiences:

1. **API Documentation Generators**: Use ecosystem tools (pdoc for Python, JSDoc for JavaScript, TypeDoc for TypeScript) to generate comprehensive HTML documentation for human developers
2. **Code Map Generators**: Use static analysis (AST for Python/JavaScript, TypeScript Compiler API for TypeScript) to generate lightweight markdown summaries designed for AI assistants

Both tool types read configuration from your project's configuration file and write to predictable output locations, requiring no command-line arguments.

## Quick Start

Generate documentation from your project root:

```bash
# Using the WSD task runner (runs all documentation tools)
wsd docs

# Or run individual scripts directly
# Python
python scripts/codedocs_pdoc.py      # Generate HTML API docs
python scripts/codedocs_python.py    # Generate markdown code map

# TypeScript
node scripts/codedocs_typedoc.js     # Generate HTML API docs
node scripts/codedocs_typescript.js  # Generate markdown code map
```

## TypeScript Documentation

The TypeScript documentation tools automatically detect your project language and skip gracefully for JavaScript-only projects. Both tools require TypeScript source files to function.

### Configuration Requirements

Both TypeScript documentation scripts read configuration from multiple sources:

**package.json** (required):
```json
{
  "name": "my-typescript-project",
  "wsd": {
    "checkDirs": ["src", "tests"]
  }
}
```

**tsconfig.json** (required):
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "strict": true
  },
  "include": ["src/**/*"]
}
```

**typedoc.json** (required for TypeDoc only):
```json
{
  "entryPoints": ["./src"],
  "entryPointStrategy": "expand",
  "out": "./dev/reports/typedoc-api-docs",
  "readme": "none",
  "cleanOutputDir": true,
  "excludePrivate": true,
  "excludeExternals": true
}
```

The `wsd.checkDirs` field specifies which directories contain source code to analyze. This configuration is shared across WSD tools for consistency.

### HTML API Documentation (codedocs_typedoc.js)

The `codedocs_typedoc.js` script generates comprehensive HTML API documentation using TypeDoc's native HTML output. This follows the same pattern as pdoc for Python—both ecosystem tools generate multi-file HTML directories for human developers.

**Basic Usage:**

```bash
node scripts/codedocs_typedoc.js
```

**Output Location:** `dev/reports/typedoc-api-docs/` (HTML directory)

**Features:**
- Uses TypeDoc's native HTML output for comprehensive API documentation
- Multi-file HTML organized by type (classes, interfaces, functions, etc.)
- Interactive navigation sidebar and search functionality
- Includes full JSDoc content with type information
- Cross-referenced type links
- Responsive design for viewing on any device
- Can be served locally or published to static hosting

**Generation Process:**

The script performs:
1. Detects project language (skips JavaScript-only projects)
2. Verifies TypeDoc is installed locally
3. Runs TypeDoc to generate multi-file HTML documentation to `dev/reports/typedoc-api-docs/`
4. TypeDoc's `cleanOutputDir` option removes stale files automatically

**Required Dependencies:**

Install TypeDoc as a development dependency:

```bash
npm install --save-dev typedoc
```


**Viewing Documentation:**

Open `dev/reports/typedoc-api-docs/index.html` in your browser, or serve it locally:

```bash
python -m http.server -d dev/reports/typedoc-api-docs
# Then open http://localhost:8000
```

### Markdown Code Map (codedocs_typescript.js)

The `codedocs_typescript.js` script generates a lightweight markdown summary of your codebase using the TypeScript Compiler API for semantic analysis.

**Basic Usage:**

```bash
node scripts/codedocs_typescript.js
```

**Output Location:** `docs/reports/TypeScript-Code-Map.md`

**Features:**
- Uses TypeScript Compiler API for deep semantic analysis
- Zero-import analysis (works even with broken imports)
- Token-conscious summaries optimized for AI consumption
- Complete type information through type checker
- Automatic JSDoc extraction and formatting
- Resolution of relative `{@link}` paths to project-root relative

**What Gets Documented:**

| Construct    | Information Extracted                           |
| ------------ | ----------------------------------------------- |
| Classes      | Name, modifiers, properties, methods with types |
| Interfaces   | Name, properties, method signatures             |
| Functions    | Name, parameters, return types, signatures      |
| Enums        | Name, members with values                       |
| Type Aliases | Name, complete type definition                  |
| Variables    | Name, modifiers, type information               |

**Output Format:**

The generated markdown includes:
- Table of contents linking to each file
- File-level JSDoc descriptions
- Categorized symbols within each file (Classes, Interfaces, Functions, etc.)
- Full type information and signatures
- Alphabetically sorted items within categories

**Example Output:**

```markdown
# TypeScript Code Map

## Table of Contents
- [`src/config.ts`](#file-src_config_ts)
- [`src/main.ts`](#file-src_main_ts)

---

## File: `src/config.ts`

Configuration management for the application.

### Classes

#### Config

*export*

Application configuration container.

**Properties**:
- **apiUrl**: `string` private
  - Base URL for API endpoints

**Methods**:
- **load**() => `Promise<void>` public
  - Loads configuration from environment
```

### TypeScript Troubleshooting

#### "TypeDoc Generator: Skipping - TypeScript project required"

**Cause:** The script detected no TypeScript files in the configured directories.

**Solution:**
1. Verify `.ts` files exist in your source directories
2. Check your `wsd.checkDirs` configuration in package.json
3. Ensure the directories listed actually contain TypeScript files
4. For JavaScript-only projects, TypeDoc cannot be used—consider JSDoc instead

#### "Code Map Generator: Skipping - TypeScript project required"

**Cause:** Same as above—no TypeScript files found in configured directories.

**Solution:** Same as above—verify TypeScript files exist and `checkDirs` is correctly configured.

#### "Warning: No wsd.checkDirs configured in package.json"

**Cause:** The `wsd.checkDirs` field is missing from package.json.

**Solution:** Add the configuration to your package.json:
```json
{
  "wsd": {
    "checkDirs": ["src", "tests"]
  }
}
```

This warning is non-fatal—the scripts will use fallback directories, but explicit configuration is recommended.

#### tsconfig.json not found

**Cause:** The TypeScript configuration file is missing from the project root.

**Solution:**
1. Create a tsconfig.json in your project root
2. Or run `npx tsc --init` to generate a default configuration

#### TypeDoc execution fails

**Cause:** TypeDoc encountered an error processing your source files.

**Common causes and solutions:**
1. Missing TypeDoc dependency—install with `npm install --save-dev typedoc`
2. Invalid typedoc.json configuration—verify JSON syntax and required fields
3. TypeScript compilation errors—run `tsc --noEmit` to check
4. Missing entry points—verify directories in `entryPoints` exist

#### Empty or minimal code map output

**Cause:** Source files are being filtered out or contain no exportable declarations.

**Solution:**
1. Check your `wsd.checkDirs` configuration points to the correct directories
2. Verify TypeScript files exist: `find src -name "*.ts"`
3. Ensure files contain exported declarations
4. Check for syntax errors: `npx tsc --noEmit`

#### Missing JSDoc in generated documentation

**Cause:** Source files lack JSDoc comments.

**Solution:** Add JSDoc comments to your source code:
```typescript
/**
 * Calculates the sum of two numbers.
 *
 * @param a - The first number
 * @param b - The second number
 * @returns The sum of a and b
 */
export function add(a: number, b: number): number {
  return a + b;
}
```

## JavaScript Documentation

The JavaScript documentation tools automatically detect your project language and skip gracefully for TypeScript projects. Both tools require JavaScript source files (no `.ts` files in check directories) to function.

### Configuration Requirements

Both JavaScript documentation scripts read configuration from `package.json`:

**package.json** (required):
```json
{
  "name": "my-javascript-project",
  "wsd": {
    "checkDirs": ["src", "lib"]
  }
}
```

**jsdoc.json** (optional, for JSDoc HTML generation):
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

The `wsd.checkDirs` field specifies which directories contain source code to analyze. This configuration is shared across WSD tools for consistency.

For complete JSDoc configuration options, see `jsdoc.json.md`.

### HTML API Documentation (codedocs_jsdoc.js)

The `codedocs_jsdoc.js` script generates comprehensive HTML API documentation by invoking the JSDoc CLI tool configured in your `package.json`.

**Basic Usage:**

```bash
node scripts/codedocs_jsdoc.js
```

**Output Location:** `dev/reports/jsdoc-api-docs/` (HTML directory)

**Features:**
- Uses JSDoc's native HTML output for comprehensive API documentation
- Multi-file HTML with navigation, search, and cross-references
- Includes full JSDoc content with type annotations from comments
- Validates that `jsdoc` script exists in `package.json` before running
- Uses detected package manager (npm/pnpm/yarn/bun) to invoke the script

**Generation Process:**

The script performs:
1. Detects project language (skips TypeScript projects)
2. Reads `wsd.checkDirs` from `package.json`
3. Validates `jsdoc` script is configured in `package.json`
4. Cleans output directory to remove stale files
5. Runs JSDoc via your package manager (`npm run jsdoc`, etc.)

**Required Setup:**

1. Install JSDoc as a development dependency:
```bash
npm install --save-dev jsdoc
```

2. Add the `jsdoc` script to your `package.json`:
```json
{
  "scripts": {
    "jsdoc": "jsdoc -c jsdoc.json -d dev/reports/jsdoc-api-docs -r"
  }
}
```

**Viewing Documentation:**

Open `dev/reports/jsdoc-api-docs/index.html` in your browser, or serve it locally:

```bash
python -m http.server -d dev/reports/jsdoc-api-docs
# Then open http://localhost:8000
```

### Markdown Code Map (codedocs_javascript.js)

The `codedocs_javascript.js` script generates a lightweight markdown summary of your codebase using the Babel parser for JavaScript AST analysis.

**Basic Usage:**

```bash
node scripts/codedocs_javascript.js
```

**Output Location:** `docs/reports/JavaScript-Code-Map.md`

**Features:**
- Uses Babel parser for ES2024+ syntax support
- Zero-import analysis (works even with broken imports)
- Token-conscious summaries optimized for AI consumption
- Extracts JSDoc comments and type annotations
- Automatic private member filtering (names starting with `_`)

**What Gets Documented:**

| Construct          | Information Extracted                        |
| ------------------ | -------------------------------------------- |
| ES6 Classes        | Name, JSDoc, methods, properties             |
| Class Methods      | Name, parameters, return type from JSDoc     |
| Class Properties   | Name, type from JSDoc, description           |
| Functions          | Name, parameters, return type, JSDoc         |
| Arrow Functions    | Name, parameters, JSDoc (when exported)      |
| Variables          | Name, type from JSDoc, description           |

**File Filtering:**

The code mapper excludes certain directories and file patterns:

**Excluded Directories:**
- `node_modules/`, `dist/`, `build/`, `coverage/`, `__tests__/`

**Excluded File Patterns:**
- `*.min.js`, `*.bundle.js`, `*.test.js`, `*.spec.js`, `*.config.js`

**Output Format:**

The generated markdown includes:
- Table of contents linking to each file
- File-level JSDoc descriptions
- Categorized symbols within each file (Classes, Functions, Variables)
- Full type information from JSDoc annotations
- Alphabetically sorted items within categories

**Example Output:**

```markdown
# JavaScript Code Map

## Table of Contents
- [`src/config.js`](#file-src_config_js)
- [`src/main.js`](#file-src_main_js)

---

## File: `src/config.js`

Configuration management for the application.

### Classes

#### Config

*export*

Application configuration container.

**Properties**:
- **apiUrl**: `string`
  - Base URL for API endpoints

**Methods**:
- **load**() => `Promise<void>`
  - Loads configuration from environment
```

### JavaScript Troubleshooting

#### "JSDoc Generator: Skipping - JavaScript-only project required"

**Cause:** The script detected TypeScript files (`.ts`) in the configured directories.

**Solution:**
1. JavaScript documentation tools are designed for JavaScript-only projects
2. If your project contains `.ts` files, use the TypeScript tools instead:
   ```bash
   node scripts/codedocs_typedoc.js    # For HTML docs
   node scripts/codedocs_typescript.js  # For code maps
   ```

#### "Error: jsdoc script not found in package.json"

**Cause:** The `jsdoc` script is not configured in your `package.json`.

**Solution:**
1. Install JSDoc as a dev dependency:
   ```bash
   npm install --save-dev jsdoc
   ```
2. Add the script to your `package.json`:
   ```json
   {
     "scripts": {
       "jsdoc": "jsdoc -c jsdoc.json -d dev/reports/jsdoc-api-docs -r"
     }
   }
   ```

#### "Warning: No wsd.checkDirs configured in package.json"

**Cause:** The `wsd.checkDirs` field is missing from `package.json`.

**Solution:** Add the configuration to your `package.json`:
```json
{
  "wsd": {
    "checkDirs": ["src", "lib"]
  }
}
```

#### "Warning: Could not parse file.js: SyntaxError"

**Cause:** The JavaScript file contains syntax errors and cannot be parsed by Babel.

**Solution:**
1. Fix the syntax errors in your source files
2. The code mapper uses Babel parser with ES2024+ syntax support
3. Check for: unclosed brackets, invalid module syntax, unsupported experimental features

The code mapper skips unparseable files and continues with remaining files, so one broken file won't halt entire documentation generation.

#### Empty or minimal code map output

**Cause:** Source files are being filtered out or contain no exportable declarations.

**Solution:**
1. Check your `wsd.checkDirs` configuration points to the correct directories
2. Verify JavaScript files exist: `find src -name "*.js"`
3. Ensure files contain exported declarations (classes, functions, variables)
4. Check files don't match exclusion patterns (`*.test.js`, `*.config.js`, etc.)

#### Missing descriptions in generated documentation

**Cause:** JavaScript files lack JSDoc comments.

**Solution:** Add JSDoc comments to your source code:
```javascript
/**
 * Calculates the sum of two numbers.
 * @param {number} a - The first number
 * @param {number} b - The second number
 * @returns {number} The sum of a and b
 */
function add(a, b) {
  return a + b;
}
```

Items without JSDoc comments will show "No description available." in the code map.

## Python Documentation

### Configuration Requirements

Both Python documentation scripts read configuration from `pyproject.toml`:

```toml
[project]
name = "mypackage"  # Package name (required for pdoc)

[tool.wsd]
check_dirs = ["src", "tests"]  # Source directory is check_dirs[0]
```

The `[project].name` value must match the actual package directory name within your source directory. The first entry in `check_dirs` is used as the source directory for documentation generation.

### HTML API Documentation (codedocs_pdoc.py)

The `codedocs_pdoc.py` script generates comprehensive HTML API documentation using pdoc with automatic module discovery and Google-style docstring support.

**Basic Usage:**

```bash
python scripts/codedocs_pdoc.py
```

**Output Location:** `dev/reports/pydoc-api-docs/`

**Features:**
- Automatic module discovery within your package
- Google-style docstring parsing
- Searchable documentation with navigation
- Source code viewing capability
- Cross-referenced type annotations

**Module Discovery:**

The script automatically discovers all Python modules in your package by:
1. Locating the package directory at `{source_dir}/{package_name}`
2. Recursively scanning for all `.py` files
3. Filtering out non-documentable files (tests, cache, data directories)
4. Converting file paths to Python module notation

**Excluded Files:**
- `__pycache__` directories
- `/data/` directories
- `test_*.py` and `*_test.py` files
- `__main__.py` files

**Debug Mode:**

To see which modules will be documented, set the `DEBUG_DOCS` environment variable:

```bash
DEBUG_DOCS=1 python scripts/codedocs_pdoc.py
```

This prints the complete list of discovered modules before generation.

**Auto-Installation:**

If pdoc is not installed, the script automatically installs it using `uv pip install pdoc`.

### Markdown Code Map (codedocs_python.py)

The `codedocs_python.py` script generates a lightweight markdown summary of your codebase structure using Python's AST module for static analysis.

**Basic Usage:**

```bash
python scripts/codedocs_python.py
```

**Output Location:** `docs/reports/Python-Code-Map.md`

**Features:**
- Zero-import analysis (works even with broken imports)
- Token-conscious summaries for AI consumption
- Automatic docstring extraction and summarization
- Private member filtering (focuses on public API)

**Output Format:**

The generated markdown includes:
- Module names with docstring summaries
- Class definitions with public method lists
- Function definitions with descriptions
- Alphabetically sorted for consistency

**Example Output:**

```markdown
# Python API Structure

## Modules

### `mypackage.cli`

Command-line interface implementation.

**Functions:**

- `main()`: Entry point for CLI application.
- `parse_args()`: Parse command-line arguments.

### `mypackage.config`

Configuration management.

**Classes:**

- `Config`: Application configuration container.
  - Methods: `load()`, `save()`, `validate()`
```

**Error Handling:**

Files with syntax errors are silently skipped, allowing documentation of valid modules even when some files are broken. This makes the tool safe to run on codebases with work-in-progress files.

### Python Troubleshooting

#### "pyproject.toml not found"

**Cause:** The script cannot locate the configuration file.

**Solution:** Ensure `pyproject.toml` exists in your project root with the required configuration:
```toml
[project]
name = "your-package-name"

[tool.wsd]
check_dirs = ["src", "tests"]
```

#### "[project].name missing in pyproject.toml"

**Cause:** The pdoc script requires the package name for module discovery.

**Solution:** Add the project name to your configuration:
```toml
[project]
name = "your-package-name"
```

#### "[tool.wsd].check_dirs missing"

**Cause:** Both scripts require the source directory configuration.

**Solution:** Add the WSD configuration:
```toml
[tool.wsd]
check_dirs = ["src", "tests"]
```

#### "Package not found in source directory"

**Cause:** The package name in `[project].name` doesn't match the directory name under your source path.

**Solution:**
1. Verify your package directory exists: `ls src/`
2. Ensure `[project].name` exactly matches the package directory name (case-sensitive)
3. Common issue: hyphens in TOML (`my-package`) vs underscores in directory (`my_package`)

#### "pdoc is not installed"

**Cause:** pdoc is not available and automatic installation failed.

**Solution:** Install manually:
```bash
uv pip install pdoc
# or
pip install pdoc
```

#### Modules missing from documentation

**Cause:** Files are being filtered by exclusion rules.

**Solution:**
1. Check if files match exclusion patterns (`test_*.py`, `*_test.py`, `__main__.py`, `/data/`)
2. Use debug mode to see discovered modules: `DEBUG_DOCS=1 python scripts/codedocs_pdoc.py`
3. Rename files if they incorrectly match test patterns

#### Empty or minimal code map output

**Cause:** Either the source directory is empty or files have syntax errors.

**Solution:**
1. Verify Python files exist: `find src -name "*.py"`
2. Check for syntax errors: `python -m py_compile src/mypackage/module.py`
3. Files with syntax errors are silently skipped

#### "No module description" in code map

**Cause:** Python files lack module-level docstrings.

**Solution:** Add a docstring at the top of each file:
```python
"""Module description goes here.

This is the first paragraph that appears in the code map.
"""
```

#### HTML pages have broken imports

**Cause:** pdoc imports modules to generate documentation, and some imports fail.

**Solution:**
1. Verify all dependencies are installed
2. Check for circular imports
3. Use the AST-based code map generator as an alternative (doesn't require imports)

## CI/CD Integration

### GitHub Actions

```yaml
name: Generate Documentation

on: [push, pull_request]

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # For TypeScript projects
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Generate TypeScript API docs
        run: node scripts/codedocs_typedoc.js

      - name: Generate TypeScript code map
        run: node scripts/codedocs_typescript.js

      # For Python projects
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install pdoc

      - name: Generate Python API docs
        run: python scripts/codedocs_pdoc.py

      - name: Generate Python code map
        run: python scripts/codedocs_python.py
```

### GitLab CI

```yaml
generate-docs:
  stage: build
  script:
    # TypeScript
    - npm ci
    - node scripts/codedocs_typedoc.js
    - node scripts/codedocs_typescript.js
    # Python
    - pip install pdoc
    - python scripts/codedocs_pdoc.py
    - python scripts/codedocs_python.py
  artifacts:
    paths:
      - dev/reports/typedoc-api-docs/
      - docs/reports/TypeScript-Code-Map.md
      - dev/reports/pydoc-api-docs/
      - dev/reports/jsdoc-api-docs/
      - docs/reports/JavaScript-Code-Map.md
      - docs/reports/Python-Code-Map.md
```

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Generate code maps and stage them
python scripts/codedocs_python.py
node scripts/codedocs_typescript.js
git add docs/reports/Python-Code-Map.md
git add docs/reports/TypeScript-Code-Map.md
```

This ensures code maps stay synchronized with code changes.

## Recommended Workflow

1. **Configure your project**: Ensure your configuration file has the required settings (`pyproject.toml` for Python, `package.json` + `tsconfig.json` for TypeScript)

2. **Generate documentation** after significant code changes:
   ```bash
   # TypeScript
   node scripts/codedocs_typedoc.js
   node scripts/codedocs_typescript.js

   # Python
   python scripts/codedocs_pdoc.py
   python scripts/codedocs_python.py
   ```

3. **Review the code map** to verify your public API is documented correctly:
   ```bash
   cat docs/reports/TypeScript-Code-Map.md
   cat docs/reports/Python-Code-Map.md
   ```

4. **Browse HTML documentation** locally (Python only):
   ```bash
   python -m http.server -d dev/reports/pydoc-api-docs
   # Open http://localhost:8000 in your browser
   ```

5. **Commit the code maps** to version control for AI assistant access:
   ```bash
   git add docs/reports/TypeScript-Code-Map.md
   git add docs/reports/Python-Code-Map.md
   git commit -m "Update code maps"
   ```

## Related Documentation

- [Health Check Guide](Health-Check-Guide.md) - Code quality validation
- [Task Runner Guide](Task-Runner-Guide.md) - WSD command reference
- [Python Standards](../../docs/read-only/standards/Python-Standards.md) - Python coding standards
- [TypeScript Standards](../../docs/read-only/standards/TypeScript-Standards.md) - TypeScript coding standards
