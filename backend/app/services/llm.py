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
from app.schemas import AIProposedRulebook, AIReviewOutput, Rule, Rulebook
from app.services import demo_reviewer

logger = logging.getLogger(__name__)

PROMPTS_DIR = PROJECT_ROOT / "prompts"
EVALUATE_PROMPT = "evaluate_rules_v1"
DRAFT_RULES_PROMPT = "draft_rules_v1"
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


def evaluate_rules(document_text: str, rules: list[Rule], document_type_name: str) -> tuple[AIReviewOutput, str, str]:
    """Judge every rule against the document. Returns (judgements, model name, prompt version)."""
    if not ai_available():
        return demo_reviewer.evaluate(document_text, rules), demo_reviewer.MODEL_NAME, demo_reviewer.PROMPT_VERSION

    system = load_prompt(EVALUATE_PROMPT).replace("{{document_type}}", document_type_name)
    user = f"<rules>\n{_rules_as_text(rules)}\n</rules>\n\n<document>\n{document_text}\n</document>"
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

    output = _ask_claude(system, user, AIReviewOutput, problem)
    return output, settings.anthropic_model, EVALUATE_PROMPT


def draft_rules(instruction: str, existing: Rulebook | None, display_name: str | None) -> AIProposedRulebook:
    """Ask the AI to write rules for a new type, or to change an existing rulebook."""
    if not ai_available():
        raise AINotConfigured()

    if existing is None:
        user = f"Create rules for a NEW document type called: {display_name or 'Custom document'}\n\n<instruction>\n{instruction}\n</instruction>"
    else:
        current = "\n\n".join(
            f"id: {r.id}\ntitle: {r.title}\ncategory: {r.category}\nweight: {r.weight}\ncritical: {str(r.critical).lower()}\n"
            f"check: {r.check}\npass_example: {r.pass_example or ''}\nfail_example: {r.fail_example or ''}"
            for r in existing.rules
        )
        user = (
            f"EXISTING rulebook: {existing.display_name}\nDescription: {existing.description}\n\n"
            f"<rules>\n{current}\n</rules>\n\nChange it as follows.\n<instruction>\n{instruction}\n</instruction>"
        )

    def problem(output: AIProposedRulebook) -> str | None:
        return None if output.rules else "no rules were returned"

    return _ask_claude(load_prompt(DRAFT_RULES_PROMPT), user, AIProposedRulebook, problem)
