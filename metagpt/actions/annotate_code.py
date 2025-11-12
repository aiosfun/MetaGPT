#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast
import re
from pathlib import Path
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

from metagpt.actions.action import Action
from metagpt.logs import logger

SAFE_CONTEXT_LIMIT = 24576

LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".h": "c_header",
    ".hpp": "cpp_header",
    ".sh": "shell",
    ".bash": "shell",
    ".go": "go",
    ".rs": "rust",
}

ANNOTATION_PROMPTS = {
    "python": """You are a code documentation expert. Analyze the following Python code and add comprehensive documentation comments.

Follow these guidelines:
1. Add module-level docstring at the top following PEP 257
2. Add class docstrings describing purpose, attributes, and usage
3. Add function/method docstrings with:
   - Brief description
   - Args: parameter descriptions with types
   - Returns: return value description with type
   - Raises: exceptions that may be raised
4. Add inline comments for complex logic, algorithms, and non-obvious code:
   - Explain the purpose of complex conditional statements (if/elif/else chains)
   - Document loop logic and iteration purposes
   - Clarify mathematical operations or formulas
   - Explain nested structures and their relationships
   - Add comments before code blocks that implement specific algorithms
   - Clarify any non-intuitive variable usage or transformations
5. Keep existing code logic unchanged

IMPORTANT: Pay special attention to adding inline comments inside function bodies for:
- Complex if/elif/else conditions
- Loop constructs (for, while) with non-trivial logic
- List comprehensions or generator expressions
- Lambda functions
- Error handling blocks
- Any line of code that might not be immediately obvious to another developer

Code to annotate:
```python
{code}
```

Return ONLY the annotated code without any explanation or markdown formatting.""",

    "javascript": """You are a code documentation expert. Analyze the following JavaScript code and add comprehensive JSDoc comments.

Follow these guidelines:
1. Add file-level JSDoc comment at the top
2. Add class JSDoc with @class, description
3. Add function JSDoc with:
   - Brief description
   - @param {type} name - description
   - @returns {type} description
   - @throws {Error} description if applicable
4. Add inline comments for complex logic, algorithms, and non-obvious code:
   - Explain complex conditionals and switch statements
   - Document loop logic and array operations
   - Clarify callbacks, promises, and async operations
   - Explain object manipulations and destructuring
   - Add comments for DOM operations or event handlers
   - Clarify any non-obvious transformations or side effects
5. Keep existing code logic unchanged

IMPORTANT: Add inline comments inside function bodies for complex statements, loops, conditionals, and algorithm steps.

Code to annotate:
```javascript
{code}
```

Return ONLY the annotated code without any explanation or markdown formatting.""",

    "typescript": """You are a code documentation expert. Analyze the following TypeScript code and add comprehensive JSDoc/TSDoc comments.

Follow these guidelines:
1. Add file-level documentation at the top
2. Add interface/class documentation with descriptions
3. Add function documentation with:
   - Brief description
   - @param name - description (types already in TypeScript)
   - @returns description
4. Add inline comments for complex logic, algorithms, and non-obvious code:
   - Explain complex type manipulations and generics usage
   - Document async/await patterns and promise chains
   - Clarify non-trivial type guards and assertions
   - Explain complex conditionals and control flow
   - Add comments for algorithm implementations
5. Keep existing code logic unchanged

IMPORTANT: Add inline comments inside function bodies for complex statements, type operations, and algorithm steps.

Code to annotate:
```typescript
{code}
```

Return ONLY the annotated code without any explanation or markdown formatting.""",

    "java": """You are a code documentation expert. Analyze the following Java code and add comprehensive JavaDoc comments.

Follow these guidelines:
1. Add class-level JavaDoc with description and @author
2. Add method JavaDoc with:
   - Brief description
   - @param name description
   - @return description
   - @throws exception description
3. Add field JavaDoc where appropriate
4. Add inline comments for complex logic, algorithms, and non-obvious code:
   - Explain complex conditionals and switch statements
   - Document loop logic and stream operations
   - Clarify exception handling strategies
   - Explain synchronization or threading logic
   - Add comments for algorithm implementations
   - Clarify any non-obvious object interactions
5. Keep existing code logic unchanged

IMPORTANT: Add inline comments inside method bodies for complex statements, loops, conditionals, and algorithm steps.

Code to annotate:
```java
{code}
```

Return ONLY the annotated code without any explanation or markdown formatting.""",

    "c": """You are a code documentation expert. Analyze the following C code and add comprehensive Doxygen-style comments.

Follow these guidelines:
1. Add file header comment with @file, @brief
2. Add function comments with:
   - @brief brief description
   - @param name description
   - @return description
3. Add struct/typedef comments
4. Add inline comments for complex logic
5. Keep existing code logic unchanged

Code to annotate:
```c
{code}
```

Return ONLY the annotated code without any explanation or markdown formatting.""",

    "cpp": """You are a code documentation expert. Analyze the following C++ code and add comprehensive Doxygen-style comments.

Follow these guidelines:
1. Add file header comment with @file, @brief
2. Add class comments with @brief, @details
3. Add method comments with:
   - @brief brief description
   - @param name description
   - @return description
4. Add inline comments for complex logic
5. Keep existing code logic unchanged

Code to annotate:
```cpp
{code}
```

Return ONLY the annotated code without any explanation or markdown formatting.""",

    "shell": """You are a code documentation expert. Analyze the following shell script and add comprehensive comment blocks.

Follow these guidelines:
1. Add script header with purpose, usage, author
2. Add function comments describing:
   - Function purpose
   - Parameters (arguments)
   - Return values/exit codes
3. Add inline comments for complex commands
4. Keep existing code logic unchanged

Code to annotate:
```bash
{code}
```

Return ONLY the annotated code without any explanation or markdown formatting.""",

    "go": """You are a code documentation expert. Analyze the following Go code and add comprehensive documentation comments.

Follow these guidelines:
1. Add package comment at the top
2. Add type/struct comments (above declaration)
3. Add function comments (above declaration) with:
   - Brief description starting with function name
   - Parameter descriptions if needed
   - Return value descriptions if needed
4. Add inline comments for complex logic
5. Keep existing code logic unchanged

Code to annotate:
```go
{code}
```

Return ONLY the annotated code without any explanation or markdown formatting.""",

    "rust": """You are a code documentation expert. Analyze the following Rust code and add comprehensive documentation comments.

Follow these guidelines:
1. Add module-level doc comment with //!
2. Add struct/enum doc comments with ///
3. Add function doc comments with ///
   - Brief description
   - # Arguments
   - # Returns
   - # Examples (if complex)
4. Add inline comments for complex logic
5. Keep existing code logic unchanged

Code to annotate:
```rust
{code}
```

Return ONLY the annotated code without any explanation or markdown formatting.""",
}


class CodeChunk(BaseModel):
    content: str
    start_line: int
    end_line: int
    context: str = ""


class AnnotateCode(Action):
    name: str = "AnnotateCode"
    
    @staticmethod
    def detect_language(file_path: Path) -> Optional[str]:
        ext = file_path.suffix.lower()
        lang = LANGUAGE_EXTENSIONS.get(ext)
        if not lang:
            logger.warning(f"Unsupported file extension: {ext}")
        return lang

    @staticmethod
    def estimate_tokens(text: str) -> int:
        return len(text) // 4

    @staticmethod
    def chunk_python_code(code: str, max_tokens: int = SAFE_CONTEXT_LIMIT) -> List[CodeChunk]:
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            logger.error(f"Syntax error parsing Python code: {e}")
            return [CodeChunk(content=code, start_line=0, end_line=len(code.splitlines()))]

        lines = code.splitlines(keepends=True)
        chunks = []
        
        imports = []
        module_docstring = ""
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(ast.get_source_segment(code, node))
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                if node.lineno == 1 or (len(tree.body) > 0 and tree.body[0] == node):
                    module_docstring = ast.get_source_segment(code, node)
        
        context_header = "\n".join(filter(None, imports))
        if module_docstring:
            context_header = module_docstring + "\n" + context_header
        
        current_chunk = []
        current_tokens = AnnotateCode.estimate_tokens(context_header)
        
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and node == tree.body[0]:
                continue
                
            segment = ast.get_source_segment(code, node)
            if segment is None:
                continue
                
            segment_tokens = AnnotateCode.estimate_tokens(segment)
            
            if current_tokens + segment_tokens > max_tokens and current_chunk:
                chunk_content = context_header + "\n\n" + "".join(current_chunk)
                chunks.append(CodeChunk(
                    content=chunk_content,
                    start_line=0,
                    end_line=0,
                    context=context_header
                ))
                current_chunk = []
                current_tokens = AnnotateCode.estimate_tokens(context_header)
            
            current_chunk.append(segment + "\n")
            current_tokens += segment_tokens
        
        if current_chunk:
            chunk_content = context_header + "\n\n" + "".join(current_chunk)
            chunks.append(CodeChunk(
                content=chunk_content,
                start_line=0,
                end_line=0,
                context=context_header
            ))
        
        if not chunks:
            chunks.append(CodeChunk(content=code, start_line=0, end_line=len(lines)))
        
        return chunks

    @staticmethod
    def chunk_code_regex(code: str, language: str, max_tokens: int = SAFE_CONTEXT_LIMIT) -> List[CodeChunk]:
        lines = code.splitlines(keepends=True)
        
        if language in ["javascript", "typescript", "java"]:
            pattern = r'^(class\s+\w+|function\s+\w+|const\s+\w+\s*=\s*function|export\s+(class|function)\s+\w+)'
        elif language in ["c", "cpp", "c_header", "cpp_header"]:
            pattern = r'^(struct\s+\w+|class\s+\w+|[\w\s\*]+\s+\w+\s*\([^)]*\)\s*\{?|typedef\s+)'
        elif language == "go":
            pattern = r'^(func\s+\w+|type\s+\w+\s+(struct|interface))'
        elif language == "rust":
            pattern = r'^(fn\s+\w+|struct\s+\w+|enum\s+\w+|impl\s+)'
        elif language == "shell":
            pattern = r'^(function\s+\w+|\w+\s*\(\)\s*\{)'
        else:
            return [CodeChunk(content=code, start_line=0, end_line=len(lines))]
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for i, line in enumerate(lines):
            if re.match(pattern, line.strip(), re.MULTILINE):
                if current_tokens > max_tokens and current_chunk:
                    chunks.append(CodeChunk(
                        content="".join(current_chunk),
                        start_line=0,
                        end_line=0
                    ))
                    current_chunk = []
                    current_tokens = 0
            
            current_chunk.append(line)
            current_tokens += AnnotateCode.estimate_tokens(line)
        
        if current_chunk:
            chunks.append(CodeChunk(
                content="".join(current_chunk),
                start_line=0,
                end_line=0
            ))
        
        if not chunks:
            chunks.append(CodeChunk(content=code, start_line=0, end_line=len(lines)))
        
        return chunks

    @staticmethod
    def chunk_code(code: str, language: str, max_tokens: int = SAFE_CONTEXT_LIMIT) -> List[CodeChunk]:
        estimated_tokens = AnnotateCode.estimate_tokens(code)
        
        if estimated_tokens <= max_tokens:
            return [CodeChunk(content=code, start_line=0, end_line=len(code.splitlines()))]
        
        logger.info(f"File exceeds token limit ({estimated_tokens} > {max_tokens}), chunking...")
        
        if language == "python":
            return AnnotateCode.chunk_python_code(code, max_tokens)
        else:
            return AnnotateCode.chunk_code_regex(code, language, max_tokens)

    async def annotate_chunk(self, chunk: CodeChunk, language: str) -> str:
        prompt_template = ANNOTATION_PROMPTS.get(language, ANNOTATION_PROMPTS.get("python"))
        prompt = prompt_template.format(code=chunk.content)
        
        try:
            annotated = await self._aask(prompt)
            annotated = annotated.strip()
            
            if annotated.startswith("```"):
                lines = annotated.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                annotated = "\n".join(lines)
            
            return annotated
        except Exception as e:
            logger.error(f"Failed to annotate chunk: {e}")
            return chunk.content

    async def annotate_file(self, file_path: Path) -> Tuple[str, bool]:
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return "", False
        
        language = self.detect_language(file_path)
        if not language:
            return "", False
        
        try:
            code = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return "", False
        
        chunks = self.chunk_code(code, language)
        logger.info(f"Processing {file_path.name} in {len(chunks)} chunk(s)")
        
        annotated_chunks = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Annotating chunk {i+1}/{len(chunks)}...")
            annotated = await self.annotate_chunk(chunk, language)
            annotated_chunks.append(annotated)
        
        if len(chunks) == 1:
            final_code = annotated_chunks[0]
        else:
            final_code = "\n\n".join(annotated_chunks)
        
        return final_code, True

    def get_output_path(self, input_path: Path, is_directory: bool = False) -> Path:
        if is_directory:
            return input_path.parent / f"{input_path.name}_annotated"
        else:
            stem = input_path.stem
            suffix = input_path.suffix
            return input_path.parent / f"{stem}.annotated{suffix}"

    async def run(self, file_path: str) -> str:
        path = Path(file_path)
        
        if path.is_file():
            annotated_code, success = await self.annotate_file(path)
            if success:
                output_path = self.get_output_path(path)
                output_path.write_text(annotated_code, encoding="utf-8")
                logger.info(f"Annotated file saved to: {output_path}")
                return str(output_path)
            else:
                logger.error(f"Failed to annotate {path}")
                return ""
        
        elif path.is_dir():
            output_dir = self.get_output_path(path, is_directory=True)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            processed = 0
            for file in path.rglob("*"):
                if file.is_file() and file.suffix in LANGUAGE_EXTENSIONS:
                    logger.info(f"Processing {file.relative_to(path)}...")
                    
                    annotated_code, success = await self.annotate_file(file)
                    if success:
                        relative_path = file.relative_to(path)
                        output_file = output_dir / relative_path
                        output_file.parent.mkdir(parents=True, exist_ok=True)
                        output_file.write_text(annotated_code, encoding="utf-8")
                        processed += 1
            
            logger.info(f"Processed {processed} files. Output directory: {output_dir}")
            return str(output_dir)
        
        else:
            logger.error(f"Path does not exist: {path}")
            return ""
