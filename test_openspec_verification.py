#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenSpec Integration Verification Test

This test verifies that the MetaGPT OpenSpec integration is working correctly
by analyzing the most recent execution results and generated files.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, '.')


def verify_recent_openspec_activity():
    """Verify recent OpenSpec activity and file generation"""
    print("🔍 Verifying Recent OpenSpec Activity")
    print("=" * 50)

    try:
        from metagpt.config2 import config
        workspace_path = Path(config.openspec.workspace_path).expanduser()
        changes_dir = workspace_path / "changes"

        # Get recent directories (last 15 minutes)
        recent_threshold = datetime.now().timestamp() - 900  # 15 minutes ago
        recent_dirs = []

        for change_dir in changes_dir.glob("*"):
            if change_dir.is_dir():
                mtime = change_dir.stat().st_mtime
                if mtime > recent_threshold:
                    recent_dirs.append({
                        'name': change_dir.name,
                        'path': change_dir,
                        'mtime': mtime,
                        'time_str': datetime.fromtimestamp(mtime).strftime('%H:%M:%S')
                    })

        # Sort by modification time
        recent_dirs.sort(key=lambda x: x['mtime'], reverse=True)

        print(f"📊 Found {len(recent_dirs)} recent OpenSpec directories (last 15 min):")

        if not recent_dirs:
            print("   ❌ No recent activity found")
            return False

        total_files = 0
        total_md_files = 0
        complete_sets = 0

        for dir_info in recent_dirs:
            dir_path = dir_info['path']
            files = list(dir_path.glob("*"))
            md_files = [f for f in files if f.suffix == '.md']
            json_files = [f for f in files if f.suffix == '.json']

            total_files += len(files)
            total_md_files += len(md_files)

            # Check for complete OpenSpec file set
            required_files = ["requirement.md", "design.md", "tasks.md"]
            found_required = []
            for req_file in required_files:
                if (dir_path / req_file).exists():
                    found_required.append(req_file)

            if len(found_required) == 3:
                complete_sets += 1

            print(f"\n   📁 {dir_info['name']} ({dir_info['time_str']}):")
            print(f"      - Total files: {len(files)}")
            print(f"      - Markdown: {len(md_files)}, JSON: {len(json_files)}")
            print(f"      - Required files: {', '.join(found_required) if found_required else 'None'}")

            # Show file details
            for file_path in md_files:
                size = file_path.stat().st_size
                print(f"      📄 {file_path.name}: {size} bytes")

        print(f"\n📊 Summary:")
        print(f"   Recent directories: {len(recent_dirs)}")
        print(f"   Total files: {total_files}")
        print(f"   Markdown files: {total_md_files}")
        print(f"   Complete file sets: {complete_sets}")

        # Success criteria
        success = len(recent_dirs) > 0 and total_md_files > 0

        if success:
            print("\n✅ OpenSpec integration is ACTIVE and generating files!")
            return True
        else:
            print("\n❌ OpenSpec integration needs attention")
            return False

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_metagpt_openspec_logs():
    """Check for MetaGPT OpenSpec integration in recent logs"""
    print("\n📋 Checking MetaGPT OpenSpec Integration Indicators")
    print("=" * 50)

    # Look for recent log files or processes
    import subprocess

    try:
        # Check if there are any running MetaGPT processes
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True
        )

        metagpt_processes = [line for line in result.stdout.split('\n')
                           if 'metagpt' in line and 'python' in line]

        if metagpt_processes:
            print(f"🔄 Found {len(metagpt_processes)} running MetaGPT processes:")
            for process in metagpt_processes[:2]:  # Show first 2
                print(f"   {process.strip()}")
        else:
            print("ℹ️ No running MetaGPT processes found")

        # Since we can't access MetaGPT logs directly, we'll check for recent file creation
        print("\n📝 Recent OpenSpec Activity Evidence:")

        from metagpt.config2 import config
        workspace_path = Path(config.openspec.workspace_path).expanduser()

        # Check for very recent activity (last 5 minutes)
        very_recent_threshold = datetime.now().timestamp() - 300  # 5 minutes ago
        very_recent_dirs = []

        for change_dir in (workspace_path / "changes").glob("*"):
            if change_dir.is_dir() and change_dir.stat().st_mtime > very_recent_threshold:
                very_recent_dirs.append(change_dir.name)

        if very_recent_dirs:
            print(f"✅ Evidence of very recent OpenSpec activity:")
            for dir_name in very_recent_dirs:
                print(f"   📁 {dir_name}")
            return True
        else:
            print("⚠️ No very recent OpenSpec activity detected")
            return False

    except Exception as e:
        print(f"❌ Log verification failed: {e}")
        return False


def check_openspec_file_quality():
    """Check the quality of generated OpenSpec files"""
    print("\n🔍 Checking OpenSpec File Quality")
    print("=" * 50)

    try:
        from metagpt.config2 import config
        workspace_path = Path(config.openspec.workspace_path).expanduser()

        # Find the most recent complete directory
        recent_dirs = sorted(
            [d for d in (workspace_path / "changes").glob("*") if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        quality_scores = []

        for dir_path in recent_dirs[:3]:  # Check top 3 most recent
            required_files = ["requirement.md", "design.md", "tasks.md"]
            file_quality = {}

            for req_file in required_files:
                file_path = dir_path / req_file
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8')

                    # Quality criteria
                    criteria = {
                        'length': len(content) > 200,
                        'has_sections': any(line.startswith('#') for line in content.split('\n')),
                        'has_content': len(content.strip()) > 100,
                        'not_empty': len(content.strip()) > 0
                    }

                    score = sum(criteria.values()) / len(criteria)
                    file_quality[req_file] = {
                        'size': len(content),
                        'score': score,
                        'criteria': criteria
                    }

            if file_quality:
                avg_score = sum(f['score'] for f in file_quality.values()) / len(file_quality)
                quality_scores.append({
                    'directory': dir_path.name,
                    'files': file_quality,
                    'avg_score': avg_score
                })

                print(f"\n📁 {dir_path.name}:")
                for file_name, quality in file_quality.items():
                    print(f"   📄 {file_name}: {quality['size']} chars, "
                          f"quality: {quality['score']:.1%}")

        if quality_scores:
            overall_quality = sum(q['avg_score'] for q in quality_scores) / len(quality_scores)
            print(f"\n📊 Overall file quality: {overall_quality:.1%}")

            if overall_quality >= 0.7:
                print("✅ High quality OpenSpec files")
                return True
            elif overall_quality >= 0.5:
                print("⚠️ Moderate quality OpenSpec files")
                return True
            else:
                print("❌ Low quality OpenSpec files")
                return False
        else:
            print("❌ No OpenSpec files found for quality check")
            return False

    except Exception as e:
        print(f"❌ File quality check failed: {e}")
        return False


def main():
    """Main verification function"""
    print("🧪 OpenSpec Integration Verification")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Run verification checks
    checks = [
        ("Recent Activity", verify_recent_openspec_activity),
        ("MetaGPT Integration", verify_metagpt_openspec_logs),
        ("File Quality", check_openspec_file_quality)
    ]

    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} check failed: {e}")
            results.append((check_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)

    passed_checks = sum(1 for _, passed in results if passed)
    total_checks = len(results)

    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {check_name:<20}: {status}")

    success_rate = (passed_checks / total_checks) * 100
    print(f"\nSuccess Rate: {success_rate:.1f}% ({passed_checks}/{total_checks})")

    if success_rate >= 66:
        print("\n🎉 OpenSpec Integration is WORKING!")
        print("   MetaGPT is successfully generating OpenSpec files.")
    elif success_rate >= 33:
        print("\n⚠️ OpenSpec Integration is PARTIALLY WORKING!")
        print("   Some components need attention.")
    else:
        print("\n❌ OpenSpec Integration NEEDS ATTENTION!")
        print("   Multiple issues detected.")

    print("\n" + "=" * 60)
    return success_rate >= 66


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)