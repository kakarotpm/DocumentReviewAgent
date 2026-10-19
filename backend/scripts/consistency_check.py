"""Review the same document several times and report how much the score varies.

The target (intent.md §14) is that repeat reviews of an unchanged document stay within ±3 points.
Needs ANTHROPIC_API_KEY in .env (without it, the demo reviewer always gives the same score).
Each run costs one AI review.

Run from the backend folder:
    .\.venv\Scripts\python.exe scripts\consistency_check.py ..\samples\brd_strong.md --type brd --runs 3
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # so "app" can be imported

from app.config import settings  # noqa: E402
from app.services import llm, rulebooks  # noqa: E402
from app.services.extraction import extract_text  # noqa: E402
from app.services.scoring import calculate_score  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", type=Path)
    parser.add_argument("--type", default="brd", help="rulebook file name in rulebooks/, e.g. brd")
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()

    rulebook = rulebooks.parse_rulebook((settings.rulebooks_dir / f"{args.type}.md").read_text(encoding="utf-8"))
    _, text = extract_text(args.file.name, args.file.read_bytes())
    if not llm.ai_available():
        print("Note: no API key set, so this uses the demo reviewer (scores will always match).")

    scores = []
    for run in range(1, args.runs + 1):
        output, model, _ = llm.evaluate_rules(text, rulebook.rules, rulebook.display_name)
        statuses = {r.rule_id: r.status for r in output.results}
        result = calculate_score(rulebook.rules, statuses, rulebook.pass_threshold)
        scores.append(result.score)
        summary = " ".join(f"{rule_id}:{status[0].upper()}" for rule_id, status in statuses.items())
        print(f"Run {run}: score {result.score} ({'Pass' if result.passed else 'Fail'})  {summary}")

    spread = max(scores) - min(scores)
    print(f"\nModel: {model}\nScores: {scores}\nSpread: {spread} points -> {'OK (within 6, i.e. ±3)' if spread <= 6 else 'TOO WIDE'}")


if __name__ == "__main__":
    main()
