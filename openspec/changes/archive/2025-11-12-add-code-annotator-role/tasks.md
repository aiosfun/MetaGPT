## 1. Implementation

### 1.1 Create AnnotateCode Action
- [ ] 1.1.1 Create `metagpt/actions/annotate_code.py`
- [ ] 1.1.2 Implement language detection from file extension (support .py, .js, .ts, .java, .c, .cpp, .h, .hpp, .sh, .bash, .go, .rs)
- [ ] 1.1.3 Create language-specific annotation prompt templates:
  - [ ] Python (PEP 257 docstrings)
  - [ ] JavaScript/TypeScript (JSDoc)
  - [ ] Java (JavaDoc)
  - [ ] C/C++ (Doxygen)
  - [ ] Shell/Bash (comment blocks)
  - [ ] Go (standard Go comments)
  - [ ] Rust (/// doc comments)
- [ ] 1.1.4 Implement token estimation utility (1 token ≈ 4 characters)
- [ ] 1.1.5 Implement LLM context limit detection:
  - [ ] Support Ollama models (e.g., qwen2.5-coder:7b with 32,768 context)
  - [ ] Support OpenAI models (various context limits)
  - [ ] Support other providers (Claude, etc.)
  - [ ] Allow manual context limit override
- [ ] 1.1.6 Implement semantic code chunking:
  - [ ] Python AST-based chunking (using built-in `ast` module)
  - [ ] Regex-based chunking for other languages (detect function/class boundaries)
  - [ ] Preserve imports and module context in each chunk
  - [ ] Add configurable chunk overlap (default 200 tokens)
- [ ] 1.1.7 Implement chunk reassembly logic to merge annotated chunks
- [ ] 1.1.8 Implement single file annotation logic with `.annotated` suffix output
- [ ] 1.1.9 Implement directory traversal and batch annotation logic
- [ ] 1.1.10 Implement output directory creation with `_annotated` suffix
- [ ] 1.1.11 Add error handling for invalid paths and unsupported file types
- [ ] 1.1.12 Add logic to handle existing output file conflicts

### 1.2 Create CodeAnnotator Role
- [ ] 1.2.1 Create `metagpt/roles/code_annotator.py`
- [ ] 1.2.2 Extend from base `Role` class
- [ ] 1.2.3 Configure role with AnnotateCode action
- [ ] 1.2.4 Set appropriate role profile, goal, and constraints
- [ ] 1.2.5 Implement `_act` method to execute annotation action
- [ ] 1.2.6 Add support for both single file and directory inputs
- [ ] 1.2.7 Ensure role can be instantiated standalone (without team/environment context)
- [ ] 1.2.8 Implement `run()` method to accept file or directory path directly

### 1.3 Integration
- [ ] 1.3.1 Register CodeAnnotator in `metagpt/roles/__init__.py`
- [ ] 1.3.2 Ensure compatibility with existing role patterns
- [ ] 1.3.3 Verify LLM provider integration works correctly

## 2. Testing

### 2.1 Unit Tests
- [ ] 2.1.1 Create `tests/metagpt/actions/test_annotate_code.py`
- [ ] 2.1.2 Test language detection for Python, JavaScript, TypeScript, Java, C/C++, Shell, Go, Rust
- [ ] 2.1.3 Test token estimation accuracy
- [ ] 2.1.4 Test LLM context limit detection for various models
- [ ] 2.1.5 Test chunking logic:
  - [ ] Small files (no chunking needed)
  - [ ] Medium files (2-3 chunks)
  - [ ] Large files (many chunks)
  - [ ] Semantic boundary detection (functions, classes)
- [ ] 2.1.6 Test chunk reassembly and syntax preservation
- [ ] 2.1.7 Test single file annotation with mock LLM responses
- [ ] 2.1.8 Test output file naming (`.annotated` suffix)
- [ ] 2.1.9 Test directory traversal logic
- [ ] 2.1.10 Test directory structure preservation in `_annotated` output
- [ ] 2.1.11 Test error handling for invalid paths
- [ ] 2.1.12 Test error handling for unsupported file types
- [ ] 2.1.13 Test handling of existing output file conflicts

### 2.2 Role Tests
- [ ] 2.2.1 Create `tests/metagpt/roles/test_code_annotator.py`
- [ ] 2.2.2 Test role initialization
- [ ] 2.2.3 Test standalone role instantiation (without team context)
- [ ] 2.2.4 Test role execution with single file input
- [ ] 2.2.5 Test role execution with directory input
- [ ] 2.2.6 Test integration with message passing
- [ ] 2.2.7 Create standalone test script that demonstrates direct usage

### 2.3 Integration Tests
- [ ] 2.3.1 Test end-to-end annotation on real sample files
- [ ] 2.3.2 Verify generated annotations follow language conventions for all supported languages
- [ ] 2.3.3 Test with Python, JavaScript, Java, C/C++, Shell, Go, Rust files
- [ ] 2.3.4 Test with Ollama local LLM (qwen2.5-coder:7b):
  - [ ] Small files (< 20k tokens)
  - [ ] Large files requiring chunking (> 30k tokens)
  - [ ] Verify chunk quality and reassembly
- [ ] 2.3.5 Test with cloud LLMs (GPT-4, Claude) for comparison
- [ ] 2.3.6 Verify output file/directory structure is correct
- [ ] 2.3.7 Test large directory processing performance
- [ ] 2.3.8 Benchmark: Annotate 10 files of varying sizes and review quality

## 3. Documentation

### 3.1 Code Documentation
- [ ] 3.1.1 Add docstrings to all public methods in AnnotateCode action
- [ ] 3.1.2 Add docstrings to CodeAnnotator role class
- [ ] 3.1.3 Add inline comments for complex logic

### 3.2 Usage Examples
- [ ] 3.2.1 Create example script in `examples/annotate_code.py` demonstrating:
  - [ ] Single file annotation
  - [ ] Directory annotation
  - [ ] Standalone role instantiation
  - [ ] Different language examples
  - [ ] Ollama local LLM configuration
  - [ ] Handling large files with chunking
- [ ] 3.2.2 Create test driver script for quick testing
- [ ] 3.2.3 Add README section or tutorial showing how to use CodeAnnotator
- [ ] 3.2.4 Document output file/directory naming conventions
- [ ] 3.2.5 Document chunking strategy and when it applies
- [ ] 3.2.6 Document recommended models and context limits

## 4. Validation
- [ ] 4.1 Run all tests and ensure they pass
- [ ] 4.2 Test with different LLM providers:
  - [ ] Ollama (qwen2.5-coder:7b, deepseek-coder)
  - [ ] OpenAI (GPT-4, GPT-3.5)
  - [ ] Anthropic (Claude)
- [ ] 4.3 Verify chunking works correctly with 32,768 token context limit
- [ ] 4.4 Verify no regression in existing roles
- [ ] 4.5 Performance check for large directories (100+ files)
- [ ] 4.6 Quality check: Manual review of 10 annotated files for accuracy
