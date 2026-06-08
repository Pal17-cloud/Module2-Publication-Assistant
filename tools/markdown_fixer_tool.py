"""
MarkdownFixerTool
-----------------
Validates and fixes a Markdown draft for publication readiness.
Includes input validation and graceful failure handling.
"""

import re


REQUIRED_SECTIONS = [
    "installation",
    "usage",
    "dependencies",
    "requirements",
    "evaluation",
    "conclusion",
]


class MarkdownFixerTool:

    def use(self, raw_draft: str) -> dict:
        if not raw_draft or not raw_draft.strip():
            return {
                "clean_draft": "",
                "issues_found": ["Input draft is empty."],
                "issues_fixed": [],
                "missing_sections": REQUIRED_SECTIONS,
                "passed": False,
                "error": "Empty input received."
            }

        issues_found = []
        issues_fixed = []
        draft = raw_draft

        if not draft.lstrip().startswith("#"):
            issues_found.append("Missing H1 title at the top.")
            draft = "# Project Documentation\n\n" + draft
            issues_fixed.append("Added placeholder H1 title.")

        if re.search(r"\n{4,}", draft):
            issues_found.append("Excessive blank lines detected.")
            draft = re.sub(r"\n{4,}", "\n\n\n", draft)
            issues_fixed.append("Reduced excessive blank lines.")

        fence_count = draft.count("```")
        if fence_count % 2 != 0:
            issues_found.append("Unclosed code fence detected.")
            draft += "\n```\n"
            issues_fixed.append("Appended closing ``` to fix unclosed code block.")

        missing_sections = []
        headings = [h.lower() for h in re.findall(r"^#{1,3}\s+(.+)$", draft, re.MULTILINE)]
        for section in REQUIRED_SECTIONS:
            if not any(section in h for h in headings):
                missing_sections.append(section)
                issues_found.append(f"Missing required section: '{section}'")

        if re.search(r" +\n", draft):
            issues_found.append("Trailing whitespace on some lines.")
            draft = re.sub(r" +\n", "\n", draft)
            issues_fixed.append("Removed trailing whitespace.")

        if not draft.endswith("\n"):
            draft += "\n"
            issues_fixed.append("Added trailing newline.")

        passed = len(missing_sections) == 0 and len(issues_found) == len(issues_fixed)

        return {
            "clean_draft": draft,
            "issues_found": issues_found,
            "issues_fixed": issues_fixed,
            "missing_sections": missing_sections,
            "passed": passed,
        }
