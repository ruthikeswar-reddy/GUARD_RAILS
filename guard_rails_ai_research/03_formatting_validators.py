"""
TOPIC 3: Formatting & Structure Validators — 30+ practical examples
Covers: RegexMatch, ValidJSON, ValidHTML, ValidURL, ValidLength, ValidRange,
        ValidChoices, ContainsString, EndsWith, Lowercase, Uppercase,
        OneLineSummary, TwoWords, ReadingTime, CSVValidator, ValidAddress

Install:
  guardrails hub install hub://guardrails/regex_match
  guardrails hub install hub://guardrails/valid_json
  guardrails hub install hub://guardrails/valid_html
  guardrails hub install hub://guardrails/valid_url
  guardrails hub install hub://guardrails/valid_length
  guardrails hub install hub://guardrails/valid_range
  guardrails hub install hub://guardrails/valid_choices
  guardrails hub install hub://guardrails/contains_string
  guardrails hub install hub://guardrails/ends_with
  guardrails hub install hub://guardrails/lowercase
  guardrails hub install hub://guardrails/uppercase
  guardrails hub install hub://guardrails/one_line
  guardrails hub install hub://guardrails/two_words
  guardrails hub install hub://guardrails/reading_time
  guardrails hub install hub://guardrails/csv_validator
  guardrails hub install hub://guardrails/valid_address
"""

from guardrails import Guard

# ── 1. Regex — US phone number ────────────────────────────────────────────────
from guardrails.hub import RegexMatch

guard = Guard().use(RegexMatch, regex=r"^\d{3}-\d{3}-\d{4}$", on_fail="exception")
guard.parse("123-456-7890")

# ── 2. Regex — email format ───────────────────────────────────────────────────
guard2 = Guard().use(
    RegexMatch, regex=r"^[\w.+-]+@[\w-]+\.[\w.]+$", on_fail="exception"
)
guard2.parse("user@example.com")

# ── 3. Regex — zip code ───────────────────────────────────────────────────────
guard3 = Guard().use(RegexMatch, regex=r"^\d{5}(-\d{4})?$", on_fail="exception")
guard3.parse("90210")

# ── 4. Regex — ISO 8601 date ─────────────────────────────────────────────────
guard4 = Guard().use(
    RegexMatch, regex=r"^\d{4}-\d{2}-\d{2}$", on_fail="exception"
)
guard4.parse("2024-01-15")

# ── 5. Regex — UUID ───────────────────────────────────────────────────────────
guard5 = Guard().use(
    RegexMatch,
    regex=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    on_fail="exception",
)
guard5.parse("550e8400-e29b-41d4-a716-446655440000")

# ── 6. Regex — hex color ─────────────────────────────────────────────────────
guard6 = Guard().use(RegexMatch, regex=r"^#[0-9a-fA-F]{6}$", on_fail="exception")
guard6.parse("#ff5733")

# ── 7. Valid JSON ─────────────────────────────────────────────────────────────
from guardrails.hub import ValidJson

guard7 = Guard().use(ValidJson, on_fail="exception")
guard7.parse('{"name": "Alice", "age": 30}')

# ── 8. Valid JSON — reask until LLM produces valid JSON ──────────────────────
guard8 = Guard().use(ValidJson, on_fail="reask")
res8 = guard8(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Return a JSON object with name and score."}],
    num_reasks=2,
)
print(res8.validated_output)

# ── 9. Valid HTML ─────────────────────────────────────────────────────────────
from guardrails.hub import ValidHtml

guard9 = Guard().use(ValidHtml, on_fail="exception")
guard9.parse("<h1>Hello</h1><p>World</p>")

# ── 10. Valid URL ─────────────────────────────────────────────────────────────
from guardrails.hub import ValidUrl

guard10 = Guard().use(ValidUrl, on_fail="exception")
guard10.parse("https://www.guardrailsai.com")

# ── 11. Valid URL — check URL is reachable ───────────────────────────────────
from guardrails.hub import EndpointIsReachable

guard11 = Guard().use(EndpointIsReachable, on_fail="exception")
guard11.parse("https://www.google.com")

# ── 12. Valid length — minimum ────────────────────────────────────────────────
from guardrails.hub import ValidLength

guard12 = Guard().use(ValidLength, min=10, on_fail="exception")
guard12.parse("This is a valid sentence with enough length.")

# ── 13. Valid length — maximum ────────────────────────────────────────────────
guard13 = Guard().use(ValidLength, max=280, on_fail="exception")
guard13.parse("Short tweet content.")   # must be ≤ 280 chars

# ── 14. Valid length — min & max ─────────────────────────────────────────────
guard14 = Guard().use(ValidLength, min=50, max=500, on_fail="exception")
guard14.parse("A" * 200)

# ── 15. Valid range — numeric string in range ────────────────────────────────
from guardrails.hub import ValidRange

guard15 = Guard().use(ValidRange, min=1, max=10, on_fail="exception")
guard15.parse("7")   # LLM should output a number 1-10

# ── 16. Valid choices ─────────────────────────────────────────────────────────
from guardrails.hub import ValidChoices

guard16 = Guard().use(
    ValidChoices, choices=["positive", "negative", "neutral"], on_fail="exception"
)
guard16.parse("positive")

# ── 17. Valid choices — sentiment classifier ─────────────────────────────────
sentiment_guard = Guard().use(
    ValidChoices, choices=["POSITIVE", "NEGATIVE", "NEUTRAL"], on_fail="reask"
)
res17 = sentiment_guard(
    model="gpt-4o-mini",
    messages=[{
        "role": "user",
        "content": "Classify the sentiment of 'I love this!'. Reply with exactly one word: POSITIVE, NEGATIVE, or NEUTRAL.",
    }],
    num_reasks=2,
)
print(res17.validated_output)

# ── 18. ContainsString ────────────────────────────────────────────────────────
from guardrails.hub import ContainsString

guard18 = Guard().use(ContainsString, needle="disclaimer", on_fail="exception")
guard18.parse("This is not financial advice. disclaimer: consult a professional.")

# ── 19. EndsWith ──────────────────────────────────────────────────────────────
from guardrails.hub import EndsWith

guard19 = Guard().use(EndsWith, end=".", on_fail="fix")
res19 = guard19.parse("The sky is blue")
print(res19.validated_output)   # "The sky is blue."

# ── 20. Lowercase ────────────────────────────────────────────────────────────
from guardrails.hub import LowerCase

guard20 = Guard().use(LowerCase, on_fail="fix")
res20 = guard20.parse("Hello WORLD")
print(res20.validated_output)   # "hello world"

# ── 21. Uppercase ────────────────────────────────────────────────────────────
from guardrails.hub import UpperCase

guard21 = Guard().use(UpperCase, on_fail="fix")
res21 = guard21.parse("hello world")
print(res21.validated_output)   # "HELLO WORLD"

# ── 22. One-line response enforcement ────────────────────────────────────────
from guardrails.hub import OneLine

guard22 = Guard().use(OneLine, on_fail="exception")
guard22.parse("This is exactly one line.")
try:
    guard22.parse("Line one.\nLine two.")
except Exception as e:
    print(f"Multi-line blocked: {e}")

# ── 23. Two words enforcement ────────────────────────────────────────────────
from guardrails.hub import TwoWords

guard23 = Guard().use(TwoWords, on_fail="exception")
guard23.parse("Hello world")
try:
    guard23.parse("Too many words here")
except Exception as e:
    print(f"Not two words: {e}")

# ── 24. Reading time constraint ──────────────────────────────────────────────
from guardrails.hub import ReadingTime

guard24 = Guard().use(ReadingTime, reading_time=2, on_fail="exception")
# reading_time=2 means the text should be readable in ≤ 2 minutes

# ── 25. CSV validator ────────────────────────────────────────────────────────
from guardrails.hub import CsvValidator

guard25 = Guard().use(CsvValidator, on_fail="exception")
guard25.parse("name,age,city\nAlice,30,NYC\nBob,25,LA")

# ── 26. Valid address ────────────────────────────────────────────────────────
from guardrails.hub import ValidAddress

guard26 = Guard().use(ValidAddress, on_fail="exception")
guard26.parse("1600 Pennsylvania Ave NW, Washington, DC 20500")

# ── 27. Regex + ValidLength — tweet enforcer ─────────────────────────────────
from guardrails.hub import RegexMatch, ValidLength

tweet_guard = Guard().use_many(
    ValidLength(max=280, on_fail="exception"),
    RegexMatch(regex=r"^[^@#]*$", on_fail="exception"),   # no mentions/hashtags
)
tweet_guard.parse("Just had an amazing breakfast this morning!")

# ── 28. JSON + ContainsString — API response validator ───────────────────────
from guardrails.hub import ValidJson, ContainsString

api_guard = Guard().use_many(
    ValidJson(on_fail="exception"),
    ContainsString(needle="status", on_fail="exception"),
)
api_guard.parse('{"status": "ok", "data": [1, 2, 3]}')

# ── 29. Format-chain: lowercase + one-line + valid length ────────────────────
keyword_guard = Guard().use_many(
    LowerCase(on_fail="fix"),
    OneLine(on_fail="exception"),
    ValidLength(max=50, on_fail="exception"),
)
res29 = keyword_guard.parse("Machine Learning")
print(res29.validated_output)   # "machine learning"

# ── 30. LLM forced to produce valid choices with reask ───────────────────────
priority_guard = Guard().use(
    ValidChoices, choices=["low", "medium", "high", "critical"], on_fail="reask"
)
res30 = priority_guard(
    model="gpt-4o-mini",
    messages=[{
        "role": "user",
        "content": "Classify ticket priority. Reply with exactly one word: low, medium, high, or critical.",
    }],
    num_reasks=3,
)
print(res30.validated_output)

# ── 31. Guard valid HTML from LLM ────────────────────────────────────────────
html_guard = Guard().use(ValidHtml, on_fail="reask")
res31 = html_guard(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Generate valid HTML for a simple webpage about cats."}],
    num_reasks=2,
)
print(res31.validated_output)

# ── 32. URL list validator — extract and validate each URL ────────────────────
from guardrails.hub import ValidUrl

def validate_url_list(urls: list[str]) -> list[str]:
    guard_url = Guard().use(ValidUrl, on_fail="filter")
    return [
        guard_url.parse(u).validated_output
        for u in urls
        if guard_url.parse(u).validation_passed
    ]

valid_urls = validate_url_list([
    "https://google.com",
    "not-a-url",
    "https://openai.com",
    "ftp://invalid",
])
print(valid_urls)

# ── 33. Structured output enforcer: JSON with schema validation ───────────────
from guardrails import Guard
from pydantic import BaseModel
from guardrails.hub import ValidJson

class UserProfile(BaseModel):
    username: str
    email: str
    age: int

profile_guard = Guard.for_pydantic(UserProfile).use(ValidJson, on_fail="reask")
res33 = profile_guard(
    model="gpt-4o-mini",
    messages=[{
        "role": "user",
        "content": 'Create a fake user profile as JSON with username, email, and age fields.',
    }],
    num_reasks=2,
)
print(res33.validated_output)
