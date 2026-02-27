/**
 * @file WSD utility functions for language detection, configuration, and package management.
 *
 * Provides centralized utility functions for detecting project language type
 * (TypeScript vs JavaScript), package manager preferences, and script/tool availability.
 * These functions are used by the health check script, documentation generators, and other
 * WSD tools to adapt their behavior appropriately for each project type.
 *
 * Functions:
 * - findPackageJsonRoot(): Find the project-root directory via package.json
 * - getCheckDirs(): Read configured check directories from package.json
 * - hasTypeScriptFiles(): Scan directories for .ts files
 * - detectProjectLanguages(): Detect all Node.js languages present in the project
 * - detectPackageManager(): Detect user's preferred package manager from lock files
 * - detectTestRunner(): Detect which test runner is configured in package.json
 * - isScriptAvailable(): Check if a script exists in package.json
 * - isToolAvailable(): Check if a package exists in dependencies
 */

const fs = require('fs');
const path = require('path');

/**
 * Find the directory containing the project-root package.json.
 *
 * Walks up the directory tree from the script location until it finds a
 * directory containing a package.json with a "name" field, which
 * distinguishes project-root files from module-boundary files (e.g.,
 * `{"type": "commonjs"}` placed in subdirectories to control module
 * resolution).
 *
 * This function specifically searches for package.json, not the general
 * project root (which could be indicated by pyproject.toml for Python).
 * @returns {string} Absolute path to directory containing the project-root
 *                   package.json, or parent directory of script location
 *                   if not found.
 */
function findPackageJsonRoot() {
  let currentDir = __dirname;
  while (currentDir !== path.dirname(currentDir)) {
    const candidate = path.join(currentDir, 'package.json');
    if (fs.existsSync(candidate)) {
      try {
        const content = JSON.parse(fs.readFileSync(candidate, 'utf-8'));
        if (content.name) {
          return currentDir;
        }
      } catch {
        // Malformed JSON — skip this candidate
      }
    }
    currentDir = path.dirname(currentDir);
  }
  // Fallback: assume script is in scripts/ subdirectory
  return path.resolve(__dirname, '..');
}

/**
 * Read check directories from package.json wsd.checkDirs field.
 *
 * Reads the "wsd.checkDirs" configuration from package.json, which specifies
 * which directories should be scanned for source files during language detection
 * and tool execution.
 *
 * Returns `null` when configuration is not found (no package.json, no `wsd`
 * section, no `checkDirs` key, or parse failure). Returns an empty array when
 * `checkDirs: []` is explicitly configured, which is valid for projects where
 * tools manage their own paths via tool-specific config files.
 * @returns {string[] | null} Array of directory paths relative to project root
 *                            when configured (may be empty if `checkDirs: []`),
 *                            or `null` if configuration is not found.
 */
function getCheckDirs() {
  const packageJsonPath = path.join(findPackageJsonRoot(), 'package.json');

  if (!fs.existsSync(packageJsonPath)) {
    console.error('Note: wsd.checkDirs not configured. Code quality tools will be skipped.');
    return null;
  }

  try {
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
    const wsdConfig = packageJson.wsd === undefined ? {} : packageJson.wsd;

    if (typeof wsdConfig !== 'object' || wsdConfig === null || Array.isArray(wsdConfig)) {
      console.error('Warning: wsd field in package.json must be an object.');
      return null;
    }

    if (!('checkDirs' in wsdConfig)) {
      console.error(
        'Note: wsd.checkDirs not configured in package.json. Code quality tools will be skipped.'
      );
      return null;
    }

    if (!Array.isArray(wsdConfig.checkDirs)) {
      console.error('Warning: wsd.checkDirs must be an array in package.json.');
      return null;
    }

    return wsdConfig.checkDirs;
  } catch {
    return null;
  }
}

/**
 * Recursively scan a directory for files matching a pattern.
 * @param {string} dir - Directory path to scan (relative to root)
 * @param {string} extension - File extension to match (e.g., '.ts')
 * @param {Set<string>} excludeDirs - Set of directory names to exclude
 * @param {string|null} root - Project root directory path. If null, resolves via findPackageJsonRoot().
 * @returns {boolean} True if any matching files found
 */
function hasFilesWithExtension(dir, extension, excludeDirs, root = null) {
  const effectiveRoot = root || findPackageJsonRoot();
  const fullPath = path.join(effectiveRoot, dir);

  if (!fs.existsSync(fullPath)) {
    return false;
  }

  try {
    const entries = fs.readdirSync(fullPath, { withFileTypes: true });

    for (const entry of entries) {
      if (entry.isDirectory()) {
        if (excludeDirs.has(entry.name)) {
          continue;
        }
        if (
          hasFilesWithExtension(path.join(dir, entry.name), extension, excludeDirs, effectiveRoot)
        ) {
          return true;
        }
      } else if (entry.isFile() && entry.name.endsWith(extension)) {
        return true;
      }
    }
  } catch {
    return false;
  }

  return false;
}

/**
 * Scan directories for TypeScript files (.ts).
 *
 * Recursively scans the provided directories looking for any .ts files.
 * Excludes node_modules/ and dist/ directories from scanning.
 * Type declaration files (.d.ts) are included in the scan.
 * @param {string[]} checkDirs - Directories to scan (relative to root)
 * @param {string|null} root - Project root directory path. If null, resolves via findPackageJsonRoot().
 * @returns {boolean} True if any .ts files found, false otherwise
 */
function hasTypeScriptFiles(checkDirs, root = null) {
  const effectiveRoot = root || findPackageJsonRoot();
  const excludeDirs = new Set(['node_modules', 'dist']);

  for (const dir of checkDirs) {
    if (hasFilesWithExtension(dir, '.ts', excludeDirs, effectiveRoot)) {
      return true;
    }
  }

  return false;
}

/**
 * Detect all programming languages present in the project.
 *
 * Returns an array of detected Node.js languages: ["typescript"] or ["javascript"].
 * Returns an empty array if no package.json exists (codeless from JS perspective).
 *
 * Note: This function only detects Node.js languages (TypeScript/JavaScript).
 * It does NOT detect Python. This asymmetry is intentional because:
 * 1. JS scripts only need to know about JS/TS (their own ecosystem)
 * 2. Python is the lingua franca and handles universal detection
 * 3. Importing a TOML parser into JS just for Python detection adds unnecessary complexity
 * @param {string|null} projectRoot - Optional project root directory path.
 *                                    If null, automatically finds project root.
 * @returns {string[]} Array of detected languages, or empty array if no Node.js project
 */
function detectProjectLanguages(projectRoot = null) {
  const root = projectRoot || findPackageJsonRoot();
  const packageJsonPath = path.join(root, 'package.json');

  if (!fs.existsSync(packageJsonPath)) {
    return [];
  }

  const languages = [];

  // Read wsd.checkDirs from package.json at the specified root
  let checkDirs = [];
  try {
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
    const wsdConfig = packageJson.wsd || {};
    checkDirs = wsdConfig.checkDirs || [];
  } catch {
    checkDirs = [];
  }

  // Scan for TypeScript files in configured directories using the specified root
  if (hasTypeScriptFiles(checkDirs, root)) {
    languages.push('typescript');
  } else {
    languages.push('javascript');
  }

  return languages;
}

/**
 * Detect the user's preferred package manager by checking for lock files.
 *
 * Examines the project root for package manager lock files in priority order
 * to determine which package manager the project uses. This enables tools to
 * invoke scripts using the correct package manager command.
 * @returns {string | null} Package manager name ('pnpm', 'npm', 'yarn', 'bun'),
 *                          or null if no lock file is found.
 * @remarks Checks lock files in priority order: pnpm-lock.yaml, package-lock.json,
 *          yarn.lock, bun.lock/bun.lockb.
 */
function detectPackageManager() {
  const root = findPackageJsonRoot();
  if (fs.existsSync(path.join(root, 'pnpm-lock.yaml'))) {
    return 'pnpm';
  }
  if (fs.existsSync(path.join(root, 'package-lock.json'))) {
    return 'npm';
  }
  if (fs.existsSync(path.join(root, 'yarn.lock'))) {
    return 'yarn';
  }
  if (fs.existsSync(path.join(root, 'bun.lock'))) {
    return 'bun';
  }
  if (fs.existsSync(path.join(root, 'bun.lockb'))) {
    return 'bun';
  }

  return null;
}

/**
 * Detect which test runner is configured in package.json devDependencies.
 *
 * Checks the devDependencies section of package.json for known test runners
 * in priority order: vitest, jest, mocha. Returns the first match found.
 * @param {string | null} projectRoot - Root directory of the project. If null, searches from
 *                                       the script's directory up the tree for package.json.
 * @returns {string | null} Test runner name ('vitest', 'jest', or 'mocha') if detected,
 *                          or null if no known test runner is found.
 * @example
 * const runner = detectTestRunner();  // Auto-detect from current directory
 * console.log(runner);  // 'vitest'
 *
 * const runner2 = detectTestRunner('/path/to/project');
 * console.log(runner2);  // 'jest'
 */
function detectTestRunner(projectRoot = null) {
  const root = projectRoot || findPackageJsonRoot();
  const packageJsonPath = path.join(root, 'package.json');

  if (!fs.existsSync(packageJsonPath)) {
    return null;
  }

  try {
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
    const devDependencies = packageJson.devDependencies || {};

    if (typeof devDependencies !== 'object') {
      return null;
    }

    if ('vitest' in devDependencies) {
      return 'vitest';
    }
    if ('jest' in devDependencies) {
      return 'jest';
    }
    if ('mocha' in devDependencies) {
      return 'mocha';
    }

    return null;
  } catch {
    return null;
  }
}

/**
 * Check if a script is defined in the project's package.json.
 *
 * Examines the scripts section of package.json to determine if a specific
 * script name is available for execution via the package manager.
 * @param {string} scriptName - Name of the script to check (e.g., 'build', 'test', 'typedoc').
 * @returns {boolean} True if the script exists in package.json scripts, false otherwise.
 * @remarks Returns false if package.json doesn't exist or cannot be parsed.
 */
function isScriptAvailable(scriptName) {
  const packageJsonPath = path.join(findPackageJsonRoot(), 'package.json');

  if (!fs.existsSync(packageJsonPath)) {
    return false;
  }

  try {
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
    return !!(packageJson.scripts && packageJson.scripts[scriptName]);
  } catch {
    return false;
  }
}

/**
 * Check if a package is available for use.
 *
 * Determines whether a package can be required in the current Node.js environment.
 * This is the JavaScript equivalent of Python's is_tool_available(), enabling
 * consistent tool availability checking across both ecosystems.
 * @param {string} packageName - Name of the package to check (e.g., 'typedoc', 'eslint').
 * @returns {boolean} True if the package can be required, false otherwise.
 * @remarks Uses require.resolve() to check actual package availability rather than
 *          just checking package.json declarations. A package may be declared but
 *          not installed, or installed globally but not declared.
 */
function isToolAvailable(packageName) {
  if (!packageName || typeof packageName !== 'string') {
    return false;
  }
  try {
    require.resolve(packageName);
    return true;
  } catch {
    return false;
  }
}

module.exports = {
  findPackageJsonRoot,
  getCheckDirs,
  hasTypeScriptFiles,
  detectProjectLanguages,
  detectPackageManager,
  detectTestRunner,
  isScriptAvailable,
  isToolAvailable,
};
