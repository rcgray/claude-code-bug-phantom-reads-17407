/**
 * @file Generate JSDoc API documentation for JavaScript projects.
 *
 * This script orchestrates JSDoc documentation generation:
 * 1. Detects project language (skips TypeScript projects)
 * 2. Validates jsdoc script availability in package.json
 * 3. Runs JSDoc via the detected package manager to generate native HTML documentation
 *
 * Uses shared utilities from wsd_utils.js for:
 * - Language detection (detectProjectLanguages)
 * - Package manager detection (detectPackageManager)
 * - Script availability checking (isScriptAvailable)
 * - Directory configuration (getCheckDirs)
 *
 * Configuration:
 * - Output location: dev/reports/jsdoc-api-docs/ (HTML directory)
 * - JSDoc configuration: jsdoc.json in project root (optional)
 * - Source directories: wsd.checkDirs from package.json
 *
 * For TypeScript projects, the script detects the project language and exits
 * gracefully with a helpful message, since JSDoc is specifically designed for
 * JavaScript projects and TypeScript projects should use TypeDoc instead.
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Import shared utilities for language detection, package management, and configuration
const {
  detectProjectLanguages,
  detectPackageManager,
  getCheckDirs,
  isScriptAvailable,
} = require('./wsd_utils.js');

// Resolve project root from script location to ensure consistent path resolution
// regardless of the current working directory when the script is invoked.
// This pattern handles both direct execution and require() scenarios.
const __dirname_custom = path.dirname(require.main.filename || __filename);
const PROJECT_ROOT = path.resolve(__dirname_custom, '..');
const REPORTS_DIR = path.join(PROJECT_ROOT, 'dev', 'reports');
const OUTPUT_DIR = path.join(REPORTS_DIR, 'jsdoc-api-docs');

/**
 * Run a command and return its results.
 *
 * Executes a shell command synchronously and captures output. Used for running
 * JSDoc during documentation generation.
 * @param {string[]} cmd - Command and arguments to run (will be joined with spaces)
 * @param {object} options - Options for command execution
 * @param {string} [options.cwd] - Working directory for command execution (defaults to PROJECT_ROOT)
 * @param {boolean} [options.captureOutput] - If true, capture stdout/stderr; if false, inherit stdio
 * @returns {{returncode: number, stdout: string, stderr: string}} Command results with exit code and output
 */
function runCommand(cmd, options = {}) {
  try {
    // Join command array into string for shell execution; execSync handles
    // proper escaping when given a string with shell: false (default)
    const stdout = execSync(cmd.join(' '), {
      encoding: 'utf-8',
      cwd: options.cwd || PROJECT_ROOT,
      // Use 'pipe' for all streams when capturing output, otherwise 'inherit'
      // to show real-time output to user during long-running commands
      stdio: options.captureOutput ? ['pipe', 'pipe', 'pipe'] : 'inherit',
    });
    return {
      returncode: 0,
      stdout: stdout || '',
      stderr: '',
    };
  } catch (error) {
    // execSync throws on non-zero exit codes; extract status and output
    // from the error object for consistent return format
    return {
      returncode: error.status || -1,
      stdout: error.stdout ? error.stdout.toString() : '',
      stderr: error.stderr ? error.stderr.toString() : error.message,
    };
  }
}

/**
 * Clean up the output directory before regeneration.
 *
 * Removes all existing files from the output directory to prevent stale
 * documentation from previous runs. Creates the directory if it doesn't exist.
 */
function cleanOutputDirectory() {
  if (fs.existsSync(OUTPUT_DIR)) {
    fs.rmSync(OUTPUT_DIR, { recursive: true, force: true });
  }
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

/**
 * Generate JSDoc API documentation.
 *
 * Validates that the 'jsdoc' script is available in package.json, then runs
 * JSDoc via the detected package manager to generate native HTML documentation.
 *
 * Uses shared utilities from wsd_utils.js for package manager detection and
 * script availability checking to ensure consistent behavior across WSD tools.
 * @param {string[]} [checkDirs] - Directories to document (optional, reads from config if not provided)
 * @returns {boolean} True if documentation generated successfully, false on any error
 */
function generateJsdocDocs(checkDirs) {
  // If checkDirs not provided as parameter, read from configuration
  if (!checkDirs) {
    checkDirs = getCheckDirs();
    if (checkDirs.length === 0) {
      console.log('Skipping JSDoc documentation: no source directories configured.');
      return true; // Return true to indicate graceful skip, not an error
    }
  }

  console.log('Generating JSDoc API documentation...');

  // Check if jsdoc script is available in package.json
  if (!isScriptAvailable('jsdoc')) {
    console.error('');
    console.error('Error: "jsdoc" script not found in package.json.');
    console.error('');
    console.error('JSDoc must be configured as a package.json script to generate documentation.');
    console.error('');
    console.error('To fix this issue:');
    console.error('');
    console.error('1. Install JSDoc as a dev dependency:');
    console.error('   npm install jsdoc --save-dev');
    console.error('   # or: pnpm add -D jsdoc');
    console.error('   # or: yarn add --dev jsdoc');
    console.error('   # or: bun add -d jsdoc');
    console.error('');
    console.error('2. Add a "jsdoc" script to your package.json:');
    console.error('   "scripts": {');
    console.error('     "jsdoc": "jsdoc -d dev/reports/jsdoc-api-docs -r"');
    console.error('   }');
    console.error('');
    process.exit(1);
  }

  // Ensure reports directory exists for output
  if (!fs.existsSync(REPORTS_DIR)) {
    fs.mkdirSync(REPORTS_DIR, { recursive: true });
  }

  // Clean output directory to remove stale files before regeneration
  cleanOutputDirectory();

  // Detect package manager (checkDirs already validated by caller)
  const packageManager = detectPackageManager();
  if (packageManager === null) {
    console.error('Error: No package manager lock file found.');
    console.error('Create one by running: pnpm install, npm install, yarn install, or bun install');
    process.exit(1);
  }

  // Build command using package manager script pattern with directories as entry points
  const jsdocCommand = [packageManager, 'run', 'jsdoc', '--', ...checkDirs];
  const result = runCommand(jsdocCommand, { captureOutput: true, cwd: PROJECT_ROOT });

  if (result.returncode === 0) {
    console.log(`JSDoc successfully generated HTML documentation in: ${OUTPUT_DIR}`);
    if (result.stdout) {
      console.log(`JSDoc Output:\n${result.stdout}`);
    }
    if (result.stderr) {
      console.log(`JSDoc Stderr (Info/Warnings):\n${result.stderr}`);
    }
    return true;
  } else {
    console.error(`Error generating JSDoc documentation (return code: ${result.returncode}):`);
    if (result.stdout) console.error(`--- JSDoc STDOUT ---\n${result.stdout}`);
    if (result.stderr) console.error(`--- JSDoc STDERR ---\n${result.stderr}`);
    console.error('Failed to generate JSDoc documentation.');
    return false;
  }
}

/**
 * Main function to generate JSDoc documentation.
 *
 * Detects project language and exits gracefully for TypeScript projects,
 * since JSDoc is specifically designed for JavaScript and TypeScript projects
 * should use TypeDoc instead.
 */
function main() {
  // Check for configured source directories first
  const checkDirs = getCheckDirs();
  if (checkDirs.length === 0) {
    console.log('Skipping JSDoc documentation: no source directories configured.');
    return;
  }

  // Detect project languages - JSDoc is for JavaScript only
  const languages = detectProjectLanguages();

  if (languages.includes('typescript')) {
    console.log('');
    console.log('JSDoc Generator: Skipping - JavaScript-only project required');
    console.log('');
    console.log('JSDoc is a documentation generator specifically designed for JavaScript');
    console.log('projects. It analyzes JavaScript source files and JSDoc comments to');
    console.log('generate comprehensive API documentation.');
    console.log('');
    console.log('Detected: TypeScript project (.ts files found)');
    console.log('');
    console.log('For TypeScript projects, use TypeDoc instead:');
    console.log('  node scripts/codedocs_typedoc.js');
    console.log('');
    return;
  }

  if (!languages.includes('javascript')) {
    console.log('');
    console.log('JSDoc Generator: Skipping - No JavaScript project detected');
    console.log('');
    console.log('Detected: No package.json found or unable to determine project type.');
    console.log('');
    return;
  }

  if (!generateJsdocDocs(checkDirs)) {
    console.error('\nJSDoc generation process encountered an error.');
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { generateJsdocDocs };
