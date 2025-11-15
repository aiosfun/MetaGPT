#!/usr/bin/env python3
"""
Test script to verify the agent fixes work correctly
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from v1_basic_agent_improved import validate_content_block, normalize_content_list, validate_message

def test_content_validation():
    """Test the content validation functions"""
    print("Testing content validation...")
    
    # Test 1: Valid text block
    valid_text = {"type": "text", "text": "Hello world"}
    result = validate_content_block(valid_text)
    assert result["type"] == "text"
    assert result["text"] == "Hello world"
    print("PASS: Valid text block test passed")
    
    # Test 2: Invalid block (should be normalized)
    invalid_block = "just a string"
    result = validate_content_block(invalid_block)
    assert result["type"] == "text"
    assert result["text"] == "just a string"
    print("PASS: Invalid block normalization test passed")

    # Test 3: Tool result block
    tool_result = {"type": "tool_result", "tool_use_id": "test123", "content": "Success"}
    result = validate_content_block(tool_result)
    assert result["type"] == "tool_result"
    assert result["tool_use_id"] == "test123"
    print("PASS: Tool result block test passed")

    # Test 4: Content list normalization
    mixed_content = [
        {"type": "text", "text": "Hello"},
        "just a string",
        {"type": "tool_result", "content": "Result"}
    ]
    result = normalize_content_list(mixed_content)
    assert len(result) == 3
    assert all(item["type"] in ["text", "tool_result"] for item in result)
    print("PASS: Content list normalization test passed")

    # Test 5: Message validation
    message = {
        "role": "user",
        "content": [
            {"type": "text", "text": "Hello"},
            {"invalid": "block"}  # This should be normalized
        ]
    }
    result = validate_message(message)
    assert result["role"] == "user"
    assert len(result["content"]) == 2
    print("PASS: Message validation test passed")

    print("All content validation tests passed!")

if __name__ == "__main__":
    test_content_validation()
    print("\nAgent fix validation completed successfully!")