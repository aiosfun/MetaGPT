# Design: CodeAnnotator Role

## Context

The CodeAnnotator role needs to support both cloud-based LLMs (OpenAI, Anthropic) and local LLMs (Ollama with models like qwen2.5-coder:7b). Local models have significant context length limitations:

- **Ollama qwen2.5-coder:7b**: 32,768 tokens context length
- **Typical large files**: Can easily exceed 10,000+ lines (50,000+ tokens)
- **Challenge**: How to annotate files that exceed the model's context window

Additionally, the system must preserve original source files, generate language-specific documentation, and support standalone execution.

## Goals / Non-Goals

### Goals
- Support both cloud LLMs (unlimited context) and local LLMs (limited context)
- Handle files larger than LLM context window through intelligent chunking
- Generate high-quality, language-specific annotations
- Preserve original files and create separate annotated versions
- Enable standalone execution without full MetaGPT team workflow
- Support 7+ programming languages with appropriate documentation styles

### Non-Goals
- Real-time streaming annotation (batch processing is acceptable)
- Modifying original source files in-place
- Training or fine-tuning custom models
- Supporting every programming language (focus on mainstream languages)
- GUI interface (CLI/script-based execution only)

## Decisions

### Decision 1: Chunking Strategy for Large Files

**Problem**: Files may exceed LLM context length (e.g., 32,768 tokens for qwen2.5-coder:7b)

**Solution**: Implement semantic code chunking with context preservation

**Approach**:
1. **Token Estimation**: Estimate tokens using simple heuristic (1 token ≈ 4 characters for code)
2. **Semantic Boundaries**: Split at natural code boundaries (function/class definitions, not mid-function)
3. **Context Window**: Reserve 25% of context for prompts/output (e.g., 24,000 tokens for code input)
4. **Chunk Strategy**:
   - **Small files** (<20k tokens): Process entire file in one pass
   - **Medium files** (20k-60k tokens): Split into 2-3 chunks at class/function boundaries
   - **Large files** (>60k tokens): Process function-by-function or class-by-class
5. **Reassembly**: Merge annotated chunks back into complete file

**Chunking Algorithm**:
```python
def chunk_code(file_content, language, max_tokens=24000):
    # Parse code into AST (Abstract Syntax Tree)
    # Identify top-level structures: classes, functions, modules
    # Group structures to fit within token limit
    # Preserve imports and module-level docstrings in each chunk
    # Return list of chunks with line number mappings
```

**Alternatives Considered**:
- **Naive line-based splitting**: Rejected - breaks code semantics, produces poor annotations
- **Sliding window**: Rejected - creates redundant processing and inconsistent annotations
- **Multiple model calls per function**: Rejected - too slow and expensive

### Decision 2: LLM Configuration Reuse

**Problem**: Need to know LLM context limits for chunking decisions

**Solution**: Reuse existing MetaGPT LLM configuration from `config2.yaml`

**Implementation**:
- Read LLM settings from MetaGPT's `config2.yaml` (api_type, model, base_url, etc.)
- Assume all LLMs have context limitations requiring chunking support
- Define minimum assumed context length: 32,768 tokens (based on qwen2.5-coder:7b)
- Use 75% of assumed context as safe limit: 24,576 tokens for code input
- Reserve 25% for prompts, output, and safety buffer

**Rationale**:
- Chunking works universally for both local LLMs (Ollama) and cloud LLMs (OpenAI, Claude)
- Cloud LLMs also have context limits (GPT-4: 128k, Claude: 200k, but still finite)
- Conservative chunking strategy ensures compatibility with any LLM provider
- No need for provider-specific detection logic - chunking auto-adapts
- Simpler implementation and maintenance

**Configuration Example** (`config2.yaml`):
```yaml
llm:
  api_type: "ollama"
  model: "qwen2.5-coder:7b"
  base_url: "http://localhost:11434"
  # CodeAnnotator automatically uses 75% of 32,768 = ~24,576 tokens
```

### Decision 3: Language-Specific Prompt Templates

**Problem**: Different languages require different documentation formats

**Solution**: Create templated prompts per language with examples

**Template Structure**:
```python
ANNOTATION_PROMPTS = {
    "python": """
Analyze this Python code and add comprehensive docstrings following PEP 257.
- Add module-level docstring at the top
- Add class docstrings describing purpose and attributes
- Add function docstrings with Args, Returns, Raises sections
- Add inline comments for complex logic
...
""",
    "java": """
Analyze this Java code and add JavaDoc comments.
- Add class-level JavaDoc with @author, description
- Add method JavaDoc with @param, @return, @throws
...
""",
    # ... other languages
}
```

### Decision 4: Output File Management

**Problem**: Need to create annotated files without overwriting originals

**Solution**: 
- **Single file**: `example.py` → `example.annotated.py` (same directory)
- **Directory**: `src/` → `src_annotated/` (parallel directory, mirrored structure)

**Conflict Handling**:
- Check if output file/directory exists
- Log warning and overwrite by default
- Optional: Add `--no-overwrite` flag to append timestamp suffix

### Decision 5: AST Parsing for Semantic Chunking

**Problem**: Need to split code at semantic boundaries

**Solution**: Use language-specific AST parsers

**Implementation**:
```python
AST_PARSERS = {
    "python": ast.parse,  # Built-in Python AST
    "javascript": esprima.parse,  # Install esprima-python
    "java": javalang.parse,  # Install javalang
    "cpp": pycparser.parse,  # Limited C/C++ support
    # Fallback: regex-based splitting for unsupported languages
}
```

**Fallback Strategy**: If AST parsing fails, use regex to detect function/class patterns

## Risks / Trade-offs

### Risk 1: Chunking Quality
- **Risk**: Semantic chunking may miss cross-function dependencies
- **Mitigation**: 
  - Include imports/module context in each chunk
  - Add overlap between chunks (last class of chunk N in chunk N+1 context)
  - Manual review of annotated output recommended

### Risk 2: Conservative Context Limit
- **Risk**: Assuming 32,768 token limit may underutilize larger context LLMs (GPT-4, Claude)
- **Mitigation**:
  - Chunking is still efficient - larger context means fewer chunks
  - Better to be conservative and work universally than optimize per-model
  - Future enhancement: Optional context limit override parameter

### Risk 3: Performance on Large Codebases
- **Risk**: Annotating large directories may take significant time
- **Mitigation**:
  - Add progress logging for each file
  - Support parallel processing (optional, future enhancement)
  - Allow users to filter by file patterns

### Risk 4: AST Parser Dependencies
- **Risk**: Adding AST parsers for multiple languages increases dependencies
- **Mitigation**:
  - Make language-specific parsers optional dependencies
  - Fallback to regex-based splitting if parser unavailable
  - Document which languages have full AST support

## Migration Plan

**Initial Implementation (v1)**:
1. Support Python with full AST-based chunking
2. Support JavaScript/TypeScript with regex-based chunking
3. Test with qwen2.5-coder:7b and GPT-4

**Future Enhancements (v2+)**:
1. Add AST support for Java, C/C++
2. Implement parallel processing for directories
3. Add incremental annotation (only re-annotate changed functions)
4. Support configuration file for chunk size, overlap settings

## Open Questions

1. **Q: Should we support in-place annotation (modify original files)?**
   - **A**: No for v1. Too risky. Keep as future optional flag with explicit confirmation.

2. **Q: What should be the default chunk overlap size?**
   - **A**: Start with 200 tokens (approximately one function). Make configurable later.

3. **Q: Should we cache LLM responses to avoid re-annotating unchanged code?**
   - **A**: Not in v1. Add in v2 if performance becomes an issue.

4. **Q: How do we handle syntax errors in source files?**
   - **A**: Skip annotation and log error. Don't fail entire directory processing.

## Implementation Notes

### Key Components

1. **TokenEstimator**: Estimates token count for code chunks
2. **CodeChunker**: Splits code into semantic chunks based on AST or regex
3. **AnnotationPromptBuilder**: Builds language-specific prompts
4. **ChunkReassembler**: Merges annotated chunks back into complete files
5. **OutputFileManager**: Handles output file/directory creation and naming

### Configuration Example

```python
# CodeAnnotator uses LLM config from MetaGPT's config2.yaml
# No need to specify context limits - assumes minimum 32,768 tokens

annotator = CodeAnnotator()

await annotator.run(
    input_path="src/my_project.py",
    output_path=None  # Auto-generate: src/my_project.annotated.py
)
```

**config2.yaml**:
```yaml
llm:
  api_type: "ollama"
  model: "qwen2.5-coder:7b"
  base_url: "http://localhost:11434"
  # CodeAnnotator automatically chunks for 32,768 token context
```

### Testing Strategy

1. **Unit tests**: Test chunking with files of various sizes (1k, 10k, 50k+ lines)
2. **Integration tests**: Test with actual Ollama qwen2.5-coder:7b model
3. **Benchmark**: Measure annotation quality (manual review of 10 sample files)
4. **Performance**: Test directory with 100+ files, measure total time

## Technical Dependencies

- **Existing**: MetaGPT LLM integration, file I/O utilities
- **New (required)**: None (use regex-based chunking as baseline)
- **New (optional)**: 
  - `esprima-python` for JavaScript AST parsing
  - `javalang` for Java AST parsing
  - `pycparser` for C/C++ parsing (limited)

## Success Criteria

1. Successfully annotate Python files up to 100k tokens with qwen2.5-coder:7b
2. Generated annotations pass language-specific linting (e.g., Python docstrings valid)
3. Processing time: <5 seconds per 1000 lines of code (with local LLM)
4. Chunk reassembly produces valid, executable code (no syntax errors introduced)
