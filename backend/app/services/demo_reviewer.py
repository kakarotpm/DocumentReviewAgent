"""Demo reviewer: used when no Anthropic API key is set, so every screen can be tried out.

It is NOT an AI review. It checks whether the key words of each rule's title appear in the
document. Results are labelled as demo results everywhere they're shown.
"""

import re

from app.schemas import AIReviewOutput, AIRuleJudgement, AISuggestion, Rule

MODEL_NAME = "demo (keyword matching, not AI)"
PROMPT_VERSION = "demo_v1"

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "each", "for", "from", "has", "have", "in", "is",
    "it", "its", "of", "on", "or", "out", "per", "the", "their", "to", "with", "what", "why", "how",
    "all", "any", "both", "clear", "clearly", "explicit", "explicitly", "listed", "stated", "identified",
    "defined", "specific", "every", "one",
}


def _key_terms(rule: Rule) -> list[str]:
    """Words from the rule title worth looking for, shortened so 'objectives' also finds 'objective'."""
    words = re.findall(r"[a-z]+", rule.title.lower())
    terms = []
    for word in words:
        if word in STOPWORDS or len(word) < 3:
            continue
        stem = word[:6] if len(word) > 6 else word.rstrip("s")
        if stem not in terms:
            terms.append(stem)
    return terms or [rule.title.lower()[:6]]


def _find_line(lines: list[str], term: str) -> tuple[str, str] | None:
    """The first line containing `term`, and the heading (or page) it sits under."""
    heading = "Start of document"
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or re.match(r"^\[Page \d+\]$", stripped):
            heading = stripped.lstrip("# ").strip()
        if term in stripped.lower():
            quote = stripped if len(stripped) <= 200 else stripped[:197] + "..."
            return quote, heading
    return None


def evaluate(document_text: str, rules: list[Rule]) -> AIReviewOutput:
    lines = [line for line in document_text.splitlines() if line.strip()]
    text = document_text.lower()
    results = []
    for rule in rules:
        terms = _key_terms(rule)
        found = [t for t in terms if t in text]
        share = len(found) / len(terms)
        status = "met" if share >= 0.75 else "partially_met" if share >= 0.4 else "not_met"

        hit = _find_line(lines, found[0]) if found else None
        evidence, location = hit if hit else ("No relevant content found.", "Not found")
        explanation = (
            f"Demo review (keyword matching, not AI): found {len(found)} of {len(terms)} key terms "
            f"from the rule title ({', '.join(terms)})."
        )

        suggestions = []
        if status == "not_met":
            suggestions.append(AISuggestion(
                type="add",
                location="New section",
                proposed_text=f"Add a section on '{rule.title}'. It should cover: {rule.check}",
                rationale="Demo suggestion: this topic wasn't found in the document.",
            ))
        elif status == "partially_met":
            suggestions.append(AISuggestion(
                type="change",
                location=location,
                current_text=evidence,
                proposed_text=f"Expand this so it fully covers: {rule.check}",
                rationale="Demo suggestion: this topic is only partly covered.",
            ))
        results.append(AIRuleJudgement(
            rule_id=rule.id, status=status, evidence=evidence, location=location,
            explanation=explanation, suggestions=suggestions,
        ))
    return AIReviewOutput(results=results)
