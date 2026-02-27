# ESLint Configuration for WSD JavaScript/TypeScript Projects

This file documents the ESLint configuration required for WSD integration in JavaScript and TypeScript projects. ESLint is used by the WSD health check and task runner commands for code quality validation.

For complete setup instructions, see `Node-Project-Guide.md`.

---

## Purpose

ESLint provides static code analysis to identify problematic patterns and enforce coding standards. WSD uses ESLint through the following commands:

| WSD Command | npm Script | Description |
|-------------|-----------|-------------|
| `./wsd.py lint` | `lint` | Check for lint errors |
| `./wsd.py lint:fix` | `lint:fix` | Auto-fix lint errors |
| `./wsd.py health` | Multiple | Runs lint as part of health check |

The ESLint configuration differs between TypeScript and JavaScript projects, primarily in parser settings and type-aware rules.

---

## Configuration Format

ESLint uses the **flat config** format (`eslint.config.js`). Flat config exports an array of configuration objects, each applying rules to specific file patterns.

Key characteristics of flat config:

- Configuration is an exported array of objects (CommonJS `module.exports` or ESM `export default`)
- Plugins are imported as JavaScript objects rather than referenced by string name
- Environment globals (Node.js, browser, Jest) are provided via the `globals` npm package
- File-specific overrides are separate objects in the array with a `files` property
- Ignored paths are specified via an `ignores` property in a standalone config object

---

## Minimum Configuration

### JavaScript Projects

A minimal `eslint.config.js` for JavaScript projects:

```javascript
const js = require("@eslint/js");
const globals = require("globals");

module.exports = [
  { ignores: ["node_modules/", "dist/", "*.min.js"] },

  js.configs.recommended,

  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        ...globals.node,
      },
    },
    rules: {
      "no-console": "warn",
      "prefer-const": "error",
    },
  },
];
```

### TypeScript Projects

A minimal `eslint.config.js` for TypeScript projects:

```javascript
const js = require("@eslint/js");
const tseslint = require("typescript-eslint");
const globals = require("globals");

module.exports = [
  { ignores: ["node_modules/", "dist/", "*.min.js"] },

  js.configs.recommended,
  ...tseslint.configs.recommended,

  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        ...globals.node,
      },
      parserOptions: {
        project: "./tsconfig.json",
      },
    },
    rules: {
      "@typescript-eslint/explicit-function-return-type": "warn",
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      "@typescript-eslint/no-explicit-any": "warn",
      "no-console": "warn",
      "prefer-const": "error",
    },
  },
];
```

---

## TypeScript vs JavaScript Configuration

The key differences between TypeScript and JavaScript ESLint configurations are summarized below:

### Parser Configuration

| Setting | TypeScript | JavaScript |
|---------|------------|------------|
| Plugin | `typescript-eslint` | Not needed |
| `parserOptions.project` | `"./tsconfig.json"` | Not used |
| Type-aware rules | Available | Not available |

### The `project` Field

The `project` field in `languageOptions.parserOptions` is the critical difference between TypeScript and JavaScript configurations:

**TypeScript Projects:**
```javascript
{
  languageOptions: {
    parserOptions: {
      project: "./tsconfig.json",  // Enables type-aware rules
    },
  },
}
```

The `project` field enables TypeScript type-aware linting rules that can catch errors based on type information (e.g., `@typescript-eslint/no-floating-promises`). This requires:
- A valid `tsconfig.json` in your project
- TypeScript files (`.ts`) in the directories being linted

**JavaScript Projects:**
```javascript
{
  languageOptions: {
    // NO 'project' field - type-aware rules disabled
    ecmaVersion: 2022,
    sourceType: "module",
  },
}
```

JavaScript projects must NOT include the `project` field because there are no TypeScript files to provide type information.

---

## Mixed TypeScript/JavaScript Projects

Projects containing both `.ts` and `.js` files use separate configuration objects for each file type. The flat config array naturally supports this by applying different rules to different file patterns:

```javascript
const js = require("@eslint/js");
const tseslint = require("typescript-eslint");
const globals = require("globals");

module.exports = [
  { ignores: ["node_modules/", "dist/", "*.min.js"] },

  js.configs.recommended,
  ...tseslint.configs.recommended,

  // TypeScript files - with type-aware rules
  {
    files: ["**/*.ts", "**/*.tsx"],
    languageOptions: {
      parserOptions: {
        project: "./tsconfig.json",
      },
    },
    rules: {
      "@typescript-eslint/explicit-function-return-type": "warn",
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
    },
  },

  // JavaScript files - no type-aware rules
  {
    files: ["**/*.js", "**/*.jsx"],
    rules: {
      "@typescript-eslint/explicit-function-return-type": "off",
    },
  },

  // Test files
  {
    files: ["**/*.test.ts", "**/*.spec.ts", "**/*.test.js", "**/*.spec.js"],
    languageOptions: {
      globals: {
        ...globals.jest,
      },
    },
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
    },
  },
];
```

**Key Points:**
- The `files` property on each config object controls which files the rules apply to
- TypeScript files get `parserOptions.project` for type-aware rules
- JavaScript files have TypeScript-specific rules disabled
- Test files get relaxed rules and Jest globals

---

## JSDoc Validation

WSD supports JSDoc documentation validation via `eslint-plugin-jsdoc`. The plugin provides flat config presets:

```javascript
const jsdoc = require("eslint-plugin-jsdoc");

module.exports = [
  // Use the flat config preset
  jsdoc.configs["flat/recommended"],

  {
    rules: {
      "jsdoc/require-jsdoc": ["warn", {
        require: {
          FunctionDeclaration: true,
          MethodDefinition: true,
          ClassDeclaration: true,
        },
      }],
      "jsdoc/require-description": "warn",
      "jsdoc/require-param-description": "warn",
      "jsdoc/require-returns-description": "warn",
      "jsdoc/check-param-names": "error",
      "jsdoc/check-tag-names": ["error", { definedTags: ["remarks"] }],
      "jsdoc/check-types": "error",
    },
  },
];
```

---

## Security Scanning

WSD health checks can include security scanning via `eslint-plugin-security`. In flat config, plugins are imported as objects:

```javascript
const security = require("eslint-plugin-security");

module.exports = [
  // Option 1: Use the recommended flat config preset
  security.configs.recommended,

  // Option 2: Configure rules explicitly
  {
    plugins: {
      security,
    },
    rules: {
      "security/detect-unsafe-regex": "warn",
      "security/detect-non-literal-regexp": "warn",
      "security/detect-non-literal-require": "warn",
      "security/detect-non-literal-fs-filename": "warn",
      "security/detect-eval-with-expression": "warn",
      "security/detect-pseudoRandomBytes": "warn",
      "security/detect-possible-timing-attacks": "warn",
      "security/detect-no-csrf-before-method-override": "warn",
      "security/detect-buffer-noassert": "warn",
      "security/detect-child-process": "warn",
      "security/detect-disable-mustache-escape": "warn",
      "security/detect-object-injection": "warn",
      "security/detect-new-buffer": "warn",
      "security/detect-bidi-characters": "warn",
    },
  },
];
```

---

## TSDoc Validation

For TypeScript projects, WSD can validate TSDoc comment syntax using `eslint-plugin-tsdoc`:

```javascript
const tsdoc = require("eslint-plugin-tsdoc");

module.exports = [
  {
    plugins: {
      tsdoc,
    },
    rules: {
      "tsdoc/syntax": "warn",
    },
  },
];
```

This requires the `eslint-plugin-tsdoc` package to be installed.

---

## Environment Globals

The flat config format uses the `globals` npm package to provide environment-specific global variable definitions.

```javascript
const globals = require("globals");

module.exports = [
  {
    languageOptions: {
      globals: {
        ...globals.node,      // Node.js globals (require, process, __dirname, etc.)
      },
    },
  },

  // Test files with Jest globals
  {
    files: ["**/*.test.js", "**/*.spec.js"],
    languageOptions: {
      globals: {
        ...globals.jest,      // Jest globals (describe, it, expect, etc.)
      },
    },
  },
];
```

Common globals sets: `globals.node`, `globals.browser`, `globals.jest`, `globals.es2022`.

---

## Common Issues and Troubleshooting

### Type-Aware Rules Fail on JavaScript Files

**Symptom:**
```
Parsing error: "parserOptions.project" has been set for @typescript-eslint/parser.
```

**Cause:** The `project` option is set but ESLint is trying to lint JavaScript files that aren't included in `tsconfig.json`.

**Solution:** Use a separate config object for JavaScript files without the `project` option:

```javascript
{
  files: ["**/*.js"],
  languageOptions: {
    parserOptions: {
      project: null,  // Disable type-aware rules for JS
    },
  },
},
```

### ESLint Not Finding TypeScript Parser

**Symptom:**
```
Error: Failed to load parser '@typescript-eslint/parser'
```

**Cause:** The `typescript-eslint` package is not installed.

**Solution:** Install the required packages:

```bash
npm install --save-dev typescript-eslint
```

### ESLint Fails on Files Outside tsconfig Include

**Symptom:**
```
Parsing error: ESLint was configured to run on `<file>` but that file is not included in your tsconfig.json
```

**Cause:** ESLint is trying to lint a file that isn't included in `tsconfig.json`, but type-aware rules require all linted files to be in the TypeScript project.

**Solutions:**

1. **Add the file to tsconfig.json:**
   ```json
   {
     "include": ["src/**/*", "tests/**/*", "scripts/**/*"]
   }
   ```

2. **Or exclude the file from ESLint:**
   ```javascript
   { ignores: ["scripts/legacy/**"] },
   ```

3. **Or use a config object to disable type-aware rules for that file:**
   ```javascript
   {
     files: ["scripts/legacy/**/*.ts"],
     languageOptions: {
       parserOptions: {
         project: null,
       },
     },
   },
   ```

### Health Check Shows "Linting SKIPPED"

**Symptom:** The WSD health check shows linting as skipped.

**Cause:** The `lint` script is not defined in `package.json`.

**Solution:** Add the required lint script to your `package.json`:

```json
{
  "scripts": {
    "lint": "eslint src tests"
  }
}
```

See `package.json.md` for the complete list of required scripts.

---

## Notable ESLint Behaviors

### Catch Variable Handling

The `no-unused-vars` rule flags unused catch block variables by default. To allow unused catch variables prefixed with underscore, configure:

```javascript
"no-unused-vars": ["error", {
  argsIgnorePattern: "^_",
  caughtErrorsIgnorePattern: "^_",
}],
```

This allows patterns like `catch (_error) { ... }` without triggering lint errors.

### Rules in eslint:recommended

The `eslint:recommended` preset (via `@eslint/js`) includes rules for common error detection:

- `no-constant-binary-expression` - Catches always-truthy/falsy binary expressions
- `no-empty-static-block` - Flags empty static blocks in classes
- `no-new-native-nonconstructor` - Prevents `new` on non-constructor natives
- `no-unused-private-class-members` - Catches unused private class fields

These rules are beneficial for catching subtle bugs that might otherwise go unnoticed.

---

## Complete Example

Here's a complete `eslint.config.js` for a WSD TypeScript project with JSDoc validation, security scanning, and TSDoc validation:

```javascript
const js = require("@eslint/js");
const tseslint = require("typescript-eslint");
const jsdoc = require("eslint-plugin-jsdoc");
const security = require("eslint-plugin-security");
const tsdoc = require("eslint-plugin-tsdoc");
const globals = require("globals");

module.exports = [
  // Global ignores
  { ignores: ["node_modules/", "dist/", "*.min.js", "docs/reports/"] },

  // Base recommended configs
  js.configs.recommended,
  ...tseslint.configs.recommended,
  jsdoc.configs["flat/recommended"],
  security.configs.recommended,

  // Main configuration
  {
    plugins: {
      tsdoc,
    },
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        ...globals.node,
      },
      parserOptions: {
        project: "./tsconfig.json",
      },
    },
    rules: {
      // TSDoc validation
      "tsdoc/syntax": "warn",

      // TypeScript-specific rules
      "@typescript-eslint/explicit-function-return-type": "warn",
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      "@typescript-eslint/no-explicit-any": "warn",

      // JSDoc validation
      "jsdoc/require-jsdoc": ["warn", {
        require: {
          FunctionDeclaration: true,
          MethodDefinition: true,
          ClassDeclaration: true,
        },
      }],

      // General code quality
      "no-console": "warn",
      "prefer-const": "error",

      // Security rules (explicit for granular control)
      "security/detect-unsafe-regex": "warn",
      "security/detect-non-literal-regexp": "warn",
      "security/detect-non-literal-require": "warn",
      "security/detect-non-literal-fs-filename": "warn",
      "security/detect-eval-with-expression": "warn",
      "security/detect-pseudoRandomBytes": "warn",
      "security/detect-possible-timing-attacks": "warn",
      "security/detect-no-csrf-before-method-override": "warn",
      "security/detect-buffer-noassert": "warn",
      "security/detect-child-process": "warn",
      "security/detect-disable-mustache-escape": "warn",
      "security/detect-object-injection": "warn",
      "security/detect-new-buffer": "warn",
      "security/detect-bidi-characters": "warn",
    },
  },

  // JavaScript files - no type-aware rules
  {
    files: ["**/*.js"],
    languageOptions: {
      parserOptions: {
        project: null,
      },
    },
    rules: {
      "@typescript-eslint/explicit-function-return-type": "off",
    },
  },

  // Test files
  {
    files: ["**/*.test.ts", "**/*.spec.ts", "**/*.test.js", "**/*.spec.js"],
    languageOptions: {
      globals: {
        ...globals.jest,
      },
    },
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
    },
  },
];
```

---

## Required Packages

Install the following packages for full ESLint support:

### Core (Required)

```bash
npm install --save-dev eslint globals
```

### TypeScript Support (Required for TypeScript projects)

```bash
npm install --save-dev typescript-eslint
```

### Optional Enhancements

```bash
# JSDoc validation
npm install --save-dev eslint-plugin-jsdoc

# Security scanning
npm install --save-dev eslint-plugin-security

# TSDoc validation (TypeScript only)
npm install --save-dev eslint-plugin-tsdoc
```

See `package.json.md` for the complete dependency reference.

---

*See `Node-Project-Guide.md` for complete setup instructions and `package.json.md` for required scripts.*
