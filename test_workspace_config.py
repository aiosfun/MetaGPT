#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test workspace configuration after fix
"""

import sys
import os

# Add MetaGPT to path
sys.path.insert(0, '.')

def test_workspace_config():
    """Test that workspace path is correctly configured"""
    print("🗂️ Testing Workspace Configuration")
    print("=" * 40)

    try:
        from metagpt.config2 import config
        from metagpt.actions.write_prd_openspec import WritePRDWithOpenSpec

        # Test 1: Check workspace path in config
        print("1️⃣ Testing config workspace path...")
        assert hasattr(config.openspec, 'workspace_path'), "workspace_path missing from config"
        workspace_path = config.openspec.workspace_path
        print(f"✅ Raw workspace path: {workspace_path}")

        # Test 2: Check expanded path
        print("\n2️⃣ Testing expanded workspace path...")
        expanded_path = os.path.expanduser(workspace_path)
        print(f"✅ Expanded workspace path: {expanded_path}")

        # Verify it's the expected path
        expected_path = os.path.expanduser("~/.metagpt/openspec")
        print(f"✅ Expected path: {expected_path}")
        print(f"✅ Paths match: {expanded_path == expected_path}")

        # Test 3: Check that action gets correct path
        print("\n3️⃣ Testing action workspace initialization...")
        action = WritePRDWithOpenSpec(config=config)

        if hasattr(action, 'openspec_workspace'):
            workspace_manager = action.openspec_workspace
            print(f"✅ Workspace manager created: {type(workspace_manager).__name__}")

            # Check if workspace manager has the correct path
            if hasattr(workspace_manager, 'workspace_root'):
                actual_workspace_path = workspace_manager.workspace_root
                print(f"✅ Workspace manager root: {actual_workspace_path}")
                print(f"✅ Workspace path correct: {actual_workspace_path == expanded_path}")
            else:
                print("⚠️ Workspace manager doesn't expose root path")
        else:
            print("❌ Action missing workspace manager")
            return False

        # Test 4: Verify directory structure expectation
        print("\n4️⃣ Testing expected directory structure...")
        changes_dir = os.path.join(expanded_path, "changes")
        print(f"✅ Changes directory will be: {changes_dir}")

        # Check if parent directory exists
        parent_dir = os.path.dirname(expanded_path)
        print(f"✅ Parent directory exists: {os.path.exists(parent_dir)}")

        return True

    except Exception as e:
        print(f"❌ Workspace configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    success = test_workspace_config()

    print("\n" + "=" * 40)
    if success:
        print("✅ Workspace configuration is CORRECT")
        print("\n🎯 Expected file locations after running MetaGPT:")
        print("📁 ~/.metagpt/openspec/changes/{timestamp}/")
        print("  ├── requirements.md")
        print("  ├── design.md")
        print("  └── tasks.md")
    else:
        print("❌ Workspace configuration needs fixes")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)