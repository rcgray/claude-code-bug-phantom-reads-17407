/**
 * @file Generate code map documentation for JavaScript projects.
 *
 * This script uses the Babel parser to analyze JavaScript source files
 * and generate lightweight markdown documentation including classes,
 * functions, and variables with their JSDoc comments.
 *
 * Configuration:
 * - Source directories: Read from package.json wsd.checkDirs field
 * - Output location: docs/reports/JavaScript-Code-Map.md (hardcoded)
 * - Title: "JavaScript Code Map" (hardcoded)
 *
 * For TypeScript projects, the script detects the project language and exits
 * gracefully with a helpful message, directing users to the TypeScript
 * code mapper instead.
 * @see {@link docs/features/javascript-document-generator/JavaScript-Document-Generator-Overview.md}
 */

const { parse } = require('@babel/parser');
const fs = require('fs');
const path = require('path');

// Import language detection and configuration utilities
const { detectProjectLanguages, getCheckDirs } = require('./wsd_utils.js');

// Resolve project root from script location for consistent path resolution
// regardless of the current working directory when the script is invoked.
// This pattern handles both direct execution and require() scenarios.
const __dirname_custom = path.dirname(require.main.filename || __filename);
const PROJECT_ROOT = path.resolve(__dirname_custom, '..');
const OUTPUT_PATH = path.join(PROJECT_ROOT, 'docs', 'reports', 'JavaScript-Code-Map.md');
const TITLE = 'JavaScript Code Map';

// Directories to exclude from file discovery
const EXCLUDED_DIRS = new Set(['node_modules', 'dist', 'build', 'coverage', '__tests__']);

// File patterns to exclude from documentation
const EXCLUDED_PATTERNS = ['.min.js', '.bundle.js', '.test.js', '.spec.js', '.config.js'];

/**
 * Check if a filename matches any excluded pattern.
 * @param {string} filename - The filename to check
 * @returns {boolean} True if the file should be excluded
 */
function isExcludedFile(filename) {
  return EXCLUDED_PATTERNS.some((pattern) => filename.endsWith(pattern));
}

/**
 * Recursively discover all JavaScript files in a directory.
 * @param {string} dir - Directory path relative to project root
 * @param {string[]} files - Accumulator array for discovered files
 * @returns {string[]} Array of file paths relative to project root
 */
function discoverJsFiles(dir, files = []) {
  const fullPath = path.join(PROJECT_ROOT, dir);

  if (!fs.existsSync(fullPath)) {
    return files;
  }

  try {
    const entries = fs.readdirSync(fullPath, { withFileTypes: true });

    for (const entry of entries) {
      if (entry.isDirectory()) {
        if (EXCLUDED_DIRS.has(entry.name)) {
          continue;
        }
        discoverJsFiles(path.join(dir, entry.name), files);
      } else if (entry.isFile() && entry.name.endsWith('.js')) {
        if (!isExcludedFile(entry.name)) {
          files.push(path.join(dir, entry.name));
        }
      }
    }
  } catch (error) {
    console.warn(`Warning: Could not read directory ${dir}: ${error.message}`);
  }

  return files;
}

/**
 * Parse a JavaScript file using Babel parser.
 * @param {string} filePath - Path to the JavaScript file relative to project root
 * @returns {object|null} Babel AST or null if parsing failed
 */
function parseFile(filePath) {
  const fullPath = path.join(PROJECT_ROOT, filePath);

  try {
    const sourceCode = fs.readFileSync(fullPath, 'utf-8');
    const ast = parse(sourceCode, {
      sourceType: 'unambiguous',
      attachComment: true,
      plugins: ['jsx', 'classProperties', 'classPrivateProperties'],
    });
    return ast;
  } catch (error) {
    console.warn(`Warning: Could not parse ${filePath}: ${error.message}`);
    console.warn('Skipping file and continuing...');
    return null;
  }
}

/**
 * Extract JSDoc comment from a node's leading comments.
 * @param {object} node - Babel AST node
 * @returns {string|null} JSDoc comment text or null if not found
 */
function getJSDocComment(node) {
  if (!node.leadingComments || node.leadingComments.length === 0) {
    return null;
  }

  // Find the last block comment that looks like JSDoc (starts with *)
  const jsdocComment = node.leadingComments
    .filter((c) => c.type === 'CommentBlock' && c.value.startsWith('*'))
    .pop();

  return jsdocComment ? jsdocComment.value : null;
}

/**
 * Extract file-level JSDoc comment (first comment before any statements).
 * @param {object} ast - Babel AST
 * @returns {string} Cleaned file-level description or empty string
 */
function extractFileLevelDoc(ast) {
  if (!ast.comments || ast.comments.length === 0) {
    return '';
  }

  // Find the first JSDoc comment that appears before any statements
  const firstStatement = ast.program.body[0];
  const firstStatementStart = firstStatement ? firstStatement.start : Infinity;

  for (const comment of ast.comments) {
    if (comment.type === 'CommentBlock' && comment.value.startsWith('*')) {
      if (comment.end < firstStatementStart) {
        return cleanJSDoc(comment.value);
      }
    }
  }

  return '';
}

/**
 * Clean and format a JSDoc comment string.
 * @param {string} rawComment - Raw JSDoc comment content (without delimiters)
 * @returns {string} Cleaned JSDoc text
 */
function cleanJSDoc(rawComment) {
  if (!rawComment) return '';

  // Remove leading asterisks and clean up whitespace
  const lines = rawComment.split('\n').map((line) => line.replace(/^\s*\*\s?/, '').trim());

  return lines.join('\n').trim();
}

/**
 * Extract the first paragraph from a JSDoc comment (summary).
 * @param {string|null} jsdocComment - Raw JSDoc comment
 * @returns {string} First paragraph or default message
 */
function getDocstringSummary(jsdocComment) {
  if (!jsdocComment) return 'No description available.';

  const cleaned = cleanJSDoc(jsdocComment);

  // Extract first paragraph (before first blank line or @tag)
  const firstPara = cleaned.split(/\n\n|\n@/)[0].trim();

  return firstPara || 'No description available.';
}

/**
 * Parse JSDoc tags (@param, @returns, @type) from a comment.
 * @param {string|null} jsdocComment - Raw JSDoc comment
 * @returns {object} Object with params, returns, and type arrays
 */
function parseJSDocTags(jsdocComment) {
  const result = {
    params: [],
    returns: null,
    type: null,
  };

  if (!jsdocComment) return result;

  const cleaned = cleanJSDoc(jsdocComment);
  const lines = cleaned.split('\n');

  for (const line of lines) {
    // Parse @param {type} name - description
    const paramMatch = line.match(/^@param\s+\{([^}]+)\}\s+(\w+)\s*(?:-\s*)?(.*)$/);
    if (paramMatch) {
      result.params.push({
        type: paramMatch[1],
        name: paramMatch[2],
        description: paramMatch[3] || '',
      });
      continue;
    }

    // Parse @returns {type} description
    const returnsMatch = line.match(/^@returns?\s+\{([^}]+)\}\s*(.*)$/);
    if (returnsMatch) {
      result.returns = {
        type: returnsMatch[1],
        description: returnsMatch[2] || '',
      };
      continue;
    }

    // Parse @type {type}
    const typeMatch = line.match(/^@type\s+\{([^}]+)\}/);
    if (typeMatch) {
      result.type = typeMatch[1];
    }
  }

  return result;
}

/**
 * Check if a name represents a private member (starts with _).
 * @param {string} name - Member name to check
 * @returns {boolean} True if private
 */
function isPrivateMember(name) {
  return name.startsWith('_');
}

/**
 * Extract function parameters from AST node.
 * @param {object[]} params - Array of parameter nodes
 * @returns {string[]} Array of parameter names
 */
function extractParams(params) {
  return params.map((param) => {
    if (param.type === 'Identifier') {
      return param.name;
    } else if (param.type === 'AssignmentPattern' && param.left.type === 'Identifier') {
      return param.left.name;
    } else if (param.type === 'RestElement' && param.argument.type === 'Identifier') {
      return `...${param.argument.name}`;
    }
    return 'param';
  });
}

/**
 * Process a class declaration and extract documentation.
 * @param {object} node - ClassDeclaration AST node
 * @returns {object} Processed class documentation
 */
function processClass(node) {
  const className = node.id ? node.id.name : 'AnonymousClass';
  const jsdoc = getJSDocComment(node);
  const description = getDocstringSummary(jsdoc);

  const properties = [];
  const methods = [];

  if (node.body && node.body.body) {
    for (const member of node.body.body) {
      // Skip private members
      const memberName =
        member.key && member.key.name ? member.key.name : member.key && member.key.value;
      if (memberName && isPrivateMember(memberName)) {
        continue;
      }

      if (member.type === 'ClassMethod') {
        // Skip constructor from documentation
        if (member.kind === 'constructor') continue;

        const methodJsdoc = getJSDocComment(member);
        const methodTags = parseJSDocTags(methodJsdoc);
        const params = extractParams(member.params);

        methods.push({
          name: memberName,
          params,
          description: getDocstringSummary(methodJsdoc),
          returnType: methodTags.returns ? methodTags.returns.type : 'void',
          isStatic: member.static,
          isAsync: member.async,
        });
      } else if (member.type === 'ClassProperty') {
        const propJsdoc = getJSDocComment(member);
        const propTags = parseJSDocTags(propJsdoc);

        properties.push({
          name: memberName,
          type: propTags.type || 'any',
          description: getDocstringSummary(propJsdoc),
          isStatic: member.static,
        });
      }
    }
  }

  return {
    name: className,
    description,
    properties,
    methods,
    isExported: false, // Will be set by caller
  };
}

/**
 * Process a function declaration and extract documentation.
 * @param {object} node - FunctionDeclaration AST node
 * @returns {object} Processed function documentation
 */
function processFunction(node) {
  const funcName = node.id ? node.id.name : 'anonymous';
  const jsdoc = getJSDocComment(node);
  const tags = parseJSDocTags(jsdoc);
  const params = extractParams(node.params);

  return {
    name: funcName,
    params,
    description: getDocstringSummary(jsdoc),
    returnType: tags.returns ? tags.returns.type : 'void',
    paramDocs: tags.params,
    returnDoc: tags.returns,
    isAsync: node.async,
    isExported: false,
  };
}

/**
 * Process a variable declaration and extract documentation.
 * @param {object} node - VariableDeclaration AST node
 * @param {object} declarator - VariableDeclarator node
 * @returns {object} Processed variable documentation
 */
function processVariable(node, declarator) {
  const varName = declarator.id.name;
  const jsdoc = getJSDocComment(node);
  const tags = parseJSDocTags(jsdoc);

  // Check if it's an arrow function
  const isArrowFunction = declarator.init && declarator.init.type === 'ArrowFunctionExpression';

  if (isArrowFunction) {
    const params = extractParams(declarator.init.params);
    return {
      kind: 'arrow-function',
      name: varName,
      params,
      description: getDocstringSummary(jsdoc),
      returnType: tags.returns ? tags.returns.type : 'void',
      paramDocs: tags.params,
      returnDoc: tags.returns,
      isAsync: declarator.init.async,
      isExported: false,
      declarationType: node.kind,
    };
  }

  return {
    kind: 'variable',
    name: varName,
    type: tags.type || 'any',
    description: getDocstringSummary(jsdoc),
    isExported: false,
    declarationType: node.kind,
  };
}

/**
 * Analyze a JavaScript file and extract documentation.
 * @param {string} filePath - Path to file relative to project root
 * @returns {object|null} File documentation or null if parsing failed
 */
function analyzeFile(filePath) {
  const ast = parseFile(filePath);
  if (!ast) return null;

  const fileDoc = {
    filePath,
    description: extractFileLevelDoc(ast),
    classes: [],
    functions: [],
    variables: [],
  };

  const exportedNames = new Set();

  // First pass: identify exported names
  for (const node of ast.program.body) {
    if (node.type === 'ExportNamedDeclaration') {
      if (node.declaration) {
        if (node.declaration.type === 'ClassDeclaration' && node.declaration.id) {
          exportedNames.add(node.declaration.id.name);
        } else if (node.declaration.type === 'FunctionDeclaration' && node.declaration.id) {
          exportedNames.add(node.declaration.id.name);
        } else if (node.declaration.type === 'VariableDeclaration') {
          for (const decl of node.declaration.declarations) {
            if (decl.id && decl.id.name) {
              exportedNames.add(decl.id.name);
            }
          }
        }
      }
      if (node.specifiers) {
        for (const spec of node.specifiers) {
          if (spec.exported && spec.exported.name) {
            exportedNames.add(spec.exported.name);
          }
        }
      }
    } else if (node.type === 'ExportDefaultDeclaration') {
      if (node.declaration && node.declaration.id) {
        exportedNames.add(node.declaration.id.name);
      }
    }
  }

  // Second pass: process declarations
  for (const node of ast.program.body) {
    let declaration = node;
    let isExportedDecl = false;

    // Handle export wrappers
    if (node.type === 'ExportNamedDeclaration' && node.declaration) {
      declaration = node.declaration;
      isExportedDecl = true;
    } else if (node.type === 'ExportDefaultDeclaration' && node.declaration) {
      declaration = node.declaration;
      isExportedDecl = true;
    }

    // Process class declarations
    if (declaration.type === 'ClassDeclaration') {
      const classDoc = processClass(declaration);
      classDoc.isExported =
        isExportedDecl || (declaration.id && exportedNames.has(declaration.id.name));
      if (!isPrivateMember(classDoc.name)) {
        fileDoc.classes.push(classDoc);
      }
    }
    // Process function declarations
    else if (declaration.type === 'FunctionDeclaration') {
      const funcDoc = processFunction(declaration);
      funcDoc.isExported =
        isExportedDecl || (declaration.id && exportedNames.has(declaration.id.name));
      if (!isPrivateMember(funcDoc.name)) {
        fileDoc.functions.push(funcDoc);
      }
    }
    // Process variable declarations
    else if (declaration.type === 'VariableDeclaration') {
      for (const declarator of declaration.declarations) {
        if (declarator.id && declarator.id.name) {
          const varName = declarator.id.name;
          if (isPrivateMember(varName)) continue;

          const varDoc = processVariable(declaration, declarator);
          varDoc.isExported = isExportedDecl || exportedNames.has(varName);

          if (varDoc.kind === 'arrow-function') {
            fileDoc.functions.push(varDoc);
          } else {
            fileDoc.variables.push(varDoc);
          }
        }
      }
    }
  }

  return fileDoc;
}

/**
 * Generate a slug for markdown anchor links.
 * @param {string} filePath - File path to convert
 * @returns {string} URL-safe slug
 */
function generateSlug(filePath) {
  return filePath.replace(/[/.]/g, '_').toLowerCase();
}

/**
 * Generate markdown Table of Contents.
 * @param {object[]} fileDocs - Array of file documentation objects
 * @returns {string} Markdown TOC
 */
function generateTOC(fileDocs) {
  let toc = '## Table of Contents\n\n';

  for (const fileDoc of fileDocs) {
    const slug = generateSlug(fileDoc.filePath);
    toc += `- [\`${fileDoc.filePath}\`](#file-${slug})\n`;
  }

  return toc + '\n---\n';
}

/**
 * Generate markdown for a class.
 * @param {object} cls - Class documentation object
 * @returns {string} Markdown string
 */
function classToMarkdown(cls) {
  let md = `#### ${cls.name}\n\n`;

  if (cls.isExported) {
    md += '*export*\n\n';
  }

  md += `${cls.description}\n\n`;

  if (cls.properties.length > 0) {
    md += '**Properties**:\n';
    for (const prop of cls.properties) {
      const staticMod = prop.isStatic ? 'static ' : '';
      md += `- **${prop.name}**: \`${prop.type}\` ${staticMod}\n`;
      if (prop.description && prop.description !== 'No description available.') {
        md += `  - ${prop.description}\n`;
      }
    }
    md += '\n';
  }

  if (cls.methods.length > 0) {
    md += '**Methods**:\n';
    for (const method of cls.methods) {
      const staticMod = method.isStatic ? 'static ' : '';
      const asyncMod = method.isAsync ? 'async ' : '';
      const params = method.params.join(', ');
      md += `- **${method.name}**(${params}) => \`${method.returnType}\` ${asyncMod}${staticMod}\n`;
      if (method.description && method.description !== 'No description available.') {
        md += `  - ${method.description}\n`;
      }
    }
    md += '\n';
  }

  return md;
}

/**
 * Generate markdown for a function.
 * @param {object} func - Function documentation object
 * @returns {string} Markdown string
 */
function functionToMarkdown(func) {
  let md = `#### ${func.name}\n\n`;

  if (func.isExported) {
    if (func.kind === 'arrow-function') {
      md += `*export ${func.declarationType}*\n\n`;
    } else {
      md += '*export*\n\n';
    }
  }

  md += `${func.description}\n\n`;

  const asyncMod = func.isAsync ? 'async ' : '';
  const params = func.params.join(', ');
  md += `**Signature**: \`${asyncMod}function ${func.name}(${params})\`\n\n`;

  if (func.paramDocs && func.paramDocs.length > 0) {
    md += '**Parameters**:\n';
    for (const param of func.paramDocs) {
      md += `- \`${param.name}\` (\`${param.type}\`): ${param.description}\n`;
    }
    md += '\n';
  }

  if (func.returnDoc) {
    md += `**Returns**: \`${func.returnDoc.type}\` - ${func.returnDoc.description}\n\n`;
  }

  return md;
}

/**
 * Generate markdown for a variable.
 * @param {object} varItem - Variable documentation object
 * @returns {string} Markdown string
 */
function variableToMarkdown(varItem) {
  let md = `#### ${varItem.name}\n\n`;

  if (varItem.isExported) {
    md += `*export ${varItem.declarationType}*\n\n`;
  }

  md += `${varItem.description}\n\n`;
  md += `**Type**: \`${varItem.type}\`\n\n`;

  return md;
}

/**
 * Generate markdown for a file section.
 * @param {object} fileDoc - File documentation object
 * @returns {string} Markdown string
 */
function fileToMarkdown(fileDoc) {
  const slug = generateSlug(fileDoc.filePath);
  let md = `\n## File: \`${fileDoc.filePath}\` <a name="file-${slug}"></a>\n\n`;

  if (fileDoc.description) {
    md += `${fileDoc.description}\n\n`;
  }

  // Classes
  if (fileDoc.classes.length > 0) {
    md += '### Classes\n\n';
    const sortedClasses = [...fileDoc.classes].sort((a, b) => a.name.localeCompare(b.name));
    for (const cls of sortedClasses) {
      md += classToMarkdown(cls);
    }
  }

  // Functions
  if (fileDoc.functions.length > 0) {
    md += '### Functions\n\n';
    const sortedFuncs = [...fileDoc.functions].sort((a, b) => a.name.localeCompare(b.name));
    for (const func of sortedFuncs) {
      md += functionToMarkdown(func);
    }
  }

  // Variables
  if (fileDoc.variables.length > 0) {
    md += '### Variables\n\n';
    const sortedVars = [...fileDoc.variables].sort((a, b) => a.name.localeCompare(b.name));
    for (const varItem of sortedVars) {
      md += variableToMarkdown(varItem);
    }
  }

  md += '\n---\n';
  return md;
}

/**
 * Generate the complete markdown code map.
 * @param {object[]} fileDocs - Array of file documentation objects
 * @returns {string} Complete markdown document
 */
function generateMarkdown(fileDocs) {
  let md = `# ${TITLE}\n\n`;
  md += generateTOC(fileDocs);

  for (const fileDoc of fileDocs) {
    md += fileToMarkdown(fileDoc);
  }

  return md;
}

/**
 * Main function to generate the JavaScript code map.
 *
 * Reads configuration from package.json (wsd.checkDirs), then generates
 * a markdown code map at docs/reports/JavaScript-Code-Map.md.
 *
 * Detects project language and exits gracefully for TypeScript projects,
 * since this tool is specifically designed for JavaScript-only projects.
 */
function main() {
  // Check for configured source directories first
  const checkDirs = getCheckDirs();
  if (checkDirs.length === 0) {
    console.log('Skipping JavaScript code map: no source directories configured.');
    return;
  }

  // Detect project languages - this tool is for JavaScript only
  const languages = detectProjectLanguages();

  if (languages.includes('typescript')) {
    console.log('');
    console.log('Code Map Generator: Skipping - JavaScript-only project required');
    console.log('');
    console.log('This tool uses the Babel parser to analyze .js files and generate');
    console.log('lightweight code documentation. It is designed for JavaScript-only projects.');
    console.log('');
    console.log('Detected: TypeScript project (.ts files found)');
    console.log('');
    console.log('For TypeScript projects, use the TypeScript code mapper instead:');
    console.log('  node scripts/codedocs_typescript.js');
    console.log('');
    return;
  }

  if (!languages.includes('javascript')) {
    console.log('');
    console.log('Code Map Generator: Skipping - No JavaScript project detected');
    console.log('');
    console.log('Detected: No package.json found or unable to determine project type.');
    console.log('');
    return;
  }

  console.log('Generating JavaScript code map...');
  console.log(`Source directories: ${checkDirs.join(', ')}`);

  // Discover all JavaScript files
  const allFiles = [];
  for (const dir of checkDirs) {
    discoverJsFiles(dir, allFiles);
  }

  if (allFiles.length === 0) {
    console.log('No JavaScript files found in configured directories.');
    console.log('Generating empty code map.');
  } else {
    console.log(`Found ${allFiles.length} JavaScript files to analyze.`);
  }

  // Analyze each file
  const fileDocs = [];
  for (const filePath of allFiles) {
    console.log(`Analyzing ${filePath}...`);
    const fileDoc = analyzeFile(filePath);
    if (fileDoc) {
      fileDocs.push(fileDoc);
    }
  }

  // Sort files alphabetically
  fileDocs.sort((a, b) => a.filePath.localeCompare(b.filePath));

  // Generate markdown
  const markdown = generateMarkdown(fileDocs);

  // Ensure output directory exists
  const outputDir = path.dirname(OUTPUT_PATH);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // Write output
  fs.writeFileSync(OUTPUT_PATH, markdown);
  console.log(`Code map written to ${path.relative(PROJECT_ROOT, OUTPUT_PATH)}`);
}

// Run main() only when executed directly, not when required as a module
if (require.main === module) {
  main();
}

// Export for testing
module.exports = { main, analyzeFile, parseFile, discoverJsFiles };
