"""
Agent 3 — Content Improver (Technical Editor)
----------------------------------------------
Generates and validates the final publication-ready README.md.
Includes input validation, timeout handling, and graceful failures.
"""

import os
from datetime import datetime
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError
from tools.markdown_fixer_tool import MarkdownFixerTool


class ContentImprover:

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY is not set.")
        self.client = OpenAI(api_key=api_key)
        self.markdown_fixer_tool = MarkdownFixerTool()
        self.model = "gpt-4o"

    def run(self, state: dict) -> dict:
        project_summary = state.get("project_summary", "")
        metadata = state.get("metadata_recommendations", {})
        repo_context = state.get("repo_context", {})
        goal = state.get("goal", "")

        if not project_summary:
            raise ValueError("project_summary missing. Run RepoAnalyzer first.")
        if not metadata:
            raise ValueError("metadata_recommendations missing. Run MetadataRecommender first.")

        print(f"\n[ContentImprover] Generating final README...")

        prompt = self._build_prompt(project_summary, metadata, repo_context, goal)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a senior technical writer for AI/ML open-source projects. "
                            "Write clear, professional, complete README.md files in "
                            "GitHub-flavoured Markdown. Always include all required sections."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2000,
                timeout=60,
            )
            raw_draft = response.choices[0].message.content.strip()

        except APITimeoutError:
            print("[ContentImprover] OpenAI timed out. Using minimal fallback README.")
            raw_draft = self._fallback_readme(metadata, repo_context)
        except RateLimitError:
            print("[ContentImprover] Rate limit reached.")
            raise
        except APIConnectionError:
            print("[ContentImprover] Cannot connect to OpenAI API.")
            raise
        except Exception as e:
            print(f"[ContentImprover] Unexpected error: {e}")
            raw_draft = self._fallback_readme(metadata, repo_context)

        print(f"[ContentImprover] Draft generated ({len(raw_draft)} chars). Running QA...")

        fix_result = self.markdown_fixer_tool.use(raw_draft)
        clean_draft = fix_result["clean_draft"]
        critique_report = self._build_critique(fix_result)
        output_path = self._save_output(clean_draft, repo_context)

        print(f"[ContentImprover] Saved to: {output_path}")
        print(f"[ContentImprover] QA passed: {fix_result['passed']}")

        state["final_output"] = clean_draft
        state["critique_report"] = critique_report
        state["output_path"] = output_path
        state["qa_passed"] = fix_result["passed"]
        return state

    def _build_prompt(self, summary, metadata, repo_context, goal):
        return f"""
Title: {metadata.get('optimized_title', 'Project')}
Description: {metadata.get('one_line_description', '')}
Tags: {metadata.get('suggested_tags', [])}
URL: {repo_context.get('url', '')}
Goal: {goal}
Summary: {summary}
Dependencies: {repo_context.get('requirements', [])}

Write a complete README.md with ALL of these sections:
1. Title and badges
2. One-line description
3. Table of Contents
4. Overview
5. Features
6. Requirements and Dependencies
7. Installation and Usage with code blocks
8. Evaluation Metrics
9. Project Structure
10. Conclusion
11. License MIT
""".strip()

    def _fallback_readme(self, metadata: dict, repo_context: dict) -> str:
        title = metadata.get("optimized_title", repo_context.get("repo_name", "Project"))
        desc = metadata.get("one_line_description", "")
        tags = " ".join([f"`{t}`" for t in metadata.get("suggested_tags", [])])
        return f"""# {title}

{desc}

**Tags:** {tags}

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Dependencies

See requirements.txt for full dependency list.

## Evaluation

See evaluate.py for evaluation metrics.

## Conclusion

{title} is an AI-powered documentation optimization tool.

## License

MIT License
"""

    def _build_critique(self, fix_result: dict) -> str:
        lines = [
            "## Structural Critique Report",
            f"**QA Passed:** {'✅ Yes' if fix_result['passed'] else '❌ No'}",
            "",
        ]
        if fix_result["issues_found"]:
            lines.append("### Issues Detected")
            for i in fix_result["issues_found"]:
                lines.append(f"- {i}")
        if fix_result["issues_fixed"]:
            lines.append("\n### Auto-Fixed")
            for f in fix_result["issues_fixed"]:
                lines.append(f"- ✅ {f}")
        if fix_result["missing_sections"]:
            lines.append("\n### Still Missing (add manually)")
            for s in fix_result["missing_sections"]:
                lines.append(f"- ⚠️ `{s}`")
        return "\n".join(lines)

    def _save_output(self, content: str, repo_context: dict) -> str:
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        repo_name = repo_context.get("repo_name", "project").replace("/", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"{output_dir}/README_{repo_name}_{timestamp}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path
