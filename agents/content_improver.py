"""
Agent 1 — Repo Analyzer (Data Extractor)
-----------------------------------------
Role    : Simulates RAG retrieval to understand the repository
          structure and extract raw project context.
Input   : Project URL and User Goal statement.
Output  : Raw project context, file inventory, and structured
          metadata summary — stored in the shared pipeline state.
"""

import os
from openai import OpenAI
from tools.repo_reader_tool import RepoReaderTool


class RepoAnalyzer:
    """Extracts and summarises project context from a GitHub repository."""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.repo_reader_tool = RepoReaderTool()
        self.model = "gpt-4o"

    def run(self, state: dict) -> dict:
        """
        Step 1 of the pipeline.

        Reads the repository, then uses an LLM to produce a structured
        project summary that downstream agents can consume.

        Args:
            state: Pipeline state dict containing 'url' and 'goal'.

        Returns:
            Updated state dict with 'repo_context' and 'project_summary' added.
        """
        url = state.get("url", "")
        goal = state.get("goal", "")

        print(f"\n[RepoAnalyzer] Reading repository: {url}")

        # --- Tool call: read the repository ---
        repo_data = self.repo_reader_tool.use(url)

        if "error" in repo_data:
            print(f"[RepoAnalyzer] Warning: {repo_data['error']}")

        # --- LLM call: produce a structured project summary ---
        prompt = self._build_prompt(repo_data, goal)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a technical analyst specialising in AI/ML repositories. "
                        "Your job is to extract a clear, structured project summary from "
                        "raw repository data. Be factual and concise."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=800,
        )

        project_summary = response.choices[0].message.content.strip()
        print(f"[RepoAnalyzer] Summary generated ({len(project_summary)} chars).")

        # --- Update and return state ---
        state["repo_context"] = repo_data
        state["project_summary"] = project_summary
        return state

    def _build_prompt(self, repo_data: dict, goal: str) -> str:
        file_tree_preview = "\n".join(repo_data.get("file_tree", [])[:30])
        readme_preview = repo_data.get("readme_content", "")[:1500]
        requirements = ", ".join(repo_data.get("requirements", [])) or "Not found"

        return f"""
You have been given the following raw data from a GitHub repository.

Repository: {repo_data.get('repo_name', 'Unknown')}
Description: {repo_data.get('description', 'None provided')}
Primary Language: {repo_data.get('language', 'Unknown')}
Existing Topics/Tags: {repo_data.get('topics', [])}
Stars: {repo_data.get('stars', 0)}

User's Goal: {goal}

File Tree (first 30 files):
{file_tree_preview}

Requirements:
{requirements}

README Preview:
{readme_preview}

---
Please produce a structured project summary with the following sections:
1. Project Purpose (2-3 sentences)
2. Core Technical Stack (bullet list)
3. Key Features (bullet list, max 5)
4. Target Audience
5. Gaps or Weaknesses in Current Documentation (bullet list)
""".strip()
