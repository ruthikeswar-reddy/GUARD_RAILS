"""
TOPIC 8: Custom Validators — 30+ practical examples
Covers: @register_validator, Validator base class, sync/async validators,
        validators with metadata, field-level and full-text validators,
        validator composition, error messages, fix actions

Install:
  pip install guardrails-ai
"""

from typing import Any, Callable, Optional
from guardrails import Guard
from guardrails.validator_base import (
    Validator,
    register_validator,
    ValidationResult,
    PassResult,
    FailResult,
)

# ──────────────────────────────────────────────────────────────────────────────
# BASIC CUSTOM VALIDATORS
# ──────────────────────────────────────────────────────────────────────────────

# ── 1. Simplest custom validator: no cursing ──────────────────────────────────
@register_validator(name="no-curse-words", data_type="string")
class NoCurseWords(Validator):
    CURSES = {"damn", "hell", "crap"}

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        found = [w for w in value.lower().split() if w in self.CURSES]
        if found:
            return FailResult(error_message=f"Curse words found: {found}")
        return PassResult()

guard1 = Guard().use(NoCurseWords, on_fail="exception")
guard1.validate("This is a great product!")
try:
    guard1.validate("Oh damn, what a bad day.")
except Exception as e:
    print(f"Blocked: {e}")

# ── 2. Validator with constructor arguments ───────────────────────────────────
@register_validator(name="min-word-count", data_type="string")
class MinWordCount(Validator):
    def __init__(self, min_words: int = 10, **kwargs):
        super().__init__(**kwargs)
        self._min_words = min_words

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        count = len(value.split())
        if count < self._min_words:
            return FailResult(
                error_message=f"Text has {count} words; minimum is {self._min_words}.",
                fix_value=value + " [Content too short, please expand.]",
            )
        return PassResult()

guard2 = Guard().use(MinWordCount, min_words=5, on_fail="fix")
res2 = guard2.validate("Too short.")
print(res2.validated_output)

# ── 3. Validator with metadata ─────────────────────────────────────────────────
@register_validator(name="allowed-topics", data_type="string")
class AllowedTopics(Validator):
    def validate(self, value: str, metadata: dict) -> ValidationResult:
        allowed = metadata.get("allowed_topics", [])
        if not allowed:
            return PassResult()
        text_lower = value.lower()
        if not any(topic.lower() in text_lower for topic in allowed):
            return FailResult(
                error_message=f"Response must cover one of: {allowed}"
            )
        return PassResult()

guard3 = Guard().use(AllowedTopics, on_fail="exception")
guard3.validate(
    "Python is a great programming language.",
    metadata={"allowed_topics": ["Python", "JavaScript", "Rust"]},
)

# ── 4. Validator that auto-fixes ──────────────────────────────────────────────
@register_validator(name="title-case-enforcer", data_type="string")
class TitleCaseEnforcer(Validator):
    def validate(self, value: str, metadata: dict) -> ValidationResult:
        if value != value.title():
            return FailResult(
                error_message="Value must be in Title Case.",
                fix_value=value.title(),
            )
        return PassResult()

guard4 = Guard().use(TitleCaseEnforcer, on_fail="fix")
res4 = guard4.validate("hello world")
print(res4.validated_output)   # "Hello World"

# ── 5. Regex-based custom validator ───────────────────────────────────────────
import re

@register_validator(name="sku-format", data_type="string")
class SKUFormat(Validator):
    PATTERN = re.compile(r"^[A-Z]{3}-\d{4}-[A-Z]{2}$")

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        if not self.PATTERN.match(value):
            return FailResult(error_message=f"'{value}' is not a valid SKU (format: ABC-1234-XY).")
        return PassResult()

guard5 = Guard().use(SKUFormat, on_fail="exception")
guard5.validate("ABC-1234-XY")   # valid

# ── 6. Numeric range validator ─────────────────────────────────────────────────
@register_validator(name="numeric-range", data_type="string")
class NumericRange(Validator):
    def __init__(self, lo: float, hi: float, **kwargs):
        super().__init__(**kwargs)
        self._lo, self._hi = lo, hi

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        try:
            num = float(value)
        except ValueError:
            return FailResult(error_message=f"'{value}' is not a number.")
        if not (self._lo <= num <= self._hi):
            clamped = max(self._lo, min(self._hi, num))
            return FailResult(
                error_message=f"{num} is out of range [{self._lo}, {self._hi}].",
                fix_value=str(clamped),
            )
        return PassResult()

guard6 = Guard().use(NumericRange, lo=1, hi=100, on_fail="fix")
res6 = guard6.validate("150")
print(res6.validated_output)   # "100"

# ── 7. Language detection validator ───────────────────────────────────────────
@register_validator(name="english-only", data_type="string")
class EnglishOnly(Validator):
    def validate(self, value: str, metadata: dict) -> ValidationResult:
        try:
            from langdetect import detect
            lang = detect(value)
            if lang != "en":
                return FailResult(error_message=f"Detected language '{lang}', expected English.")
        except Exception:
            pass   # skip if langdetect not available
        return PassResult()

# ── 8. Keyword density validator ──────────────────────────────────────────────
@register_validator(name="keyword-density", data_type="string")
class KeywordDensity(Validator):
    def __init__(self, keyword: str, min_pct: float = 1.0, max_pct: float = 5.0, **kwargs):
        super().__init__(**kwargs)
        self._keyword = keyword.lower()
        self._min_pct = min_pct
        self._max_pct = max_pct

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        words = value.lower().split()
        if not words:
            return FailResult(error_message="Empty text.")
        count = words.count(self._keyword)
        density = (count / len(words)) * 100
        if not (self._min_pct <= density <= self._max_pct):
            return FailResult(
                error_message=f"Keyword '{self._keyword}' density {density:.1f}% not in [{self._min_pct}%, {self._max_pct}%]."
            )
        return PassResult()

guard8 = Guard().use(KeywordDensity, keyword="python", min_pct=1.0, max_pct=10.0, on_fail="reask")

# ── 9. Sentence count validator ────────────────────────────────────────────────
@register_validator(name="sentence-count", data_type="string")
class SentenceCount(Validator):
    def __init__(self, min_sentences: int = 1, max_sentences: int = 10, **kwargs):
        super().__init__(**kwargs)
        self._min = min_sentences
        self._max = max_sentences

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        sentences = [s.strip() for s in re.split(r"[.!?]+", value) if s.strip()]
        n = len(sentences)
        if not (self._min <= n <= self._max):
            return FailResult(
                error_message=f"Expected {self._min}-{self._max} sentences, got {n}."
            )
        return PassResult()

guard9 = Guard().use(SentenceCount, min_sentences=2, max_sentences=5, on_fail="exception")
guard9.validate("This is one sentence. This is another. And a third one.")

# ── 10. Timestamp format validator ────────────────────────────────────────────
from datetime import datetime

@register_validator(name="iso-timestamp", data_type="string")
class ISOTimestamp(Validator):
    def validate(self, value: str, metadata: dict) -> ValidationResult:
        try:
            datetime.fromisoformat(value)
            return PassResult()
        except ValueError:
            return FailResult(error_message=f"'{value}' is not a valid ISO timestamp.")

guard10 = Guard().use(ISOTimestamp, on_fail="exception")
guard10.validate("2024-01-15T10:30:00")

# ── 11. JSON schema validator ─────────────────────────────────────────────────
import json
from typing import Any

@register_validator(name="json-schema-check", data_type="string")
class JSONSchemaCheck(Validator):
    def __init__(self, schema: dict, **kwargs):
        super().__init__(**kwargs)
        self._schema = schema

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        try:
            data = json.loads(value)
        except json.JSONDecodeError as e:
            return FailResult(error_message=f"Invalid JSON: {e}")
        for key in self._schema.get("required", []):
            if key not in data:
                return FailResult(error_message=f"Missing required field: '{key}'")
        return PassResult()

guard11 = Guard().use(
    JSONSchemaCheck,
    schema={"required": ["name", "age", "email"]},
    on_fail="exception",
)
guard11.validate('{"name": "Alice", "age": 30, "email": "alice@example.com"}')

# ── 12. URL slug validator ─────────────────────────────────────────────────────
@register_validator(name="url-slug", data_type="string")
class URLSlug(Validator):
    PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        if not self.PATTERN.match(value):
            slug = re.sub(r"[^a-z0-9\s-]", "", value.lower())
            slug = re.sub(r"\s+", "-", slug.strip())
            return FailResult(
                error_message=f"'{value}' is not a valid URL slug.",
                fix_value=slug,
            )
        return PassResult()

guard12 = Guard().use(URLSlug, on_fail="fix")
res12 = guard12.validate("My Blog Post Title!")
print(res12.validated_output)   # "my-blog-post-title"

# ── 13. Readability score (Flesch) ────────────────────────────────────────────
@register_validator(name="flesch-readability", data_type="string")
class FleschReadability(Validator):
    def __init__(self, min_score: float = 60.0, **kwargs):
        super().__init__(**kwargs)
        self._min_score = min_score

    def _flesch(self, text: str) -> float:
        sentences = max(1, len(re.split(r"[.!?]+", text)))
        words = text.split()
        syllables = sum(self._count_syllables(w) for w in words)
        if not words:
            return 0
        return 206.835 - 1.015 * (len(words) / sentences) - 84.6 * (syllables / len(words))

    def _count_syllables(self, word: str) -> int:
        word = word.lower()
        count = len(re.findall(r"[aeiou]", word))
        return max(1, count)

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        score = self._flesch(value)
        if score < self._min_score:
            return FailResult(
                error_message=f"Flesch readability score {score:.1f} is below minimum {self._min_score}."
            )
        return PassResult()

guard13 = Guard().use(FleschReadability, min_score=50.0, on_fail="reask")

# ── 14. Async custom validator ────────────────────────────────────────────────
import asyncio
from guardrails.validator_base import Validator, PassResult, FailResult

@register_validator(name="async-url-check", data_type="string")
class AsyncURLCheck(Validator):
    async def validate_async(self, value: str, metadata: dict) -> ValidationResult:
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(value, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status >= 400:
                        return FailResult(error_message=f"URL returned status {resp.status}.")
        except Exception as e:
            return FailResult(error_message=f"URL unreachable: {e}")
        return PassResult()

# ── 15. Banned keywords validator ────────────────────────────────────────────
@register_validator(name="banned-keywords", data_type="string")
class BannedKeywords(Validator):
    def __init__(self, keywords: list[str], **kwargs):
        super().__init__(**kwargs)
        self._keywords = [k.lower() for k in keywords]

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        text_lower = value.lower()
        found = [k for k in self._keywords if k in text_lower]
        if found:
            return FailResult(error_message=f"Banned keywords detected: {found}")
        return PassResult()

guard15 = Guard().use(
    BannedKeywords,
    keywords=["click here", "act now", "limited time offer", "free money"],
    on_fail="exception",
)
try:
    guard15.validate("Click here to claim your free money now!")
except Exception as e:
    print(f"Spam detected: {e}")

# ── 16. Character limit by type ────────────────────────────────────────────────
@register_validator(name="char-type-limit", data_type="string")
class CharTypeLimit(Validator):
    def __init__(self, max_digits_pct: float = 30.0, **kwargs):
        super().__init__(**kwargs)
        self._max_digits_pct = max_digits_pct

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        if not value:
            return PassResult()
        digit_pct = (sum(c.isdigit() for c in value) / len(value)) * 100
        if digit_pct > self._max_digits_pct:
            return FailResult(
                error_message=f"Text is {digit_pct:.1f}% digits, max allowed is {self._max_digits_pct}%."
            )
        return PassResult()

guard16 = Guard().use(CharTypeLimit, max_digits_pct=20.0, on_fail="exception")
guard16.validate("Call us at 123-456-7890 for more information about our services.")

# ── 17. Citation required validator ───────────────────────────────────────────
@register_validator(name="citation-required", data_type="string")
class CitationRequired(Validator):
    CITATION_PATTERN = re.compile(r"\[[\d]+\]|\(https?://\S+\)|Source:|Reference:")

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        if not self.CITATION_PATTERN.search(value):
            return FailResult(
                error_message="Response must include at least one citation or source reference."
            )
        return PassResult()

guard17 = Guard().use(CitationRequired, on_fail="reask")

# ── 18. Disclaimer required validator ─────────────────────────────────────────
@register_validator(name="disclaimer-required", data_type="string")
class DisclaimerRequired(Validator):
    def __init__(self, disclaimer: str, **kwargs):
        super().__init__(**kwargs)
        self._disclaimer = disclaimer.lower()

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        if self._disclaimer not in value.lower():
            return FailResult(
                error_message=f"Response must contain the disclaimer: '{self._disclaimer}'",
                fix_value=value + f"\n\nDisclaimer: {self._disclaimer}",
            )
        return PassResult()

guard18 = Guard().use(
    DisclaimerRequired,
    disclaimer="This is not financial advice.",
    on_fail="fix",
)
res18 = guard18.validate("Buy AAPL stock now.")
print(res18.validated_output)

# ── 19. Response length in tokens (approximate) ───────────────────────────────
@register_validator(name="token-length", data_type="string")
class TokenLength(Validator):
    def __init__(self, max_tokens: int = 500, **kwargs):
        super().__init__(**kwargs)
        self._max_tokens = max_tokens

    def _approx_tokens(self, text: str) -> int:
        return len(text.split()) * 4 // 3   # rough approximation

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        tokens = self._approx_tokens(value)
        if tokens > self._max_tokens:
            return FailResult(
                error_message=f"Approx {tokens} tokens exceeds max {self._max_tokens}."
            )
        return PassResult()

guard19 = Guard().use(TokenLength, max_tokens=100, on_fail="exception")

# ── 20. Response format: starts with uppercase ────────────────────────────────
@register_validator(name="starts-uppercase", data_type="string")
class StartsUppercase(Validator):
    def validate(self, value: str, metadata: dict) -> ValidationResult:
        stripped = value.lstrip()
        if stripped and not stripped[0].isupper():
            return FailResult(
                error_message="Response must start with an uppercase letter.",
                fix_value=stripped[0].upper() + stripped[1:],
            )
        return PassResult()

guard20 = Guard().use(StartsUppercase, on_fail="fix")
res20 = guard20.validate("the quick brown fox")
print(res20.validated_output)   # "The quick brown fox"

# ── 21. Metadata-driven allowlist validator ───────────────────────────────────
@register_validator(name="dynamic-allowlist", data_type="string")
class DynamicAllowlist(Validator):
    def validate(self, value: str, metadata: dict) -> ValidationResult:
        allowed_values = metadata.get("allowed_values", [])
        if allowed_values and value not in allowed_values:
            return FailResult(
                error_message=f"'{value}' is not in the allowed list: {allowed_values}"
            )
        return PassResult()

guard21 = Guard().use(DynamicAllowlist, on_fail="exception")
guard21.validate(
    "gpt-4o",
    metadata={"allowed_values": ["gpt-4o", "gpt-4o-mini", "claude-sonnet-4-6"]},
)

# ── 22. Composite custom validator pipeline ───────────────────────────────────
blog_guard = Guard().use_many(
    MinWordCount(min_words=50, on_fail="reask"),
    NoCurseWords(on_fail="exception"),
    StartsUppercase(on_fail="fix"),
    SentenceCount(min_sentences=3, max_sentences=20, on_fail="reask"),
)

def validate_blog_post(text: str) -> str:
    res = blog_guard.validate(text)
    return res.validated_output

# ── 23. Marketing copy validator ─────────────────────────────────────────────
@register_validator(name="marketing-safe", data_type="string")
class MarketingSafe(Validator):
    SUPERLATIVES = ["best", "greatest", "only", "perfect", "guaranteed", "100%"]
    CLAIMS = re.compile(r"(cure|treat|heal|fix|guarantee)", re.IGNORECASE)

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        issues = []
        lower = value.lower()
        for s in self.SUPERLATIVES:
            if s in lower.split():
                issues.append(f"Unverified superlative: '{s}'")
        if self.CLAIMS.search(value):
            issues.append("Unverified claim detected.")
        if issues:
            return FailResult(error_message="; ".join(issues))
        return PassResult()

guard23 = Guard().use(MarketingSafe, on_fail="reask")

# ── 24. Hallucination heuristic validator ────────────────────────────────────
@register_validator(name="no-confident-unknown", data_type="string")
class NoConfidentUnknown(Validator):
    """Flags responses that assert facts the LLM commonly hallucinates."""
    RISKY_PATTERNS = re.compile(
        r"\b(according to (a |the )?recent study|research shows|scientists (found|discovered|proved))\b",
        re.IGNORECASE,
    )

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        if self.RISKY_PATTERNS.search(value):
            return FailResult(
                error_message="Response contains unverified research claims. Add specific citations."
            )
        return PassResult()

guard24 = Guard().use(NoConfidentUnknown, on_fail="reask")

# ── 25. Time-zone-aware timestamp validator ───────────────────────────────────
@register_validator(name="utc-timestamp", data_type="string")
class UTCTimestamp(Validator):
    PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$")

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        if not self.PATTERN.match(value):
            return FailResult(error_message=f"'{value}' must be a timezone-aware ISO 8601 timestamp.")
        return PassResult()

guard25 = Guard().use(UTCTimestamp, on_fail="exception")
guard25.validate("2024-01-15T10:30:00Z")

# ── 26. Structured data field count ───────────────────────────────────────────
@register_validator(name="json-field-count", data_type="string")
class JSONFieldCount(Validator):
    def __init__(self, min_fields: int = 1, max_fields: int = 20, **kwargs):
        super().__init__(**kwargs)
        self._min = min_fields
        self._max = max_fields

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        try:
            data = json.loads(value)
            if isinstance(data, dict):
                n = len(data)
                if not (self._min <= n <= self._max):
                    return FailResult(
                        error_message=f"JSON has {n} fields; expected {self._min}-{self._max}."
                    )
        except json.JSONDecodeError:
            return FailResult(error_message="Invalid JSON.")
        return PassResult()

guard26 = Guard().use(JSONFieldCount, min_fields=3, max_fields=10, on_fail="exception")
guard26.validate('{"a": 1, "b": 2, "c": 3}')

# ── 27. Profanity replacer (custom on_fail="fix") ────────────────────────────
@register_validator(name="profanity-replacer", data_type="string")
class ProfanityReplacer(Validator):
    WORDS = {"damn": "darn", "hell": "heck", "crap": "crud"}

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        new_val = value
        for bad, good in self.WORDS.items():
            new_val = re.sub(rf"\b{bad}\b", good, new_val, flags=re.IGNORECASE)
        if new_val != value:
            return FailResult(
                error_message="Mild profanity detected and replaced.",
                fix_value=new_val,
            )
        return PassResult()

guard27 = Guard().use(ProfanityReplacer, on_fail="fix")
res27 = guard27.validate("Oh damn, that was tough!")
print(res27.validated_output)   # "Oh darn, that was tough!"

# ── 28. Domain-specific entity validator ─────────────────────────────────────
@register_validator(name="medical-dosage-format", data_type="string")
class MedicalDosageFormat(Validator):
    PATTERN = re.compile(r"\b\d+(\.\d+)?\s*(mg|ml|mcg|g|units?)\b", re.IGNORECASE)

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        if not self.PATTERN.search(value):
            return FailResult(
                error_message="Medical response should include specific dosage with units (e.g., '500 mg')."
            )
        return PassResult()

guard28 = Guard().use(MedicalDosageFormat, on_fail="reask")

# ── 29. Response contains required sections ───────────────────────────────────
@register_validator(name="required-sections", data_type="string")
class RequiredSections(Validator):
    def __init__(self, sections: list[str], **kwargs):
        super().__init__(**kwargs)
        self._sections = sections

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        missing = [s for s in self._sections if s.lower() not in value.lower()]
        if missing:
            return FailResult(
                error_message=f"Response is missing required sections: {missing}"
            )
        return PassResult()

guard29 = Guard().use(
    RequiredSections,
    sections=["Introduction", "Key Points", "Conclusion"],
    on_fail="reask",
)

res29 = guard29(
    model="gpt-4o-mini",
    messages=[{
        "role": "user",
        "content": "Write a short essay about AI with Introduction, Key Points, and Conclusion sections.",
    }],
    num_reasks=2,
)
print(res29.validated_output)

# ── 30. Currency format validator ─────────────────────────────────────────────
@register_validator(name="currency-format", data_type="string")
class CurrencyFormat(Validator):
    PATTERN = re.compile(r"^\$?\d{1,3}(,\d{3})*(\.\d{2})?$")

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        clean = value.strip().replace("USD", "").strip()
        if not self.PATTERN.match(clean):
            return FailResult(error_message=f"'{value}' is not a valid currency amount.")
        return PassResult()

guard30 = Guard().use(CurrencyFormat, on_fail="exception")
guard30.validate("$1,234.56")

# ── 31. Chain of validators with logging ─────────────────────────────────────
import logging

@register_validator(name="logged-validator", data_type="string")
class LoggedValidator(Validator):
    def __init__(self, inner: Validator, logger_name: str = "guardrails", **kwargs):
        super().__init__(**kwargs)
        self._inner = inner
        self._logger = logging.getLogger(logger_name)

    def validate(self, value: str, metadata: dict) -> ValidationResult:
        result = self._inner.validate(value, metadata)
        if isinstance(result, FailResult):
            self._logger.warning("Validation failed: %s", result.error_message)
        else:
            self._logger.info("Validation passed for: %s...", value[:30])
        return result

# ── 32. Guardrails-compatible async validator ─────────────────────────────────
@register_validator(name="async-fact-check", data_type="string")
class AsyncFactCheck(Validator):
    async def validate_async(self, value: str, metadata: dict) -> ValidationResult:
        import aiohttp
        keywords = value.split()[:5]   # simplified: check first 5 words
        async with aiohttp.ClientSession() as session:
            url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={'+'.join(keywords)}&limit=1"
            async with session.get(url) as resp:
                data = await resp.json()
                if not data[1]:   # no results found
                    return FailResult(error_message="Could not verify facts via Wikipedia.")
        return PassResult()
