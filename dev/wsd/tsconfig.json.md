# Sample tsconfig.json for WSD TypeScript Projects

> **TypeScript projects only**: This file applies only to TypeScript projects. JavaScript projects do not need a `tsconfig.json` file and should skip this documentation.

This file documents the tsconfig.json configuration required for WSD integration in TypeScript projects. Copy the relevant sections into your project's tsconfig.json.

For complete setup instructions, see `Node-Project-Guide.md`.

---

## Purpose

The `tsconfig.json` file configures the TypeScript compiler and is used by:
- **TypeScript compiler (`tsc`)** - Type checking and builds
- **`codedocs_typescript.js`** - Code map generation (uses TS Compiler API)
- **WSD health check** - Runs `npm run build` which typically uses tsc
- **IDEs and editors** - TypeScript language support

---

## Minimum Configuration

A minimal tsconfig.json for WSD:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

---

## Compiler Options Explained

### Essential Options

| Option    | Purpose                       | Recommended Value                               |
| --------- | ----------------------------- | ----------------------------------------------- |
| `target`  | JavaScript version output     | `"ES2022"` or higher                            |
| `module`  | Module system                 | `"commonjs"` (Node.js) or `"esnext"` (bundlers) |
| `strict`  | Enable all strict type checks | `true` (always)                                 |
| `outDir`  | Build output directory        | `"./dist"`                                      |
| `rootDir` | Source root directory         | `"./src"`                                       |

### WSD-Specific Requirements

**For `codedocs_typescript.js` to work:**
- `include` must specify source directories (e.g., `["src/**/*"]`)
- The script respects `exclude` patterns automatically
- Declaration files (`.d.ts`) are automatically excluded from code maps

**For health check builds:**
- `outDir` should be set if using tsc for builds
- Or configure your bundler (Vite, webpack) in the `build` script

### Quality & Safety Options

```json
{
  "compilerOptions": {
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true
  }
}
```

**Recommendations:**
- `strict: true` - Essential for type safety
- `noUnusedLocals` / `noUnusedParameters` - Catch dead code
- `skipLibCheck: true` - Skip type checking of `.d.ts` files for faster builds

### Declaration Generation

For libraries or API documentation:

```json
{
  "compilerOptions": {
    "declaration": true,
    "declarationMap": true
  }
}
```

---

## Include and Exclude Patterns

### Standard Patterns

```json
{
  "include": ["src/**/*"],
  "exclude": [
    "node_modules",
    "dist",
    "**/*.test.ts",
    "**/*.spec.ts"
  ]
}
```

### Multiple Source Directories

```json
{
  "include": [
    "src/**/*",
    "lib/**/*",
    "shared/**/*"
  ]
}
```

### Monorepo Structure

```json
{
  "include": ["packages/*/src/**/*"],
  "exclude": [
    "node_modules",
    "**/dist",
    "**/__tests__"
  ]
}
```

---

## Configuration Examples by Project Type

### Node.js Backend (CommonJS)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
```

### Node.js Backend (ESM)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "esnext",
    "moduleResolution": "bundler",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

### React Application (Vite)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

### Library Package

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.test.ts", "**/*.spec.ts"]
}
```

---

## Path Mapping and Module Resolution

### Path Aliases

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@components/*": ["src/components/*"],
      "@utils/*": ["src/utils/*"]
    }
  }
}
```

**Note:** If using path aliases, you may need to configure your bundler (Vite, webpack) to match.

### Module Resolution Strategies

| Strategy                  | When to Use                           |
| ------------------------- | ------------------------------------- |
| `"node"`                  | Traditional Node.js projects          |
| `"node16"` / `"nodenext"` | Modern Node.js with ESM support       |
| `"bundler"`               | Projects using Vite, webpack, esbuild |

---

## Complete Example

Here's a complete tsconfig.json for a WSD TypeScript project (Node.js backend):

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",

    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,

    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,

    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,

    "moduleResolution": "node"
  },
  "include": ["src/**/*"],
  "exclude": [
    "node_modules",
    "dist",
    "**/*.test.ts",
    "**/*.spec.ts"
  ]
}
```

---

## Common Issues

### Build Output Not Where Expected

**Symptom:** `tsc` outputs files to unexpected locations

**Solution:** Verify `outDir` and `rootDir` match your project structure:
```json
{
  "compilerOptions": {
    "outDir": "./dist",
    "rootDir": "./src"
  }
}
```

### Import Errors in Built Code

**Symptom:** Runtime errors about missing modules

**Solution:** Ensure `module` matches your runtime environment:
- Node.js CommonJS: `"module": "commonjs"`
- Node.js ESM: `"module": "esnext"` with `"moduleResolution": "node16"`
- Bundlers: `"module": "esnext"` with `"moduleResolution": "bundler"`

### Type Errors in Tests

**Symptom:** Test files have TypeScript errors

**Solution:** Include test files in `include` or remove from `exclude`:
```json
{
  "include": ["src/**/*", "tests/**/*"]
}
```

Or use a separate `tsconfig.test.json` that extends the main config.

---

*See `Node-Project-Guide.md` for complete setup instructions and `package.json.md` for required scripts.*
