/**
 * @file WSD utility functions for language detection, configuration, and package management.
 *
 * Provides centralized utility functions for detecting project language type
 * (TypeScript vs JavaScript), package manager preferences, and script/tool availability.
 * These functions are used by the health check script, documentation generators, and other
 * WSD tools to adapt their behavior appropriately for each project type.
 *
 * Functions:
 * - getCheckDirs(): Read configured check directories from package.json
 * - hasTypeScriptFiles(): Scan directories for .ts files
 * - detectProjectLanguages(): Detect all Node.js languages present in the project
 * - detectPackageManager(): Detect user's preferred package manager from lock files
 * - isScriptAvailable(): Check if a script exists in package.json
 * - isToolAvailable(): Check if a package exists in dependencies
 */

const fs = require('fs');
const path = require('path');

/**
 * Find the directory containing package.json for Node.js language detection.
 *
 * Internal helper function used by Node.js detection functions to locate
 * the package.json file. Walks up the directory tree from the script
 * location until it finds a directory containing package.json.
 *
 * This function specifically searches for package.json, not the general
 * project root (which could be indicated by pyproject.toml for Python).
 * @private
 * @returns {string} Absolute path to directory containing package.json,
 *                   or parent directory of script location if not found.
 */
function _findPackageJsonRoot() {
  let currentDir = __dirname;
  while (currentDir !== path.dirname(currentDir)) {
    if (fs.existsSync(path.join(currentDir, 'package.json'))) {
      return currentDir;
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
 * @returns {string[]} Array of directory paths relative to project root,
 *                     or empty array if not configured or package.json missing
 */
function getCheckDirs() {
  const packageJsonPath = path.join(_findPackageJsonRoot(), 'package.json');

  if (!fs.existsSync(packageJsonPath)) {
    console.error('Note: wsd.checkDirs not configured. Code quality tools will be skipped.');
    return [];
  }

  try {
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
    const wsdConfig = packageJson.wsd || {};

    if (!wsdConfig.checkDirs) {
      console.error(
        'Note: wsd.checkDirs not configured in package.json. Code quality tools will be skipped.'
      );
      return [];
    }

    if (!Array.isArray(wsdConfig.checkDirs)) {
      console.error('Warning: wsd.checkDirs must be an array in package.json.');
      return [];
    }

    return wsdConfig.checkDirs;
  } catch {
    return [];
  }
}

/**
 * Recursively scan a directory for files matching a pattern.
 * @param {string} dir - Directory path to scan (relative to root)
 * @param {string} extension - File extension to match (e.g., '.ts')
 * @param {Set<string>} excludeDirs - Set of directory names to exclude
 * @param {string|null} root - Project root directory path. If null, resolves via _findPackageJsonRoot().
 * @returns {boolean} True if any matching files found
 */
function hasFilesWithExtension(dir, extension, excludeDirs, root = null) {
  const effectiveRoot = root || _findPackageJsonRoot();
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
 * @param {string|null} root - Project root directory path. If null, resolves via _findPackageJsonRoot().
 * @returns {boolean} True if any .ts files found, false otherwise
 */
function hasTypeScriptFiles(checkDirs, root = null) {
  const effectiveRoot = root || _findPackageJsonRoot();
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
  const root = projectRoot || _findPackageJsonRoot();
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
 *          yarn.lock, bun.lockb.
 */
function detectPackageManager() {
  const root = _findPackageJsonRoot();
  if (fs.existsSync(path.join(root, 'pnpm-lock.yaml'))) {
    return 'pnpm';
  }
  if (fs.existsSync(path.join(root, 'package-lock.json'))) {
    return 'npm';
  }
  if (fs.existsSync(path.join(root, 'yarn.lock'))) {
    return 'yarn';
  }
  if (fs.existsSync(path.join(root, 'bun.lockb'))) {
    return 'bun';
  }

  return null;
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
  const packageJsonPath = path.join(_findPackageJsonRoot(), 'package.json');

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
  getCheckDirs,
  hasTypeScriptFiles,
  detectProjectLanguages,
  detectPackageManager,
  isScriptAvailable,
  isToolAvailable,
};
