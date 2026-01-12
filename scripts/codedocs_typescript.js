/**
 * Generate code map documentation for TypeScript projects.
 *
 * This script uses the TypeScript Compiler API to analyze TypeScript source files
 * and generate comprehensive markdown documentation including classes, interfaces,
 * functions, enums, types, and variables with their JSDoc comments.
 *
 * Configuration:
 * - Source directories: Read from package.json wsd.checkDirs field
 * - Compiler options: Read from ./tsconfig.json
 * - Output location: docs/reports/TypeScript-Code-Map.md (hardcoded)
 * - Title: "TypeScript Code Map" (hardcoded)
 *
 * For JavaScript-only projects, the script detects the project language and exits
 * gracefully with a helpful message, since the TypeScript Compiler API requires
 * TypeScript source files to function properly.
 */

const ts = require('typescript');
const fs = require('fs');
const path = require('path');

// Import language detection and configuration utilities
const { detectProjectLanguages, getCheckDirs } = require('./wsd_utils.js');

// Resolve project root from script location for consistent path resolution
// regardless of the current working directory when the script is invoked.
const PROJECT_ROOT = path.resolve(__dirname, '..');
const OUTPUT_PATH = path.join(PROJECT_ROOT, 'docs', 'reports', 'TypeScript-Code-Map.md');
const TSCONFIG_PATH = path.join(PROJECT_ROOT, 'tsconfig.json');
const TITLE = 'TypeScript Code Map';

/**
 * Generates a "code map" for AI consumption from a TypeScript project.
 *
 * Uses configuration from package.json wsd.checkDirs for source directories
 * and tsconfig.json for TypeScript compiler options.
 */
class CodeMapGenerator {
  program;
  checker;
  result = [];
  projectBasePath;
  includeDirectories;

  /**
   * Initializes the CodeMapGenerator.
   *
   * Reads tsconfig.json for compiler options and uses wsd.checkDirs from
   * package.json for directory filtering.
   * @param {string[]} checkDirs - Directories to include (must not be empty)
   */
  constructor(checkDirs) {
    // Use check directories passed from main (already validated)
    this.includeDirectories = checkDirs;

    // Parse tsconfig.json using TypeScript's config file reader, which handles
    // JSON with comments (tsconfig allows // comments) and extends chains.
    const config = ts.readConfigFile(TSCONFIG_PATH, ts.sys.readFile);
    // parseJsonConfigFileContent resolves include/exclude patterns, extends,
    // and produces the final list of files and compiler options.
    const parsedConfig = ts.parseJsonConfigFileContent(
      config.config,
      ts.sys,
      path.dirname(TSCONFIG_PATH)
    );

    this.projectBasePath = path.dirname(TSCONFIG_PATH);

    // Create the TypeScript program and type checker. The program represents
    // the entire compilation unit; the type checker provides semantic analysis
    // capabilities like resolving types and signatures.
    this.program = ts.createProgram(parsedConfig.fileNames, parsedConfig.options);
    this.checker = this.program.getTypeChecker();
  }

  /**
   * Generates the code map by processing all relevant source files in the project.
   * It iterates through source files, extracts file-level and symbol-level documentation,
   * and populates the internal `result` array with `ProcessedFileDoc` objects.
   * @returns {Array<object>} An array of `ProcessedFileDoc` objects representing the structured code map.
   */
  generate() {
    // Exclude configuration files that are valid TypeScript but not part of
    // the project's API surface. These files pollute documentation output.
    const excludedFiles = ['vite.config.ts', 'jest.config.js'];

    // Iterate through all source files in the TypeScript program.
    // The program includes all files discovered via tsconfig include/exclude patterns.
    for (const sourceFile of this.program.getSourceFiles()) {
      const baseName = path.basename(sourceFile.fileName);
      // Filter out: declaration files (.d.ts), node_modules, and config files.
      // Declaration files are type definitions, not implementation we want to document.
      if (
        !sourceFile.isDeclarationFile &&
        !sourceFile.fileName.includes('node_modules') &&
        !excludedFiles.includes(baseName)
      ) {
        // Normalize path separators for cross-platform consistency
        const relativeFilePath = path
          .relative(this.projectBasePath, sourceFile.fileName)
          .replace(/\\/g, '/');

        // Filter to only files within wsd.checkDirs directories.
        // This ensures documentation scope matches the project's configured source directories.
        if (this.includeDirectories && this.includeDirectories.length > 0) {
          const shouldInclude = this.includeDirectories.some((dir) => {
            const normalizedDir = dir.replace(/\\/g, '/');
            // Match files directly in dir or in subdirectories of dir
            return (
              relativeFilePath.startsWith(normalizedDir + '/') || relativeFilePath === normalizedDir
            );
          });

          if (!shouldInclude) {
            continue;
          }
        }

        const currentFileDoc = {
          filePath: relativeFilePath,
          description: this.extractFileLevelDocComment(sourceFile, relativeFilePath),
          classes: [],
          interfaces: [],
          functions: [],
          enums: [],
          types: [],
          variables: [],
        };

        this.visitSourceFile(sourceFile, currentFileDoc);
        this.result.push(currentFileDoc);
      }
    }
    return this.result;
  }

  /**
   * Traverses the Abstract Syntax Tree (AST) of a given source file to find and process
   * top-level declarations (classes, interfaces, functions, enums, types, variables).
   * Populates the provided `currentFileDoc` with extracted `DocItem`s.
   * @param {object} sourceFile - The `ts.SourceFile` to visit.
   * @param {object} currentFileDoc - The `ProcessedFileDoc` object for the current file, to be populated.
   */
  visitSourceFile(sourceFile, currentFileDoc) {
    // Walk the AST using forEachChild, which visits only direct children.
    // We only process top-level declarations, not nested ones (e.g., class methods
    // are handled within processClass, not here).
    ts.forEachChild(sourceFile, (node) => {
      if (ts.isClassDeclaration(node) && node.name) {
        currentFileDoc.classes.push(this.processClass(node, currentFileDoc.filePath));
      } else if (ts.isInterfaceDeclaration(node) && node.name) {
        currentFileDoc.interfaces.push(this.processInterface(node, currentFileDoc.filePath));
      } else if (ts.isFunctionDeclaration(node) && node.name) {
        currentFileDoc.functions.push(this.processFunction(node, currentFileDoc.filePath));
      } else if (ts.isEnumDeclaration(node) && node.name) {
        currentFileDoc.enums.push(this.processEnum(node, currentFileDoc.filePath));
      } else if (ts.isTypeAliasDeclaration(node) && node.name) {
        currentFileDoc.types.push(this.processTypeAlias(node, currentFileDoc.filePath));
      } else if (ts.isVariableStatement(node)) {
        this.processVariableStatement(node, currentFileDoc);
      }
    });
  }

  /**
   * Processes a `ts.ClassDeclaration` node to extract relevant documentation.
   * @param {object} node - The TypeScript AST node for the class declaration.
   * @param {string} containingFilePath - The path of the file containing this class, relative to project root.
   * @returns {object} A `DocItem` representing the processed class.
   */
  processClass(node, containingFilePath) {
    // Use the type checker to get the symbol for this class declaration.
    // The symbol provides access to the class's members map.
    const symbol = this.checker.getSymbolAtLocation(node.name);
    const members = [];

    // Iterate through class members via the symbol's members map.
    // This gives us all properties and methods declared in the class.
    if (symbol) {
      symbol.members?.forEach((member, _key) => {
        const declarations = member.getDeclarations();
        if (declarations && declarations.length > 0) {
          const declaration = declarations[0];

          // Process methods
          if (ts.isMethodDeclaration(declaration)) {
            members.push(this.processMethod(declaration, containingFilePath));
          }
          // Process properties
          else if (ts.isPropertyDeclaration(declaration)) {
            members.push(this.processProperty(declaration, containingFilePath));
          }
        }
      });
    }

    // Extract modifiers (public, abstract, etc.)
    const modifiers = node.modifiers ? node.modifiers.map((m) => m.getText()) : undefined;

    return {
      name: node.name.getText(),
      kind: 'class',
      description: this.getDocCommentText(node, containingFilePath),
      members,
      modifiers,
    };
  }

  /**
   * Processes a `ts.InterfaceDeclaration` node to extract relevant documentation.
   * @param {object} node - The TypeScript AST node for the interface declaration.
   * @param {string} containingFilePath - The path of the file containing this interface, relative to project root.
   * @returns {object} A `DocItem` representing the processed interface.
   */
  processInterface(node, containingFilePath) {
    const members = [];

    // Process properties and methods
    node.members.forEach((member) => {
      if (ts.isPropertySignature(member) && member.name) {
        members.push({
          name: member.name.getText(),
          kind: 'property',
          description: this.getDocCommentText(member, containingFilePath),
          type: member.type ? member.type.getText() : 'any',
        });
      } else if (ts.isMethodSignature(member) && member.name) {
        members.push(this.processMethodSignature(member, containingFilePath));
      }
    });

    return {
      name: node.name.getText(),
      kind: 'interface',
      description: this.getDocCommentText(node, containingFilePath),
      members,
    };
  }

  /**
   * Processes an array of `ts.ParameterDeclaration` nodes to extract DocItem representations.
   * @param {Array<object>} params - Array of parameter declaration nodes.
   * @param {string} containingFilePath - The path of the file containing these parameters, relative to project root.
   * @returns {Array<object>} An array of `DocItem` objects representing the parameters.
   */
  processParameters(params, containingFilePath) {
    return params.map((param) => ({
      name: param.name.getText(),
      kind: 'parameter',
      description: this.getDocCommentText(param, containingFilePath),
      type: param.type ? param.type.getText() : 'any',
    }));
  }

  /**
   * Processes a `ts.MethodDeclaration` (typically within a class) to extract documentation.
   * @param {object} node - The TypeScript AST node for the method declaration.
   * @param {string} containingFilePath - The path of the file containing this method, relative to project root.
   * @returns {object} A `DocItem` representing the processed method.
   */
  processMethod(node, containingFilePath) {
    const parameters = this.processParameters(node.parameters, containingFilePath);

    // Use the type checker to get the method's call signature, then extract
    // the return type. This provides semantic type information, resolving
    // inferred types and type aliases to their actual types.
    const signature = this.checker.getSignatureFromDeclaration(node);
    const returnType = signature
      ? this.checker.typeToString(this.checker.getReturnTypeOfSignature(signature))
      : 'void';

    // Extract modifiers
    const modifiers = node.modifiers ? node.modifiers.map((m) => m.getText()) : undefined;

    return {
      name: node.name.getText(),
      kind: 'method',
      description: this.getDocCommentText(node, containingFilePath),
      parameters,
      returnType,
      modifiers,
    };
  }

  /**
   * Processes a `ts.MethodSignature` (typically within an interface) to extract documentation.
   * @param {object} node - The TypeScript AST node for the method signature.
   * @param {string} containingFilePath - The path of the file containing this method signature, relative to project root.
   * @returns {object} A `DocItem` representing the processed method signature.
   */
  processMethodSignature(node, containingFilePath) {
    // Process parameters
    const parameters = this.processParameters(node.parameters, containingFilePath);

    return {
      name: node.name.getText(),
      kind: 'method',
      description: this.getDocCommentText(node, containingFilePath),
      parameters,
      returnType: node.type ? node.type.getText() : 'void',
    };
  }

  /**
   * Processes a `ts.PropertyDeclaration` (typically within a class) to extract documentation.
   * @param {object} node - The TypeScript AST node for the property declaration.
   * @param {string} containingFilePath - The path of the file containing this property, relative to project root.
   * @returns {object} A `DocItem` representing the processed property.
   */
  processProperty(node, containingFilePath) {
    // Extract modifiers
    const modifiers = node.modifiers ? node.modifiers.map((m) => m.getText()) : undefined;

    return {
      name: node.name.getText(),
      kind: 'property',
      description: this.getDocCommentText(node, containingFilePath),
      type: node.type ? node.type.getText() : 'any',
      modifiers,
    };
  }

  /**
   * Processes a `ts.FunctionDeclaration` node to extract relevant documentation.
   * @param {object} node - The TypeScript AST node for the function declaration.
   * @param {string} containingFilePath - The path of the file containing this function, relative to project root.
   * @returns {object} A `DocItem` representing the processed function.
   */
  processFunction(node, containingFilePath) {
    // Process parameters
    const parameters = this.processParameters(node.parameters, containingFilePath);

    // Extract return type
    const signature = this.checker.getSignatureFromDeclaration(node);
    const returnType = signature
      ? this.checker.typeToString(this.checker.getReturnTypeOfSignature(signature))
      : 'void';

    // Extract modifiers
    const modifiers = node.modifiers ? node.modifiers.map((m) => m.getText()) : undefined;

    return {
      name: node.name.getText(),
      kind: 'function',
      description: this.getDocCommentText(node, containingFilePath),
      parameters,
      returnType,
      modifiers,
      signature: node.getText().split('{')[0].trim(),
    };
  }

  /**
   * Processes a `ts.EnumDeclaration` node to extract relevant documentation.
   * @param {object} node - The TypeScript AST node for the enum declaration.
   * @param {string} containingFilePath - The path of the file containing this enum, relative to project root.
   * @returns {object} A `DocItem` representing the processed enum.
   */
  processEnum(node, containingFilePath) {
    const members = node.members.map((member) => ({
      name: member.name.getText(),
      kind: 'enum member',
      description: this.getDocCommentText(member, containingFilePath),
      value: member.initializer ? member.initializer.getText() : undefined,
    }));

    return {
      name: node.name.getText(),
      kind: 'enum',
      description: this.getDocCommentText(node, containingFilePath),
      members,
    };
  }

  /**
   * Processes a `ts.TypeAliasDeclaration` node to extract relevant documentation.
   * @param {object} node - The TypeScript AST node for the type alias declaration.
   * @param {string} containingFilePath - The path of the file containing this type alias, relative to project root.
   * @returns {object} A `DocItem` representing the processed type alias.
   */
  processTypeAlias(node, containingFilePath) {
    return {
      name: node.name.getText(),
      kind: 'type',
      description: this.getDocCommentText(node, containingFilePath),
      type: node.type.getText(),
    };
  }

  /**
   * Processes a `ts.VariableStatement` node to extract documentation for its declared variables.
   * Populates `currentFileDoc.variables` with extracted `DocItem`s.
   * @param {object} node - The TypeScript AST node for the variable statement.
   * @param {object} currentFileDoc - The `ProcessedFileDoc` for the current file.
   */
  processVariableStatement(node, currentFileDoc) {
    node.declarationList.declarations.forEach((declaration) => {
      if (declaration.name && ts.isIdentifier(declaration.name)) {
        const modifiers = node.modifiers ? node.modifiers.map((m) => m.getText()) : undefined;

        const docItem = {
          name: declaration.name.getText(),
          kind: 'variable',
          description: this.getDocCommentText(node, currentFileDoc.filePath),
          type: declaration.type ? declaration.type.getText() : 'inferred',
          modifiers,
        };

        currentFileDoc.variables.push(docItem);
      }
    });
  }

  /**
   * Cleans and formats a raw JSDoc comment string.
   * Removes `/**`, `*\/`, and leading asterisks from lines.
   * Resolves relative @link tag paths to be project-root relative.
   * Formats `@see` lines as Markdown list items.
   * @param {string} rawComment - The raw JSDoc comment string.
   * @param {string} containingFilePath - The path of the file containing this JSDoc, relative to project root.
   * @returns {string} The cleaned JSDoc comment string, or an empty string if input is falsy.
   */
  cleanAndFormatJSDoc(rawComment, containingFilePath) {
    if (!rawComment) return '';

    // Strip JSDoc delimiters and leading asterisks from each line.
    // The regex removes the optional leading whitespace, asterisk, and one optional space.
    const lines = rawComment
      .replace(/^\/\*\*/, '')
      .replace(/\*\/$/, '')
      .split('\n')
      .map((line) => line.replace(/^\s*\*\s?/, '').trim());

    const processedLines = lines.map((line) => {
      let processedLine = line;

      // Resolve relative {@link} paths to project-root-relative paths.
      // This ensures links work correctly in consolidated documentation regardless
      // of the original source file's location in the directory structure.
      processedLine = processedLine.replace(/\{@link\s+([^}\s]+)\s*}/g, (match, linkPath) => {
        // Skip URLs, fragment links, and absolute paths - these don't need resolution
        if (
          !linkPath.startsWith('http:') &&
          !linkPath.startsWith('https:') &&
          !linkPath.startsWith('#') &&
          !path.isAbsolute(linkPath)
        ) {
          try {
            // Resolve the relative path from the containing file's directory
            const dirOfContainingFile = path.dirname(containingFilePath);
            const absoluteLinkTarget = path.resolve(
              path.join(this.projectBasePath, dirOfContainingFile),
              linkPath
            );
            // Convert back to project-root-relative for consistent referencing
            const newRelativePath = path
              .relative(this.projectBasePath, absoluteLinkTarget)
              .replace(/\\/g, '/');
            return `{@link ${newRelativePath}}`;
          } catch (e) {
            // If path resolution fails, preserve the original link
            return match;
          }
        }
        return match;
      });

      // Format @see tags as markdown list items for better readability
      if (processedLine.startsWith('@see')) {
        return `- ${processedLine}`;
      }
      return processedLine;
    });

    return processedLines.join('\n').trim();
  }

  /**
   * Extracts the primary file-level JSDoc comment from a source file.
   * It looks for the first leading JSDoc comment that appears before any statements.
   * @param {object} sourceFile - The `ts.SourceFile` to extract the comment from.
   * @param {string} relativeFilePath - The path of the source file, relative to project root.
   * @returns {string} The cleaned file-level JSDoc comment, or an empty string if not found.
   */
  extractFileLevelDocComment(sourceFile, relativeFilePath) {
    let fileCommentText = '';
    const fileContent = sourceFile.getFullText();

    // Get all leading comments at position 0 (start of file).
    // This includes both file-level and first-declaration comments.
    const commentRanges = ts.getLeadingCommentRanges(fileContent, 0);

    if (commentRanges && commentRanges.length > 0) {
      for (const range of commentRanges) {
        const commentText = fileContent.substring(range.pos, range.end);
        // Only process JSDoc-style comments (starting with /**)
        if (commentText.startsWith('/**')) {
          // Determine if this is a file-level comment vs. a declaration comment.
          // File-level comments appear before any statements in the file.
          let isFileLevelComment = sourceFile.statements.length === 0;
          if (sourceFile.statements.length > 0) {
            // Compare comment end position with first statement start.
            // If the comment ends before the first statement starts, it's file-level.
            const firstStatementStart = sourceFile.statements[0].getStart(sourceFile, false);
            if (firstStatementStart >= range.end) {
              isFileLevelComment = true;
            }
          }

          if (isFileLevelComment) {
            fileCommentText = commentText;
            break;
          }
        }
      }
    }

    return this.cleanAndFormatJSDoc(fileCommentText, relativeFilePath);
  }

  /**
   * Extracts and cleans JSDoc comments associated with a given AST node.
   * If multiple JSDoc blocks are present, they are concatenated.
   * @param {object} node - The `ts.Node` to extract JSDoc from.
   * @param {string} containingFilePath - The path of the file containing this node, relative to project root.
   * @returns {string} The cleaned JSDoc string, or an empty string if no JSDoc is found.
   */
  getDocCommentText(node, containingFilePath) {
    // getFullText() includes leading trivia (comments, whitespace) for this node
    const text = node.getFullText();
    const commentRanges = ts.getLeadingCommentRanges(text, 0);

    if (!commentRanges || commentRanges.length === 0) {
      return '';
    }

    // Filter to only JSDoc comments (/** ... */), excluding regular block and line comments.
    // Multiple JSDoc blocks can precede a declaration; we concatenate them all.
    const jsdocComments = commentRanges
      .filter((r) => text.substring(r.pos, r.end).startsWith('/**'))
      .map((r) => {
        const comment = text.substring(r.pos, r.end);
        return this.cleanAndFormatJSDoc(comment, containingFilePath);
      });

    return jsdocComments.join('\n\n');
  }

  /**
   * Converts the generated documentation (an array of `ProcessedFileDoc`) to a structured Markdown string.
   * Includes a Table of Contents, file-level sections with descriptions, and categorized symbols within each file.
   * @returns {string} A string containing the full code map in Markdown format.
   */
  toMarkdown() {
    let md = `# ${TITLE}\n\n`;
    //md += `*Generated on ${new Date().toLocaleString()}*\n\n`;

    // Generate TOC for Files
    md += `## Table of Contents\n\n`;
    this.result.forEach((fileDoc) => {
      const fileSlug = fileDoc.filePath.replace(/[/.]/g, '_').toLowerCase();
      md += `- [\`${fileDoc.filePath}\`](#file-${fileSlug})\n`;
    });
    md += '\n---\n';

    // Process each file
    this.result.forEach((fileDoc) => {
      const fileSlug = fileDoc.filePath.replace(/[/.]/g, '_').toLowerCase();
      md += `\n## File: \`${fileDoc.filePath}\` <a name="file-${fileSlug}"></a>\n\n`;

      if (fileDoc.description) {
        md += `${fileDoc.description}\n\n`;
      }

      // Classes in this file
      if (fileDoc.classes.length > 0) {
        md += `### Classes\n\n`;
        fileDoc.classes
          .sort((a, b) => a.name.localeCompare(b.name))
          .forEach((cls) => {
            md += this.classToMarkdown(cls);
          });
      }

      // Interfaces in this file
      if (fileDoc.interfaces.length > 0) {
        md += `### Interfaces\n\n`;
        fileDoc.interfaces
          .sort((a, b) => a.name.localeCompare(b.name))
          .forEach((iface) => {
            md += this.interfaceToMarkdown(iface);
          });
      }

      // Functions in this file
      if (fileDoc.functions.length > 0) {
        md += `### Functions\n\n`;
        fileDoc.functions
          .sort((a, b) => a.name.localeCompare(b.name))
          .forEach((func) => {
            md += this.functionToMarkdown(func);
          });
      }

      // Enums in this file
      if (fileDoc.enums.length > 0) {
        md += `### Enums\n\n`;
        fileDoc.enums
          .sort((a, b) => a.name.localeCompare(b.name))
          .forEach((enumItem) => {
            md += this.enumToMarkdown(enumItem);
          });
      }

      // Types in this file
      if (fileDoc.types.length > 0) {
        md += `### Types\n\n`;
        fileDoc.types
          .sort((a, b) => a.name.localeCompare(b.name))
          .forEach((typeItem) => {
            md += this.typeToMarkdown(typeItem);
          });
      }

      // Variables in this file
      if (fileDoc.variables.length > 0) {
        md += `### Variables\n\n`;
        fileDoc.variables
          .sort((a, b) => a.name.localeCompare(b.name))
          .forEach((varItem) => {
            md += this.variableToMarkdown(varItem);
          });
      }
      md += '\n---\n'; // Separator between files
    });

    return md;
  }

  /**
   * Converts a class `DocItem` to its Markdown representation.
   * @param {object} cls - The `DocItem` for the class.
   * @returns {string} Markdown string for the class.
   */
  classToMarkdown(cls) {
    let md = `#### ${cls.name}\n\n`; // Changed to H4 for better nesting under file sections

    if (cls.modifiers && cls.modifiers.length > 0) {
      md += `*${cls.modifiers.join(' ')}*\n\n`;
    }

    if (cls.description) {
      md += `${cls.description}\n\n`;
    }

    const properties = cls.members?.filter((m) => m.kind === 'property') || [];
    if (properties.length > 0) {
      md += `**Properties**:
`;
      properties.forEach((prop) => {
        const modifiers = prop.modifiers ? `${prop.modifiers.join(' ')} ` : '';
        md += `- **${prop.name}**: \`${prop.type}\` ${modifiers}\n`;
        if (prop.description) {
          md += `  - ${prop.description.replace(/\\n/g, '\\n  ')}\n`; // Indent description
        }
      });
      md += '\n';
    }

    const methods = cls.members?.filter((m) => m.kind === 'method') || [];
    if (methods.length > 0) {
      md += `**Methods**:
`;
      methods.forEach((method) => {
        const modifiers = method.modifiers ? `${method.modifiers.join(' ')} ` : '';
        const params = method.parameters?.map((p) => `${p.name}: ${p.type}`).join(', ') || '';
        md += `- **${method.name}**(${params}) => \`${method.returnType}\` ${modifiers}\n`;
        if (method.description) {
          md += `  - ${method.description.replace(/\\n/g, '\\n  ')}\n`; // Indent description
        }
      });
      md += '\n';
    }
    return md;
  }

  /**
   * Converts an interface `DocItem` to its Markdown representation.
   * @param {object} iface - The `DocItem` for the interface.
   * @returns {string} Markdown string for the interface.
   */
  interfaceToMarkdown(iface) {
    let md = `#### ${iface.name}\n\n`; // Changed to H4

    if (iface.description) {
      md += `${iface.description}\n\n`;
    }

    const properties = iface.members?.filter((m) => m.kind === 'property') || [];
    if (properties.length > 0) {
      md += `**Properties**:
`;
      properties.forEach((prop) => {
        md += `- **${prop.name}**: \`${prop.type}\`\n`;
        if (prop.description) {
          md += `  - ${prop.description.replace(/\\n/g, '\\n  ')}\n`;
        }
      });
      md += '\n';
    }

    const methods = iface.members?.filter((m) => m.kind === 'method') || [];
    if (methods.length > 0) {
      md += `**Methods**:
`;
      methods.forEach((method) => {
        const params = method.parameters?.map((p) => `${p.name}: ${p.type}`).join(', ') || '';
        md += `- **${method.name}**(${params}) => \`${method.returnType}\`\n`;
        if (method.description) {
          md += `  - ${method.description.replace(/\\n/g, '\\n  ')}\n`;
        }
      });
      md += '\n';
    }
    return md;
  }

  /**
   * Converts a function `DocItem` to its Markdown representation.
   * @param {object} func - The `DocItem` for the function.
   * @returns {string} Markdown string for the function.
   */
  functionToMarkdown(func) {
    let md = `#### ${func.name}\n\n`; // Changed to H4

    if (func.modifiers && func.modifiers.length > 0) {
      md += `*${func.modifiers.join(' ')}*\n\n`;
    }

    if (func.description) {
      md += `${func.description}\n\n`;
    }

    if (func.signature) {
      md += `**Signature**: \`${func.signature.replace(/\s*{\s*$/, '')}\`\n\n`; // Remove trailing brace if present
    } else {
      const params = func.parameters?.map((p) => `${p.name}: ${p.type}`).join(', ') || '';
      md += `**Signature**: \`${func.name}(${params}) => ${func.returnType}\`\n\n`;
    }
    return md;
  }

  /**
   * Converts an enum `DocItem` to its Markdown representation.
   * @param {object} enumItem - The `DocItem` for the enum.
   * @returns {string} Markdown string for the enum.
   */
  enumToMarkdown(enumItem) {
    let md = `#### ${enumItem.name}\n\n`; // Changed to H4

    if (enumItem.description) {
      md += `${enumItem.description}\n\n`;
    }

    enumItem.members?.forEach((member) => {
      md += `- **${member.name}**`;
      if (member.value !== undefined) {
        // Check for undefined explicitly
        md += ` = \`${member.value}\``;
      }
      md += '\n';

      if (member.description) {
        md += `  - ${member.description.replace(/\\n/g, '\\n  ')}\n`;
      }
    });
    md += '\n';
    return md;
  }

  /**
   * Converts a type alias `DocItem` to its Markdown representation.
   * @param {object} typeItem - The `DocItem` for the type alias.
   * @returns {string} Markdown string for the type alias.
   */
  typeToMarkdown(typeItem) {
    let md = `#### ${typeItem.name}\n\n`; // Changed to H4

    if (typeItem.description) {
      md += `${typeItem.description}\n\n`;
    }

    md += `\`\`\`typescript
type ${typeItem.name} = ${typeItem.type};
\`\`\`\n\n`;
    return md;
  }

  /**
   * Converts a variable `DocItem` to its Markdown representation.
   * @param {object} varItem - The `DocItem` for the variable.
   * @returns {string} Markdown string for the variable.
   */
  variableToMarkdown(varItem) {
    let md = `#### ${varItem.name}\n\n`; // Changed to H4

    if (varItem.modifiers && varItem.modifiers.length > 0) {
      md += `*${varItem.modifiers.join(' ')}*\n\n`;
    }

    if (varItem.description) {
      md += `${varItem.description}\n\n`;
    }

    md += `**Type**: \`${varItem.type}\`\n\n`;
    return md;
  }
}

/**
 * Main function to generate the TypeScript code map.
 *
 * Reads configuration from package.json (wsd.checkDirs) and tsconfig.json,
 * then generates a markdown code map at docs/reports/TypeScript-Code-Map.md.
 *
 * Detects project language and exits gracefully for JavaScript-only projects,
 * since the TypeScript Compiler API requires TypeScript source files.
 */
async function main() {
  // Check for configured source directories first
  const checkDirs = getCheckDirs();
  if (checkDirs.length === 0) {
    console.log('Skipping TypeScript code map: no source directories configured.');
    return;
  }

  // Detect project languages - this tool requires TypeScript
  const languages = detectProjectLanguages();

  if (!languages.includes('typescript')) {
    console.log('');
    console.log('Code Map Generator: Skipping - TypeScript project required');
    console.log('');
    console.log('This tool uses the TypeScript Compiler API to analyze .ts files and');
    console.log('generate comprehensive code documentation. It requires TypeScript');
    console.log('source files to function properly.');
    console.log('');
    if (languages.includes('javascript')) {
      console.log('Detected: JavaScript-only project (no .ts files found)');
      console.log('');
      console.log('For JavaScript projects, consider using JSDoc comments in your source');
      console.log('files and a documentation tool like JSDoc or documentation.js instead.');
    } else {
      console.log('Detected: No package.json found or unable to determine project type.');
    }
    console.log('');
    return;
  }

  console.log('Generating TypeScript code map...');

  const generator = new CodeMapGenerator(checkDirs);

  // Log the directories being processed
  console.log(`Filtering to directories: ${generator.includeDirectories.join(', ')}`);

  generator.generate();
  const markdown = generator.toMarkdown();

  // Ensure output directory exists
  const outputDir = path.dirname(OUTPUT_PATH);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  fs.writeFileSync(OUTPUT_PATH, markdown);
  console.log(`Code map written to ${path.relative(PROJECT_ROOT, OUTPUT_PATH)}`);
}

// Run main() only when executed directly, not when required as a module
if (require.main === module) {
  main().catch((error) => {
    console.error('Error generating code map:', error);
    process.exit(1);
  });
}

// Export for testing
module.exports = { CodeMapGenerator, main };
