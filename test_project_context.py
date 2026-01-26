#!/usr/bin/env python
"""Test script for project context detection"""

import sys
import os
import tempfile
import json
sys.path.insert(0, '.')

from ttyt_cli.project_context import (
    detect_project_type,
    get_project_context,
    get_context_for_prompt,
    is_ambiguous_request,
    extract_scripts_from_package_json,
    extract_targets_from_makefile,
)


def test_detect_node_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        package_json = os.path.join(tmpdir, "package.json")
        with open(package_json, "w") as f:
            json.dump({
                "name": "test-project",
                "scripts": {
                    "start": "node server.js",
                    "test": "jest",
                    "build": "webpack"
                }
            }, f)
        
        result = detect_project_type(tmpdir)
        assert result is not None
        filepath, filename, project_type = result
        assert filename == "package.json"
        assert project_type == "node"
        
        ctx = get_project_context(tmpdir)
        assert ctx is not None
        assert ctx.project_type == "node"
        assert "start" in ctx.available_scripts
        assert ctx.available_scripts["start"] == "node server.js"
        
        print("[PASS] Node project detection")
        return True


def test_detect_python_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        pyproject = os.path.join(tmpdir, "pyproject.toml")
        with open(pyproject, "w") as f:
            f.write("""
[project]
name = "my-project"
version = "0.1.0"
""")
        
        result = detect_project_type(tmpdir)
        assert result is not None
        filepath, filename, project_type = result
        assert filename == "pyproject.toml"
        assert project_type == "python"
        
        print("[PASS] Python project detection")
        return True


def test_detect_rust_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        cargo_toml = os.path.join(tmpdir, "Cargo.toml")
        with open(cargo_toml, "w") as f:
            f.write("""
[package]
name = "my-rust-app"
version = "0.1.0"
""")
        
        result = detect_project_type(tmpdir)
        assert result is not None
        filepath, filename, project_type = result
        assert filename == "Cargo.toml"
        assert project_type == "rust"
        
        ctx = get_project_context(tmpdir)
        assert ctx is not None
        assert "run" in ctx.available_scripts
        assert ctx.available_scripts["run"] == "cargo run"
        
        print("[PASS] Rust project detection")
        return True


def test_detect_makefile_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        makefile = os.path.join(tmpdir, "Makefile")
        with open(makefile, "w") as f:
            f.write("""
build:
\tgcc -o app main.c

test:
\t./run_tests.sh

clean:
\trm -rf build/
""")
        
        result = detect_project_type(tmpdir)
        assert result is not None
        filepath, filename, project_type = result
        assert filename == "Makefile"
        assert project_type == "make"
        
        ctx = get_project_context(tmpdir)
        assert ctx is not None
        assert "build" in ctx.available_scripts
        assert "test" in ctx.available_scripts
        assert "clean" in ctx.available_scripts
        
        print("[PASS] Makefile project detection")
        return True


def test_ambiguous_request_detection():
    assert is_ambiguous_request("run the project") == True
    assert is_ambiguous_request("start this") == True
    assert is_ambiguous_request("build it") == True
    assert is_ambiguous_request("test the app") == True
    assert is_ambiguous_request("list files in current directory") == False
    assert is_ambiguous_request("cat readme.md") == False
    
    print("[PASS] Ambiguous request detection")
    return True


def test_context_for_prompt_with_ambiguous_request():
    with tempfile.TemporaryDirectory() as tmpdir:
        package_json = os.path.join(tmpdir, "package.json")
        with open(package_json, "w") as f:
            json.dump({
                "name": "test-app",
                "scripts": {
                    "dev": "next dev",
                    "build": "next build",
                    "start": "next start"
                }
            }, f)
        
        context = get_context_for_prompt(tmpdir, "run the project")
        
        assert "node" in context
        assert "dev" in context
        assert "next dev" in context
        assert "package.json" in context
        
        print("[PASS] Context includes scripts for ambiguous request")
        print(f"\nGenerated context:\n{context[:500]}...")
        return True


def test_no_project_with_ambiguous_request():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "random.txt"), "w") as f:
            f.write("just a file")
        
        context = get_context_for_prompt(tmpdir, "run this")
        
        assert "No recognized project config" in context
        assert "Directory contents" in context
        
        print("[PASS] Directory listing for unknown project")
        return True


def test_context_for_specific_request():
    with tempfile.TemporaryDirectory() as tmpdir:
        package_json = os.path.join(tmpdir, "package.json")
        with open(package_json, "w") as f:
            json.dump({"name": "test", "scripts": {"test": "jest"}}, f)
        
        context = get_context_for_prompt(tmpdir, "show me git log")
        
        assert "node" in context
        assert "jest" in context
        
        print("[PASS] Context provided for specific request too")
        return True


if __name__ == "__main__":
    print("Testing Project Context Detection")
    print("=" * 60)
    
    all_passed = True
    tests = [
        test_detect_node_project,
        test_detect_python_project,
        test_detect_rust_project,
        test_detect_makefile_project,
        test_ambiguous_request_detection,
        test_context_for_prompt_with_ambiguous_request,
        test_no_project_with_ambiguous_request,
        test_context_for_specific_request,
    ]
    
    for test in tests:
        try:
            all_passed &= test()
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
            all_passed = False
        except Exception as e:
            print(f"[ERROR] {test.__name__}: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)
