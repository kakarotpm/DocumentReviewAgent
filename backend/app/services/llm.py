"""Everything that talks to the AI: Claude (Anthropic) or GPT (OpenAI), chosen by AI_PROVIDER in .env.
Without that provider's API key, reviews use the demo reviewer instead.

Prompts are loaded from the prompts/ folder; their file name (e.g. evaluate_rules_v1) is the
prompt version stored with each review. Both providers get the same prompts and must return the
same Pydantic models (structured outputs), so the rest of the app doesn't care which one is used.
"""

import logging
from collections.abc import Callable
from typing import TypeVar

import anthropic
import openai
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

# AI_PROVIDER value -> (name shown to users, the .env setting that holds its key)
PROVIDERS = {
    "anthropic": ("Anthropic (Claude)", "ANTHROPIC_API_KEY"),
    "openai": ("OpenAI (GPT)", "OPENAI_API_KEY"),
}

T = TypeVar("T", bound=BaseModel)


class AIError(Exception):
    """The AI call failed. The message is safe to show to users and says what to do next."""


class AINotConfigured(AIError):
    def __init__(self):
        super().__init__(
            f"This feature needs the AI, and no API key is set. Add {key_setting()} to the .env file and "
            "restart the backend. Until then, you can add rules manually or upload a .md file."
        )


def ai_provider() -> str:
    return settings.ai_provider.strip().lower()


def provider_name() -> str:
    """e.g. 'OpenAI (GPT)', for messages and the health check."""
    return PROVIDERS.get(ai_provider(), (f"unknown provider '{settings.ai_provider}'", ""))[0]


def key_setting() -> str:
    return PROVIDERS.get(ai_provider(), ("", "ANTHROPIC_API_KEY or OPENAI_API_KEY"))[1]


def model_name() -> str:
    """The model reviews will use; it's saved with each review."""
    return settings.openai_model.strip() if ai_provider() == "openai" else settings.anthropic_model


def ai_available() -> bool:
    """True when the chosen provider has an API key. An unknown AI_PROVIDER counts as no key (demo mode)."""
    if ai_provider() == "openai":
        return bool(settings.openai_api_key.strip())
    if ai_provider() == "anthropic":
        return bool(settings.anthropic_api_key.strip())
    return False


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


def _friendly_error(sdk, e: Exception, prefix: str, model: str) -> AIError:
    """Turn an API error into a message that says what to do next. Both SDKs use the same error names.
    `prefix` is ANTHROPIC or OPENAI, for the .env setting names."""
    if isinstance(e, sdk.AuthenticationError):
        return AIError(f"The API key was rejected. Check {prefix}_API_KEY in the .env file.")
    if isinstance(e, sdk.NotFoundError):
        return AIError(f"The model '{model}' wasn't found, or your key can't use it. Check {prefix}_MODEL in the .env file.")
    if isinstance(e, sdk.RateLimitError):
        return AIError("The AI service is busy, or the account has run out of credit. Wait a minute, then click Re-run review.")
    if isinstance(e, sdk.APIConnectionError):
        return AIError("Couldn't reach the AI service. Check your internet connection, then click Re-run review.")
    if isinstance(e, sdk.BadRequestError):
        return AIError(f"The AI service rejected the request ({e.message[:200]}). Check the AI settings in the .env file.")
    status = getattr(e, "status_code", "unknown")
    return AIError(f"The AI service returned an error ({status}). Try Re-run review in a few minutes.")


# Each provider call returns (answer, issue): issue is None, "refusal" or "cut_off".
# API errors become AIError; an answer that doesn't fit the model raises ValidationError/ValueError.


def _call_anthropic(system: str, user: str, output_format: type[T]) -> tuple[T | None, str | None]:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    try:
        response = client.messages.parse(
            model=settings.anthropic_model,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_format=output_format,
            output_config={"effort": settings.anthropic_effort},
        )
    except anthropic.APIError as e:
        raise _friendly_error(anthropic, e, "ANTHROPIC", settings.anthropic_model)
    if response.stop_reason == "refusal":
        return None, "refusal"
    if response.stop_reason == "max_tokens":
        return None, "cut_off"
    return response.parsed_output, None


def _call_openai(system: str, user: str, output_format: type[T]) -> tuple[T | None, str | None]:
    model = settings.openai_model.strip()
    if not model:
        raise AIError(
            "OPENAI_MODEL isn't set. Add the name of a model your OpenAI key can use (see the OpenAI dashboard) "
            "to the .env file, for example OPENAI_MODEL=model-name, then restart the backend."
        )
    client = openai.OpenAI(api_key=settings.openai_api_key)
    effort = settings.openai_reasoning_effort.strip()
    try:
        response = client.responses.parse(
            model=model,
            instructions=system,
            input=user,
            text_format=output_format,
            max_output_tokens=MAX_TOKENS,
            store=False,  # don't keep the document text on OpenAI's side
            **({"reasoning": {"effort": effort}} if effort else {}),
        )
    except openai.APIError as e:
        raise _friendly_error(openai, e, "OPENAI", model)
    refused = any(c.type == "refusal" for item in response.output if item.type == "message" for c in item.content)
    if refused or (response.incomplete_details and response.incomplete_details.reason == "content_filter"):
        return None, "refusal"
    if response.status == "incomplete":
        return None, "cut_off"
    return response.output_parsed, None


def _ask_ai(system: str, user: str, output_format: type[T], problem: Callable[[T], str | None]) -> T:
    """Call the chosen AI and return a validated answer. Retries once if the answer is invalid.

    `problem` returns a description of what's wrong with an answer, or None if it's fine.
    """
    call = _call_openai if ai_provider() == "openai" else _call_anthropic
    last_problem = ""
    for attempt in (1, 2):
        try:
            answer, issue = call(system, user, output_format)
        except (ValidationError, ValueError) as e:
            last_problem = f"answer didn't match the expected format ({type(e).__name__})"
            logger.warning("AI answer invalid on attempt %s: %s", attempt, last_problem)
            continue

        if issue == "refusal":
            raise AIError("The AI declined to process this content. Check the document doesn't contain unrelated material, then try again.")
        if issue == "cut_off" or answer is None:
            last_problem = "answer was cut off before it finished"
        else:
            last_problem = problem(answer) or ""
            if not last_problem:
                return answer
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
    output = _ask_ai(system, user, AIReviewOutput, _one_result_per_rule(rules))
    return output, model_name(), EVALUATE_PROMPT


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
    output = _ask_ai(system, user, AIReviewOutput, _one_result_per_rule(rules))
    return output, model_name(), EVALUATE_WORKBOOK_PROMPT


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

    return _ask_ai(load_prompt(DRAFT_RULES_PROMPT), user, AIProposedRulebook, problem)


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
    return _ask_ai(load_prompt(DRAFT_RULE_PROMPT), user, AIProposedSingleRule, lambda output: None)
