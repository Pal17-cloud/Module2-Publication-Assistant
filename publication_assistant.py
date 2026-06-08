"""
Publication Assistant — Main Orchestrator
==========================================
Manages the full 3-step pipeline with error handling and input validation.

Usage (CLI):    python main.py
Usage (code):   from publication_assistant import PublicationAssistantOrchestrator
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

from agents.repo_analyzer import RepoAnalyzer
from agents.metadata_recommender import MetadataRecommender
from agents.content_improver import ContentImprover

load_dotenv()


class PublicationAssistantOrchestrator:

    def __init__(self):
        self.repo_analyzer = RepoAnalyzer()
        self.metadata_recommender = MetadataRecommender()
        self.content_improver = ContentImprover()

    def run(self, url: str, goal: str) -> dict:
        if not url or not url.strip():
            raise ValueError("Repository URL cannot be empty.")
        if not url.startswith("http"):
            raise ValueError(f"Invalid URL format: {url}. Must start with http:// or https://")

        self._validate_env()

        print("\n" + "=" * 60)
        print("  Publication Assistant — Multi-Agent Pipeline")
        print("=" * 60)
        print(f"  URL  : {url}")
        print(f"  Goal : {goal or 'General optimization'}")
        print(f"  Time : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        state = {"url": url.strip(), "goal": goal.strip() if goal else ""}

        try:
            print("\n[ STEP 1/3 ] Running Repo Analyzer...")
            state = self.repo_analyzer.run(state)
            self._check_state(state, ["project_summary"], step=1)

            print("\n[ STEP 2/3 ] Running Metadata Recommender...")
            state = self.metadata_recommender.run(state)
            self._check_state(state, ["metadata_recommendations"], step=2)

            print("\n[ STEP 3/3 ] Running Content Improver...")
            state = self.content_improver.run(state)
            self._check_state(state, ["final_output"], step=3)

        except ValueError as e:
            print(f"\n❌ Validation Error: {e}")
            raise
        except EnvironmentError as e:
            print(f"\n❌ Environment Error: {e}")
            raise
        except Exception as e:
            print(f"\n❌ Pipeline Error: {e}")
            raise

        print("\n" + "=" * 60)
        print("  ✅  Pipeline complete!")
        print(f"  Output : {state.get('output_path', 'N/A')}")
        print(f"  QA     : {'✅ Passed' if state.get('qa_passed') else '⚠️ Review needed'}")
        print("=" * 60 + "\n")

        return state

    def _check_state(self, state: dict, required_keys: list, step: int):
        for key in required_keys:
            if key not in state or not state[key]:
                raise RuntimeError(
                    f"Pipeline failed at Step {step}: "
                    f"'{key}' missing from state. Check agent logs above."
                )

    def _validate_env(self):
        if not os.getenv("OPENAI_API_KEY"):
            raise EnvironmentError(
                "OPENAI_API_KEY is not set.\n"
                "Run: cp .env.example .env  then add your key."
            )
        if not os.getenv("SERPER_API_KEY"):
            print("\n⚠️  SERPER_API_KEY not set. Using fallback keywords.\n")


def main():
    print("\nPublication Assistant — Interactive Mode")
    print("-" * 40)

    url = input("Enter GitHub repository URL: ").strip()
    if not url:
        print("❌ Error: URL cannot be empty.")
        sys.exit(1)

    goal = input("Enter your optimization goal: ").strip()
    if not goal:
        goal = "Optimize for general AI/ML developers"

    orchestrator = PublicationAssistantOrchestrator()

    try:
        result = orchestrator.run(url=url, goal=goal)
    except (ValueError, EnvironmentError) as e:
        print(f"\n❌ {e}")
        sys.exit(1)

    print("\n--- METADATA RECOMMENDATIONS ---")
    meta = result.get("metadata_recommendations", {})
    print(f"Title    : {meta.get('optimized_title', 'N/A')}")
    print(f"Tags     : {meta.get('suggested_tags', [])}")
    print(f"Keywords : {meta.get('trending_keywords', [])}")

    print("\n--- CRITIQUE REPORT ---")
    print(result.get("critique_report", "No report generated."))
    print(f"\n✅ README saved to: {result.get('output_path', 'N/A')}")


if __name__ == "__main__":
    main()
