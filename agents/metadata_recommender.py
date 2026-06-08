"""
Agent 2 — Metadata Recommender (Discoverability Strategist)
------------------------------------------------------------
Recommends optimised titles, tags, and keywords.
Includes input validation, timeout handling, and graceful failures.
"""

import os
import json
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError
from tools.google_search_tool import GoogleSearchTool


class MetadataRecommender:

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY is not set.")
        self.client = OpenAI(api_key=api_key)
        self.search_tool = GoogleSearchTool()
        self.model = "gpt-4o"

    def run(self, state: dict) -> dict:
        project_summary = state.get("project_summary", "")
        goal = state.get("goal", "")
        repo_name = state.get("repo_context", {}).get("repo_name", "this project")

        if not project_summary:
            raise ValueError(
                "project_summary is missing from state. "
                "Ensure RepoAnalyzer ran successfully before MetadataRecommender."
            )

        print(f"\n[MetadataRecommender] Searching for trending keywords...")

        search_query = f"{goal} github trending keywords tags 2024"
        search_results = self.search_tool.use(search_query)
        trending_keywords = search_results.get("keywords", [])

        print(f"[MetadataRecommender] Found {len(trending_keywords)} trending keywords.")

        prompt = self._build_prompt(project_summary, goal, repo_name, trending_keywords)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a technical marketing strategist specialising in "
                            "open-source AI/ML project discoverability. "
                            "Return ONLY valid JSON. No extra text."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=600,
                timeout=30,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content.strip()
            recommendations = json.loads(raw)

        except APITimeoutError:
            print("[MetadataRecommender] OpenAI API timed out. Using fallback metadata.")
            recommendations = self._fallback_metadata(repo_name, trending_keywords)
        except json.JSONDecodeError:
            print("[MetadataRecommender] Failed to parse JSON response. Using fallback.")
            recommendations = self._fallback_metadata(repo_name, trending_keywords)
        except RateLimitError:
            print("[MetadataRecommender] Rate limit reached.")
            raise
        except APIConnectionError:
            print("[MetadataRecommender] Cannot connect to OpenAI API.")
            raise
        except Exception as e:
            print(f"[MetadataRecommender] Unexpected error: {e}")
            recommendations = self._fallback_metadata(repo_name, trending_keywords)

        print(f"[MetadataRecommender] Title: {recommendations.get('optimized_title')}")

        state["metadata_recommendations"] = recommendations
        state["trending_keywords"] = trending_keywords
        return state

    def _build_prompt(self, summary, goal, repo_name, keywords):
        return f"""
Project: {repo_name}
Goal: {goal}
Trending Keywords: {keywords}
Summary: {summary}

Return JSON with exactly:
{{
  "optimized_title": "keyword-rich title (max 12 words)",
  "one_line_description": "one sentence (max 20 words)",
  "suggested_tags": ["tag1","tag2","tag3","tag4","tag5"],
  "trending_keywords": ["kw1","kw2","kw3"],
  "seo_rationale": "one sentence explaining tag choices"
}}
""".strip()

    def _fallback_metadata(self, repo_name: str, keywords: list) -> dict:
        return {
            "optimized_title": repo_name,
            "one_line_description": "An AI-powered multi-agent documentation optimization system.",
            "suggested_tags": keywords[:5] if keywords else ["multi-agent", "LangGraph", "AI", "documentation", "python"],
            "trending_keywords": keywords[:3] if keywords else ["agentic-AI", "LLM", "automation"],
            "seo_rationale": "Tags based on trending search terms in the project domain.",
        }
