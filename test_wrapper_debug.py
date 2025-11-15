#!/usr/bin/env python3
"""
Test script to debug the OpenAIWrapper issue
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_import():
    """Test importing the module"""
    print("=== Testing Import ===")
    try:
        import v1_basic_agent
        print("OK Import successful")
        return v1_basic_agent
    except Exception as e:
        print(f"FAIL Import failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_wrapper_creation(v1_basic_agent):
    """Test creating the wrapper"""
    print("\n=== Testing Wrapper Creation ===")
    try:
        # Test OpenAIWrapper class exists
        if not hasattr(v1_basic_agent, 'OpenAIWrapper'):
            print("✗ OpenAIWrapper class not found")
            return False
        
        wrapper = v1_basic_agent.OpenAIWrapper(None)
        print("OK OpenAIWrapper created successfully")
        return wrapper
    except Exception as e:
        print(f"✗ Wrapper creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_messages_method(wrapper):
    """Test the messages() method"""
    print("\n=== Testing messages() Method ===")
    try:
        messages_obj = wrapper.messages()
        print(f"✓ messages() returned: {type(messages_obj)}")
        print(f"✓ messages() type: {type(messages_obj).__name__}")
        print(f"✓ messages() has create: {hasattr(messages_obj, 'create')}")
        return messages_obj
    except Exception as e:
        print(f"✗ messages() method failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_create_method(messages_obj):
    """Test the create method exists and is callable"""
    print("\n=== Testing create() Method ===")
    try:
        create_method = getattr(messages_obj, 'create', None)
        print(f"✓ create method: {create_method}")
        print(f"✓ create type: {type(create_method)}")
        print(f"✓ create callable: {callable(create_method)}")
        return create_method
    except Exception as e:
        print(f"✗ create() method test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_full_chain(v1_basic_agent):
    """Test the full chain: client.messages.create"""
    print("\n=== Testing Full Chain ===")
    try:
        # Get the actual client from the module
        client = getattr(v1_basic_agent, 'client', None)
        print(f"Client type: {type(client)}")
        print(f"Client: {client}")
        
        if hasattr(client, 'messages'):
            print("✓ client has messages attribute")
            messages_attr = getattr(client, 'messages')
            print(f"messages type: {type(messages_attr)}")
            print(f"messages callable: {callable(messages_attr)}")
            
            if callable(messages_attr):
                messages_obj = messages_attr()
                print(f"messages() returned: {type(messages_obj)}")
                print(f"messages() has create: {hasattr(messages_obj, 'create')}")
                
                if hasattr(messages_obj, 'create'):
                    create_attr = getattr(messages_obj, 'create')
                    print(f"create type: {type(create_attr)}")
                    print(f"create callable: {callable(create_attr)}")
                    
                    if not callable(create_attr):
                        print("✗ ERROR: create is not callable!")
                        print(f"create value: {create_attr}")
                        return False
                else:
                    print("✗ ERROR: messages_obj has no create attribute!")
                    return False
            else:
                print("✗ ERROR: messages is not callable!")
                return False
        else:
            print("✗ ERROR: client has no messages attribute!")
            return False
            
        print("✓ Full chain test passed")
        return True
        
    except Exception as e:
        print(f"✗ Full chain test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Testing OpenAIWrapper Implementation")
    print("=" * 50)
    
    # Test import
    v1_basic_agent = test_import()
    if not v1_basic_agent:
        return False
    
    # Test wrapper creation
    wrapper = test_wrapper_creation(v1_basic_agent)
    if not wrapper:
        return False
    
    # Test messages method
    messages_obj = test_messages_method(wrapper)
    if not messages_obj:
        return False
    
    # Test create method
    create_method = test_create_method(messages_obj)
    if not create_method:
        return False
    
    # Test full chain
    success = test_full_chain(v1_basic_agent)
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All tests passed! The wrapper should work.")
    else:
        print("✗ Some tests failed. The wrapper needs fixing.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)