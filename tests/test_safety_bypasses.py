"""TDD RED phase — safety bypass test suite.

All bypass tests MUST FAIL with AssertionError, proving the bypass exists in
the current CommandSafety implementation in ttyt_cli/safety.py.

Do NOT modify ttyt_cli/safety.py — that is Task 2 (GREEN phase).

Current known bypass categories:
    B1:   Newline injection (chain splitter ignores \\n)
    B2:   python -c with destructive os.system(...)
    B3:   perl -e with destructive system(...)
    B4:   ruby -e with destructive system(...)
    B5:   node -e with destructive child_process.execSync(...)
    B6:   go run (executes arbitrary code from a file)
    B7:   find . -exec rm (destructive action on matched files)
    B8:   awk BEGIN {system(...)} (arbitrary command execution)
    B9:   sed -i (in-place file modification)
    B11:  rm -rf ~ (home directory destruction)
    B12:  rm -rf /* (root destruction)
    B13:  rm -rf $HOME (variable expansion destruction)
    B14:  rm -rf . (current directory destruction)
    B15:  \\rm -rf / (backslash-escaped rm)
    B16:  {rm,-rf,/} (brace expansion)
    B17:  eval "rm -rf /"
    B18:  exec rm -rf /
    B19:  source malicious.sh
    B20:  pwsh -Command destructive PowerShell Core operations
    B21:  doas rm -rf / (privilege escalation via doas)
"""

import pytest

from ttyt_cli.safety import CommandSafety, CommandRisk


# =============================================================================
# HAPPY PATH — must ALL PASS
# =============================================================================

class TestHappyPath:
    """Legitimate commands the classifier should correctly mark SAFE."""

    def test_python_script(self):
        """python script.py — legitimate Python invocation, no risk."""
        assert CommandSafety.classify("python script.py") == CommandRisk.SAFE

    def test_find_readonly(self):
        """find . -name '*.py' — read-only search, no modification."""
        assert CommandSafety.classify('find . -name "*.py"') == CommandRisk.SAFE

    def test_sed_no_inplace(self):
        """sed without -i — read-only stream transformation."""
        assert CommandSafety.classify("sed 's/a/b/' file.txt") == CommandRisk.SAFE

    def test_ls_la(self):
        """ls -la — harmless directory listing."""
        assert CommandSafety.classify("ls -la") == CommandRisk.SAFE


# =============================================================================
# BYPASS TESTS — all must FAIL (RED phase)
#
# Each test asserts the CORRECT classification that current safety.py does NOT
# produce, proving the bypass exists.
# =============================================================================

class TestNewlineInjection:
    """
    B1 / B10 — Newline as chain operator.

    _split_chained_command only splits on ``&&``, ``||``, ``;`` — NOT ``\\n``.
    The entire multi-line input is fed to _classify_single, which classifies
    by the first token (``ls``) and returns SAFE.  A destructive ``rm -rf /``
    on the second line bypasses all safety checks.
    """

    def test_newline_injection(self):
        """ls -la<NEWLINE>rm -rf / should NOT be safe."""
        cmd = "ls -la\nrm -rf /"
        assert CommandSafety.classify(cmd) != CommandRisk.SAFE


class TestInterpreterSystemCalls:
    """
    B2–B6 — Interpreters in SAFE_COMMANDS with arbitrary execution.

    ``python``, ``perl``, ``ruby``, ``node``, ``go`` are blanket-listed as
    SAFE_COMMANDS.  Each can trivially execute arbitrary shell commands.
    """

    def test_python_c_os_system(self):
        """python -c can run destructive os.system()."""
        cmd = 'python -c "import os; os.system(\'rm -rf /\')"'
        assert CommandSafety.classify(cmd) != CommandRisk.SAFE

    def test_perl_e_system(self):
        """perl -e can run destructive system()."""
        cmd = 'perl -e "system(\'rm -rf /\')"'
        assert CommandSafety.classify(cmd) != CommandRisk.SAFE

    def test_ruby_e_system(self):
        """ruby -e can run destructive system()."""
        cmd = 'ruby -e "system(\'rm -rf /\')"'
        assert CommandSafety.classify(cmd) != CommandRisk.SAFE

    def test_node_e_exec(self):
        """node -e can run destructive child_process.execSync()."""
        cmd = "node -e \"require('child_process').execSync('rm -rf /')\""
        assert CommandSafety.classify(cmd) != CommandRisk.SAFE

    def test_go_run(self):
        """go run executes arbitrary code from a source file."""
        assert CommandSafety.classify("go run malicious.go") != CommandRisk.SAFE


class TestFindExecDestructive:
    """
    B7 — find . -exec with destructive action.

    ``find`` is blanket SAFE even though ``-exec`` runs a command on every
    matched file.
    """

    def test_find_exec_rm(self):
        """find . -exec rm {} \\; runs rm on matched files."""
        cmd = "find . -exec rm {} \\;"
        assert CommandSafety.classify(cmd) != CommandRisk.SAFE


class TestAwkSedSystemCalls:
    """
    B8–B9 — awk / sed arbitrary command execution.

    ``awk`` is SAFE_COMMANDS but its ``system()`` function runs shell
    commands.  ``sed`` is SAFE_COMMANDS, but ``-i`` modifies files in place.
    """

    def test_awk_system(self):
        """awk BEGIN {system(...)} executes shell commands."""
        cmd = "awk 'BEGIN {system(\"rm -rf /\")}'"
        assert CommandSafety.classify(cmd) != CommandRisk.SAFE

    def test_sed_inplace(self):
        """sed -i modifies files in place — destructive."""
        assert CommandSafety.classify("sed -i 's/a/b/' file.txt") != CommandRisk.SAFE


class TestRmVariantsDanger:
    """
    B11–B16 — rm -rf variants that evade DANGER_COMMANDS prefix matching.

    DANGER_COMMANDS uses strict:
        startswith(danger_cmd + " ") or cmd_lower == danger_cmd

    Many destructive ``rm`` forms do not match, returning only CAUTION.
    """

    def test_rm_rf_home(self):
        """rm -rf ~ destroys the home directory — must be DANGER."""
        assert CommandSafety.classify("rm -rf ~") == CommandRisk.DANGER

    def test_rm_rf_root_splat(self):
        """rm -rf /* destroys root — must be DANGER."""
        assert CommandSafety.classify("rm -rf /*") == CommandRisk.DANGER

    def test_rm_rf_env_home(self):
        """rm -rf $HOME destroys home via variable — must be DANGER."""
        assert CommandSafety.classify("rm -rf $HOME") == CommandRisk.DANGER

    def test_rm_rf_dot(self):
        """rm -rf . destroys current directory — must be DANGER."""
        assert CommandSafety.classify("rm -rf .") == CommandRisk.DANGER

    def test_rm_r_flag_root(self):
        """rm -r / (without -f) is still destructive — must be DANGER."""
        assert CommandSafety.classify("rm -r /") == CommandRisk.DANGER

    def test_rm_escaped_backslash(self):
        """\\rm -rf / backslash-escaped command — must be DANGER."""
        assert CommandSafety.classify("\\rm -rf /") == CommandRisk.DANGER

    def test_rm_brace_expansion(self):
        """{rm,-rf,/} brace expansion — must be DANGER."""
        assert CommandSafety.classify("{rm,-rf,/}") == CommandRisk.DANGER


class TestDangerWrappers:
    """
    B17–B19 — Wrappers that execute destructive commands.

    ``eval``, ``exec``, and ``source`` are not in DANGER_COMMANDS and not
    matched by the prefix-based detection.  They return only CAUTION.
    """

    def test_eval_rm(self):
        """eval 'rm -rf /' runs destructive command — must be DANGER."""
        assert CommandSafety.classify('eval "rm -rf /"') == CommandRisk.DANGER

    def test_exec_rm(self):
        """exec rm -rf / replaces shell with destructive command — must be DANGER."""
        assert CommandSafety.classify("exec rm -rf /") == CommandRisk.DANGER

    def test_source_malicious(self):
        """source executes script in current shell — must be DANGER."""
        assert CommandSafety.classify("source malicious.sh") == CommandRisk.DANGER


class TestPrivilegeEscalation:
    """B21 — Privilege escalation via doas."""

    def test_doas_rm(self):
        """doas rm -rf / escalates privileges for destructive act — must be DANGER."""
        assert CommandSafety.classify("doas rm -rf /") == CommandRisk.DANGER


class TestPowerShellCore:
    """B20 — PowerShell Core (pwsh) destructive operations."""

    def test_pwsh_destructive(self):
        """pwsh -Command destructive operation — must be DANGER."""
        cmd = 'pwsh -Command "Remove-Item -Recurse C:\\"'
        assert CommandSafety.classify(cmd) == CommandRisk.DANGER
