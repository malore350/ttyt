"""Parse LLM output to extract shell commands.

Strips markdown code fences and prose to recover a single command string.
Used by the provider wrappers after every LLM call.
"""

import re
from typing import Optional


def _looks_like_command(s: str) -> bool:
    """Heuristic: a command-like string should not end with sentence punctuation."""
    s = s.strip()
    if not s:
        return False
    # Sentence-ending punctuation indicates prose, not a command
    return s[-1] not in ".?!:"


def parse_llm_command(raw_output: str) -> Optional[str]:
    """Strip markdown code fences and surrounding prose from LLM output.

    Processing order:
    1. Strip whitespace and return None if empty.
    2. Detect and extract content from a fenced code block (with optional
       language tag like `` ```bash ``).
    3. If no fence, check for a paragraph break (``\\n\\n``) and use the last
       section if it looks like a command.
    4. Return the stripped string if it already looks command-like.
    5. Otherwise return None.

    Args:
        raw_output: Raw response string from an LLM provider.

    Returns:
        Extracted command string, or None if no command could be identified.
    """
    stripped = raw_output.strip()

    if not stripped:
        return None

    # --- Fenced code block (with optional language tag) ---
    # Pattern: ^```[lang]\n<content>\n```$
    # re.DOTALL lets .*? match newlines inside the fence.
    fence_match = re.match(
        r'^```[a-z]*\s*\n(.*?)\n```$',
        stripped,
        re.DOTALL,
    )
    if fence_match:
        content = fence_match.group(1).strip()
        return content if content else None

    # --- Paragraph-split heuristic ---
    # If the output contains a double-newline, split into sections and
    # test the *last* non-empty section as a candidate command.
    if "\n\n" in stripped:
        sections = stripped.split("\n\n")
        for section in reversed(sections):
            section = section.strip()
            if section:
                if _looks_like_command(section):
                    return section
                return None

    # --- Bare pass-through ---
    if _looks_like_command(stripped):
        return stripped

    return None
