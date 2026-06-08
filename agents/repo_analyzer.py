"""
Agent 1 — Repo Analyzer (Data Extractor)
-----------------------------------------
Reads the repository and produces a structured project summary.
Includes input validation, timeout handling, and graceful failures.
"""

import os
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError
from tools.repo_reader_tool import RepoReaderTool


class RepoAnalyzer:

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. Please add it to your .env file."
            )
        self.client = OpenAI(api_key=api_key)
        self.repo_reader_tool = RepoReaderTool()
        self.model = "gpt-4o"

    def run(self, state: dict) -> dict:
        url = state.get("url", "").strip()
        goal = state.get("goal", "").strip()

        if not url:
            raise ValueError("Repository URL is required and cannot be empty.")
        if not goal:
            print("[RepoAnalyzer] Warning: No goal provided. Using default.")
            goal = "Optimize for general AI/ML developers"
            state["goal"] = goal

        print(f"\n[RepoAnalyzer] Reading repository: {url}")

        repo_data = self.repo_reader_tool.use(url)

        if "error" in repo_data:
            print(f"[RepoAnalyzer] Repository read error: {repo_data['error']}")
            repo_data["repo_name"] = url.split("/")[-1] if "/" in url else "unknown"

        prompt = self._build_prompt(repo_data, goal)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a technical analyst specialising in AI/ML repositories. "
                            "Extract a clear, structured project summary from raw repository data. "
                            "Be factual and concise."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=800,
                timeout=30,
            )
            project_summary = response.choices[0].message.content.strip()

        except APITimeoutError:
            print("[RepoAnalyzer] OpenAI API timed out. Using fallback summary.")
            project_summary = self._fallback_summary(repo_data, goal)
        except RateLimitError:
            print("[RepoAnalyzer] Rate limit reached. Please wait and try again.")
            raise
        except APIConnectionError:
            print("[RepoAnalyzer] Cannot connect to OpenAI API. Check your internet connection.")
            raise
        except Exception as e:
            print(f"[RepoAnalyzer] Unexpected error: {e}")
            project_summary = self._fallback_summary(repo_data, goal)

        print(f"[RepoAnalyzer] Summary generated ({len(project_summary)} chars).")
        state["repo_context"] = repo_data
        state["project_summary"] = project_summary
        return state

    def _build_prompt(self, repo_data: dict, goal: str) -> str:
        file_tree_preview = "\n".join(repo_data.get("file_tree", [])[:30])
        readme_preview = repo_data.get("readme_content", "")[:1500]
        requirements = ", ".join(repo_data.get("requirements", [])) or "Not found"

        return f"""
Repository: {repo_data.get('repo_name', 'Unknown')}
Description: {repo_data.get('description', 'None provided')}
Language: {repo_data.get('language', 'Unknown')}
Topics: {repo_data.get('topics', [])}
Stars: {repo_data.get('stars', 0)}
User Goal: {goal}

File Tree (first 30 files):
{file_tree_preview}

Requirements: {requirements}

README Preview:
{readme_preview}

Produce a structured summary with:
1. Project Purpose (2-3 sentences)
2. Core Technical Stack (bullet list)
3. Key Features (bullet list, max 5)
4. Target Audience
5. Documentation Gaps (bullet list)
""".strip()

    def _fallback_summary(self, repo_data: dict, goal: str) -> str:
        return (
            f"Project: {repo_data.get('repo_name', 'Unknown')}\n"
            f"Description: {repo_data.get('description', 'No description available.')}\n"
            f"Goal: {goal}\n"
            f"Requirements: {', '.join(repo_data.get('requirements', []))}\n"
            f"Files: {len(repo_data.get('file_tree', []))} files found."
        )
