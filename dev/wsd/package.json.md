# Sample package.json for WSD JavaScript/TypeScript Projects

This file documents the package.json scripts and dependencies required for WSD integration in JavaScript and TypeScript projects. Copy the relevant sections into your project's package.json.

For complete setup instructions, see `Node-Project-Guide.md`.

---

## Required: NPM Scripts

WSD's task runner (`wsd.py`) delegates to your package.json scripts. The following scripts are required for WSD commands to function:

### Required Scripts for Health Check

These scripts are **required** for `./wsd.py health` to pass. The health check invokes these scripts directly:

```json
{
  "scripts": {
    "build": "tsc",
    "lint": "eslint --ext .ts,.tsx,.js,.jsx source tests",
    "lint:fix": "eslint --ext .ts,.tsx,.js,.jsx source tests --fix",
    "lint:json": "eslint --ext .ts,.tsx,.js,.jsx source tests --format json",
    "format": "prettier --write \"source/**/*.{ts,tsx,js,jsx}\" \"tests/**/*.{ts,tsx,js,jsx}\"",
    "format:check": "prettier --check \"source/**/*.{ts,tsx,js,jsx}\" \"tests/**/*.{ts,tsx,js,jsx}\""
  }
}
```

**Notes:**
- `build` is **TypeScript only** — JavaScript projects do not need this script. The health check skips build validation for JavaScript projects.
- `lint:json` is consumed internally by `./wsd.py health` for structured ESLint output parsing. There is no standalone `./wsd.py lint:json` command — users do not invoke this script directly.
- Use explicit file extensions (`--ext .ts,.tsx,.js,.jsx`) to prevent ESLint from scanning non-code files
- Scope commands to your source directories (e.g., `source tests`) rather than the entire project
- The `format:check` script is required for the health check's formatting validation

### Optional Scripts (Testing and Quality)

These scripts provide testing and quality tooling via `./wsd.py`:

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage --coverageDirectory=dev/reports/coverage-node",
    "test:e2e": "playwright test",
    "typecheck": "tsc --noEmit",
    "validate": "npm run lint && npm run typecheck && npm run format:check",
    "watch": "tsc --watch"
  }
}
```

| Script         | Purpose                                      |
| -------------- | -------------------------------------------- |
| `test`         | Run test suite                               |
| `test:watch`   | Run tests in watch mode                      |
| `test:coverage`| Run tests with coverage report               |
| `test:e2e`     | Run end-to-end tests                         |
| `typecheck`    | Type safety validation (TypeScript only)     |
| `validate`     | Composite of lint + typecheck + format:check |
| `watch`        | Watch mode compilation (TypeScript only)     |

**Note:** `typecheck` and `watch` are TypeScript-specific. The health check reports type checking status when the `typecheck` script is available and gracefully skips it when absent.

### Optional Scripts (Health Check Enhancement)

These scripts enable additional health check features. The health check **gracefully skips** these checks if the scripts are missing (they require corresponding dependencies):

```json
{
  "scripts": {
    "lint:security": "eslint --ext .ts,.tsx,.js,.jsx source tests --plugin security --format json",
    "typedoc:validate": "typedoc --validation --treatWarningsAsErrors --emit none"
  }
}
```

| Script            | Requires Package         | Purpose                              |
|-------------------|--------------------------|--------------------------------------|
| `lint:security`   | `eslint-plugin-security` | Security vulnerability scanning      |
| `typedoc:validate`| `typedoc`                | TypeDoc generation validation (TypeScript only) |

**Note:** Each script requires both the package to be installed AND the script to be defined. If either is missing, the health check skips the corresponding check with "⏭️ SKIPPED" status.

### Optional Scripts (Task Runner)

These scripts provide additional task runner commands via `./wsd.py`:

```json
{
  "scripts": {
    "lint:aggressive": "eslint --ext .ts,.tsx,.js,.jsx source tests --fix --max-warnings 0"
  }
}
```

| Script            | Requires Package | Purpose                              |
|-------------------|------------------|--------------------------------------|
| `lint:aggressive` | `eslint`         | Auto-fix lint errors with zero-warning policy |

**Note:** `lint:aggressive` combines `--fix` with `--max-warnings 0`, treating any remaining warning as an error after auto-fixes are applied. Mapped to `./wsd.py lint:aggressive`.

### Optional Scripts (Documentation Generation)

These scripts are consumed by WSD's codedocs scripts to generate API documentation. They are **not** used by the health check or task runner.

**JavaScript projects:**

```json
{
  "scripts": {
    "jsdoc": "jsdoc -c jsdoc.json -d dev/reports/jsdoc-api-docs -r"
  }
}
```

**TypeScript projects:**

```json
{
  "scripts": {
    "typedoc": "typedoc"
  }
}
```

| Script   | Requires Package | Language   | Consumer                |
|----------|------------------|------------|-------------------------|
| `jsdoc`  | `jsdoc`          | JavaScript | `codedocs_jsdoc.js`     |
| `typedoc`| `typedoc`        | TypeScript | `codedocs_typedoc.js`   |

**Note:** `typedoc` is distinct from `typedoc:validate` (listed above under Health Check Enhancement). The `typedoc` script generates HTML API documentation, while `typedoc:validate` checks for documentation warnings without generating output. These scripts will fail with a clear error message if the corresponding dependency is not installed.

### Optional Scripts (Project-Type Dependent)

These scripts are useful for specific project types but not universally needed:

```json
{
  "scripts": {
    "dev": "vite dev",
    "serve": "vite preview"
  }
}
```

**Note:** Web applications typically need `dev` and `serve` scripts, while CLI tools and libraries may not require them.

### Complete Scripts (Full WSD Support)

For full WSD task runner support, combine all the above categories:

```json
{
  "scripts": {
    "build": "tsc",
    "lint": "eslint --ext .ts,.tsx,.js,.jsx source tests",
    "lint:fix": "eslint --ext .ts,.tsx,.js,.jsx source tests --fix",
    "lint:json": "eslint --ext .ts,.tsx,.js,.jsx source tests --format json",
    "lint:aggressive": "eslint --ext .ts,.tsx,.js,.jsx source tests --fix --max-warnings 0",
    "lint:security": "eslint --ext .ts,.tsx,.js,.jsx source tests --plugin security --format json",
    "format": "prettier --write \"source/**/*.{ts,tsx,js,jsx}\" \"tests/**/*.{ts,tsx,js,jsx}\"",
    "format:check": "prettier --check \"source/**/*.{ts,tsx,js,jsx}\" \"tests/**/*.{ts,tsx,js,jsx}\"",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage --coverageDirectory=dev/reports/coverage-node",
    "test:e2e": "playwright test",
    "typecheck": "tsc --noEmit",
    "typedoc": "typedoc",
    "typedoc:validate": "typedoc --validation --treatWarningsAsErrors --emit none",
    "validate": "npm run lint && npm run typecheck && npm run format:check",
    "watch": "tsc --watch",
    "dev": "vite dev",
    "serve": "vite preview"
  }
}
```

**Important Notes:**
- Script names are fixed (e.g., must be `lint`, not `eslint-check`)
- Script implementations are flexible (use your preferred tools)
- WSD runs these via your package manager (`pnpm run lint`, `npm run lint`, etc.)

---

## WSD Configuration

### Check Directories (`wsd.checkDirs`)

The `wsd.checkDirs` field specifies which directories WSD should scan for language detection and tool execution. This configuration is essential for accurate JavaScript/TypeScript detection.

```json
{
  "name": "my-project",
  "wsd": {
    "checkDirs": ["src", "tests"]
  }
}
```

**Purpose:**

1. **Language Detection**: WSD scans these directories for `.ts` files to determine if your project is TypeScript or JavaScript
2. **Tool Targeting**: Health check tools (ESLint, Prettier, security scans) target these directories
3. **Consistent Behavior**: Provides a single source of truth for which directories contain source code

**Configuration Details:**

| Field | Type | Description |
|-------|------|-------------|
| `wsd.checkDirs` | `string[]` | Array of directory paths relative to project root |

**Example Configurations:**

**Standard project with `src` and `tests`:**
```json
{
  "wsd": {
    "checkDirs": ["src", "tests"]
  }
}
```

**Project using `source` and `lib`:**
```json
{
  "wsd": {
    "checkDirs": ["source", "lib", "tests"]
  }
}
```

**Monorepo with multiple packages:**
```json
{
  "wsd": {
    "checkDirs": ["packages/core/src", "packages/cli/src", "tests"]
  }
}
```

**Fallback Behavior:**

If `wsd.checkDirs` is not configured, WSD falls back to:

1. **TypeScript projects**: Parse `tsconfig.json` include patterns to extract base directories
2. **All projects**: Conventional directories: `src`, `lib`, `source`, `tests`, `test`

**Warning:** When using fallback behavior, WSD displays a warning message recommending explicit configuration:

```
Warning: No wsd.checkDirs configured in package.json.
Add "wsd": { "checkDirs": ["src", "tests"] } to package.json for accurate
language detection.
```

**Best Practice:** Always configure `wsd.checkDirs` explicitly to ensure reliable language detection and consistent tool behavior across different environments.

**Placement in package.json:**

The `wsd` field can be placed anywhere in your package.json at the root level:

```json
{
  "name": "my-project",
  "version": "1.0.0",
  "wsd": {
    "checkDirs": ["src", "tests"]
  },
  "scripts": {
    "...": "..."
  },
  "devDependencies": {
    "...": "..."
  }
}
```
- Use explicit file extensions and scoped directories in lint/format scripts

---

## Test Coverage Output Convention

WSD expects Node.js test coverage data to be output to `dev/reports/coverage-node/`. The `update_docs.py` pipeline looks for `coverage-final.json` in this directory after running your `test:coverage` script to generate coverage reports. Both Jest and Vitest produce Istanbul-format coverage data, so the same pipeline works with either test runner.

Configure your `test:coverage` script to write coverage reports to this location:

**Jest:**
```json
{
  "scripts": {
    "test:coverage": "jest --coverage --coverageDirectory=dev/reports/coverage-node"
  }
}
```

**Vitest:**
```json
{
  "scripts": {
    "test:coverage": "vitest run --coverage --coverage.reportsDirectory=dev/reports/coverage-node"
  }
}
```

Vitest requires `@vitest/coverage-v8` (or `@vitest/coverage-istanbul`) as a dev dependency for coverage support:

```json
{
  "devDependencies": {
    "vitest": "^1.0.0",
    "@vitest/coverage-v8": "^1.0.0"
  }
}
```

When `test:coverage` is not defined in your `package.json`, the documentation pipeline falls back to running the `test` script without coverage. Tests still run and results are reported, but no coverage report is generated.

---

## Script Mapping Reference

### Scripts Required for Health Check

The health check (`./wsd.py health`) requires these scripts:

| Script         | Purpose                                      |
| -------------- | -------------------------------------------- |
| `build`        | TypeScript compilation and bundling (TypeScript only) |
| `lint`         | Check for lint errors                        |
| `lint:fix`     | Auto-fix lint errors (safe mode)             |
| `lint:json`    | Lint output in JSON format (internal use by `./wsd.py health`) |
| `format`       | Format code with auto-fix                    |
| `format:check` | Check formatting without modifying files     |

**Note:** The health check's aggressive mode (`./wsd.py health --aggressive`) uses `lint:fix` with `--max-warnings 0` appended. This treats warnings as errors rather than enabling unsafe fixes (ESLint does not have an "unsafe fixes" concept like Python's ruff).

### Optional Scripts for Health Check

These scripts enable additional health check features (gracefully skipped if missing):

| Script            | Requires Package         | Purpose                              |
|-------------------|--------------------------|--------------------------------------|
| `typecheck`       | `typescript`             | Type safety validation               |
| `lint:security`   | `eslint-plugin-security` | Security vulnerability scanning      |
| `typedoc:validate`| `typedoc`                | TypeDoc generation validation        |

### All WSD Command Mappings

| WSD Command           | Required Script  | Description                           |
| --------------------- | ---------------- | ------------------------------------- |
| `./wsd.py health`     | (see table above)| Runs health check                     |
| `./wsd.py test`       | `test`           | Run test suite                        |
| `./wsd.py test:watch` | `test:watch`     | Run tests in watch mode               |
| `./wsd.py test:coverage` | `test:coverage` | Run tests with coverage             |
| `./wsd.py test:e2e`   | `test:e2e`       | Run end-to-end tests                  |
| `./wsd.py lint`       | `lint`           | Check for lint errors                 |
| `./wsd.py lint:fix`   | `lint:fix`       | Auto-fix lint errors                  |
| `./wsd.py lint:aggressive` | `lint:aggressive` | Auto-fix lint errors with zero-warning policy |
| `./wsd.py format`     | `format`         | Format code                           |
| `./wsd.py format:check` | `format:check` | Check formatting                      |
| `./wsd.py type`       | `typecheck`      | Type check code                       |
| `./wsd.py validate`   | `validate`       | Lint + type + format check            |
| `./wsd.py build`      | `build`          | Build project (TypeScript only)       |
| `./wsd.py dev`        | `dev`            | Start development server              |
| `./wsd.py serve`      | `serve`          | Start preview server                  |
| `./wsd.py watch`      | `watch`          | Watch mode compilation                |
| `./wsd.py sync`       | N/A              | Runs package manager install directly |
| `./wsd.py audit`      | N/A              | Runs package manager audit directly   |

---

## Required: Development Dependencies

These dependencies are required for WSD tools to function. The requirements differ between JavaScript and TypeScript projects.

### JavaScript Project Core Dependencies

```json
{
  "devDependencies": {
    "eslint": "^8.56.0",
    "prettier": "^3.1.0"
  }
}
```

Install with:
```bash
npm install --save-dev eslint prettier
```

**Why these are required (JavaScript):**
- `eslint` - Linting (health check requirement)
- `prettier` - Formatting (health check requirement)

### TypeScript Project Core Dependencies

```json
{
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/node": "^20.0.0",
    "eslint": "^8.56.0",
    "prettier": "^3.1.0"
  }
}
```

Install with:
```bash
npm install --save-dev typescript @types/node eslint prettier
```

**Why these are required (TypeScript):**
- `typescript` - Type checking, builds, and codedocs_typescript.js
- `@types/node` - Node.js type definitions
- `eslint` - Linting (health check requirement)
- `prettier` - Formatting (health check requirement)

### Optional Dependencies (Graceful Degradation)

These packages enable additional WSD features. When missing, the health check **gracefully skips** these checks rather than failing - they appear with "⏭️ SKIPPED" status:

**For ESLint TypeScript Support:**
```json
{
  "devDependencies": {
    "@typescript-eslint/parser": "^6.0.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0"
  }
}
```

**For Security Scanning (health check skips if missing):**
```json
{
  "devDependencies": {
    "eslint-plugin-security": "^2.0.0"
  }
}
```

**For TypeDoc Validation (health check skips if missing):**
```json
{
  "devDependencies": {
    "typedoc": "^0.25.0"
  }
}
```

**For TypeScript API Documentation (`codedocs_typedoc.js`):**

This package is **required** if you want to use the TypeDoc HTML documentation generation script.

```json
{
  "devDependencies": {
    "typedoc": "^0.25.0"
  }
}
```

**Note:** TypeDoc generates HTML by default - no plugins are required. This matches the pattern used by pdoc (Python) and JSDoc (JavaScript).

**For JavaScript API Documentation (`codedocs_jsdoc.js`):**

These packages are **required** if you want to use the JSDoc documentation generation script.

```json
{
  "devDependencies": {
    "jsdoc": "^4.0.0"
  }
}
```

**For JavaScript Code Mapping (`codedocs_javascript.js`):**

This package is **required** if you want to use the JavaScript code mapper script.

```json
{
  "devDependencies": {
    "@babel/parser": "^7.23.0"
  }
}
```

**For Testing:**
```json
{
  "devDependencies": {
    "jest": "^29.7.0",
    "@types/jest": "^29.5.0",
    "ts-jest": "^29.1.0"
  }
}
```

**For Build Tools:**
```json
{
  "devDependencies": {
    "vite": "^5.0.0"
  }
}
```

### Complete Recommended Setup

For a fully-featured WSD TypeScript installation:

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
  eslint-plugin-security
```

---

## Script Customization Examples

### Using Vitest Instead of Jest

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage --coverage.reportsDirectory=dev/reports/coverage-node"
  },
  "devDependencies": {
    "vitest": "^1.0.0",
    "@vitest/coverage-v8": "^1.0.0"
  }
}
```

### Using Vite for Builds

```json
{
  "scripts": {
    "build": "vite build",
    "dev": "vite dev",
    "serve": "vite preview"
  },
  "devDependencies": {
    "vite": "^5.0.0"
  }
}
```

### Using esbuild for Fast Builds

```json
{
  "scripts": {
    "build": "esbuild src/index.ts --bundle --outdir=dist",
    "watch": "esbuild src/index.ts --bundle --outdir=dist --watch"
  },
  "devDependencies": {
    "esbuild": "^0.19.0"
  }
}
```

### Using Biome Instead of ESLint/Prettier

```json
{
  "scripts": {
    "lint": "biome check .",
    "lint:fix": "biome check --apply .",
    "format": "biome format --write .",
    "format:check": "biome format ."
  },
  "devDependencies": {
    "@biomejs/biome": "^1.4.0"
  }
}
```

---

## Complete Example

Here's a fully-configured package.json for a WSD TypeScript project:

```json
{
  "name": "my-typescript-project",
  "version": "1.0.0",
  "description": "TypeScript project with WSD",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "lint": "eslint --ext .ts,.tsx,.js,.jsx src tests",
    "lint:fix": "eslint --ext .ts,.tsx,.js,.jsx src tests --fix",
    "lint:json": "eslint --ext .ts,.tsx,.js,.jsx src tests --format json",
    "lint:aggressive": "eslint --ext .ts,.tsx,.js,.jsx src tests --fix --max-warnings 0",
    "lint:security": "eslint --ext .ts,.tsx,.js,.jsx src tests --plugin security --format json",
    "format": "prettier --write \"src/**/*.{ts,tsx,js,jsx}\" \"tests/**/*.{ts,tsx,js,jsx}\"",
    "format:check": "prettier --check \"src/**/*.{ts,tsx,js,jsx}\" \"tests/**/*.{ts,tsx,js,jsx}\"",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage --coverageDirectory=dev/reports/coverage-node",
    "typecheck": "tsc --noEmit",
    "typedoc": "typedoc",
    "typedoc:validate": "typedoc --validation --treatWarningsAsErrors --emit none",
    "validate": "npm run lint && npm run typecheck && npm run format:check",
    "watch": "tsc --watch",
    "dev": "vite dev",
    "serve": "vite preview"
  },
  "devDependencies": {
    "@types/jest": "^29.5.0",
    "@types/node": "^20.0.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "eslint": "^8.56.0",
    "eslint-plugin-security": "^2.0.0",
    "jest": "^29.7.0",
    "prettier": "^3.1.0",
    "ts-jest": "^29.1.0",
    "typedoc": "^0.25.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0"
  }
}
```

---

## Dependency Summary

### TypeScript Projects

| Package                            | Purpose                     | Required    | WSD Feature                             |
| ---------------------------------- | --------------------------- | ----------- | --------------------------------------- |
| `typescript`                       | Type checking & compilation | **Yes**     | All TS commands, codedocs_typescript.js |
| `@types/node`                      | Node.js type definitions    | **Yes**     | TypeScript compilation                  |
| `eslint`                           | Linting                     | **Yes**     | `./wsd.py lint`, health check           |
| `prettier`                         | Code formatting             | **Yes**     | `./wsd.py format`, health check         |
| `@typescript-eslint/parser`        | ESLint TS support           | **Yes**     | ESLint for TypeScript                   |
| `@typescript-eslint/eslint-plugin` | ESLint TS rules             | Optional    | ESLint for TypeScript                   |
| `eslint-plugin-security`           | Security scanning           | Optional    | Health check (skips if missing)         |
| `typedoc`                          | HTML API doc generation     | Optional    | codedocs_typedoc.js (required for script) |
| `jest`                             | Testing framework           | Optional    | `./wsd.py test`                         |
| `@types/jest`                      | Jest type definitions       | Optional    | Jest with TypeScript                    |
| `ts-jest`                          | Jest TS transformer         | Optional    | Jest with TypeScript                    |
| `vite`                             | Build tool                  | Optional    | Build/dev scripts                       |

### JavaScript Projects

| Package                            | Purpose                     | Required    | WSD Feature                             |
| ---------------------------------- | --------------------------- | ----------- | --------------------------------------- |
| `eslint`                           | Linting                     | **Yes**     | `./wsd.py lint`, health check           |
| `prettier`                         | Code formatting             | **Yes**     | `./wsd.py format`, health check         |
| `eslint-plugin-security`           | Security scanning           | Optional    | Health check (skips if missing)         |
| `jsdoc`                            | API doc generation          | Optional    | codedocs_jsdoc.js (required for script) |
| `@babel/parser`                    | JavaScript AST parsing      | Optional    | codedocs_javascript.js (required for script) |
| `jest`                             | Testing framework           | Optional    | `./wsd.py test`                         |
| `vite`                             | Build tool                  | Optional    | Build/dev scripts                       |

**Note on "Optional" documentation dependencies:** While these packages are listed as "Optional" for the health check (which skips documentation validation if they're missing), they are **required** if you want to use the corresponding codedocs scripts. The scripts will fail with a clear error message if the dependencies are not installed.

---

*See `Node-Project-Guide.md` for complete setup instructions and troubleshooting.*
