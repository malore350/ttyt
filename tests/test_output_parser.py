"""Tests for ttyt_cli.output_parser.parse_llm_command."""

from ttyt_cli.output_parser import parse_llm_command


class TestParseLLMCommand:
    """Verify parse_llm_command handles fences, prose, edge-cases."""

    def test_fenced_bash(self):
        """ ```bash\nls -la\n```  ->  "ls -la" """
        result = parse_llm_command("```bash\nls -la\n```")
        assert result == "ls -la"

    def test_fenced_no_lang(self):
        """ ```\nls -la\n```  ->  "ls -la" """
        result = parse_llm_command("```\nls -la\n```")
        assert result == "ls -la"

    def test_unfenced_command(self):
        """ "ls -la"  ->  "ls -la" """
        result = parse_llm_command("ls -la")
        assert result == "ls -la"

    def test_empty_output(self):
        """ ""  ->  None """
        result = parse_llm_command("")
        assert result is None

    def test_whitespace_only(self):
        """ "   \\n  "  ->  None """
        result = parse_llm_command("   \n  ")
        assert result is None

    def test_empty_fence(self):
        """ ```bash\\n\\n```  ->  None """
        result = parse_llm_command("```bash\n\n```")
        assert result is None

    def test_multi_line_command(self):
        """ Fenced multi-line shell script. """
        result = parse_llm_command(
            "```bash\ngit add .\ngit commit -m 'msg'\n```"
        )
        assert result == "git add .\ngit commit -m 'msg'"

    def test_prose_before_command(self):
        """ Prose followed by paragraph break + command. """
        result = parse_llm_command("Here is the command:\n\nls -la")
        assert result == "ls -la"

    def test_prose_only_returns_none(self):
        """ Pure prose without a command returns None. """
        result = parse_llm_command("This is the answer to your question.")
        assert result is None


