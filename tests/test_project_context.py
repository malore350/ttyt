"""Tests for project context detection."""

import os
import tempfile
import json

from ttyt_cli.project_context import (
    detect_project_type,
    get_project_context,
    get_context_for_prompt,
    is_ambiguous_request,
)


class TestProjectContext:
    """Verify project type detection and context generation."""

    def test_detect_node_project(self):
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

    def test_detect_python_project(self):
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

    def test_detect_rust_project(self):
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

    def test_detect_makefile_project(self):
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

    def test_ambiguous_request_detection(self):
        assert is_ambiguous_request("run the project") is True
        assert is_ambiguous_request("start this") is True
        assert is_ambiguous_request("build it") is True
        assert is_ambiguous_request("test the app") is True
        assert is_ambiguous_request("list files in current directory") is False
        assert is_ambiguous_request("cat readme.md") is False

    def test_context_for_prompt_with_ambiguous_request(self):
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

    def test_no_project_with_ambiguous_request(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "random.txt"), "w") as f:
                f.write("just a file")

            context = get_context_for_prompt(tmpdir, "run this")

            assert "No recognized project config" in context
            assert "Directory contents" in context

    def test_context_for_specific_request(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package_json = os.path.join(tmpdir, "package.json")
            with open(package_json, "w") as f:
                json.dump({"name": "test", "scripts": {"test": "jest"}}, f)

            context = get_context_for_prompt(tmpdir, "show me git log")

            assert "node" in context
            assert "jest" in context
