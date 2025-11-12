## ADDED Requirements

### Requirement: Code Annotation Role
The system SHALL provide a CodeAnnotator role that automatically analyzes and adds comprehensive documentation comments to source code files.

#### Scenario: Single file annotation
- **WHEN** a user requests annotation for a specific file path
- **THEN** the CodeAnnotator SHALL analyze the file structure, functions, classes, and logic
- **AND** generate appropriate documentation comments following language-specific conventions
- **AND** create a new file with `.annotated` suffix before the extension in the same directory
- **AND** preserve the original file unmodified

#### Scenario: Directory annotation
- **WHEN** a user requests annotation for a directory path
- **THEN** the CodeAnnotator SHALL recursively discover all source code files in the directory
- **AND** annotate each file individually
- **AND** create a new directory with `_annotated` suffix
- **AND** preserve the exact directory structure within the new annotated directory
- **AND** leave the original directory unmodified

#### Scenario: Python annotation formatting
- **WHEN** annotating Python files (.py)
- **THEN** the CodeAnnotator SHALL use docstring format (triple quotes) for functions, classes, and modules
- **AND** follow PEP 257 docstring conventions

#### Scenario: JavaScript/TypeScript annotation formatting
- **WHEN** annotating JavaScript (.js) or TypeScript (.ts) files
- **THEN** the CodeAnnotator SHALL use JSDoc comment format with appropriate tags (@param, @returns, @throws)

#### Scenario: Java annotation formatting
- **WHEN** annotating Java files (.java)
- **THEN** the CodeAnnotator SHALL use JavaDoc comment format with appropriate tags
- **AND** include @param, @return, @throws annotations

#### Scenario: C/C++ annotation formatting
- **WHEN** annotating C (.c, .h) or C++ (.cpp, .hpp, .cc) files
- **THEN** the CodeAnnotator SHALL use Doxygen-style comments with @brief, @param, @return tags

#### Scenario: Shell script annotation formatting
- **WHEN** annotating shell scripts (.sh, .bash)
- **THEN** the CodeAnnotator SHALL use hash-based comment blocks
- **AND** include function descriptions, parameter explanations, and return value documentation

#### Scenario: Go annotation formatting
- **WHEN** annotating Go files (.go)
- **THEN** the CodeAnnotator SHALL use standard Go comment format above declarations

#### Scenario: Rust annotation formatting
- **WHEN** annotating Rust files (.rs)
- **THEN** the CodeAnnotator SHALL use Rust doc comments (///) with markdown formatting

### Requirement: Annotation Quality
The CodeAnnotator SHALL generate annotations that are clear, accurate, and maintainable.

#### Scenario: Function documentation
- **WHEN** annotating a function or method
- **THEN** the annotation SHALL include:
  - A concise description of the function's purpose
  - Description of each parameter including type and constraints
  - Description of return value including type
  - Any exceptions or errors that may be raised
  - Usage examples for complex functions

#### Scenario: Class documentation
- **WHEN** annotating a class
- **THEN** the annotation SHALL include:
  - A description of the class's purpose and responsibility
  - Description of key attributes
  - Usage examples if the class has a non-trivial interface

#### Scenario: Complex logic documentation
- **WHEN** encountering complex algorithms or non-obvious logic
- **THEN** the CodeAnnotator SHALL add inline comments explaining:
  - The purpose of the logic block
  - Key steps in the algorithm
  - Any edge cases being handled

### Requirement: Action Integration
The CodeAnnotator role SHALL integrate with the existing MetaGPT action framework.

#### Scenario: Action execution
- **WHEN** the CodeAnnotator role is instantiated
- **THEN** it SHALL have an AnnotateCode action available
- **WHEN** the AnnotateCode action is invoked with a file path
- **THEN** it SHALL return the annotated code as an ActionOutput

#### Scenario: File handling
- **WHEN** processing files
- **THEN** the CodeAnnotator SHALL:
  - Read source files using the existing file utilities
  - Detect the programming language from file extension
  - Generate annotations using LLM integration
  - Return formatted output without modifying the original file (unless explicitly requested)

### Requirement: Error Handling
The CodeAnnotator SHALL handle errors gracefully and provide meaningful feedback.

#### Scenario: Invalid file path
- **WHEN** a non-existent file path is provided
- **THEN** the CodeAnnotator SHALL return an error message indicating the file was not found

#### Scenario: Unsupported file type
- **WHEN** a file with an unsupported extension is provided
- **THEN** the CodeAnnotator SHALL return a message indicating the file type is not supported for annotation

#### Scenario: LLM failure
- **WHEN** the LLM fails to generate annotations
- **THEN** the CodeAnnotator SHALL return an error message with diagnostic information
- **AND** SHALL NOT corrupt or modify the original source code

### Requirement: Standalone Execution
The CodeAnnotator role SHALL support standalone execution independent of full team workflows.

#### Scenario: Direct instantiation
- **WHEN** a user instantiates CodeAnnotator directly in a script
- **THEN** the role SHALL initialize successfully without requiring a team or environment context
- **AND** SHALL be executable via the `run()` method with file or directory path as input

#### Scenario: Test script execution
- **WHEN** a test script invokes CodeAnnotator with a file path
- **THEN** the CodeAnnotator SHALL process the file and generate output
- **AND** return results that can be verified programmatically

#### Scenario: Example script usage
- **WHEN** the example script `examples/annotate_code.py` is executed
- **THEN** it SHALL demonstrate:
  - Single file annotation
  - Directory annotation
  - Different language file processing
  - Error handling scenarios

### Requirement: Output File Management
The CodeAnnotator SHALL manage output files to avoid overwriting original source code.

#### Scenario: Single file output naming
- **WHEN** annotating a file named `example.py`
- **THEN** the output file SHALL be named `example.annotated.py`
- **AND** SHALL be created in the same directory as the source file

#### Scenario: Directory output structure
- **WHEN** annotating a directory named `src/`
- **THEN** a new directory `src_annotated/` SHALL be created
- **AND** SHALL contain the same subdirectory structure as `src/`
- **AND** each annotated file SHALL retain its original name (not include `.annotated` suffix)

#### Scenario: Output file conflict
- **WHEN** an annotated output file already exists
- **THEN** the CodeAnnotator SHALL either:
  - Overwrite with confirmation, or
  - Append a timestamp/version suffix to avoid overwriting
  - Log a warning about the existing file

### Requirement: Large File Handling and Chunking
The CodeAnnotator SHALL handle files that exceed the LLM's context window through intelligent chunking.

#### Scenario: Token estimation
- **WHEN** processing any file
- **THEN** the CodeAnnotator SHALL estimate the token count of the file content
- **AND** compare it against the configured LLM context limit

#### Scenario: Small file processing
- **WHEN** a file is estimated to be under 75% of the LLM context limit
- **THEN** the CodeAnnotator SHALL process the entire file in a single LLM call

#### Scenario: Large file chunking
- **WHEN** a file exceeds 75% of the LLM context limit
- **THEN** the CodeAnnotator SHALL:
  - Split the file into semantic chunks at function or class boundaries
  - Preserve imports and module-level context in each chunk
  - Process each chunk independently with the LLM
  - Reassemble the annotated chunks into a complete file

#### Scenario: Semantic boundary detection
- **WHEN** chunking a file
- **THEN** the CodeAnnotator SHALL split at natural code boundaries such as:
  - Function definitions
  - Class definitions
  - Module boundaries
- **AND** SHALL NOT split in the middle of functions or complex expressions

#### Scenario: Context preservation across chunks
- **WHEN** processing chunks of a large file
- **THEN** each chunk SHALL include:
  - Import statements from the original file
  - Module-level docstring context (if present)
  - Optional: Small overlap with previous chunk for continuity

#### Scenario: Chunk reassembly
- **WHEN** all chunks have been annotated
- **THEN** the CodeAnnotator SHALL:
  - Merge chunks back into a single file
  - Preserve the original line structure and formatting
  - Ensure the reassembled file is syntactically valid

### Requirement: LLM Provider Support
The CodeAnnotator SHALL support multiple LLM providers including local models with limited context.

#### Scenario: Ollama local LLM support
- **WHEN** configured with an Ollama provider (e.g., qwen2.5-coder:7b)
- **THEN** the CodeAnnotator SHALL:
  - Detect the model's context length (e.g., 32,768 tokens)
  - Use 75% of context length as safe limit for code input (e.g., 24,576 tokens)
  - Apply chunking strategy for files exceeding this limit

#### Scenario: Cloud LLM support
- **WHEN** configured with cloud providers (OpenAI, Anthropic, etc.)
- **THEN** the CodeAnnotator SHALL:
  - Use provider-specific context limits (e.g., 128k for GPT-4, 200k for Claude)
  - Optimize chunk sizes based on available context

#### Scenario: Context limit configuration
- **WHEN** the LLM model is specified in configuration
- **THEN** the CodeAnnotator SHALL automatically determine the appropriate context limit
- **AND** allow manual override via configuration parameter if needed

#### Scenario: Token estimation strategy
- **WHEN** estimating tokens for chunking decisions
- **THEN** the CodeAnnotator SHALL use a conservative estimation (e.g., 1 token ≈ 4 characters for code)
- **AND** include buffer for prompt templates and output generation
