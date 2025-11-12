#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from metagpt.actions.annotate_code import AnnotateCode, CodeChunk, SAFE_CONTEXT_LIMIT


@pytest.fixture
def annotate_action():
    return AnnotateCode()


def test_detect_language():
    assert AnnotateCode.detect_language(Path("test.py")) == "python"
    assert AnnotateCode.detect_language(Path("test.js")) == "javascript"
    assert AnnotateCode.detect_language(Path("test.ts")) == "typescript"
    assert AnnotateCode.detect_language(Path("test.java")) == "java"
    assert AnnotateCode.detect_language(Path("test.c")) == "c"
    assert AnnotateCode.detect_language(Path("test.cpp")) == "cpp"
    assert AnnotateCode.detect_language(Path("test.sh")) == "shell"
    assert AnnotateCode.detect_language(Path("test.go")) == "go"
    assert AnnotateCode.detect_language(Path("test.rs")) == "rust"
    assert AnnotateCode.detect_language(Path("test.xyz")) is None


def test_estimate_tokens():
    text = "a" * 400
    tokens = AnnotateCode.estimate_tokens(text)
    assert tokens == 100


def test_chunk_small_file():
    code = "def hello():\n    print('hello')\n"
    chunks = AnnotateCode.chunk_code(code, "python", max_tokens=SAFE_CONTEXT_LIMIT)
    assert len(chunks) == 1
    assert chunks[0].content == code


def test_chunk_python_code():
    code = '''
def func1():
    return 1

def func2():
    return 2

class MyClass:
    def method1(self):
        pass
''' * 100
    
    chunks = AnnotateCode.chunk_python_code(code, max_tokens=1000)
    assert len(chunks) > 1
    for chunk in chunks:
        assert isinstance(chunk, CodeChunk)


def test_chunk_code_regex():
    js_code = '''
function hello() {
    console.log("hello");
}

function world() {
    console.log("world");
}

class MyClass {
    constructor() {}
}
''' * 50
    
    chunks = AnnotateCode.chunk_code_regex(js_code, "javascript", max_tokens=1000)
    assert len(chunks) > 1


def test_get_output_path(annotate_action):
    input_file = Path("test.py")
    output_file = annotate_action.get_output_path(input_file, is_directory=False)
    assert output_file == Path("test.annotated.py")
    
    input_dir = Path("src")
    output_dir = annotate_action.get_output_path(input_dir, is_directory=True)
    assert output_dir == Path("src_annotated")


@pytest.mark.asyncio
async def test_annotate_chunk(annotate_action):
    chunk = CodeChunk(content="def hello():\n    pass", start_line=0, end_line=2)
    
    with patch.object(annotate_action, '_aask', new=AsyncMock(return_value="```python\ndef hello():\n    \"\"\"Say hello\"\"\"\n    pass\n```")):
        result = await annotate_action.annotate_chunk(chunk, "python")
        assert "def hello():" in result


@pytest.mark.asyncio
async def test_annotate_file(annotate_action, tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text("def greet(name):\n    return f'Hello {name}'")
    
    with patch.object(annotate_action, '_aask', new=AsyncMock(return_value='def greet(name):\n    """Greet someone"""\n    return f\'Hello {name}\'')):
        annotated, success = await annotate_action.annotate_file(test_file)
        assert success
        assert "def greet" in annotated


@pytest.mark.asyncio
async def test_annotate_nonexistent_file(annotate_action):
    annotated, success = await annotate_action.annotate_file(Path("nonexistent.py"))
    assert not success
    assert annotated == ""


@pytest.mark.asyncio
async def test_run_single_file(annotate_action, tmp_path):
    test_file = tmp_path / "sample.py"
    test_file.write_text("def test():\n    pass")
    
    with patch.object(annotate_action, '_aask', new=AsyncMock(return_value="def test():\n    pass")):
        result = await annotate_action.run(str(test_file))
        assert result
        output_path = Path(result)
        assert output_path.exists()
        assert output_path.name == "sample.annotated.py"


@pytest.mark.asyncio
async def test_run_directory(annotate_action, tmp_path):
    test_dir = tmp_path / "src"
    test_dir.mkdir()
    (test_dir / "file1.py").write_text("def func1():\n    pass")
    (test_dir / "file2.py").write_text("def func2():\n    pass")
    
    with patch.object(annotate_action, '_aask', new=AsyncMock(return_value="def func():\n    pass")):
        result = await annotate_action.run(str(test_dir))
        assert result
        output_dir = Path(result)
        assert output_dir.exists()
        assert output_dir.name == "src_annotated"
