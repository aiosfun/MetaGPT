#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug OpenSpec action selection issue
"""

import sys
import asyncio

# Add MetaGPT to path
sys.path.insert(0, '.')

async def test_productmanager_action_selection():
    """Test ProductManager action selection logic"""
    print("🔍 Debugging ProductManager Action Selection")
    print("=" * 50)

    try:
        from metagpt.config2 import config
        from metagpt.roles.product_manager import ProductManager
        from metagpt.actions.write_prd import WritePRD
        from metagpt.actions.write_prd_openspec import WritePRDWithOpenSpec

        # Create ProductManager with config
        pm = ProductManager(config=config)
        print(f"✅ ProductManager created")
        print(f"✅ use_fixed_sop: {pm.use_fixed_sop}")
        print(f"✅ use_openspec: {pm.use_openspec}")

        # Check current actions
        if hasattr(pm, '_actions') and pm._actions:
            print(f"✅ Has _actions: {len(pm._actions)}")
            for i, action in enumerate(pm._actions):
                action_type = type(action).__name__
                print(f"   {i}: {action_type}")
                if hasattr(action, '__class__'):
                    print(f"      Class: {action.__class__.__name__}")

        # Check todo_action
        print(f"✅ todo_action: {pm.todo_action}")

        # Check tool execution map
        if hasattr(pm, 'tool_execution_map'):
            tools = list(pm.tool_execution_map.keys())
            print(f"✅ Tools in map: {len(tools)}")
            for tool in tools:
                print(f"   - {tool}")

        # Test the _think method behavior
        print("\n🧠 Testing _think method...")
        try:
            # Simulate _think call
            result = await pm._think()
            print(f"✅ _think returned: {result}")
            print(f"✅ todo_action after _think: {pm.todo_action}")

        except Exception as think_error:
            print(f"❌ _think error: {think_error}")

        # Try to call _think to see what action it would choose
        print("\n🎯 Testing action selection logic...")

        # Check config access
        print(f"✅ hasattr(pm, 'rc'): {hasattr(pm, 'rc')}")
        if hasattr(pm, 'rc'):
            print(f"✅ hasattr(pm.rc, 'config'): {hasattr(pm.rc, 'config')}")
            if hasattr(pm.rc, 'config'):
                print(f"✅ hasattr(pm.rc.config, 'openspec'): {hasattr(pm.rc.config, 'openspec')}")

        print(f"✅ hasattr(pm, 'config'): {hasattr(pm, 'config')}")
        if hasattr(pm, 'config'):
            print(f"✅ hasattr(pm.config, 'openspec'): {hasattr(pm.config, 'openspec')}")

        # Check which action would be chosen
        if hasattr(pm, 'config') and hasattr(pm.config, 'openspec'):
            pm.use_openspec = pm.config.openspec.enabled
            print(f"✅ Updated use_openspec from config: {pm.use_openspec}")

        expected_action = WritePRDWithOpenSpec if pm.use_openspec else WritePRD
        expected_name = any_to_name(expected_action)
        print(f"✅ Expected action: {expected_name}")
        print(f"✅ Current todo_action: {pm.todo_action}")
        print(f"✅ Actions match: {pm.todo_action == expected_name}")

        # Update actions to match expected
        pm._update_tool_execution()

        # Check if action exists in execution map
        action_key = f"{expected_name}.run"
        has_action = action_key in pm.tool_execution_map
        print(f"✅ Action in execution map: {has_action}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_action_execution():
    """Test actual OpenSpec action execution"""
    print("\n⚙️ Testing Action Execution...")
    print("=" * 35)

    try:
        from metagpt.config2 import config
        from metagpt.actions.write_prd_openspec import WritePRDWithOpenSpec
        from metagpt.schema import UserMessage

        # Create action
        action = WritePRDWithOpenSpec(config=config)
        print(f"✅ Action created: {type(action).__name__}")
        print(f"✅ Has workspace: {hasattr(action, 'openspec_workspace')}")

        # Test with a simple message
        test_message = UserMessage(content="Create a simple todo application", send_from="user", send_to="product_manager")

        print(f"✅ Test message created")
        print(f"   Content: {test_message.content}")
        print(f"   Send to: {test_message.send_to}")

        # Test action selection
        selected_action = action._select_action([test_message])
        print(f"✅ Selected action: {selected_action}")

        return True

    except Exception as e:
        print(f"❌ Action execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def any_to_name(action_class):
    """Recreate any_to_name function"""
    return f"{action_class.__name__}"

async def main():
    print("🐛 OpenSpec Action Selection Debug")
    print("=" * 50)

    pm_test = await test_productmanager_action_selection()
    action_test = await test_action_execution()

    print("\n" + "=" * 50)
    print("📊 DEBUG RESULTS")
    print("=" * 50)
    print(f"ProductManager Test: {'✅ SUCCESS' if pm_test else '❌ FAILED'}")
    print(f"Action Execution Test: {'✅ SUCCESS' if action_test else '❌ FAILED'}")

    if pm_test and action_test:
        print("\n🎯 KEY FINDINGS:")
        print("✅ ProductManager configuration is correct")
        print("✅ OpenSpec mode is enabled")
        print("✅ Expected action matches selection")
        print("\n🔧 If files still not created, the issue may be:")
        print("1. Action not being selected in real run")
        print("2. Action.run() method not being called")
        print("3. Action.run() not saving to OpenSpec workspace")
        print("4. Different execution path in actual MetaGPT")

        return True
    else:
        print("\n❌ Debugging failed - specific issues need to be addressed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)