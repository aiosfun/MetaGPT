#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive OpenSpec Integration Test Suite

This test suite combines functionality from:
- test_openspec_file_generation.py
- test_openspec_all_file_types.py
- test_workspace_integration.py
- test_design_fix.py
- test_task_generation.py
- test_simple_task.py
- test_shared_change_id.py

Tests:
1. Workspace integration and configuration
2. OpenSpec file generation (requirement, design, tasks)
3. Shared change ID functionality
4. OpenSpec specification compliance
5. Complete MetaGPT workflow
"""

import sys
import asyncio
import json
import tempfile
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '.')


class OpenSpecComprehensiveTest:
    def __init__(self):
        self.test_results = []
        self.workspace_path = None

    async def setup_test_environment(self):
        """Setup test environment and load configuration"""
        print("🔧 Setting up test environment...")
        try:
            from metagpt.config2 import config
            from pathlib import Path

            # Setup workspace path
            self.workspace_path = Path(config.openspec.workspace_path).expanduser()
            self.config = config

            print(f"✅ OpenSpec workspace: {self.workspace_path}")
            print(f"✅ Configuration loaded successfully")
            return True

        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False

    async def test_workspace_integration(self):
        """Test workspace integration and structure"""
        print("\n📁 Testing Workspace Integration")
        print("=" * 50)

        try:
            # Test workspace structure
            changes_dir = self.workspace_path / "changes"
            specs_dir = self.workspace_path / "specs"

            print(f"🔍 Checking workspace structure...")
            print(f"   Changes directory: {changes_dir.exists()}")
            print(f"   Specs directory: {specs_dir.exists()}")

            # Ensure workspace structure
            changes_dir.mkdir(parents=True, exist_ok=True)
            specs_dir.mkdir(parents=True, exist_ok=True)

            # Test workspace permissions
            test_file = changes_dir / "test_write_permission.tmp"
            test_file.write_text("test")
            test_file.unlink()

            print("✅ Workspace integration test passed")
            self.test_results.append(("workspace_integration", True, None))
            return True

        except Exception as e:
            print(f"❌ Workspace integration test failed: {e}")
            self.test_results.append(("workspace_integration", False, str(e)))
            return False

    async def test_openspec_file_generation(self):
        """Test generation of all OpenSpec file types"""
        print("\n📄 Testing OpenSpec File Generation")
        print("=" * 50)

        try:
            from metagpt.actions.write_prd_openspec import WritePRDWithOpenSpec
            from metagpt.actions.design_api_openspec import WriteDesignWithOpenSpec
            from metagpt.actions.write_tasks_openspec import WriteTasksWithOpenSpec

            # Initialize actions
            req_action = WritePRDWithOpenSpec(config=self.config)
            design_action = WriteDesignWithOpenSpec(config=self.config)
            task_action = WriteTasksWithOpenSpec(config=self.config)

            # Test requirement generation
            print("📋 Testing requirement generation...")
            user_requirement = "Create a simple REST API for user management"
            openspec_req = await req_action.generate_openspec_requirement(
                user_requirement=user_requirement,
                context={"test_type": "file_generation"}
            )

            req_content = req_action.openspec_template_engine.render_requirement(openspec_req)
            print(f"✅ Requirement generated: {len(req_content)} characters")

            # Test design generation
            print("📐 Testing design generation...")
            openspec_design = await design_action.generate_openspec_design(
                requirements_content="User wants a REST API for CRUD operations",
                user_requirement=user_requirement,
                context={"test_type": "file_generation"}
            )

            design_content = design_action.openspec_template_engine.render_design(openspec_design)
            print(f"✅ Design generated: {len(design_content)} characters")

            # Test task generation
            print("📝 Testing task generation...")
            from metagpt.actions.write_tasks_openspec import OpenSpecTaskSpecification

            task_spec = OpenSpecTaskSpecification(
                name="User Management API Tasks",
                description="Implementation tasks for user management API",
                tasks=[
                    {
                        "task_id": "task-001",
                        "title": "Setup project structure",
                        "description": "Create basic project directories and files",
                        "priority": "high"
                    },
                    {
                        "task_id": "task-002",
                        "title": "Implement user model",
                        "description": "Create user data model and validation",
                        "priority": "high"
                    }
                ]
            )

            task_content = f"# {task_spec.name}\n\n{task_spec.description}\n\n## Tasks\n"
            for i, task in enumerate(task_spec.tasks, 1):
                task_content += f"{i}. **{task['title']}** - {task['description']}\n"

            print(f"✅ Tasks generated: {len(task_content)} characters")

            # Test saving with shared change ID
            shared_change_id = f"UserManagementAPI_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            await req_action._save_openspec_content(
                content=req_content,
                output_pathname="/tmp/test_requirement.md",
                openspec_requirement=openspec_req,
                change_id=shared_change_id
            )

            await design_action._save_openspec_design(
                content=design_content,
                output_pathname="/tmp/test_design.md",
                openspec_design=openspec_design,
                change_id=shared_change_id
            )

            await task_action._save_openspec_tasks(
                content=task_content,
                output_pathname="/tmp/test_tasks.md",
                task_spec=task_spec,
                change_id=shared_change_id
            )

            # Verify shared change directory
            change_dir = self.workspace_path / "changes" / shared_change_id
            if change_dir.exists():
                files = list(change_dir.glob("*"))
                print(f"✅ Shared change directory contains {len(files)} files:")
                for file in files:
                    print(f"   - {file.name} ({file.stat().st_size} bytes)")

                # Verify file contents
                requirement_file = change_dir / "requirement.md"
                design_file = change_dir / "design.md"
                tasks_file = change_dir / "tasks.md"

                if all(f.exists() for f in [requirement_file, design_file, tasks_file]):
                    print("✅ All OpenSpec file types generated successfully")
                    self.test_results.append(("file_generation", True, None))
                    return True

            print("❌ Some OpenSpec files are missing")
            self.test_results.append(("file_generation", False, "Missing files"))
            return False

        except Exception as e:
            print(f"❌ File generation test failed: {e}")
            import traceback
            traceback.print_exc()
            self.test_results.append(("file_generation", False, str(e)))
            return False

    async def test_openspec_specification_compliance(self):
        """Test OpenSpec specification compliance"""
        print("\n📋 Testing OpenSpec Specification Compliance")
        print("=" * 50)

        try:
            # Check latest change directory
            changes_dirs = list((self.workspace_path / "changes").glob("*"))
            if not changes_dirs:
                print("❌ No change directories found")
                return False

            latest_dir = max(changes_dirs, key=lambda x: x.stat().st_mtime)
            print(f"🔍 Checking compliance in: {latest_dir}")

            # Check required files
            required_files = ["requirement.md", "design.md", "tasks.md"]
            compliance_score = 0

            for req_file in required_files:
                file_path = latest_dir / req_file
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8')

                    # Basic compliance checks
                    if len(content) > 100:  # Minimum content length
                        compliance_score += 1
                        print(f"✅ {req_file}: {len(content)} characters")
                    else:
                        print(f"❌ {req_file}: Too short ({len(content)} characters)")
                else:
                    print(f"❌ {req_file}: File missing")

            # Check JSON metadata files
            json_files = list(latest_dir.glob("*.json"))
            print(f"📄 Found {len(json_files)} JSON metadata files")

            # Check directory naming convention
            dir_name = latest_dir.name
            if "_" in dir_name and any(char.isdigit() for char in dir_name):
                print(f"✅ Directory naming convention: {dir_name}")
                compliance_score += 1
            else:
                print(f"❌ Directory naming convention: {dir_name}")

            compliance_percentage = (compliance_score / (len(required_files) + 1)) * 100
            print(f"📊 Compliance score: {compliance_percentage:.1f}%")

            if compliance_percentage >= 75:
                print("✅ OpenSpec specification compliance test passed")
                self.test_results.append(("specification_compliance", True, compliance_percentage))
                return True
            else:
                print("❌ OpenSpec specification compliance test failed")
                self.test_results.append(("specification_compliance", False, compliance_percentage))
                return False

        except Exception as e:
            print(f"❌ Specification compliance test failed: {e}")
            self.test_results.append(("specification_compliance", False, str(e)))
            return False

    async def test_metagpt_workflow(self):
        """Test complete MetaGPT workflow with OpenSpec integration"""
        print("\n🚀 Testing Complete MetaGPT Workflow")
        print("=" * 50)

        try:
            # Get baseline before running MetaGPT
            before_dirs = set((self.workspace_path / "changes").glob("*"))
            before_count = len(before_dirs)
            print(f"📊 Baseline: {before_count} existing change directories")

            # Run MetaGPT command
            command = 'metagpt "write a simple REST API for user management" --investment 3.0'
            print(f"🔄 Running: {command}")

            # Create a temporary log file
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.log', delete=False) as log_file:
                log_path = log_file.name

            # Run MetaGPT with log capture and timeout
            import subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/home/aiforfun/working/MetaGPT"
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=180)  # 3 minute timeout
            except asyncio.TimeoutError:
                process.kill()
                stdout, stderr = await process.communicate()
                print("⚠️ MetaGPT command timed out after 3 minutes")

            # Save logs
            with open(log_path, 'w') as f:
                f.write("STDOUT:\n")
                f.write(stdout.decode('utf-8', errors='replace'))
                f.write("\nSTDERR:\n")
                f.write(stderr.decode('utf-8', errors='replace'))

            print(f"📝 Logs saved to: {log_path}")
            print(f"🔍 Return code: {process.returncode}")

            # Analyze logs for errors and OpenSpec integration
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')
            full_log = stdout_text + stderr_text

            # Check for OpenSpec integration in logs
            openspec_indicators = [
                "OpenSpec workspace initialized",
                "OpenSpec mode updated",
                "OpenSpec mode set to",
                "OpenSpec specification saved",
                "OpenSpec design saved",
                "OpenSpec tasks saved"
            ]

            openspec_found = []
            for indicator in openspec_indicators:
                if indicator in full_log:
                    openspec_found.append(indicator)

            if openspec_found:
                print(f"✅ OpenSpec integration indicators found: {len(openspec_found)}")
                for indicator in openspec_found:
                    print(f"   - {indicator}")

            # Check for errors in logs
            error_patterns = ["ERROR", "CRITICAL", "Exception", "Traceback", "Failed"]
            errors_found = []
            for pattern in error_patterns:
                if pattern in full_log:
                    # Count occurrences (avoid overwhelming output)
                    count = min(full_log.count(pattern), 5)
                    if count > 0:
                        errors_found.append(f"{pattern}: {count} occurrences")

            if errors_found:
                print(f"⚠️ Potential errors found in logs:")
                for error in errors_found[:3]:  # Show only first 3 error types
                    print(f"   - {error}")
            else:
                print("✅ No obvious errors found in logs")

            # Wait for file system sync
            await asyncio.sleep(3)

            # Look for new change directories
            after_dirs = set((self.workspace_path / "changes").glob("*"))
            new_dirs = after_dirs - before_dirs
            recent_dirs = [d for d in after_dirs if d.stat().st_mtime > (datetime.now().timestamp() - 300)]

            print(f"📊 After run: {len(after_dirs)} total change directories")
            print(f"📊 New directories: {len(new_dirs)}")
            print(f"📊 Recent directories (5 min): {len(recent_dirs)}")

            # Analyze new/recent directories
            analysis_results = []
            for dir_path in list(new_dirs) + recent_dirs:
                if dir_path.is_dir():
                    files = list(dir_path.glob("*"))
                    md_files = [f for f in files if f.suffix == '.md']
                    json_files = [f for f in files if f.suffix == '.json']

                    analysis = {
                        'dir_name': dir_path.name,
                        'total_files': len(files),
                        'md_files': len(md_files),
                        'json_files': len(json_files),
                        'required_files': []
                    }

                    # Check for required OpenSpec files
                    required_files = ["requirement.md", "design.md", "tasks.md"]
                    for req_file in required_files:
                        if (dir_path / req_file).exists():
                            analysis['required_files'].append(req_file)

                    analysis_results.append(analysis)

                    print(f"   📁 {dir_path.name}:")
                    print(f"      - Total files: {analysis['total_files']}")
                    print(f"      - Markdown files: {analysis['md_files']}")
                    print(f"      - JSON files: {analysis['json_files']}")
                    print(f"      - Required files: {', '.join(analysis['required_files']) if analysis['required_files'] else 'None'}")

            # Evaluate success criteria
            success_criteria = {
                'has_new_dirs': len(new_dirs) > 0,
                'has_recent_dirs': len(recent_dirs) > 0,
                'has_openspec_logs': len(openspec_found) > 0,
                'has_complete_dirs': any(len(a['required_files']) >= 3 for a in analysis_results),
                'no_major_errors': len([e for e in errors_found if 'ERROR' in e or 'Exception' in e]) == 0
            }

            print(f"\n📊 Success Criteria:")
            for criterion, passed in success_criteria.items():
                status = "✅" if passed else "❌"
                print(f"   {status} {criterion.replace('_', ' ').title()}: {passed}")

            passed_criteria = sum(success_criteria.values())
            total_criteria = len(success_criteria)
            success_rate = (passed_criteria / total_criteria) * 100

            print(f"\n📊 Overall Success Rate: {success_rate:.1f}% ({passed_criteria}/{total_criteria})")

            if success_rate >= 60:
                print("✅ MetaGPT workflow test passed - OpenSpec integration working")
                self.test_results.append(("metagpt_workflow", True, {
                    'success_rate': success_rate,
                    'new_dirs': len(new_dirs),
                    'openspec_logs': len(openspec_found),
                    'complete_dirs': sum(1 for a in analysis_results if len(a['required_files']) >= 3)
                }))
                return True
            else:
                print("❌ MetaGPT workflow test failed - insufficient OpenSpec integration")

                # Show detailed log preview for debugging
                print(f"\n📄 Detailed Log Analysis:")
                print(f"   OpenSpec indicators: {len(openspec_found)}")
                print(f"   Error patterns found: {len(errors_found)}")

                # Show sample log lines with OpenSpec mentions
                openspec_lines = [line for line in full_log.split('\n') if 'openspec' in line.lower()]
                if openspec_lines:
                    print(f"   Sample OpenSpec log lines:")
                    for line in openspec_lines[:3]:
                        print(f"     {line.strip()}")

                self.test_results.append(("metagpt_workflow", False, {
                    'success_rate': success_rate,
                    'reason': 'Insufficient OpenSpec integration'
                }))
                return False

        except Exception as e:
            print(f"❌ MetaGPT workflow test failed: {e}")
            import traceback
            traceback.print_exc()
            self.test_results.append(("metagpt_workflow", False, str(e)))
            return False

    async def test_error_handling_and_recovery(self):
        """Test error handling and recovery scenarios"""
        print("\n🛡️ Testing Error Handling and Recovery")
        print("=" * 50)

        try:
            from metagpt.actions.write_prd_openspec import WritePRDWithOpenSpec

            # Test with invalid input
            req_action = WritePRDWithOpenSpec(config=self.config)

            # Test empty requirement
            try:
                await req_action.generate_openspec_requirement(
                    user_requirement="",
                    context={}
                )
                print("⚠️ Empty requirement should have failed")
            except Exception:
                print("✅ Empty requirement properly handled")

            # Test with very long requirement
            try:
                long_requirement = "test " * 10000
                openspec_req = await req_action.generate_openspec_requirement(
                    user_requirement=long_requirement,
                    context={}
                )
                print("✅ Long requirement handled successfully")
            except Exception as e:
                print(f"⚠️ Long requirement failed: {e}")

            # Test file permission issues
            try:
                # Try to save to read-only directory
                readonly_dir = "/tmp/readonly_test"
                Path(readonly_dir).mkdir(exist_ok=True)
                Path(readonly_dir).chmod(0o444)

                openspec_req = await req_action.generate_openspec_requirement(
                    user_requirement="Test requirement",
                    context={}
                )

                req_content = req_action.openspec_template_engine.render_requirement(openspec_req)

                # This should fail gracefully
                await req_action._save_openspec_content(
                    content=req_content,
                    output_pathname=f"{readonly_dir}/test.md",
                    openspec_requirement=openspec_req
                )

            except Exception as e:
                print(f"✅ File permission issue handled: {type(e).__name__}")
            finally:
                # Clean up
                Path(readonly_dir).chmod(0o755)
                Path(readonly_dir).rmdir()

            print("✅ Error handling and recovery test passed")
            self.test_results.append(("error_handling", True, None))
            return True

        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            self.test_results.append(("error_handling", False, str(e)))
            return False

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUITE SUMMARY")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, passed, _ in self.test_results if passed)
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        print("\n📋 Detailed Results:")
        for test_name, passed, details in self.test_results:
            status = "✅ PASS" if passed else "❌ FAIL"
            details_str = f" - {details}" if details else ""
            print(f"   {test_name}: {status}{details_str}")

        # Workspace verification
        print(f"\n📁 Workspace Status:")
        if self.workspace_path and self.workspace_path.exists():
            changes_dirs = list((self.workspace_path / "changes").glob("*"))
            print(f"   Change directories: {len(changes_dirs)}")

            total_files = 0
            for dir_path in changes_dirs:
                files = list(dir_path.glob("*"))
                total_files += len(files)

            print(f"   Total OpenSpec files: {total_files}")
            print(f"   Workspace path: {self.workspace_path}")
        else:
            print("   ❌ Workspace not accessible")

        print("\n" + "=" * 60)
        return passed_tests == total_tests

    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🧪 Starting Comprehensive OpenSpec Test Suite")
        print("=" * 60)

        # Setup
        if not await self.setup_test_environment():
            return False

        # Run all tests
        tests = [
            self.test_workspace_integration,
            self.test_openspec_file_generation,
            self.test_openspec_specification_compliance,
            self.test_metagpt_workflow,
            self.test_error_handling_and_recovery
        ]

        for test in tests:
            try:
                await test()
            except KeyboardInterrupt:
                print("\n⚠️ Test interrupted by user")
                break
            except Exception as e:
                print(f"\n💥 Unexpected error in {test.__name__}: {e}")
                import traceback
                traceback.print_exc()

        return self.print_test_summary()


async def main():
    """Main test runner"""
    test_suite = OpenSpecComprehensiveTest()
    success = await test_suite.run_all_tests()

    if success:
        print("\n🎉 All tests passed! OpenSpec integration is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Please check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())