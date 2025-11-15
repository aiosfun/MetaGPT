#!/usr/bin/env python3
"""
Minimal test to reproduce the exact error
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_exact_call():
    """Test the exact call that's failing"""
    print("Testing exact client.messages.create call...")
    
    try:
        import v1_basic_agent
        
        # Get the client
        client = v1_basic_agent.client
        print(f"Client: {client}")
        print(f"Client type: {type(client)}")
        
        # Test the exact call pattern
        print("Testing: client.messages.create")
        
        # This should be the exact same call that's failing
        # But with minimal parameters to avoid actual API calls
        try:
            # Test if we can access the create method
            create_method = client.messages.create
            print(f"create method: {create_method}")
            print(f"create method type: {type(create_method)}")
            print(f"create method callable: {callable(create_method)}")
            
            if not callable(create_method):
                print("ERROR: create method is not callable!")
                print(f"Actual value: {create_method}")
                return False
            
            print("SUCCESS: create method is callable!")
            return True
            
        except AttributeError as e:
            print(f"AttributeError: {e}")
            return False
        except Exception as e:
            print(f"Other error: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"Import/setup error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_exact_call()
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)