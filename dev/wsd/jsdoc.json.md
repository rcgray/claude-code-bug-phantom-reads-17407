# Sample jsdoc.json for WSD JavaScript Projects

> **JavaScript projects only**: JSDoc generates API documentation from JavaScript source code. TypeScript projects should use TypeDoc instead.

This file documents the JSDoc configuration used by WSD's `codedocs_jsdoc.js` script to generate HTML API documentation. Copy this configuration into your project's `jsdoc.json` file in the project root.

For complete setup instructions, see `Node-Project-Guide.md`.

---

## Purpose

This JSDoc configuration is designed for generating **native HTML API documentation**. The `codedocs_jsdoc.js` script validates that a `jsdoc` script is configured in `package.json`, then invokes it via your package manager to generate comprehensive multi-file HTML documentation in `dev/reports/jsdoc-api-docs/` with navigation, search, and hierarchical organization for human developers.

---

## WSD Default Configuration

This is the recommended JSDoc configuration for WSD projects:

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

**Key Configuration Points:**
- `source.include`: Directories containing source files to document
- `source.exclude`: Directories to skip (dependencies, build output)
- `opts.destination`: Output location for multi-file HTML documentation
- `opts.recurse`: Process subdirectories recursively
- `plugins`: Enable markdown support in JSDoc comments
- `templates`: Configure output formatting options

---

## Configuration Options Explained

### Source Configuration

| Option           | Value                      | Purpose                                    |
| ---------------- | -------------------------- | ------------------------------------------ |
| `source.include` | `["src"]`                  | Directories to scan for JavaScript files   |
| `source.exclude` | `["node_modules", "dist"]` | Directories to skip during scanning        |

### Output Configuration

| Option            | Value                        | Purpose                               |
| ----------------- | ---------------------------- | ------------------------------------- |
| `opts.destination`| `"dev/reports/jsdoc-api-docs"` | Output directory for HTML files      |
| `opts.recurse`    | `true`                       | Process subdirectories recursively    |

### Plugin Configuration

| Option    | Value                   | Purpose                                |
| --------- | ----------------------- | -------------------------------------- |
| `plugins` | `["plugins/markdown"]`  | Enable markdown parsing in JSDoc comments |

The `plugins/markdown` plugin is included with JSDoc and allows you to use markdown formatting in your documentation comments.

### Template Configuration

| Option                    | Value  | Purpose                                    |
| ------------------------- | ------ | ------------------------------------------ |
| `templates.cleverLinks`   | `true` | Auto-link type names in documentation      |
| `templates.monospaceLinks`| `true` | Render links in monospace font             |

---

## Customization Examples

### Specify Multiple Source Directories

For projects with multiple source directories:

```json
{
  "source": {
    "include": ["src", "lib", "utils"],
    "exclude": ["node_modules", "dist", "build"]
  }
}
```

### Include README in Documentation

To include your README as the documentation home page:

```json
{
  "source": {
    "include": ["src"],
    "includePattern": ".+\\.js$"
  },
  "opts": {
    "readme": "./README.md"
  }
}
```

### Change Output Location

If you want JSDoc output in a different location:

```json
{
  "opts": {
    "destination": "./docs/api/"
  }
}
```

**Note:** If you change the output location from the default `dev/reports/jsdoc-api-docs/`, be aware that the `codedocs_jsdoc.js` script passes directories as arguments to JSDoc. The script's success message will reference the default path.

### Custom File Patterns

To include only specific file patterns:

```json
{
  "source": {
    "include": ["src"],
    "includePattern": ".+\\.js$",
    "excludePattern": "(^|\\/|\\\\)_"
  }
}
```

This configuration:
- Includes only `.js` files
- Excludes files and directories starting with underscore

### Add Additional Plugins

JSDoc supports various plugins for extended functionality:

```json
{
  "plugins": [
    "plugins/markdown",
    "plugins/summarize"
  ]
}
```

Common plugins:
- `plugins/markdown` - Parse markdown in JSDoc comments (recommended)
- `plugins/summarize` - Auto-generate summary from first sentence

---

## Required Dependencies

For `codedocs_jsdoc.js` to work, install JSDoc and configure the script:

**1. Install JSDoc:**

```bash
npm install --save-dev jsdoc
# or: pnpm add -D jsdoc
# or: yarn add --dev jsdoc
# or: bun add -d jsdoc
```

**2. Add the jsdoc script to package.json:**

```json
{
  "scripts": {
    "jsdoc": "jsdoc -c jsdoc.json -d dev/reports/jsdoc-api-docs -r"
  }
}
```

The `-c jsdoc.json` flag tells JSDoc to use your configuration file. The `-d` and `-r` flags can be overridden by the configuration file.

See `package.json.md` for complete dependency documentation.

---

## Usage

The `codedocs_jsdoc.js` script validates that the `jsdoc` script exists in package.json, then runs it:

```bash
node scripts/codedocs_jsdoc.js
```

Or via the unified docs script:

```bash
python scripts/update_docs.py --full
```

This will:
1. Detect project language (skip if TypeScript detected)
2. Validate that `jsdoc` script is configured in package.json
3. Run JSDoc using your package manager (`npm run jsdoc`, etc.)
4. Generate multi-file HTML in `dev/reports/jsdoc-api-docs/`

**Viewing the Documentation:**

Open `dev/reports/jsdoc-api-docs/index.html` in your browser, or serve it locally:

```bash
python -m http.server -d dev/reports/jsdoc-api-docs
# Then open http://localhost:8000 in your browser
```

---

## Complete Example

Here's a complete jsdoc.json for a WSD JavaScript project:

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

**Note:** This configuration uses JSDoc's native HTML output. The `plugins/markdown` plugin is included with JSDoc and requires no additional installation.

---

## Troubleshooting

### "jsdoc" script not found in package.json

**Symptom:** `codedocs_jsdoc.js` fails with error about missing script

**Solution:** Add the jsdoc script to your package.json:
```json
{
  "scripts": {
    "jsdoc": "jsdoc -c jsdoc.json -d dev/reports/jsdoc-api-docs -r"
  }
}
```

And install JSDoc:
```bash
npm install --save-dev jsdoc
```

### Empty Documentation Output

**Symptom:** Generated documentation has no content

**Solution:** Verify your source files have JSDoc comments:
```javascript
/**
 * This is a documented function.
 * @param {string} name - The name parameter
 * @returns {string} The greeting string
 */
function greet(name) {
  return `Hello, ${name}!`;
}
```

### Wrong Source Directories

**Symptom:** Documentation missing expected modules

**Solution:** Verify `source.include` in jsdoc.json matches your project structure:
```json
{
  "source": {
    "include": ["./src", "./lib"]
  }
}
```

### Configuration File Not Found

**Symptom:** JSDoc runs but ignores configuration

**Solution:** Ensure jsdoc.json is in your project root and the script references it:
```json
{
  "scripts": {
    "jsdoc": "jsdoc -c jsdoc.json -d dev/reports/jsdoc-api-docs -r"
  }
}
```

---

*See `Node-Project-Guide.md` for complete setup instructions and `package.json.md` for required dependencies.*
