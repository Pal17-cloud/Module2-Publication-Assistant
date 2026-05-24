"""
MarkdownFixerTool
-----------------
Validates and fixes a Markdown draft to ensure it meets
publication-ready structural requirements.
Used by the Content Improver agent as the final quality gate.
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
    """Checks and repairs Markdown structure for publication readiness."""

    def use(self, raw_draft: str) -> dict:
        """
        Validates the draft and applies automatic fixes where possible.

        Args:
            raw_draft: Raw Markdown string from the Content Improver.

        Returns:
            A dict with:
              - clean_draft (str): Fixed Markdown content.
              - issues_found (list): List of issues detected.
              - issues_fixed (list): List of issues auto-fixed.
              - missing_sections (list): Sections still missing after fixes.
              - passed (bool): True if the draft passes all checks.
        """
        issues_found = []
        issues_fixed = []
        draft = raw_draft

        # --- Check 1: Must start with H1 ---
        if not draft.lstrip().startswith("#"):
            issues_found.append("Missing H1 title at the top of the document.")
            draft = "# Project Documentation\n\n" + draft
            issues_fixed.append("Added a placeholder H1 title.")

        # --- Check 2: No consecutive blank lines (more than 2) ---
        if re.search(r"\n{4,}", draft):
            issues_found.append("Excessive blank lines detected.")
            draft = re.sub(r"\n{4,}", "\n\n\n", draft)
            issues_fixed.append("Reduced excessive blank lines to maximum 3.")

        # --- Check 3: Unclosed code fences ---
        fence_count = draft.count("```")
        if fence_count % 2 != 0:
            issues_found.append("Unclosed code fence (odd number of ``` markers).")
            draft += "\n```\n"
            issues_fixed.append("Appended closing ``` to fix unclosed code block.")

        # --- Check 4: Required sections ---
        missing_sections = []
        headings_in_draft = [
            h.lower() for h in re.findall(r"^#{1,3}\s+(.+)$", draft, re.MULTILINE)
        ]
        for section in REQUIRED_SECTIONS:
            found = any(section in heading for heading in headings_in_draft)
            if not found:
                missing_sections.append(section)
                issues_found.append(f"Missing required section: '{section}'")

        # --- Check 5: Trailing whitespace on lines ---
        if re.search(r" +\n", draft):
            issues_found.append("Trailing whitespace found on some lines.")
            draft = re.sub(r" +\n", "\n", draft)
            issues_fixed.append("Removed trailing whitespace from all lines.")

        # --- Check 6: Ensure document ends with a newline ---
        if not draft.endswith("\n"):
            draft += "\n"
            issues_fixed.append("Added trailing newline at end of document.")

        passed = len(missing_sections) == 0 and len(issues_found) == len(issues_fixed)

        return {
            "clean_draft": draft,
            "issues_found": issues_found,
            "issues_fixed": issues_fixed,
            "missing_sections": missing_sections,
            "passed": passed,
        }
