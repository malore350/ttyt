"""Tests for intent classification."""

from ttyt_cli.intent import classify_intent, IntentType


class TestClassifyIntent:
    def test_shell_command(self):
        assert classify_intent("ls -la") == IntentType.SHELL

    def test_nl_command(self):
        assert classify_intent("find my keys") == IntentType.COMMAND

    def test_question(self):
        assert classify_intent("what is git rebase?") == IntentType.QUESTION

    def test_goal(self):
        assert classify_intent("set up a python project with pytest and pre-commit") == IntentType.GOAL

    def test_nl_list_files(self):
        assert classify_intent("list files in current directory") == IntentType.COMMAND

    def test_direct_shell(self):
        assert classify_intent("git status") == IntentType.SHELL

    def test_question_how(self):
        assert classify_intent("how do I undo the last commit") == IntentType.QUESTION

    def test_question_interrogative(self):
        assert classify_intent("is this a git repo") == IntentType.QUESTION

    def test_goal_long_text(self):
        assert classify_intent("create a new django application with authentication and database migrations") == IntentType.GOAL

    def test_slash_command(self):
        assert classify_intent("/help") == IntentType.COMMAND

    def test_shell_exact_match(self):
        assert classify_intent("cd") == IntentType.SHELL

    def test_shell_with_path(self):
        assert classify_intent("cat ./README.md") == IntentType.SHELL

    def test_question_can_you(self):
        assert classify_intent("can you explain monads") == IntentType.QUESTION

    def test_goal_and_then(self):
        assert classify_intent("build the project and then run the tests") == IntentType.GOAL

    def test_nl_no_shell_starter(self):
        assert classify_intent("undo my last commit") == IntentType.COMMAND
