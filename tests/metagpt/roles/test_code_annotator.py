#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from metagpt.roles.code_annotator import CodeAnnotator
from metagpt.schema import Message


@pytest.fixture
def code_annotator():
    return CodeAnnotator()


def test_role_initialization(code_annotator):
    assert code_annotator.name == "CodeAnnotator"
    assert code_annotator.profile == "Code Annotator"
    assert "documentation comments" in code_annotator.goal


@pytest.mark.asyncio
async def test_standalone_instantiation():
    annotator = CodeAnnotator()
    assert annotator is not None
    assert len(annotator.actions) > 0


@pytest.mark.asyncio
async def test_run_with_single_file(code_annotator, tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text("def hello():\n    return 'world'")
    
    with patch('metagpt.actions.annotate_code.AnnotateCode._aask', new=AsyncMock(return_value="def hello():\n    return 'world'")):
        result = await code_annotator.run(str(test_file))
        assert result is not None


@pytest.mark.asyncio
async def test_run_with_directory(code_annotator, tmp_path):
    test_dir = tmp_path / "project"
    test_dir.mkdir()
    (test_dir / "main.py").write_text("print('hello')")
    
    with patch('metagpt.actions.annotate_code.AnnotateCode._aask', new=AsyncMock(return_value="print('hello')")):
        result = await code_annotator.run(str(test_dir))
        assert result is not None


@pytest.mark.asyncio
async def test_act_without_message(code_annotator):
    response = await code_annotator._act()
    assert "No input" in response.content or "Failed" in response.content


@pytest.mark.asyncio
async def test_act_with_message(code_annotator, tmp_path):
    test_file = tmp_path / "sample.py"
    test_file.write_text("x = 1")
    
    msg = Message(content=str(test_file), role="User")
    code_annotator.put_message(msg)
    
    with patch('metagpt.actions.annotate_code.AnnotateCode._aask', new=AsyncMock(return_value="x = 1")):
        response = await code_annotator._act()
        assert response is not None
