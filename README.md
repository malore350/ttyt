# ttyt - AI-Powered Terminal Companion

> **Stop memorizing flags. Start talking to your terminal.**

`ttyt` ("talk to your terminal") is a smart wrapper for your command line interface. It sits between you and your shell, using advanced LLMs to translate natural language into safe, executable shell commands. It supports Windows (Git Bash), Linux, and macOS.

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-win%20|%20linux%20|%20osx-lightgrey)

## ✨ Features

- **🗣️ Natural Language to Shell**: Just type "undo my last commit" or "find all large jpg files" and watch it happen.
- **🛡️ Smart Safety System**: A three-tier risk classifier (Safe, Caution, Danger) prevents you from accidentally running destructive commands like `rm -rf`.
- **🤖 Agentic Mode**: Autonomous task execution with auto-retry and intelligent error recovery. The AI will:
  - Attempt to achieve your goal through multiple iterations
  - Explore errors with read-only commands to diagnose issues
  - Generate fix commands based on failure analysis
  - Verify goal achievement before stopping
- **💬 Direct Chat Mode**: Need to ask a coding question? Use `/ask` to chat with the AI without executing commands.
- **🔌 Multi-Provider Support**: Switch seamlessly between top-tier AI models:
  - **Google Gemini** (Flash 2.5, Pro)
  - **Z.ai** (GLM-4)
  - **OpenRouter** (NVIDIA Nemotron, etc.)
- **📁 Context Aware**: The AI knows your current directory and command history, allowing for context-aware suggestions.

---

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- `pip` package manager

### 🪟 Windows (PowerShell)
1. Open PowerShell in the project directory.
2. Run the installer:
   ```powershell
   .\install.ps1
   ```
3. Restart your terminal or reload your path.

### 🐧 Unix / Linux / macOS
1. Open your terminal in the project directory.
2. Make the script executable and run it:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

### 🛠️ Manual / Developer Install
If you prefer `pip` directly:
```bash
pip install .
```

---

## 🎮 Usage

Once installed, simply type `ttyt` to enter the environment.

```bash
$ ttyt
```

### Basic Interaction
Just type what you want to do!

**User**: `list all python files sorted by size`  
**ttyt**: `find . -name "*.py" -exec ls -lS {} +`  
*[SAFE] Read-only command, auto-executing*

**User**: `delete the temp folder`
**ttyt**: `rm -rf temp`
*[CAUTION] Requires confirmation - may modify system*
*Execute? [y/N]*

### Agentic Mode

The `/agent` command enables autonomous task execution with intelligent error recovery. Instead of manually fixing errors, the AI will iterate up to 3 times to achieve your goal.

**User**: `/agent fix all lint errors in the project`

**ttyt** will then:
1. **Attempt 1**: Generate and execute a command (e.g., `npm run lint`)
2. **If failed**: Analyze the error, optionally explore with read-only commands (`cat`, `ls`, `grep`)
3. **Fix and retry**: Generate a new command based on the error and exploration
4. **Verify**: Check if the goal was achieved (exit code 0 + output analysis)
5. **Repeat**: Continue until goal achieved or max attempts reached

**Example Output**:
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Agent Mode                                 ┃
┃                                             ┃
┃ Goal: fix all lint errors in the project   ┃
┃ Max attempts: 3                            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Attempt 1/3
Command: npm run lint
[SAFE] npm run lint
... (error output)
Failed: Lint found 15 errors

Exploring: cat .eslintrc.json
Got 245 chars of context
Command: eslint --fix src/
...

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Success                                     ┃
┃                                             ┃
┃ Goal achieved!                              ┃
┃ All lint errors fixed successfully          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

**Agentic Mode Features**:
- **Auto-exploration**: The AI suggests read-only commands to diagnose issues (`ls`, `cat`, `grep`, `find`)
- **Context-aware fixes**: Uses project context (package.json, config files) to generate better commands
- **Goal verification**: Evaluates both exit codes and output to determine success
- **Visual progress**: Rich panels show current attempt, exploration status, and final result

**⚠️ Agent Mode Safety**:

By default, agent mode **auto-approves CAUTION commands** (like `npm install`, `git push`, file modifications) to enable autonomous operation. This allows the agent to iterate and fix issues without user intervention.

You can toggle this behavior using the `/settings` command, or manually by adding this to your `~/.ttyt/.env`:
```bash
AGENT_REQUIRE_CONFIRMATION=true
```

| Setting | Behavior |
|---------|----------|
| `false` (default) | CAUTION commands auto-execute in agent mode |
| `true` | Agent asks for confirmation before CAUTION commands |

**Note**: DANGER commands (like `rm -rf`, `del`, `git reset --hard`) are **always blocked** in both modes.

### Built-in Commands
`ttyt` comes with slash-commands to manage the environment:

| Command | Description |
|---------|-------------|
| `/agent <goal>` | Enter autonomous agentic mode. The AI will attempt to achieve your goal through multiple iterations, with intelligent error recovery. |
| `/models` | Open the interactive menu to switch AI providers (Gemini, Z.ai, etc.) or specific models. |
| `/settings` | Configure ttyt behavior (agent mode safety, etc.) with an interactive menu. |
| `/api` | Update or set API keys for your providers. |
| `/ask <query>` | Ask a general question. Example: `/ask How do I use regex in python?` |
| `/new` | Clear current context history and start a fresh session. |
| `/help` | Show the help screen and legend. |
| `/uninstall` | Remove configuration files (`~/.ttyt`). |

---

## ⚙️ Configuration

`ttyt` stores your API keys and preferences securely in your home directory.

- **Config Path**: `~/.ttyt/.env` (Linux/macOS) or `%USERPROFILE%\.ttyt\.env` (Windows).
- **Environment Variables**: You can manually set variables like `GEMINI_API_KEY` or `AI_PROVIDER` in this file.

### First Run
On your first run, `ttyt` will ask you to select a provider. If you don't have an API key set, it will prompt you to enter one and provide a link to get it.

### Configuration Options

You can customize `ttyt` behavior by adding these variables to `~/.ttyt/.env`:

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `AI_PROVIDER` | `gemini`, `zai`, `openrouter` | `gemini` | AI provider to use |
| `GEMINI_MODEL` | `gemini-2.5-flash-lite`, etc. | `gemini-2.5-flash-lite` | Gemini model selection |
| `AGENT_REQUIRE_CONFIRMATION` | `true`, `false` | `false` | Require confirmation for CAUTION commands in agent mode |

**Example `.env` file:**
```bash
AI_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
AGENT_REQUIRE_CONFIRMATION=false
```

---

## 🛡️ Safety System

We take safety seriously. Every command generated by AI goes through a strict classifier before execution.

| Level | Color | Description | Behavior |
|-------|-------|-------------|----------|
| **SAFE** | 🟢 Cyan | Read-only (ls, cat, echo, git status) | Auto-executes immediately. |
| **CAUTION** | 🟡 Yellow | Modifications (mkdir, npm install, git commit) | Requires `y/N` confirmation. |
| **DANGER** | 🔴 Red | Destructive (rm -rf, formatting, force push) | **BLOCKED** by default. |

---

## 🤝 Contributing

We welcome contributions!
1. Clone the repo.
2. Create a virtual environment: `python -m venv venv`.
3. Install in editable mode: `pip install -e .`.
4. Make your changes and submit a PR.

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

---

*Built with ❤️ by Kamran Gasimov*
