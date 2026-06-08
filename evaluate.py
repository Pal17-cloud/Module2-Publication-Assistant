"""
evaluate.py — Evaluation Script
Runs both formal evaluation metrics:
  5.1 Metadata Relevance   (Success Metric)
  5.2 Structural Integrity (Safety Metric)

Usage:
    python evaluate.py
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from tools.markdown_fixer_tool import MarkdownFixerTool

load_dotenv()


class Evaluator:

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY is not set.")
        self.client = OpenAI(api_key=api_key)
        self.markdown_fixer = MarkdownFixerTool()
        self.model = "gpt-4o"

    def evaluate_metadata_relevance(self, goal: str, suggested_tags: list, threshold: int = 3) -> dict:
        if not goal or not suggested_tags:
            return {"passed": False, "error": "Goal and tags are required."}

        print("\n[Evaluator] Running Metadata Relevance check...")

        prompt = f"""
Evaluate whether these repository tags are relevant to the user's goal.

User Goal: {goal}
Suggested Tags: {suggested_tags}

For each tag, decide if it is relevant (true/false).
Return ONLY JSON:
{{
  "tag_evaluations": [
    {{"tag": "tag1", "relevant": true, "reason": "..."}}
  ],
  "overall_rationale": "one sentence summary"
}}
""".strip()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=400,
                timeout=30,
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content.strip())
        except Exception as e:
            return {"passed": False, "error": str(e)}

        evaluations = data.get("tag_evaluations", [])
        relevant_tags = [e["tag"] for e in evaluations if e.get("relevant")]
        irrelevant_tags = [e["tag"] for e in evaluations if not e.get("relevant")]
        passed = len(relevant_tags) >= threshold

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"[Evaluator] Metadata Relevance: {status} ({len(relevant_tags)}/{len(suggested_tags)} relevant)")

        return {
            "passed": passed,
            "relevant_count": len(relevant_tags),
            "total_tags": len(suggested_tags),
            "relevant_tags": relevant_tags,
            "irrelevant_tags": irrelevant_tags,
            "rationale": data.get("overall_rationale", ""),
        }

    def evaluate_structural_integrity(self, markdown_content: str) -> dict:
        if not markdown_content:
            return {"passed": False, "error": "Markdown content is empty."}

        print("\n[Evaluator] Running Structural Integrity check...")
        fix_result = self.markdown_fixer.use(markdown_content)
        status = "✅ PASS" if fix_result["passed"] else "❌ FAIL"
        print(f"[Evaluator] Structural Integrity: {status}")

        return {
            "passed": fix_result["passed"],
            "issues_found": fix_result["issues_found"],
            "issues_fixed": fix_result["issues_fixed"],
            "missing_sections": fix_result["missing_sections"],
        }

    def run_full_evaluation(self, pipeline_result: dict) -> dict:
        goal = pipeline_result.get("goal", "")
        metadata = pipeline_result.get("metadata_recommendations", {})
        suggested_tags = metadata.get("suggested_tags", [])
        final_output = pipeline_result.get("final_output", "")

        relevance = self.evaluate_metadata_relevance(goal, suggested_tags)
        integrity = self.evaluate_structural_integrity(final_output)
        overall = relevance["passed"] and integrity["passed"]

        print("\n" + "=" * 50)
        print("  EVALUATION SUMMARY")
        print("=" * 50)
        print(f"  Metadata Relevance  : {'✅ PASS' if relevance['passed'] else '❌ FAIL'}")
        print(f"  Structural Integrity: {'✅ PASS' if integrity['passed'] else '❌ FAIL'}")
        print(f"  Overall             : {'✅ PASS' if overall else '❌ FAIL'}")
        print("=" * 50)

        return {
            "overall_passed": overall,
            "metadata_relevance": relevance,
            "structural_integrity": integrity,
        }


if __name__ == "__main__":
    from publication_assistant import PublicationAssistantOrchestrator

    url = input("Enter GitHub repository URL: ").strip()
    goal = input("Enter the goal: ").strip()

    orchestrator = PublicationAssistantOrchestrator()
    result = orchestrator.run(url=url, goal=goal)
    result["goal"] = goal

    evaluator = Evaluator()
    report = evaluator.run_full_evaluation(result)
    print(json.dumps(report, indent=2))
