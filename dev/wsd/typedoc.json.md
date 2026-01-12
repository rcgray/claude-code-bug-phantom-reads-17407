# Sample typedoc.json for WSD TypeScript Projects

> **TypeScript projects only**: TypeDoc generates API documentation from TypeScript source code. JavaScript projects should use JSDoc-based tools instead.

This file documents the TypeDoc configuration used by WSD's `codedocs_typedoc.js` script to generate HTML API documentation. Copy this configuration into your project's `typedoc.json` or `scripts/typedoc.json`.

For complete setup instructions, see `Node-Project-Guide.md`.

---

## Purpose

This TypeDoc configuration is designed for generating **native HTML API documentation**. The `codedocs_typedoc.js` script uses this configuration to generate comprehensive multi-file HTML documentation in `dev/reports/typedoc-api-docs/` with navigation, search, and hierarchical organization for human developers.

---

## WSD Default Configuration

This is the configuration WSD provides in `scripts/typedoc.json`:

```json
{
  "out": "./dev/reports/typedoc-api-docs/",
  "readme": "none",
  "cleanOutputDir": true,
  "excludePrivate": true,
  "excludeExternals": true,
  "entryPointStrategy": "expand",
  "categorizeByGroup": true
}
```

**Key Configuration Points:**
- `out`: Output location for multi-file HTML documentation
- `cleanOutputDir`: TypeDoc removes stale files automatically before generation
- `excludePrivate`: Focus documentation on public API only
- `excludeExternals`: Don't document external dependencies
- `entryPointStrategy`: "expand" auto-discovers all exported modules
- `categorizeByGroup`: Group members by @group tags in documentation
- **No plugin needed**: TypeDoc generates HTML by default

---

## Configuration Options Explained

### Output Configuration

| Option          | Value                                    | Purpose                                        |
| --------------- | ---------------------------------------- | ---------------------------------------------- |
| `out`           | `"./dev/reports/typedoc-api-docs/"`      | Output directory for HTML files                |
| `cleanOutputDir`| `true`                                   | Remove stale files before regeneration         |

### Content Control

| Option                 | Value    | Purpose                                 |
| ---------------------- | -------- | --------------------------------------- |
| `readme`               | `"none"` | Don't include README in docs (API only) |
| `excludePrivate`       | `true`   | Exclude private members (focus on public API) |
| `excludeExternals`     | `true`   | Exclude external dependencies from docs |
| `categorizeByGroup`    | `true`   | Group members by @group tags            |

### Output Format

TypeDoc generates HTML by default - no plugins are required. The native HTML output includes:
- Interactive navigation sidebar
- Built-in search functionality
- Responsive design
- Syntax-highlighted code examples
- Cross-referenced type links

**Note:** WSD uses TypeDoc's native HTML output to match the pattern used by pdoc (Python) and JSDoc (JavaScript). All three ecosystem tools generate HTML for human consumption.

### Entry Point Strategy

```json
{
  "entryPointStrategy": "expand"
}
```

Options:
- `"expand"` - Document all exported modules (recommended for libraries)
- `"resolve"` - Use explicit entry points from package.json
- `"packages"` - For monorepos

---

## Customization Examples

### Specify Explicit Entry Points

Instead of auto-discovering all modules:

```json
{
  "entryPoints": ["./src/index.ts"],
  "entryPointStrategy": "resolve"
}
```

### Include Private Members

For internal documentation:

```json
{
  "visibilityFilters": {
    "private": true
  }
}
```

### Change Output Location

If you want TypeDoc output in a different location:

```json
{
  "out": "./docs/api/"
}
```

**Note:** If you change the output location from the default `dev/reports/typedoc-api-docs/`, you'll need to update the `codedocs_typedoc.js` script's OUTPUT_DIR constant to match, or TypeDoc will generate to your custom location but the script may report the wrong path in success messages.

### Custom Categorization

Use @group tags in TSDoc comments:

```typescript
/**
 * @group Utilities
 */
export function formatDate(date: Date): string {
  // ...
}

/**
 * @group Utilities
 */
export function parseDate(str: string): Date {
  // ...
}
```

With `categorizeByGroup: true`, these will be grouped together in the documentation.

### Include README in Documentation

```json
{
  "readme": "./README.md",
  "mergeReadme": true
}
```

---

## Required Dependencies

For `codedocs_typedoc.js` to work, install:

```bash
npm install --save-dev typedoc
```

That's it! TypeDoc generates HTML by default without requiring any plugins.

See `package.json.md` for complete dependency documentation.

---

## Usage

The `codedocs_typedoc.js` script reads this configuration automatically:

```bash
node scripts/codedocs_typedoc.js
```

Or via the unified docs script:

```bash
python scripts/update_docs.py --full
```

This will:
1. Detect project language (skip if JavaScript-only)
2. Run TypeDoc using this configuration
3. Generate multi-file HTML in `dev/reports/typedoc-api-docs/`
4. TypeDoc's `cleanOutputDir` removes stale files automatically

**Viewing the Documentation:**

Open `dev/reports/typedoc-api-docs/index.html` in your browser, or serve it locally:

```bash
python -m http.server -d dev/reports/typedoc-api-docs
# Then open http://localhost:8000 in your browser
```

---

## Complete Example

Here's a complete typedoc.json for a WSD TypeScript project:

```json
{
  "out": "./dev/reports/typedoc-api-docs/",
  "readme": "none",
  "cleanOutputDir": true,
  "excludePrivate": true,
  "excludeExternals": true,
  "entryPointStrategy": "expand",
  "categorizeByGroup": true
}
```

**Note:** This configuration uses TypeDoc's native HTML output. No plugins are required.

---

## Troubleshooting

### Empty Documentation Output

**Symptom:** Generated documentation has no content

**Solution:** Verify your source files have TSDoc comments:
```typescript
/**
 * This is a documented function.
 * @param name - The name parameter
 * @returns The greeting string
 */
export function greet(name: string): string {
  return `Hello, ${name}!`;
}
```

### Wrong Entry Points

**Symptom:** Documentation missing expected modules

**Solution:** Explicitly set entry points:
```json
{
  "entryPoints": ["./src/index.ts", "./src/utils.ts"]
}
```

---

*See `Node-Project-Guide.md` for complete setup instructions and `package.json.md` for required dependencies.*
