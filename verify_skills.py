#!/usr/bin/env python3
"""Verification script for Genie MCP Skills implementation."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        # Core skill modules
        from genie_mcp_server.skills import (
            create_space_skill,
            ask_skill,
            inspect_skill,
            bulk_skill,
        )
        print("  ✅ All skill modules imported")
    except Exception as e:
        print(f"  ❌ Skill import failed: {e}")
        return False

    try:
        # Utility modules
        from genie_mcp_server.skills.utils import (
            warehouse_discovery,
            conversation_manager,
            result_formatter,
            space_orchestrator,
            config_analyzer,
        )
        print("  ✅ All utility modules imported")
    except Exception as e:
        print(f"  ❌ Utility import failed: {e}")
        return False

    try:
        # Check protobuf_format enhancements
        from genie_mcp_server.models.protobuf_format import protobuf_to_config
        print("  ✅ Enhanced protobuf_format imported")
    except Exception as e:
        print(f"  ❌ Protobuf format import failed: {e}")
        return False

    return True


def test_skill_signatures():
    """Test that skill functions have correct signatures."""
    print("\nTesting skill function signatures...")

    try:
        from genie_mcp_server.skills import create_space_skill

        # Check that run function exists and has expected parameters
        assert hasattr(create_space_skill, "run"), "create_space_skill.run not found"

        # Get function signature
        import inspect
        sig = inspect.signature(create_space_skill.run)
        params = list(sig.parameters.keys())

        expected = ["catalog_name", "schema_name", "table_names", "warehouse_id",
                   "domain", "space_name", "quick", "expert"]

        for param in expected:
            assert param in params, f"Missing parameter: {param}"

        print("  ✅ create_space_skill signature correct")
    except Exception as e:
        print(f"  ❌ create_space_skill signature test failed: {e}")
        return False

    try:
        from genie_mcp_server.skills import ask_skill

        assert hasattr(ask_skill, "run"), "ask_skill.run not found"

        sig = inspect.signature(ask_skill.run)
        params = list(sig.parameters.keys())

        expected = ["question", "space_id", "space_name", "new_conversation",
                   "preview_only", "timeout", "verbose"]

        for param in expected:
            assert param in params, f"Missing parameter: {param}"

        print("  ✅ ask_skill signature correct")
    except Exception as e:
        print(f"  ❌ ask_skill signature test failed: {e}")
        return False

    try:
        from genie_mcp_server.skills import inspect_skill

        assert hasattr(inspect_skill, "run"), "inspect_skill.run not found"

        sig = inspect.signature(inspect_skill.run)
        params = list(sig.parameters.keys())

        expected = ["space_id", "mode", "compare_with", "search_tables",
                   "search_keywords", "output_file"]

        for param in expected:
            assert param in params, f"Missing parameter: {param}"

        print("  ✅ inspect_skill signature correct")
    except Exception as e:
        print(f"  ❌ inspect_skill signature test failed: {e}")
        return False

    try:
        from genie_mcp_server.skills import bulk_skill

        assert hasattr(bulk_skill, "run"), "bulk_skill.run not found"

        sig = inspect.signature(bulk_skill.run)
        params = list(sig.parameters.keys())

        expected = ["operation", "space_ids", "pattern", "add_instructions",
                   "add_tables", "dry_run"]

        for param in expected:
            assert param in params, f"Missing parameter: {param}"

        print("  ✅ bulk_skill signature correct")
    except Exception as e:
        print(f"  ❌ bulk_skill signature test failed: {e}")
        return False

    return True


def test_utility_classes():
    """Test that utility classes can be instantiated."""
    print("\nTesting utility classes...")

    try:
        from genie_mcp_server.skills.utils.conversation_manager import ConversationManager

        manager = ConversationManager()
        assert hasattr(manager, "get_or_create")
        assert hasattr(manager, "update")
        assert hasattr(manager, "get_last_space")

        print("  ✅ ConversationManager works")
    except Exception as e:
        print(f"  ❌ ConversationManager test failed: {e}")
        return False

    try:
        from genie_mcp_server.skills.utils.result_formatter import ResultFormatter

        formatter = ResultFormatter()
        assert hasattr(formatter, "format")
        assert hasattr(formatter, "format_error")

        print("  ✅ ResultFormatter works")
    except Exception as e:
        print(f"  ❌ ResultFormatter test failed: {e}")
        return False

    try:
        from genie_mcp_server.skills.utils.space_orchestrator import SpaceOrchestrator

        orchestrator = SpaceOrchestrator()
        assert hasattr(orchestrator, "generate_config_from_template")
        assert hasattr(orchestrator, "validate_and_score")

        print("  ✅ SpaceOrchestrator works")
    except Exception as e:
        print(f"  ❌ SpaceOrchestrator test failed: {e}")
        return False

    try:
        from genie_mcp_server.skills.utils.config_analyzer import ConfigAnalyzer

        analyzer = ConfigAnalyzer()
        assert hasattr(analyzer, "health_score")
        assert hasattr(analyzer, "generate_health_report")

        print("  ✅ ConfigAnalyzer works")
    except Exception as e:
        print(f"  ❌ ConfigAnalyzer test failed: {e}")
        return False

    return True


def test_file_structure():
    """Test that all expected files exist."""
    print("\nTesting file structure...")

    base = Path(__file__).parent

    expected_files = [
        "src/genie_mcp_server/skills/__init__.py",
        "src/genie_mcp_server/skills/create_space_skill.py",
        "src/genie_mcp_server/skills/ask_skill.py",
        "src/genie_mcp_server/skills/inspect_skill.py",
        "src/genie_mcp_server/skills/bulk_skill.py",
        "src/genie_mcp_server/skills/utils/__init__.py",
        "src/genie_mcp_server/skills/utils/warehouse_discovery.py",
        "src/genie_mcp_server/skills/utils/conversation_manager.py",
        "src/genie_mcp_server/skills/utils/result_formatter.py",
        "src/genie_mcp_server/skills/utils/space_orchestrator.py",
        "src/genie_mcp_server/skills/utils/config_analyzer.py",
        "SKILLS_IMPLEMENTATION.md",
        "docs/SKILLS_GUIDE.md",
    ]

    all_exist = True
    for file_path in expected_files:
        full_path = base / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (missing)")
            all_exist = False

    return all_exist


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Genie MCP Skills Verification")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Skill Signatures", test_skill_signatures()))
    results.append(("Utility Classes", test_utility_classes()))
    results.append(("File Structure", test_file_structure()))

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n🎉 All verification tests passed!")
        print("\nNext steps:")
        print("1. Test with real Databricks workspace")
        print("2. Try creating a space: /create-space")
        print("3. Try asking questions: /ask")
        print("4. Check space health: /inspect")
        print("\nSee docs/SKILLS_GUIDE.md for usage examples")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
