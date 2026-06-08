"""
tests/test_tools.py
-------------------
Unit tests for all tools:
- MarkdownFixerTool
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.markdown_fixer_tool import MarkdownFixerTool


def test_markdown_fixer_empty_input():
    tool = MarkdownFixerTool()
    result = tool.use("")
    assert result["passed"] is False
    assert "error" in result
    print("✅ test_markdown_fixer_empty_input passed")


def test_markdown_fixer_missing_h1():
    tool = MarkdownFixerTool()
    result = tool.use("Some content without a title")
    assert "Missing H1" in result["issues_found"][0]
    assert result["clean_draft"].startswith("#")
    print("✅ test_markdown_fixer_missing_h1 passed")


def test_markdown_fixer_unclosed_fence():
    tool = MarkdownFixerTool()
    draft = "# Title\n\n```python\nprint('hello')\n"
    result = tool.use(draft)
    assert result["clean_draft"].count("```") % 2 == 0
    print("✅ test_markdown_fixer_unclosed_fence passed")


def test_markdown_fixer_trailing_whitespace():
    tool = MarkdownFixerTool()
    draft = "# Title   \n\nSome content   \n"
    result = tool.use(draft)
    assert "   \n" not in result["clean_draft"]
    print("✅ test_markdown_fixer_trailing_whitespace passed")


def test_markdown_fixer_valid_draft():
    tool = MarkdownFixerTool()
    draft = """# My Project

## Installation
Install the dependencies.

## Usage
Run the app.

## Dependencies
See requirements.txt

## Evaluation
See evaluate.py

## Conclusion
This is a great project.
"""
    result = tool.use(draft)
    assert result["clean_draft"].startswith("#")
    print("✅ test_markdown_fixer_valid_draft passed")


if __name__ == "__main__":
    print("\n── MarkdownFixerTool Tests ──")
    test_markdown_fixer_empty_input()
    test_markdown_fixer_missing_h1()
    test_markdown_fixer_unclosed_fence()
    test_markdown_fixer_trailing_whitespace()
    test_markdown_fixer_valid_draft()
    print("\n✅ All tests passed!")
