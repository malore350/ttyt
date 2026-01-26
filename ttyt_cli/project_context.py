import os
import json
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class ProjectContext:
    project_type: str
    config_file: str
    config_content: str
    available_scripts: Dict[str, str]
    
    def format_for_prompt(self) -> str:
        lines = [f"Project type: {self.project_type}"]
        lines.append(f"Config file: {self.config_file}")
        
        if self.available_scripts:
            lines.append("Available scripts/commands:")
            for name, cmd in self.available_scripts.items():
                lines.append(f"  - {name}: {cmd}")
        
        return "\n".join(lines)


PROJECT_FILES = [
    ("package.json", "node"),
    ("Cargo.toml", "rust"),
    ("pyproject.toml", "python"),
    ("setup.py", "python"),
    ("requirements.txt", "python"),
    ("Makefile", "make"),
    ("go.mod", "go"),
    ("pom.xml", "java-maven"),
    ("build.gradle", "java-gradle"),
    ("Gemfile", "ruby"),
    ("composer.json", "php"),
    ("CMakeLists.txt", "cmake"),
    ("Dockerfile", "docker"),
    ("docker-compose.yml", "docker-compose"),
    ("docker-compose.yaml", "docker-compose"),
]


def detect_project_type(cwd: str) -> Optional[tuple]:
    for filename, project_type in PROJECT_FILES:
        filepath = os.path.join(cwd, filename)
        if os.path.exists(filepath):
            return (filepath, filename, project_type)
    return None


def extract_scripts_from_package_json(content: str) -> Dict[str, str]:
    try:
        data = json.loads(content)
        return data.get("scripts", {})
    except (json.JSONDecodeError, KeyError):
        return {}


def extract_scripts_from_pyproject(content: str) -> Dict[str, str]:
    scripts = {}
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            return scripts
    
    try:
        data = tomllib.loads(content)
        
        if "project" in data and "scripts" in data["project"]:
            for name, entry in data["project"]["scripts"].items():
                scripts[name] = entry
        
        if "tool" in data and "poetry" in data["tool"]:
            poetry = data["tool"]["poetry"]
            if "scripts" in poetry:
                for name, cmd in poetry["scripts"].items():
                    scripts[name] = cmd
    except Exception:
        pass
    
    return scripts


def extract_scripts_from_cargo(content: str) -> Dict[str, str]:
    scripts = {
        "build": "cargo build",
        "run": "cargo run",
        "test": "cargo test",
        "check": "cargo check",
    }
    
    if "[bin]" in content or "[[bin]]" in content:
        scripts["run"] = "cargo run --bin <name>"
    
    return scripts


def extract_targets_from_makefile(content: str) -> Dict[str, str]:
    targets = {}
    for line in content.split("\n"):
        if ":" in line and not line.startswith("\t") and not line.startswith("#"):
            target = line.split(":")[0].strip()
            if target and not target.startswith(".") and " " not in target:
                targets[target] = f"make {target}"
    return targets


def extract_scripts_from_composer(content: str) -> Dict[str, str]:
    try:
        data = json.loads(content)
        return data.get("scripts", {})
    except (json.JSONDecodeError, KeyError):
        return {}


def get_project_context(cwd: str) -> Optional[ProjectContext]:
    detection = detect_project_type(cwd)
    if not detection:
        return None
    
    filepath, filename, project_type = detection
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (IOError, UnicodeDecodeError):
        return None
    
    scripts: Dict[str, str] = {}
    
    if filename == "package.json":
        scripts = extract_scripts_from_package_json(content)
    elif filename == "pyproject.toml":
        scripts = extract_scripts_from_pyproject(content)
        if not scripts:
            scripts = {"run": "python -m <module>", "test": "pytest"}
    elif filename == "Cargo.toml":
        scripts = extract_scripts_from_cargo(content)
    elif filename == "Makefile":
        scripts = extract_targets_from_makefile(content)
    elif filename == "composer.json":
        scripts = extract_scripts_from_composer(content)
    elif filename == "requirements.txt":
        scripts = {"install": "pip install -r requirements.txt"}
    elif filename == "go.mod":
        scripts = {"build": "go build", "run": "go run .", "test": "go test ./..."}
    elif filename == "Gemfile":
        scripts = {"install": "bundle install", "exec": "bundle exec <cmd>"}
    elif filename in ("Dockerfile",):
        scripts = {"build": "docker build -t <name> .", "run": "docker run <name>"}
    elif filename in ("docker-compose.yml", "docker-compose.yaml"):
        scripts = {"up": "docker-compose up", "down": "docker-compose down", "build": "docker-compose build"}
    
    content_truncated = content[:2000] if len(content) > 2000 else content
    
    return ProjectContext(
        project_type=project_type,
        config_file=filename,
        config_content=content_truncated,
        available_scripts=scripts
    )


def get_directory_listing(cwd: str, max_files: int = 30) -> str:
    try:
        entries = os.listdir(cwd)
        dirs = sorted([e for e in entries if os.path.isdir(os.path.join(cwd, e)) and not e.startswith(".")])
        files = sorted([e for e in entries if os.path.isfile(os.path.join(cwd, e)) and not e.startswith(".")])
        
        result = []
        for d in dirs[:max_files // 2]:
            result.append(f"  [dir] {d}/")
        for f in files[:max_files // 2]:
            result.append(f"  [file] {f}")
        
        if len(entries) > max_files:
            result.append(f"  ... and {len(entries) - max_files} more")
        
        return "\n".join(result)
    except OSError:
        return "  (unable to list directory)"


def is_ambiguous_request(user_input: str) -> bool:
    ambiguous_phrases = [
        "run", "start", "build", "test", "install", "deploy",
        "execute", "launch", "this project", "the project",
        "this app", "the app", "this", "it"
    ]
    input_lower = user_input.lower()
    return any(phrase in input_lower for phrase in ambiguous_phrases)


def get_context_for_prompt(cwd: str, user_input: str) -> str:
    context_parts = []
    
    project_ctx = get_project_context(cwd)
    
    if project_ctx:
        context_parts.append(project_ctx.format_for_prompt())
        
        if is_ambiguous_request(user_input):
            context_parts.append(f"\nConfig file content ({project_ctx.config_file}):")
            context_parts.append(project_ctx.config_content)
    elif is_ambiguous_request(user_input):
        context_parts.append("No recognized project config found.")
        context_parts.append("Directory contents:")
        context_parts.append(get_directory_listing(cwd))
    
    return "\n".join(context_parts) if context_parts else ""
