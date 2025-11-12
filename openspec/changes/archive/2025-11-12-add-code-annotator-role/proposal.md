# Change: Add CodeAnnotator Role

## Why
The system currently lacks a dedicated role for adding comprehensive code annotations and documentation comments to source files. This limits code maintainability, understanding, and onboarding efficiency for new developers working with the codebase.

## What Changes
- Add a new `CodeAnnotator` role to the MetaGPT role ecosystem
- Implement action to analyze and annotate single files with comprehensive comments
- Implement action to process all files in a directory recursively
- Support multiple programming languages:
  - Python (docstrings)
  - JavaScript/TypeScript (JSDoc)
  - Java (JavaDoc)
  - C/C++ (Doxygen-style)
  - Shell/Bash (comment blocks)
  - Go, Rust, and other common languages
- Generate annotations that explain:
  - Function/method purposes and behavior
  - Parameter meanings and constraints
  - Return value descriptions
  - Complex logic explanations
  - Class and module-level documentation
- Output handling:
  - Single file: Create new file with `.annotated` suffix in same directory
  - Directory: Create new parallel directory with `_annotated` suffix preserving structure
- Standalone execution:
  - Can be initialized and run independently
  - Driven by test scripts or direct instantiation
  - No dependency on full MetaGPT team workflow

## Impact
- Affected specs: NEW capability `code-annotation`
- Affected code:
  - New role: `metagpt/roles/code_annotator.py`
  - New actions: `metagpt/actions/annotate_code.py`
  - Role registration: `metagpt/roles/__init__.py`
  - Example script: `examples/annotate_code.py`
  - Test script: `tests/metagpt/roles/test_code_annotator.py`
- Dependencies:
  - Leverages existing LLM integration
  - Uses existing file I/O utilities
  - Follows existing role/action patterns from Engineer, QAEngineer roles
- Output files:
  - Single file mode: Creates `<filename>.annotated.<ext>` in source directory
  - Directory mode: Creates `<dirname>_annotated/` with mirrored structure
