"""Everything that talks to Claude. Without an API key, reviews use the demo reviewer instead.

Prompts are loaded from the prompts/ folder; their file name (e.g. evaluate_rules_v1) is the
prompt version stored with each review.
"""

import logging
from collections.abc import Callable
from typing import TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

from app.config import PROJECT_ROOT, settings
from app.schemas import AIProposedRulebook, AIProposedSingleRule, AIReviewOutput, Rule, Rulebook
from app.services import demo_reviewer

logger = logging.getLogger(__name__)

PROMPTS_DIR = PROJECT_ROOT / "prompts"
EVALUATE_PROMPT = "evaluate_rules_v1"
EVALUATE_WORKBOOK_PROMPT = "evaluate_workbook_v1"
DRAFT_RULES_PROMPT = "draft_rules_v1"
DRAFT_RULE_PROMPT = "draft_rule_v1"
MAX_TOKENS = 16000

T = TypeVar("T", bound=BaseModel)


class AIError(Exception):
    """The AI call failed. The message is safe to show to users and says what to do next."""


class AINotConfigured(AIError):
    def __init__(self):
        super().__init__(
            "This feature needs the AI, and no Anthropic API key is set. Add ANTHROPIC_API_KEY to the "
            ".env file and restart the backend. Until then, you can add rules manually or upload a .md file."
        )


def ai_available() -> bool:
    return bool(settings.anthropic_api_key.strip())


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8")


def _rules_as_text(rules: list[Rule]) -> str:
    blocks = []
    for rule in rules:
        lines = [f"Rule {rule.id}: {rule.title}", f"Check: {rule.check}"]
        if rule.pass_example:
            lines.append(f"Pass example: {rule.pass_example}")
        if rule.fail_example:
            lines.append(f"Fail example: {rule.fail_example}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _ask_claude(system: str, user: str, output_format: type[T], problem: Callable[[T], str | None]) -> T:
    """Call Claude and return a validated answer. Retries once if the answer is invalid.

    `problem` returns a description of what's wrong with an answer, or None if it's fine.
    """
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    last_problem = ""
    for attempt in (1, 2):
        try:
            response = client.messages.parse(
                model=settings.anthropic_model,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_format=output_format,
                output_config={"effort": settings.anthropic_effort},
            )
        except anthropic.AuthenticationError:
            raise AIError("The Anthropic API key was rejected. Check ANTHROPIC_API_KEY in the .env file.")
        except anthropic.NotFoundError:
            raise AIError(f"The model '{settings.anthropic_model}' wasn't found. Check ANTHROPIC_MODEL in the .env file.")
        except anthropic.RateLimitError:
            raise AIError("The AI service is busy right now. Wait a minute, then click Re-run review.")
        except anthropic.APIConnectionError:
            raise AIError("Couldn't reach the AI service. Check your internet connection, then click Re-run review.")
        except anthropic.APIStatusError as e:
            raise AIError(f"The AI service returned an error ({e.status_code}). Try Re-run review in a few minutes.")
        except (ValidationError, ValueError) as e:
            last_problem = f"answer didn't match the expected format ({type(e).__name__})"
            logger.warning("AI answer invalid on attempt %s: %s", attempt, last_problem)
            continue

        if response.stop_reason == "refusal":
            raise AIError("The AI declined to process this content. Check the document doesn't contain unrelated material, then try again.")
        if response.stop_reason == "max_tokens" or response.parsed_output is None:
            last_problem = "answer was cut off before it finished"
        else:
            last_problem = problem(response.parsed_output) or ""
            if not last_problem:
                return response.parsed_output
        logger.warning("AI answer invalid on attempt %s: %s", attempt, last_problem)

    raise AIError(
        f"The AI's answer was incomplete twice ({last_problem}). Click Re-run review to try again. "
        "If it keeps happening, the document may be very long or the rulebook very large."
    )


def _one_result_per_rule(rules: list[Rule]) -> Callable[[AIReviewOutput], str | None]:
    """A check that the AI returned exactly one result for each rule, and nothing else."""
    expected = {rule.id for rule in rules}

    def problem(output: AIReviewOutput) -> str | None:
        returned = [r.rule_id for r in output.results]
        missing = expected - set(returned)
        extra = set(returned) - expected
        if missing:
            return f"no result for {', '.join(sorted(missing))}"
        if extra:
            return f"results for unknown rules {', '.join(sorted(extra))}"
        if len(returned) != len(set(returned)):
            return "more than one result for the same rule"
        return None

    return problem


def evaluate_rules(document_text: str, rules: list[Rule], document_type_name: str) -> tuple[AIReviewOutput, str, str]:
    """Judge every rule against the document. Returns (judgements, model name, prompt version)."""
    if not ai_available():
        return demo_reviewer.evaluate(document_text, rules), demo_reviewer.MODEL_NAME, demo_reviewer.PROMPT_VERSION

    system = load_prompt(EVALUATE_PROMPT).replace("{{document_type}}", document_type_name)
    user = f"<rules>\n{_rules_as_text(rules)}\n</rules>\n\n<document>\n{document_text}\n</document>"
    output = _ask_claude(system, user, AIReviewOutput, _one_result_per_rule(rules))
    return output, settings.anthropic_model, EVALUATE_PROMPT


def evaluate_workbook(
    workbook_text: str, document_text: str, rules: list[Rule], document_type_name: str
) -> tuple[AIReviewOutput, str, str]:
    """Judge every Part B (Excel) rule against the workbook. The document text is included for
    consistency rules. Returns (judgements, model name, prompt version)."""
    if not ai_available():
        return demo_reviewer.evaluate(workbook_text, rules), demo_reviewer.MODEL_NAME, demo_reviewer.PROMPT_VERSION

    system = load_prompt(EVALUATE_WORKBOOK_PROMPT).replace("{{document_type}}", document_type_name)
    user = (
        f"<rules>\n{_rules_as_text(rules)}\n</rules>\n\n"
        f"<document>\n{document_text}\n</document>\n\n"
        f"<workbook>\n{workbook_text}\n</workbook>"
    )
    output = _ask_claude(system, user, AIReviewOutput, _one_result_per_rule(rules))
    return output, settings.anthropic_model, EVALUATE_WORKBOOK_PROMPT


EXCEL_RULE_NOTE = (
    "This rule is a Part B (Excel) rule: it checks the Excel workbook that accompanies the document "
    "(sheet names, column and row headers, and whether required content is filled in), not the document "
    "itself, and never whether the data values are correct.\n\n"
)


def _rule_as_text(rule: Rule) -> str:
    return (
        f"id: {rule.id}\ntitle: {rule.title}\npart: {rule.part}\nweight: {rule.weight}\ncritical: {str(rule.critical).lower()}\n"
        f"check: {rule.check}\npass_example: {rule.pass_example or ''}\nfail_example: {rule.fail_example or ''}"
    )


def draft_rules(instruction: str, display_name: str) -> AIProposedRulebook:
    """Ask the AI to write a full set of rules for a NEW document type."""
    if not ai_available():
        raise AINotConfigured()
    user = f"Create rules for a NEW document type called: {display_name}\n\n<instruction>\n{instruction}\n</instruction>"

    def problem(output: AIProposedRulebook) -> str | None:
        return None if output.rules else "no rules were returned"

    return _ask_claude(load_prompt(DRAFT_RULES_PROMPT), user, AIProposedRulebook, problem)


def draft_rule(instruction: str, rulebook: Rulebook, existing: Rule | None, part: str = "document") -> AIProposedSingleRule:
    """Ask the AI to write one new rule for a rulebook, or to change one existing rule."""
    if not ai_available():
        raise AINotConfigured()
    others = "\n\n".join(_rule_as_text(r) for r in rulebook.rules if existing is None or r.id != existing.id)
    context = f"Document type: {rulebook.display_name}\nDescription: {rulebook.description}\n\n<other_rules>\n{others}\n</other_rules>\n\n"
    if part == "excel":
        context += EXCEL_RULE_NOTE
    if existing is None:
        user = context + f"Write a NEW rule as described.\n<instruction>\n{instruction}\n</instruction>"
    else:
        user = context + f"<rule_to_change>\n{_rule_as_text(existing)}\n</rule_to_change>\n\nChange it as follows.\n<instruction>\n{instruction}\n</instruction>"
    return _ask_claude(load_prompt(DRAFT_RULE_PROMPT), user, AIProposedSingleRule, lambda output: None)
