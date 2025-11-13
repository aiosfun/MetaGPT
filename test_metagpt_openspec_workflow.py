#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MetaGPT OpenSpec Workflow Test

This test specifically focuses on testing the MetaGPT workflow with OpenSpec integration,
including detailed log analysis and file generation verification.
"""

import sys
import asyncio
import json
import tempfile
import re
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, '.')


class MetaGPTWorkflowTester:
    def __init__(self):
        self.test_results = []
        self.workspace_path = None

    async def setup_test_environment(self):
        """Setup test environment and load configuration"""
        print("🔧 Setting up MetaGPT workflow test environment...")
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

    async def test_metagpt_command_execution(self):
        """Test MetaGPT command execution with comprehensive analysis"""
        print("\n🚀 Testing MetaGPT Command Execution with OpenSpec")
        print("=" * 60)

        try:
            # Get baseline state
            baseline_state = await self.capture_baseline_state()

            # Execute MetaGPT command
            command = 'metagpt "create a todo list management system with web interface" --investment 4.0'
            print(f"🔄 Executing: {command}")

            execution_result = await self.execute_metagpt_command(command)

            # Analyze execution results
            analysis_result = await self.analyze_execution_results(
                execution_result, baseline_state
            )

            # Evaluate overall success
            success = self.evaluate_workflow_success(analysis_result)

            if success:
                print("✅ MetaGPT OpenSpec workflow test PASSED")
                self.test_results.append(("metagpt_workflow", True, analysis_result))
            else:
                print("❌ MetaGPT OpenSpec workflow test FAILED")
                self.test_results.append(("metagpt_workflow", False, analysis_result))

            return success

        except Exception as e:
            print(f"❌ MetaGPT workflow test failed: {e}")
            import traceback
            traceback.print_exc()
            self.test_results.append(("metagpt_workflow", False, str(e)))
            return False

    async def capture_baseline_state(self):
        """Capture the baseline state before running MetaGPT"""
        print("📊 Capturing baseline state...")

        changes_dir = self.workspace_path / "changes"

        # Count existing directories
        existing_dirs = list(changes_dir.glob("*"))
        existing_count = len(existing_dirs)

        # Get modification times
        dir_times = {d.name: d.stat().st_mtime for d in existing_dirs if d.is_dir()}

        # Count existing files
        total_files = 0
        md_files = 0
        json_files = 0

        for change_dir in existing_dirs:
            if change_dir.is_dir():
                files = list(change_dir.glob("*"))
                total_files += len(files)
                md_files += len([f for f in files if f.suffix == '.md'])
                json_files += len([f for f in files if f.suffix == '.json'])

        baseline = {
            'timestamp': datetime.now().timestamp(),
            'dir_count': existing_count,
            'total_files': total_files,
            'md_files': md_files,
            'json_files': json_files,
            'dir_times': dir_times
        }

        print(f"   Directories: {existing_count}")
        print(f"   Total files: {total_files}")
        print(f"   Markdown files: {md_files}")

        return baseline

    async def execute_metagpt_command(self, command):
        """Execute MetaGPT command and capture output"""
        print("⚡ Executing MetaGPT command...")

        # Create temporary log file
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.log', delete=False) as log_file:
            log_path = log_file.name

        try:
            # Execute command with timeout
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/home/aiforfun/working/MetaGPT"
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)  # 5 minutes

            return_code = process.returncode

            # Save logs
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')

            with open(log_path, 'w') as f:
                f.write(f"Command: {command}\n")
                f.write(f"Return Code: {return_code}\n")
                f.write(f"Timestamp: {datetime.now()}\n")
                f.write("=" * 50 + "\n")
                f.write("STDOUT:\n")
                f.write(stdout_text)
                f.write("\n" + "=" * 50 + "\n")
                f.write("STDERR:\n")
                f.write(stderr_text)

            print(f"   Command completed with return code: {return_code}")
            print(f"   Log saved to: {log_path}")

            return {
                'command': command,
                'return_code': return_code,
                'stdout': stdout_text,
                'stderr': stderr_text,
                'full_log': stdout_text + stderr_text,
                'log_path': log_path,
                'timestamp': datetime.now().timestamp()
            }

        except asyncio.TimeoutError:
            print("   ⚠️ Command timed out after 5 minutes")
            if 'process' in locals():
                process.kill()
                stdout, stderr = await process.communicate()

            return {
                'command': command,
                'return_code': -1,
                'timeout': True,
                'error': 'Command timed out',
                'log_path': log_path
            }

        except Exception as e:
            print(f"   ❌ Command execution failed: {e}")
            return {
                'command': command,
                'return_code': -2,
                'error': str(e),
                'log_path': log_path
            }

    async def analyze_execution_results(self, execution_result, baseline):
        """Analyze the results of MetaGPT execution"""
        print("\n🔍 Analyzing execution results...")

        analysis = {
            'execution_success': execution_result.get('return_code', -1) == 0,
            'timeout': execution_result.get('timeout', False),
            'log_analysis': {},
            'file_analysis': {},
            'openspec_integration': {}
        }

        # Analyze logs
        analysis['log_analysis'] = await self.analyze_logs(execution_result)

        # Analyze file changes
        analysis['file_analysis'] = await self.analyze_file_changes(baseline)

        # Analyze OpenSpec integration
        analysis['openspec_integration'] = await self.analyze_openspec_integration(
            execution_result, analysis['file_analysis']
        )

        return analysis

    async def analyze_logs(self, execution_result):
        """Analyze execution logs for indicators and errors"""
        print("   📋 Analyzing logs...")

        log_text = execution_result.get('full_log', '')
        log_analysis = {
            'openspec_indicators': [],
            'error_patterns': [],
            'success_indicators': [],
            'workflow_stages': []
        }

        # Check for OpenSpec integration indicators
        openspec_patterns = [
            r'OpenSpec workspace initialized',
            r'OpenSpec mode.*set to',
            r'OpenSpec mode.*updated',
            r'OpenSpec specification saved',
            r'OpenSpec design saved',
            r'OpenSpec tasks saved',
            r'ProductManager.*OpenSpec',
            r'Architect.*OpenSpec',
            r'ProjectManager.*OpenSpec'
        ]

        for pattern in openspec_patterns:
            matches = re.findall(pattern, log_text, re.IGNORECASE)
            if matches:
                log_analysis['openspec_indicators'].extend(matches)

        # Check for error patterns
        error_patterns = [
            (r'ERROR', 'Errors'),
            (r'CRITICAL', 'Critical errors'),
            (r'Exception', 'Exceptions'),
            (r'Traceback', 'Tracebacks'),
            (r'Failed', 'Failures'),
            (r'AttributeError', 'Attribute errors'),
            (r'ImportError', 'Import errors')
        ]

        for pattern, description in error_patterns:
            matches = re.findall(pattern, log_text, re.IGNORECASE)
            count = len(matches)
            if count > 0:
                log_analysis['error_patterns'].append({
                    'type': description,
                    'count': count
                })

        # Check for success indicators
        success_patterns = [
            (r'Task.*finished', 'Completed tasks'),
            (r'Generated.*successfully', 'Successful generation'),
            (r'Saved.*workspace', 'Workspace saves'),
            (r'Completed.*workflow', 'Workflow completion')
        ]

        for pattern, description in success_patterns:
            matches = re.findall(pattern, log_text, re.IGNORECASE)
            if matches:
                log_analysis['success_indicators'].extend(matches)

        # Check for workflow stages
        stage_patterns = [
            (r'ProductManager|Product Manager', 'Product Management'),
            (r'Architect|Architecture', 'Architecture Design'),
            (r'ProjectManager|Project Manager', 'Project Management'),
            (r'Engineer|Engineering', 'Engineering'),
            (r'QATest|Quality Assurance', 'QA Testing')
        ]

        for pattern, stage in stage_patterns:
            if re.search(pattern, log_text, re.IGNORECASE):
                log_analysis['workflow_stages'].append(stage)

        # Print summary
        print(f"      OpenSpec indicators: {len(log_analysis['openspec_indicators'])}")
        print(f"      Error patterns: {len(log_analysis['error_patterns'])}")
        print(f"      Success indicators: {len(log_analysis['success_indicators'])}")
        print(f"      Workflow stages: {len(log_analysis['workflow_stages'])}")

        return log_analysis

    async def analyze_file_changes(self, baseline):
        """Analyze file changes after MetaGPT execution"""
        print("   📁 Analyzing file changes...")

        changes_dir = self.workspace_path / "changes"

        # Get current state
        current_dirs = list(changes_dir.glob("*"))
        current_dir_times = {d.name: d.stat().st_mtime for d in current_dirs if d.is_dir()}

        # Find new directories (created after baseline)
        new_dirs = []
        modified_dirs = []

        for dir_name, mtime in current_dir_times.items():
            if mtime > baseline['timestamp']:
                if dir_name not in baseline['dir_times']:
                    new_dirs.append(dir_name)
                else:
                    modified_dirs.append(dir_name)

        # Analyze new/modified directories
        analysis_details = []
        for dir_name in new_dirs + modified_dirs:
            dir_path = changes_dir / dir_name
            if dir_path.is_dir():
                files = list(dir_path.glob("*"))

                file_analysis = {
                    'dir_name': dir_name,
                    'total_files': len(files),
                    'md_files': len([f for f in files if f.suffix == '.md']),
                    'json_files': len([f for f in files if f.suffix == '.json']),
                    'required_files': [],
                    'file_sizes': {}
                }

                # Check for required OpenSpec files
                required_files = ["requirement.md", "design.md", "tasks.md"]
                for req_file in required_files:
                    file_path = dir_path / req_file
                    if file_path.exists():
                        file_analysis['required_files'].append(req_file)
                        file_analysis['file_sizes'][req_file] = file_path.stat().st_size

                analysis_details.append(file_analysis)

        print(f"      New directories: {len(new_dirs)}")
        print(f"      Modified directories: {len(modified_dirs)}")
        print(f"      Total analyzed: {len(analysis_details)}")

        return {
            'new_dirs': new_dirs,
            'modified_dirs': modified_dirs,
            'details': analysis_details
        }

    async def analyze_openspec_integration(self, execution_result, file_analysis):
        """Analyze OpenSpec integration quality"""
        print("   🔗 Analyzing OpenSpec integration...")

        integration_score = 0
        max_score = 5
        integration_details = []

        # 1. Log indicators (20 points)
        log_indicators = len(execution_result.get('log_analysis', {}).get('openspec_indicators', []))
        if log_indicators >= 3:
            integration_score += 1
            integration_details.append("Strong OpenSpec log indicators")
        elif log_indicators >= 1:
            integration_score += 0.5
            integration_details.append("Some OpenSpec log indicators")

        # 2. File generation (20 points)
        new_dirs = len(file_analysis.get('new_dirs', []))
        if new_dirs >= 1:
            integration_score += 1
            integration_details.append(f"Generated {new_dirs} new OpenSpec directories")

        # 3. Complete file sets (20 points)
        complete_dirs = sum(1 for detail in file_analysis.get('details', [])
                           if len(detail['required_files']) == 3)
        if complete_dirs >= 1:
            integration_score += 1
            integration_details.append(f"Generated {complete_dirs} complete OpenSpec file sets")

        # 4. File quality (20 points)
        substantial_files = 0
        for detail in file_analysis.get('details', []):
            for file_name, size in detail.get('file_sizes', {}).items():
                if size > 500:  # Substantial content
                    substantial_files += 1

        if substantial_files >= 3:
            integration_score += 1
            integration_details.append(f"Generated {substantial_files} substantial files")

        # 5. Error-free execution (20 points)
        error_patterns = execution_result.get('log_analysis', {}).get('error_patterns', [])
        major_errors = [e for e in error_patterns if 'Error' in e['type'] or 'Exception' in e['type']]
        if not major_errors:
            integration_score += 1
            integration_details.append("Error-free execution")

        integration_percentage = (integration_score / max_score) * 100

        print(f"      Integration score: {integration_percentage:.1f}%")
        for detail in integration_details:
            print(f"         - {detail}")

        return {
            'score': integration_score,
            'max_score': max_score,
            'percentage': integration_percentage,
            'details': integration_details
        }

    def evaluate_workflow_success(self, analysis_result):
        """Evaluate overall workflow success"""
        print("\n📊 Evaluating workflow success...")

        success_criteria = {
            'execution_success': analysis_result['execution_success'],
            'no_timeout': not analysis_result.get('timeout', False),
            'has_openspec_logs': len(analysis_result['log_analysis']['openspec_indicators']) > 0,
            'has_new_files': len(analysis_result['file_analysis']['new_dirs']) > 0,
            'good_integration': analysis_result['openspec_integration']['percentage'] >= 60
        }

        passed_criteria = sum(success_criteria.values())
        total_criteria = len(success_criteria)

        print(f"   Success Criteria ({passed_criteria}/{total_criteria}):")
        for criterion, passed in success_criteria.items():
            status = "✅" if passed else "❌"
            print(f"      {status} {criterion.replace('_', ' ').title()}")

        overall_success = passed_criteria >= 4  # At least 4 out of 5 criteria

        if overall_success:
            print("   🎉 Overall: WORKFLOW SUCCESSFUL")
        else:
            print("   💥 Overall: WORKFLOW NEEDS IMPROVEMENT")

        return overall_success

    def print_detailed_report(self):
        """Print detailed test report"""
        print("\n" + "=" * 70)
        print("📋 METAGPT OPENSPEC WORKFLOW TEST REPORT")
        print("=" * 70)

        for test_name, passed, details in self.test_results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"\n{test_name}: {status}")

            if isinstance(details, dict):
                if 'openspec_integration' in details:
                    integration = details['openspec_integration']
                    print(f"   Integration Score: {integration['percentage']:.1f}%")
                    print(f"   Details: {', '.join(integration['details'])}")

                if 'file_analysis' in details:
                    file_analysis = details['file_analysis']
                    print(f"   New Directories: {len(file_analysis['new_dirs'])}")
                    print(f"   Modified Directories: {len(file_analysis['modified_dirs'])}")

        print("\n" + "=" * 70)

    async def run_test(self):
        """Run the complete MetaGPT OpenSpec workflow test"""
        print("🧪 Starting MetaGPT OpenSpec Workflow Test")
        print("=" * 70)

        # Setup
        if not await self.setup_test_environment():
            return False

        # Run test
        success = await self.test_metagpt_command_execution()

        # Print report
        self.print_detailed_report()

        return success


async def main():
    """Main test runner"""
    tester = MetaGPTWorkflowTester()
    success = await tester.run_test()

    if success:
        print("\n🎉 MetaGPT OpenSpec workflow test completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 MetaGPT OpenSpec workflow test failed.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())