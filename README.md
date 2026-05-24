"""
evaluate.py — Evaluation Script
================================
Runs the two formal evaluation metrics defined in the publication:

  5.1 Metadata Relevance   (Success Metric)
      Checks whether the top 5 suggested tags are relevant to the
      user's stated goal using an LLM-as-judge approach.

  5.2 Structural Integrity (Safety Metric)
      Checks whether the final Markdown output is correctly
      formatted and contains all required sections.

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
    """Runs both formal evaluation metrics and prints a summary report."""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.markdown_fixer = MarkdownFixerTool()
        self.model = "gpt-4o"

    # ------------------------------------------------------------------
    # 5.1  Metadata Relevance (Success Metric)
    # ------------------------------------------------------------------

    def evaluate_metadata_relevance(
        self, goal: str, suggested_tags: list, threshold: int = 3
    ) -> dict:
        """
        Uses an LLM judge to verify that the suggested tags are relevant
        to the user's stated goal.

        Args:
            goal:           The user's optimisation goal string.
            suggested_tags: List of tags produced by MetadataRecommender.
            threshold:      Minimum number of relevant tags to pass (default 3/5).

        Returns:
            dict with: passed (bool), relevant_count (int),
                       relevant_tags (list), irrelevant_tags (list), rationale (str)
        """
        print("\n[Evaluator] Running Metadata Relevance check...")

        prompt = f"""
You are evaluating whether a set of repository tags are relevant to a user's goal.

User Goal: {goal}
Suggested Tags: {suggested_tags}

For each tag, decide if it is relevant to the goal (YES or NO) and explain why.
Return ONLY a JSON object with this structure:
{{
  "tag_evaluations": [
    {{"tag": "tag1", "relevant": true, "reason": "..."}},
    ...
  ],
  "overall_rationale": "One sentence summary"
}}
""".strip()

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=400,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content.strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {"passed": False, "error": "LLM returned invalid JSON."}

        evaluations = data.get("tag_evaluations", [])
        relevant_tags = [e["tag"] for e in evaluations if e.get("relevant")]
        irrelevant_tags = [e["tag"] for e in evaluations if not e.get("relevant")]
        relevant_count = len(relevant_tags)
        passed = relevant_count >= threshold

        result = {
            "passed": passed,
            "relevant_count": relevant_count,
            "total_tags": len(suggested_tags),
            "relevant_tags": relevant_tags,
            "irrelevant_tags": irrelevant_tags,
            "rationale": data.get("overall_rationale", ""),
            "threshold": threshold,
        }

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"[Evaluator] Metadata Relevance: {status} ({relevant_count}/{len(suggested_tags)} relevant)")
        return result

    # ------------------------------------------------------------------
    # 5.2  Structural Integrity (Safety Metric)
    # ------------------------------------------------------------------

    def evaluate_structural_integrity(self, markdown_content: str) -> dict:
        """
        Uses the MarkdownFixerTool to verify the final Markdown output
        is correctly formatted and contains all required sections.

        Args:
            markdown_content: The final README.md content string.

        Returns:
            dict with: passed (bool), issues_found (list),
                       missing_sections (list), issues_fixed (list)
        """
        print("\n[Evaluator] Running Structural Integrity check...")

        fix_result = self.markdown_fixer.use(markdown_content)

        status = "✅ PASS" if fix_result["passed"] else "❌ FAIL"
        print(f"[Evaluator] Structural Integrity: {status}")
        if fix_result["missing_sections"]:
            print(f"            Missing sections: {fix_result['missing_sections']}")
        if fix_result["issues_fixed"]:
            print(f"            Auto-fixed: {len(fix_result['issues_fixed'])} issue(s)")

        return {
            "passed": fix_result["passed"],
            "issues_found": fix_result["issues_found"],
            "issues_fixed": fix_result["issues_fixed"],
            "missing_sections": fix_result["missing_sections"],
        }

    # ------------------------------------------------------------------
    # Full evaluation run
    # ------------------------------------------------------------------

    def run_full_evaluation(self, pipeline_result: dict) -> dict:
        """
        Runs both metrics against a completed pipeline result.

        Args:
            pipeline_result: The dict returned by PublicationAssistantOrchestrator.run()

        Returns:
            dict with results for both metrics and an overall pass/fail.
        """
        goal = pipeline_result.get("goal", "")
        metadata = pipeline_result.get("metadata_recommendations", {})
        suggested_tags = metadata.get("suggested_tags", [])
        final_output = pipeline_result.get("final_output", "")

        # Run both metrics
        relevance_result = self.evaluate_metadata_relevance(goal, suggested_tags)
        integrity_result = self.evaluate_structural_integrity(final_output)

        overall_passed = relevance_result["passed"] and integrity_result["passed"]

        report = {
            "overall_passed": overall_passed,
            "metadata_relevance": relevance_result,
            "structural_integrity": integrity_result,
        }

        print("\n" + "=" * 50)
        print("  EVALUATION SUMMARY")
        print("=" * 50)
        print(f"  Metadata Relevance  : {'✅ PASS' if relevance_result['passed'] else '❌ FAIL'}")
        print(f"  Structural Integrity: {'✅ PASS' if integrity_result['passed'] else '❌ FAIL'}")
        print(f"  Overall             : {'✅ PASS' if overall_passed else '❌ FAIL'}")
        print("=" * 50 + "\n")

        return report


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from publication_assistant import PublicationAssistantOrchestrator

    print("Publication Assistant — Evaluation Mode")
    print("-" * 40)

    url = input("Enter GitHub repository URL used in the run: ").strip()
    goal = input("Enter the goal used in the run: ").strip()

    orchestrator = PublicationAssistantOrchestrator()
    result = orchestrator.run(url=url, goal=goal)

    evaluator = Evaluator()
    result["goal"] = goal
    eval_report = evaluator.run_full_evaluation(result)

    print("Full evaluation report:")
    print(json.dumps(eval_report, indent=2))
