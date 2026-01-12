# Sample .prettierrc for WSD JavaScript/TypeScript Projects

This file documents the Prettier configuration for WSD integration in JavaScript and TypeScript projects. Prettier is used by the WSD health check and task runner commands for code formatting validation.

For complete setup instructions, see `Node-Project-Guide.md`.

---

## Purpose

Prettier is an opinionated code formatter that enforces consistent style across your codebase. WSD uses Prettier through the following commands:

| WSD Command | npm Script | Description |
|-------------|-----------|-------------|
| `./wsd.py format` | `format` | Format code with auto-fix |
| `./wsd.py format:check` | `format:check` | Check formatting without modifying files |
| `./wsd.py health` | Multiple | Runs format check as part of health check |

Unlike linters that focus on code quality and potential bugs, Prettier focuses purely on formatting: indentation, line length, quotes, semicolons, and other stylistic concerns.

---

## Minimum Configuration

A minimal `.prettierrc` for WSD projects:

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

This configuration works for both JavaScript and TypeScript projects without modification.

---

## Configuration Options Explained

### Core Formatting Options

| Option | Default | Recommended | Description |
|--------|---------|-------------|-------------|
| `semi` | `true` | `true` | Add semicolons at the end of statements |
| `singleQuote` | `false` | `true` | Use single quotes instead of double quotes |
| `tabWidth` | `2` | `2` | Number of spaces per indentation level |
| `printWidth` | `80` | `100` | Maximum line length before wrapping |
| `trailingComma` | `"all"` | `"es5"` | Add trailing commas where valid in ES5 |

### Additional Options

| Option | Default | Recommended | Description |
|--------|---------|-------------|-------------|
| `bracketSpacing` | `true` | `true` | Print spaces between brackets in object literals |
| `arrowParens` | `"always"` | `"always"` | Include parentheses around single arrow function parameters |
| `endOfLine` | `"lf"` | `"lf"` | Line ending style (lf, crlf, cr, auto) |
| `useTabs` | `false` | `false` | Use tabs instead of spaces |
| `quoteProps` | `"as-needed"` | `"as-needed"` | Quote object properties only when required |

### WSD Development Configuration

The WSD Development project uses this configuration:

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "bracketSpacing": true,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

---

## TypeScript vs JavaScript Configuration

Unlike ESLint, Prettier configuration is **identical for TypeScript and JavaScript projects**. Prettier automatically detects file types and applies appropriate formatting rules without requiring parser configuration.

### Why No Parser Configuration?

Prettier uses file extensions to determine which parser to use:
- `.js`, `.jsx` files use the JavaScript parser
- `.ts`, `.tsx` files use the TypeScript parser
- `.json` files use the JSON parser
- `.md` files use the Markdown parser

This automatic detection means you don't need separate configurations for TypeScript vs JavaScript projects.

### Type-Aware Formatting

Unlike ESLint's `project` option that enables type-aware linting rules, Prettier does not use TypeScript type information for formatting decisions. All formatting is based purely on syntax, making Prettier configuration fully portable between project types.

---

## Prettier Ignore Patterns

Create a `.prettierignore` file to exclude files and directories from formatting:

```
# Build output
dist/

# Dependencies
node_modules/

# Minified files
*.min.js

# Generated documentation
docs/reports/

# Python artifacts (if mixed project)
__pycache__/
*.pyc
.venv/
*.egg-info/

# Coverage reports
htmlcov/
coverage/

# WSD artifacts
dev/workscopes/
dev/journal/archive/
```

### Ignore Pattern Behavior

- Patterns follow `.gitignore` syntax
- Directories should end with `/` for clarity
- Wildcards (`*`) match any characters except path separators
- Double wildcards (`**`) match any characters including path separators

### Common Exclusions

| Pattern | Purpose |
|---------|---------|
| `dist/` | Build output (generated, not source) |
| `node_modules/` | Dependencies (managed by npm) |
| `*.min.js` | Minified files (optimized, not human-readable) |
| `docs/reports/` | Generated documentation (tool output) |
| `coverage/` | Test coverage reports (generated) |

---

## Common Issues and Troubleshooting

### Health Check Fails on Formatting

**Symptom:** `./wsd.py health` fails on the formatting step

**Cause:** Files don't match Prettier's expected formatting

**Solution:** Run the format command to auto-fix:

```bash
./wsd.py format
```

Then re-run the health check:

```bash
./wsd.py health
```

### Prettier Conflicts with ESLint

**Symptom:** ESLint and Prettier disagree on formatting rules

**Cause:** Both tools have overlapping concerns (e.g., semicolons, quotes)

**Solution:** Use `eslint-config-prettier` to disable ESLint rules that conflict with Prettier:

```bash
npm install --save-dev eslint-config-prettier
```

Then add to your ESLint config:

```javascript
module.exports = {
  extends: [
    'eslint:recommended',
    'prettier'  // Must be last to override other configs
  ]
};
```

### Inconsistent Line Endings

**Symptom:** Files show as modified after formatting on different operating systems

**Cause:** Different default line endings on Windows vs Unix

**Solution:** Set explicit line ending in `.prettierrc`:

```json
{
  "endOfLine": "lf"
}
```

Also configure Git to handle line endings consistently:

```bash
git config core.autocrlf input  # On Unix/Mac
git config core.autocrlf true   # On Windows
```

### Format Script Missing

**Symptom:** Health check fails with "npm run format" error

**Cause:** The `format` script is not defined in `package.json`

**Solution:** Add the required scripts to your `package.json`:

```json
{
  "scripts": {
    "format": "prettier --write .",
    "format:check": "prettier --check ."
  }
}
```

See `package.json.md` for complete script documentation.

### Prettier Not Formatting Specific Files

**Symptom:** Some files aren't being formatted

**Causes:**
1. Files are in `.prettierignore`
2. Files are in `.gitignore` (Prettier respects this by default)
3. File extension isn't recognized

**Solutions:**

1. Check if the file is excluded in `.prettierignore`

2. Override gitignore behavior if needed:
   ```bash
   prettier --write . --ignore-path .prettierignore
   ```

3. For custom file extensions, specify the parser:
   ```json
   {
     "overrides": [
       {
         "files": "*.custom",
         "options": { "parser": "babel" }
       }
     ]
   }
   ```

### Large Files Slow to Format

**Symptom:** Formatting takes a long time

**Cause:** Very long files or complex code structures

**Solution:** Add slow-processing files to `.prettierignore` or split large files into smaller modules.

---

## Integration with Editors

### VS Code

Install the Prettier extension and add to settings:

```json
{
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnSave": true
}
```

### WebStorm/IntelliJ

1. Go to Settings > Languages & Frameworks > JavaScript > Prettier
2. Enable "On save" and "On 'Reformat Code' action"
3. Point to your node_modules Prettier installation

### Vim/Neovim

Use a plugin like `vim-prettier` or configure with LSP.

---

## Required Packages

### Core (Required)

```bash
npm install --save-dev prettier
```

### ESLint Integration (Recommended)

```bash
npm install --save-dev eslint-config-prettier
```

This package disables ESLint rules that would conflict with Prettier.

---

## Complete Example

Here's a complete `.prettierrc` for a WSD JavaScript/TypeScript project:

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "bracketSpacing": true,
  "arrowParens": "always",
  "endOfLine": "lf",
  "useTabs": false,
  "quoteProps": "as-needed"
}
```

And a corresponding `.prettierignore`:

```
# Build output
dist/

# Dependencies
node_modules/

# Minified files
*.min.js

# Generated documentation
docs/reports/

# Python artifacts
__pycache__/
*.pyc
.venv/
*.egg-info/

# Coverage reports
htmlcov/
coverage/

# WSD artifacts
dev/workscopes/
dev/journal/archive/
```

---

*See `Node-Project-Guide.md` for complete setup instructions and `package.json.md` for required scripts.*
