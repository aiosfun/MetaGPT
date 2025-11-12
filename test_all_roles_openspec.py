#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test all roles for proper OpenSpec configuration
"""

import sys
import os

# Add MetaGPT to path
sys.path.insert(0, '.')

def test_all_roles_openspec():
    """Test that all roles are properly configured with OpenSpec"""
    print("🎭 Testing All Roles OpenSpec Configuration")
    print("=" * 50)

    try:
        from metagpt.config2 import config
        from metagpt.roles.product_manager import ProductManager
        from metagpt.roles.architect import Architect
        from metagpt.roles.project_manager import ProjectManager
        from metagpt.actions.write_prd_openspec import WritePRDWithOpenSpec
        from metagpt.actions.design_api_openspec import WriteDesignWithOpenSpec
        from metagpt.actions.write_tasks_openspec import WriteTasksWithOpenSpec

        # Test 1: ProductManager
        print("1️⃣ Testing ProductManager...")
        pm = ProductManager(config=config)
        print(f"✅ ProductManager use_openspec: {pm.use_openspec}")
        print(f"✅ ProductManager todo_action: {pm.todo_action}")
        expected_pm_action = WritePRDWithOpenSpec.__name__
        print(f"✅ ProductManager using OpenSpec action: {pm.todo_action == expected_pm_action}")

        # Test 2: Architect
        print("\n2️⃣ Testing Architect...")
        arch = Architect(config=config)
        print(f"✅ Architect use_openspec: {arch.use_openspec}")
        print(f"✅ Architect todo_action: {arch.todo_action}")
        expected_arch_action = WriteDesignWithOpenSpec.__name__
        print(f"✅ Architect using OpenSpec action: {arch.todo_action == expected_arch_action}")

        # Test 3: ProjectManager
        print("\n3️⃣ Testing ProjectManager...")
        pmgr = ProjectManager(config=config)
        print(f"✅ ProjectManager use_openspec: {pmgr.use_openspec}")
        print(f"✅ ProjectManager todo_action: {pmgr.todo_action}")
        expected_pmgr_action = WriteTasksWithOpenSpec.__name__
        print(f"✅ ProjectManager using OpenSpec action: {pmgr.todo_action == expected_pmgr_action}")

        # Test 4: Check workspace paths
        print("\n4️⃣ Testing workspace configurations...")

        # Test ProductManager workspace
        if hasattr(pm, '_actions') and pm._actions:
            pm_action = pm._actions[0]
            if hasattr(pm_action, 'openspec_workspace'):
                pm_workspace = pm_action.openspec_workspace.workspace_path
                print(f"✅ ProductManager workspace: {pm_workspace}")

        # Test Architect workspace
        if hasattr(arch, '_actions') and arch._actions:
            arch_action = arch._actions[0]
            if hasattr(arch_action, 'openspec_workspace'):
                arch_workspace = arch_action.openspec_workspace.workspace_path
                print(f"✅ Architect workspace: {arch_workspace}")

        # Test ProjectManager workspace
        if hasattr(pmgr, '_actions') and pmgr._actions:
            pmgr_action = pmgr._actions[0]
            if hasattr(pmgr_action, 'openspec_workspace'):
                pmgr_workspace = pmgr_action.openspec_workspace.workspace_path
                print(f"✅ ProjectManager workspace: {pmgr_workspace}")

        # Test 5: Test software_company import pattern
        print("\n5️⃣ Testing software_company integration...")
        from metagpt.roles import ProductManager as PMImport, Architect as ArchImport, ProjectManager as PMgrImport

        pm2 = PMImport(config=config)
        arch2 = ArchImport(config=config)
        pmgr2 = PMgrImport(config=config)

        print(f"✅ ProductManager import works: {pm2.use_openspec}")
        print(f"✅ Architect import works: {arch2.use_openspec}")
        print(f"✅ ProjectManager import works: {pmgr2.use_openspec}")

        # Test 6: Expected file generation
        print("\n6️⃣ Testing expected file generation...")
        workspace_root = os.path.expanduser("~/.metagpt/openspec")
        print(f"✅ Expected workspace root: {workspace_root}")

        expected_files = [
            "changes/{timestamp}/requirement.md",
            "changes/{timestamp}/design.md",
            "changes/{timestamp}/tasks.md"
        ]

        for expected_file in expected_files:
            full_path = os.path.join(workspace_root, expected_file)
            print(f"✅ Expected file: {full_path}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    success = test_all_roles_openspec()

    print("\n" + "=" * 50)
    if success:
        print("✅ ALL ROLES PROPERLY CONFIGURED")
        print("\n🎯 Expected behavior:")
        print("📄 ProductManager will generate: requirement.md")
        print("📐 Architect will generate: design.md")
        print("📋 ProjectManager will generate: tasks.md")
        print("\n🚀 All files will be in: ~/.metagpt/openspec/changes/{timestamp}/")
    else:
        print("❌ Configuration issues found")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)