# Sample .eslintrc for WSD JavaScript/TypeScript Projects

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

## Minimum Configuration

### JavaScript Projects

A minimal `.eslintrc.js` for JavaScript projects:

```javascript
module.exports = {
  root: true,
  extends: ['eslint:recommended'],
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
  },
  env: {
    node: true,
    es2020: true,
  },
  rules: {
    'no-console': 'warn',
    'prefer-const': 'error',
  },
  ignorePatterns: ['node_modules/', 'dist/', '*.min.js'],
};
```

### TypeScript Projects

A minimal `.eslintrc.js` for TypeScript projects:

```javascript
module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
  ],
  plugins: ['@typescript-eslint'],
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
    project: './tsconfig.json',
  },
  env: {
    node: true,
    es2020: true,
  },
  rules: {
    '@typescript-eslint/explicit-function-return-type': 'warn',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    '@typescript-eslint/no-explicit-any': 'warn',
    'no-console': 'warn',
    'prefer-const': 'error',
  },
  ignorePatterns: ['node_modules/', 'dist/', '*.min.js'],
};
```

---

## TypeScript vs JavaScript Configuration

The key differences between TypeScript and JavaScript ESLint configurations are summarized below:

### Parser Configuration

| Setting | TypeScript | JavaScript |
|---------|------------|------------|
| `parser` | `'@typescript-eslint/parser'` | Default (not specified) |
| `parserOptions.project` | `'./tsconfig.json'` | Not used |
| `plugins` | `['@typescript-eslint']` | Not needed |

### The `project` Field

The `project` field in `parserOptions` is the critical difference between TypeScript and JavaScript configurations:

**TypeScript Projects:**
```javascript
parserOptions: {
  project: './tsconfig.json',  // Enables type-aware rules
}
```

The `project` field enables TypeScript type-aware linting rules that can catch errors based on type information (e.g., `@typescript-eslint/no-floating-promises`). This requires:
- A valid `tsconfig.json` in your project
- TypeScript files (`.ts`) in the directories being linted

**JavaScript Projects:**
```javascript
parserOptions: {
  // NO 'project' field - type-aware rules disabled
  ecmaVersion: 2020,
  sourceType: 'module',
}
```

JavaScript projects must NOT include the `project` field because there are no TypeScript files to provide type information.

### Parser Flexibility

The `@typescript-eslint/parser` can parse both TypeScript AND JavaScript files. This allows mixed projects to use a single parser:

```javascript
module.exports = {
  parser: '@typescript-eslint/parser',
  // Works for both .ts and .js files
};
```

However, type-aware rules only work on TypeScript files.

---

## Mixed TypeScript/JavaScript Projects

Projects containing both `.ts` and `.js` files require special handling. Use the `overrides` feature to apply different rules to different file types:

```javascript
module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
  ],
  plugins: ['@typescript-eslint'],
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
    project: './tsconfig.json',
  },
  env: {
    node: true,
    es2020: true,
  },
  rules: {
    '@typescript-eslint/explicit-function-return-type': 'warn',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
  },
  ignorePatterns: ['node_modules/', 'dist/', '*.min.js'],
  overrides: [
    {
      // JavaScript files - disable type-aware features
      files: ['**/*.js'],
      parserOptions: {
        project: null,  // Disable type-aware rules for JS
      },
      rules: {
        '@typescript-eslint/explicit-function-return-type': 'off',
        '@typescript-eslint/no-var-requires': 'off',
      },
    },
    {
      // Test files
      files: ['**/*.test.ts', '**/*.spec.ts', '**/*.test.js', '**/*.spec.js'],
      env: {
        jest: true,
      },
      rules: {
        '@typescript-eslint/no-explicit-any': 'off',
      },
    },
  ],
};
```

**Key Points:**
- The main configuration targets TypeScript files with `project: './tsconfig.json'`
- The JavaScript override sets `project: null` to disable type-aware rules
- TypeScript-specific rules like `explicit-function-return-type` are disabled for JavaScript files
- Test files get relaxed rules appropriate for testing

---

## Security Scanning

WSD health checks include security scanning via `eslint-plugin-security`. There are two approaches to configuring security rules:

### Approach 1: Explicit Security Rules (Recommended)

Configure security rules explicitly to avoid potential issues with the recommended preset:

```javascript
module.exports = {
  plugins: ['security'],
  rules: {
    // Security rules
    'security/detect-unsafe-regex': 'warn',
    'security/detect-non-literal-regexp': 'warn',
    'security/detect-non-literal-require': 'warn',
    'security/detect-non-literal-fs-filename': 'warn',
    'security/detect-eval-with-expression': 'warn',
    'security/detect-pseudoRandomBytes': 'warn',
    'security/detect-possible-timing-attacks': 'warn',
    'security/detect-no-csrf-before-method-override': 'warn',
    'security/detect-buffer-noassert': 'warn',
    'security/detect-child-process': 'warn',
    'security/detect-disable-mustache-escape': 'warn',
    'security/detect-object-injection': 'warn',
    'security/detect-new-buffer': 'warn',
    'security/detect-bidi-characters': 'warn',
  },
};
```

### Approach 2: Using the Recommended Preset

```javascript
module.exports = {
  extends: [
    'eslint:recommended',
    'plugin:security/recommended',
  ],
  plugins: ['security'],
};
```

**Note:** The `plugin:security/recommended` preset may cause circular reference errors in some versions of `eslint-plugin-security`. If you encounter this issue, use Approach 1 with explicit rules instead.

---

## TSDoc Validation

For TypeScript projects, WSD can validate TSDoc comment syntax using `eslint-plugin-tsdoc`:

```javascript
module.exports = {
  plugins: ['eslint-plugin-tsdoc'],
  rules: {
    'tsdoc/syntax': 'warn',
  },
};
```

This requires the `eslint-plugin-tsdoc` package to be installed.

---

## Common Issues and Troubleshooting

### Circular Reference Error with Security Plugin

**Symptom:**
```
Error: circular reference in plugin:security/recommended
```

**Cause:** Some versions of `eslint-plugin-security` have an issue with the recommended preset configuration causing circular references.

**Solution:** Instead of using `plugin:security/recommended` in the `extends` array, configure security rules explicitly:

```javascript
// Instead of:
extends: ['plugin:security/recommended'],

// Use:
plugins: ['security'],
rules: {
  'security/detect-unsafe-regex': 'warn',
  'security/detect-non-literal-regexp': 'warn',
  'security/detect-non-literal-require': 'warn',
  'security/detect-non-literal-fs-filename': 'warn',
  'security/detect-eval-with-expression': 'warn',
  'security/detect-pseudoRandomBytes': 'warn',
  'security/detect-possible-timing-attacks': 'warn',
  'security/detect-no-csrf-before-method-override': 'warn',
  'security/detect-buffer-noassert': 'warn',
  'security/detect-child-process': 'warn',
  'security/detect-disable-mustache-escape': 'warn',
  'security/detect-object-injection': 'warn',
  'security/detect-new-buffer': 'warn',
  'security/detect-bidi-characters': 'warn',
},
```

This provides the same security coverage without the circular reference issue.

### Type-Aware Rules Fail on JavaScript Files

**Symptom:**
```
Parsing error: "parserOptions.project" has been set for @typescript-eslint/parser.
```

**Cause:** The `project` option is set but ESLint is trying to lint JavaScript files that aren't included in `tsconfig.json`.

**Solution:** Use overrides to disable the `project` option for JavaScript files:

```javascript
overrides: [
  {
    files: ['**/*.js'],
    parserOptions: {
      project: null,
    },
  },
],
```

### ESLint Not Finding TypeScript Parser

**Symptom:**
```
Error: Failed to load parser '@typescript-eslint/parser'
```

**Cause:** The `@typescript-eslint/parser` package is not installed.

**Solution:** Install the required packages:

```bash
npm install --save-dev @typescript-eslint/parser @typescript-eslint/eslint-plugin
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
   ignorePatterns: ['scripts/legacy/**'],
   ```

3. **Or use an override to disable type-aware rules for that file:**
   ```javascript
   overrides: [
     {
       files: ['scripts/legacy/**/*.ts'],
       parserOptions: {
         project: null,
       },
     },
   ],
   ```

### Health Check Shows "Linting SKIPPED"

**Symptom:** The WSD health check shows linting as skipped.

**Cause:** The `lint` script is not defined in `package.json`.

**Solution:** Add the required lint script to your `package.json`:

```json
{
  "scripts": {
    "lint": "eslint --ext .ts,.tsx,.js,.jsx src tests"
  }
}
```

See `package.json.md` for the complete list of required scripts.

---

## Complete Example

Here's a complete `.eslintrc.js` for a WSD TypeScript project with security scanning and TSDoc validation:

```javascript
module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
  ],
  plugins: ['@typescript-eslint', 'security', 'eslint-plugin-tsdoc'],
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
    project: './tsconfig.json',
  },
  env: {
    node: true,
    es2020: true,
  },
  rules: {
    // TSDoc validation
    'tsdoc/syntax': 'warn',

    // TypeScript-specific rules
    '@typescript-eslint/explicit-function-return-type': 'warn',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    '@typescript-eslint/no-explicit-any': 'warn',

    // General code quality
    'no-console': 'warn',
    'prefer-const': 'error',

    // Security rules (explicit to avoid circular reference)
    'security/detect-unsafe-regex': 'warn',
    'security/detect-non-literal-regexp': 'warn',
    'security/detect-non-literal-require': 'warn',
    'security/detect-non-literal-fs-filename': 'warn',
    'security/detect-eval-with-expression': 'warn',
    'security/detect-pseudoRandomBytes': 'warn',
    'security/detect-possible-timing-attacks': 'warn',
    'security/detect-no-csrf-before-method-override': 'warn',
    'security/detect-buffer-noassert': 'warn',
    'security/detect-child-process': 'warn',
    'security/detect-disable-mustache-escape': 'warn',
    'security/detect-object-injection': 'warn',
    'security/detect-new-buffer': 'warn',
    'security/detect-bidi-characters': 'warn',
  },
  ignorePatterns: ['node_modules/', 'dist/', '*.min.js', 'docs/reports/'],
  overrides: [
    {
      // JavaScript files
      files: ['**/*.js'],
      parserOptions: {
        project: null,
      },
      rules: {
        '@typescript-eslint/explicit-function-return-type': 'off',
        '@typescript-eslint/no-var-requires': 'off',
      },
    },
    {
      // Test files
      files: ['**/*.test.ts', '**/*.spec.ts', '**/*.test.js', '**/*.spec.js'],
      env: {
        jest: true,
      },
      rules: {
        '@typescript-eslint/no-explicit-any': 'off',
      },
    },
  ],
};
```

---

## Required Packages

Install the following packages for full ESLint support:

### Core (Required)

```bash
npm install --save-dev eslint
```

### TypeScript Support (Required for TypeScript projects)

```bash
npm install --save-dev @typescript-eslint/parser @typescript-eslint/eslint-plugin
```

### Optional Enhancements

```bash
# Security scanning
npm install --save-dev eslint-plugin-security

# TSDoc validation (TypeScript only)
npm install --save-dev eslint-plugin-tsdoc
```

See `package.json.md` for the complete dependency reference.

---

*See `Node-Project-Guide.md` for complete setup instructions and `package.json.md` for required scripts.*
