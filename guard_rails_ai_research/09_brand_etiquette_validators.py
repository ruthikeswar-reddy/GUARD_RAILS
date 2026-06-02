"""
TOPIC 9: Brand & Etiquette Validators — 30+ practical examples
Covers: CompetitorCheck, BiasCheck, QuotesPrice, CorrectLanguage,
        FinancialTone, HighQualityTranslation, GibberishText,
        LogicCheck, PolitenesCheck, ReadingLevel

Install:
  guardrails hub install hub://guardrails/competitor_check
  guardrails hub install hub://guardrails/bias_check
  guardrails hub install hub://guardrails/quotes_price
  guardrails hub install hub://guardrails/correct_language
  guardrails hub install hub://guardrails/financial_tone
  guardrails hub install hub://guardrails/high_quality_translation
  guardrails hub install hub://guardrails/gibberish_text
  guardrails hub install hub://guardrails/logic_check
  guardrails hub install hub://guardrails/politeness_check
  guardrails hub install hub://guardrails/reading_level
"""

import openai
from guardrails import Guard

# ──────────────────────────────────────────────────────────────────────────────
# COMPETITOR CHECK
# ──────────────────────────────────────────────────────────────────────────────

# ── 1. Basic competitor mention block ────────────────────────────────────────
from guardrails.hub import CompetitorCheck

guard1 = Guard().use(
    CompetitorCheck,
    competitors=["OpenAI", "Google", "Microsoft", "Amazon"],
    on_fail="exception",
)
try:
    guard1.parse("You should switch to Google Bard instead.")
except Exception as e:
    print(f"Competitor mention blocked: {e}")

# ── 2. Competitor check — passes for own company ─────────────────────────────
guard1.parse("Our AI platform offers superior accuracy and support.")   # passes

# ── 3. Competitor check — filter (remove mention) ────────────────────────────
guard3 = Guard().use(
    CompetitorCheck, competitors=["Slack", "Teams"], on_fail="filter"
)
res3 = guard3.parse("Unlike Slack, our messaging is end-to-end encrypted.")
print(res3.validated_output)   # competitor name filtered out

# ── 4. Competitor check — reask for clean response ───────────────────────────
guard4 = Guard().use(
    CompetitorCheck, competitors=["Salesforce", "HubSpot"], on_fail="reask"
)
res4 = guard4(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What makes our CRM unique? Don't mention competitors."}],
    num_reasks=2,
)
print(res4.validated_output)

# ── 5. Customer-facing chatbot: no competitor mentions ────────────────────────
chatbot_guard = Guard(name="brand-chatbot").use(
    CompetitorCheck,
    competitors=["CompetitorA", "CompetitorB", "CompetitorC"],
    on_fail="filter",
)

def brand_safe_chatbot_reply(user_question: str) -> str:
    raw = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for OurCompany."},
            {"role": "user", "content": user_question},
        ],
    ).choices[0].message.content
    return chatbot_guard.parse(raw).validated_output

# ──────────────────────────────────────────────────────────────────────────────
# BIAS CHECK
# ──────────────────────────────────────────────────────────────────────────────

# ── 6. Basic bias detection ───────────────────────────────────────────────────
from guardrails.hub import BiasCheck

guard6 = Guard().use(BiasCheck, on_fail="exception")
guard6.parse("The study examines economic trends across multiple demographics.")   # neutral

# ── 7. Bias check — reject biased content ────────────────────────────────────
try:
    guard6.parse("Men are naturally better at engineering than women.")
except Exception as e:
    print(f"Bias detected: {e}")

# ── 8. Bias check in HR application ──────────────────────────────────────────
hr_guard = Guard(name="hr-fairness").use(BiasCheck, on_fail="exception")

def fair_job_description(role: str) -> str:
    raw = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Write a job description for a {role}."}],
    ).choices[0].message.content
    return hr_guard.parse(raw).validated_output

# ── 9. Bias check in content generation ──────────────────────────────────────
guard9 = Guard().use(BiasCheck, on_fail="reask")
res9 = guard9(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Write an article about leadership styles."}],
    num_reasks=2,
)
print(res9.validated_output)

# ──────────────────────────────────────────────────────────────────────────────
# QUOTES PRICE / FINANCIAL RESTRICTIONS
# ──────────────────────────────────────────────────────────────────────────────

# ── 10. Block price quotes ────────────────────────────────────────────────────
from guardrails.hub import QuotesPrice

guard10 = Guard().use(QuotesPrice, on_fail="exception")
try:
    guard10.parse("AAPL will hit $210 by the end of Q2.")
except Exception as e:
    print(f"Price quote blocked: {e}")

# ── 11. Financial assistant — no price predictions ───────────────────────────
fin_guard = Guard(name="fin-assistant").use(QuotesPrice, on_fail="exception")

def safe_financial_response(question: str) -> str:
    raw = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a financial assistant. Never predict specific prices."},
            {"role": "user", "content": question},
        ],
    ).choices[0].message.content
    return fin_guard.parse(raw).validated_output

# ── 12. Financial tone check ──────────────────────────────────────────────────
from guardrails.hub import FinancialTone

guard12 = Guard().use(FinancialTone, on_fail="reask")
res12 = guard12(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Explain the risks of investing in volatile markets."}],
    num_reasks=2,
)
print(res12.validated_output)

# ── 13. Finance: tone + no price quotes ──────────────────────────────────────
full_fin_guard = Guard(name="financial-safe").use_many(
    FinancialTone(on_fail="reask"),
    QuotesPrice(on_fail="exception"),
    BiasCheck(on_fail="exception"),
)

def regulatory_safe_response(query: str) -> str:
    res = full_fin_guard(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a regulated financial advisor. Be balanced and factual."},
            {"role": "user", "content": query},
        ],
        num_reasks=2,
    )
    return res.validated_output

# ──────────────────────────────────────────────────────────────────────────────
# CORRECT LANGUAGE
# ──────────────────────────────────────────────────────────────────────────────

# ── 14. Enforce English output ────────────────────────────────────────────────
from guardrails.hub import CorrectLanguage

guard14 = Guard().use(CorrectLanguage, expected_language="en", on_fail="exception")
guard14.parse("The weather today is sunny and warm.")

# ── 15. Enforce Spanish output ────────────────────────────────────────────────
guard15 = Guard().use(CorrectLanguage, expected_language="es", on_fail="reask")
res15 = guard15(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Respond in Spanish: What is 2+2?"}],
    num_reasks=2,
)
print(res15.validated_output)

# ── 16. Multi-language support routing ───────────────────────────────────────
def language_guarded_response(user_msg: str, lang: str) -> str:
    guard = Guard().use(CorrectLanguage, expected_language=lang, on_fail="reask")
    res = guard(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"Always respond in {lang}."},
            {"role": "user", "content": user_msg},
        ],
        num_reasks=2,
    )
    return res.validated_output

# ──────────────────────────────────────────────────────────────────────────────
# TRANSLATION QUALITY
# ──────────────────────────────────────────────────────────────────────────────

# ── 17. High-quality translation validator ────────────────────────────────────
from guardrails.hub import HighQualityTranslation

guard17 = Guard().use(HighQualityTranslation, on_fail="reask")
res17 = guard17(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Translate 'The quick brown fox jumps over the lazy dog' to French."}],
    num_reasks=2,
)
print(res17.validated_output)

# ── 18. Translation pipeline with quality + language check ───────────────────
translation_guard = Guard().use_many(
    HighQualityTranslation(on_fail="reask"),
    CorrectLanguage(expected_language="de", on_fail="reask"),
)

def safe_translate_to_german(english_text: str) -> str:
    res = translation_guard(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Translate to German: {english_text}"}],
        num_reasks=2,
    )
    return res.validated_output

# ──────────────────────────────────────────────────────────────────────────────
# GIBBERISH TEXT DETECTION
# ──────────────────────────────────────────────────────────────────────────────

# ── 19. Detect gibberish in LLM output ───────────────────────────────────────
from guardrails.hub import GibberishText

guard19 = Guard().use(GibberishText, on_fail="exception")
guard19.parse("The stock market fluctuated significantly today due to earnings reports.")

# ── 20. Gibberish detection catches nonsense ─────────────────────────────────
try:
    guard19.parse("asdfghjkl zxcvbnm qwertyuiop lorem gibberish foo bar baz")
except Exception as e:
    print(f"Gibberish detected: {e}")

# ── 21. Gibberish + valid length — meaningful response enforcer ───────────────
from guardrails.hub import ValidLength

meaningful_guard = Guard().use_many(
    GibberishText(on_fail="reask"),
    ValidLength(min=20, on_fail="reask"),
)
res21 = meaningful_guard(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is machine learning?"}],
    num_reasks=2,
)
print(res21.validated_output)

# ──────────────────────────────────────────────────────────────────────────────
# LOGIC CHECK
# ──────────────────────────────────────────────────────────────────────────────

# ── 22. Logic check validator ─────────────────────────────────────────────────
from guardrails.hub import LogicCheck

guard22 = Guard().use(LogicCheck, llm_callable="gpt-4o-mini", on_fail="reask")
res22 = guard22(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Explain why renewable energy is important for the environment."}],
    num_reasks=2,
)
print(res22.validated_output)

# ── 23. Logic check — catch contradictions ───────────────────────────────────
try:
    guard22.parse(
        "Electric cars are better for the environment. Also, electric cars produce more CO2 than gas cars.",
    )
except Exception as e:
    print(f"Logical contradiction: {e}")

# ──────────────────────────────────────────────────────────────────────────────
# READING LEVEL
# ──────────────────────────────────────────────────────────────────────────────

# ── 24. Reading level for children's content ─────────────────────────────────
from guardrails.hub import ReadingLevel

kids_guard = Guard().use(ReadingLevel, grade_level=4, on_fail="reask")
res24 = kids_guard(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Explain photosynthesis for a 4th grader."}],
    num_reasks=2,
)
print(res24.validated_output)

# ── 25. Reading level for academic content ────────────────────────────────────
academic_guard = Guard().use(ReadingLevel, grade_level=16, on_fail="reask")
res25 = academic_guard(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Explain quantum entanglement at a college graduate level."}],
    num_reasks=2,
)
print(res25.validated_output)

# ── 26. Adaptive reading level by audience ───────────────────────────────────
def audience_appropriate_response(topic: str, grade: int) -> str:
    guard = Guard().use(ReadingLevel, grade_level=grade, on_fail="reask")
    res = guard(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Explain {topic} at a grade {grade} reading level.",
        }],
        num_reasks=3,
    )
    return res.validated_output

# ──────────────────────────────────────────────────────────────────────────────
# POLITENESS CHECK
# ──────────────────────────────────────────────────────────────────────────────

# ── 27. Politeness check ──────────────────────────────────────────────────────
from guardrails.hub import PolitenesCheck

guard27 = Guard().use(PolitenesCheck, on_fail="exception")
guard27.parse("I hope this information helps. Please feel free to ask any questions!")

# ── 28. Customer service politeness enforcer ─────────────────────────────────
service_guard = Guard(name="cs-politeness").use_many(
    PolitenesCheck(on_fail="reask"),
    GibberishText(on_fail="reask"),
    ReadingLevel(grade_level=8, on_fail="reask"),
)

def polished_support_reply(issue: str) -> str:
    res = service_guard(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a polite, professional customer service agent."},
            {"role": "user", "content": issue},
        ],
        num_reasks=2,
    )
    return res.validated_output

# ──────────────────────────────────────────────────────────────────────────────
# FULL BRAND SAFETY PIPELINES
# ──────────────────────────────────────────────────────────────────────────────

# ── 29. Complete brand-safe output pipeline ───────────────────────────────────
from guardrails.hub import (
    CompetitorCheck, BiasCheck, PolitenesCheck,
    GibberishText, ReadingLevel, ToxicLanguage
)

brand_guard = Guard(name="brand-safe-full").use_many(
    CompetitorCheck(competitors=["CompetitorA", "CompetitorB"], on_fail="filter"),
    BiasCheck(on_fail="reask"),
    PolitenesCheck(on_fail="reask"),
    GibberishText(on_fail="reask"),
    ToxicLanguage(threshold=0.4, on_fail="filter"),
    ReadingLevel(grade_level=10, on_fail="reask"),
)

def brand_safe_content(prompt: str) -> str:
    res = brand_guard(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a brand-aligned content creator."},
            {"role": "user", "content": prompt},
        ],
        num_reasks=3,
    )
    return res.validated_output

# ── 30. Marketing copy pipeline ──────────────────────────────────────────────
marketing_guard = Guard(name="marketing").use_many(
    CompetitorCheck(competitors=["RivalCorp", "OtherBrand"], on_fail="filter"),
    BiasCheck(on_fail="reask"),
    GibberishText(on_fail="reask"),
    ValidLength(min=50, max=500, on_fail="reask"),
)

def generate_safe_marketing_copy(product: str, audience: str) -> str:
    res = marketing_guard(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Write marketing copy for '{product}' targeting '{audience}'. Be engaging, unbiased, and avoid mentioning competitors.",
        }],
        num_reasks=2,
    )
    return res.validated_output

from guardrails.hub import ValidLength

copy = generate_safe_marketing_copy("EcoBottle Pro", "health-conscious millennials")
print(copy)

# ── 31. Multilingual brand safety ─────────────────────────────────────────────
multilingual_guard = Guard(name="multilingual-brand").use_many(
    CompetitorCheck(competitors=["Rival Inc"], on_fail="filter"),
    PolitenesCheck(on_fail="reask"),
    HighQualityTranslation(on_fail="reask"),
)

def safe_localized_content(content: str, target_lang: str) -> str:
    res = multilingual_guard(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Translate this to {target_lang}, keeping brand tone: {content}",
        }],
        num_reasks=2,
    )
    return res.validated_output

# ── 32. Async brand safety ────────────────────────────────────────────────────
import asyncio
from guardrails import AsyncGuard

async def async_brand_safe(prompt: str) -> str:
    aguard = AsyncGuard().use_many(
        CompetitorCheck(competitors=["CompetitorX"], on_fail="filter"),
        ToxicLanguage(threshold=0.4, on_fail="filter"),
        GibberishText(on_fail="reask"),
    )
    res = await aguard(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        num_reasks=2,
    )
    return res.validated_output

asyncio.run(async_brand_safe("Write a paragraph about our commitment to sustainability."))
