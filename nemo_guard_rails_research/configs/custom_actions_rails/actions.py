import re
from typing import Optional
from nemoguardrails.actions import action


BLOCKED_PATTERNS = [
    r"ignore (previous|all|your) (instructions?|rules?|guidelines?)",
    r"(system prompt|you are now|pretend|act as|dan|jailbreak)",
    r"(hack|exploit|bypass|circumvent).{0,20}(security|system|policy)",
    r"\b(ssn|social security|credit card|cvv|passwd|password)\b",
]

REQUIRED_DISCLAIMER_TOPICS = ["investment", "medical", "legal", "financial advice"]


@action(name="check_content_safety")
async def check_content_safety(user_input: str) -> bool:
    """Returns True if content is safe, False if blocked."""
    lower = user_input.lower()
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, lower, re.IGNORECASE):
            print(f"[BLOCKED] Pattern matched: {pattern}")
            return False
    return True


@action(name="validate_output")
async def validate_output(bot_output: str) -> bool:
    """Returns True if output passes validation, False otherwise."""
    lower = bot_output.lower()
    for topic in REQUIRED_DISCLAIMER_TOPICS:
        if topic in lower and "consult" not in lower and "professional" not in lower:
            print(f"[FLAGGED] Output mentions '{topic}' without disclaimer.")
            return False
    if len(bot_output.strip()) < 5:
        return False
    return True


@action(name="log_interaction")
async def log_interaction(user_input: str, bot_output: Optional[str] = None) -> dict:
    """Audit logger — returns metadata dict for tracing."""
    import hashlib, time
    return {
        "timestamp": time.time(),
        "input_hash": hashlib.sha256(user_input.encode()).hexdigest()[:12],
        "output_hash": hashlib.sha256((bot_output or "").encode()).hexdigest()[:12],
        "flagged": False,
    }
