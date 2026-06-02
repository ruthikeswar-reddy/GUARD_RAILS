"""
TOPIC 7: Structured Output with Pydantic — 30+ practical examples
Covers: Guard.for_pydantic, nested models, validators on fields,
        custom field validators, JSON parsing, schema enforcement

Install:
  pip install guardrails-ai pydantic
"""

from __future__ import annotations
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from guardrails import Guard
import openai

# ──────────────────────────────────────────────────────────────────────────────
# BASIC PYDANTIC GUARDS
# ──────────────────────────────────────────────────────────────────────────────

# ── 1. Simple flat model ──────────────────────────────────────────────────────
class ProductReview(BaseModel):
    product_name: str
    rating: int          # 1-5
    review_text: str

guard1 = Guard.for_pydantic(ProductReview)
res1 = guard1(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Write a product review for a wireless mouse. Return JSON."}],
)
review: ProductReview = res1.validated_output
print(review.product_name, review.rating)

# ── 2. Model with Optional fields ────────────────────────────────────────────
class UserProfile(BaseModel):
    username: str
    email: str
    bio: Optional[str] = None
    age: Optional[int] = None

guard2 = Guard.for_pydantic(UserProfile)
res2 = guard2(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Generate a fake user profile as JSON."}],
)
print(res2.validated_output)

# ── 3. Model with Literal choices ────────────────────────────────────────────
class SentimentAnalysis(BaseModel):
    text: str
    sentiment: Literal["positive", "negative", "neutral"]
    confidence: float

guard3 = Guard.for_pydantic(SentimentAnalysis)
res3 = guard3(
    model="gpt-4o-mini",
    messages=[{
        "role": "user",
        "content": "Analyze the sentiment of 'I love this product!' and return JSON with text, sentiment, and confidence.",
    }],
)
print(res3.validated_output)

# ── 4. Model with List fields ─────────────────────────────────────────────────
class RecipeOutput(BaseModel):
    name: str
    ingredients: List[str]
    steps: List[str]
    prep_time_minutes: int

guard4 = Guard.for_pydantic(RecipeOutput)
res4 = guard4(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Give me a pasta recipe as JSON."}],
)
recipe: RecipeOutput = res4.validated_output
print(f"{recipe.name}: {len(recipe.ingredients)} ingredients")

# ── 5. Nested models ─────────────────────────────────────────────────────────
class Address(BaseModel):
    street: str
    city: str
    country: str
    zip_code: str

class Company(BaseModel):
    name: str
    industry: str
    address: Address
    employee_count: int

guard5 = Guard.for_pydantic(Company)
res5 = guard5(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Generate a fake tech company with address as nested JSON."}],
)
print(res5.validated_output)

# ── 6. List of nested models ──────────────────────────────────────────────────
class StockItem(BaseModel):
    symbol: str
    price: float
    change_percent: float

class PortfolioSnapshot(BaseModel):
    timestamp: str
    total_value: float
    holdings: List[StockItem]

guard6 = Guard.for_pydantic(PortfolioSnapshot)
res6 = guard6(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Generate a stock portfolio snapshot JSON with 3 holdings."}],
)
print(res6.validated_output)

# ── 7. Model with field validators ───────────────────────────────────────────
class Temperature(BaseModel):
    value: float
    unit: Literal["celsius", "fahrenheit", "kelvin"]

    @field_validator("value")
    @classmethod
    def value_in_range(cls, v: float) -> float:
        if v < -273.15:
            raise ValueError("Temperature cannot be below absolute zero.")
        return v

guard7 = Guard.for_pydantic(Temperature)
res7 = guard7(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Return the boiling point of water as JSON with value and unit (celsius)."}],
)
print(res7.validated_output)

# ── 8. Model with model_validator (cross-field) ───────────────────────────────
class DateRange(BaseModel):
    start_date: str   # YYYY-MM-DD
    end_date: str

    @model_validator(mode="after")
    def check_date_order(self) -> "DateRange":
        if self.start_date > self.end_date:
            raise ValueError("start_date must be before end_date.")
        return self

guard8 = Guard.for_pydantic(DateRange)
res8 = guard8(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Give me a date range for Q1 2024 as JSON."}],
)
print(res8.validated_output)

# ── 9. Model with Field descriptions (used in prompt injection) ───────────────
class JobPosting(BaseModel):
    title: str = Field(description="Job title, e.g. 'Senior Software Engineer'")
    company: str = Field(description="Company name")
    salary_range: str = Field(description="Salary range, e.g. '$100k-$150k'")
    remote: bool = Field(description="Whether the job is remote")
    requirements: List[str] = Field(description="List of required skills")

guard9 = Guard.for_pydantic(JobPosting)
res9 = guard9(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Generate a job posting for a Python developer role as JSON."}],
)
print(res9.validated_output)

# ── 10. Enum-based model ──────────────────────────────────────────────────────
from enum import Enum

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SupportTicket(BaseModel):
    ticket_id: str
    subject: str
    priority: Priority
    description: str
    tags: List[str]

guard10 = Guard.for_pydantic(SupportTicket)
res10 = guard10(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Create a support ticket for a login issue as JSON."}],
)
ticket: SupportTicket = res10.validated_output
print(f"Priority: {ticket.priority}")

# ── 11. Guard with reask for invalid structured output ───────────────────────
class BudgetAllocation(BaseModel):
    total_budget: float
    marketing: float
    engineering: float
    operations: float

    @model_validator(mode="after")
    def allocations_sum_to_budget(self) -> "BudgetAllocation":
        total = self.marketing + self.engineering + self.operations
        if abs(total - self.total_budget) > 0.01:
            raise ValueError(f"Allocations ({total}) must sum to total_budget ({self.total_budget}).")
        return self

guard11 = Guard.for_pydantic(BudgetAllocation)
res11 = guard11(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Allocate a $1,000,000 budget across marketing, engineering, and operations as JSON."}],
    num_reasks=2,
)
print(res11.validated_output)

# ── 12. Structured output for entity extraction ───────────────────────────────
class ExtractedEntity(BaseModel):
    text: str
    entity_type: Literal["PERSON", "ORG", "LOCATION", "DATE", "PRODUCT"]
    confidence: float

class NEROutput(BaseModel):
    input_text: str
    entities: List[ExtractedEntity]

guard12 = Guard.for_pydantic(NEROutput)
res12 = guard12(
    model="gpt-4o-mini",
    messages=[{
        "role": "user",
        "content": "Extract entities from: 'Apple Inc. was founded by Steve Jobs in Cupertino in 1976.' Return JSON.",
    }],
)
ner: NEROutput = res12.validated_output
for entity in ner.entities:
    print(f"{entity.text} -> {entity.entity_type}")

# ── 13. Structured output for classification ─────────────────────────────────
class DocumentClassification(BaseModel):
    category: Literal["finance", "healthcare", "legal", "technology", "marketing", "other"]
    subcategory: Optional[str]
    confidence_score: float
    reasoning: str

guard13 = Guard.for_pydantic(DocumentClassification)
res13 = guard13(
    model="gpt-4o-mini",
    messages=[{
        "role": "user",
        "content": "Classify this document: 'Q3 earnings show 15% revenue growth driven by SaaS subscriptions.' Return JSON.",
    }],
)
print(res13.validated_output)

# ── 14. Structured output for summarization ───────────────────────────────────
class ArticleSummary(BaseModel):
    title: str
    one_liner: str
    key_points: List[str]
    word_count: int
    reading_time_minutes: float

guard14 = Guard.for_pydantic(ArticleSummary)

def structured_summarize(article_text: str) -> ArticleSummary:
    res = guard14(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Summarize this article as JSON:\n\n{article_text}",
        }],
        num_reasks=2,
    )
    return res.validated_output

# ── 15. Structured output for Q&A ────────────────────────────────────────────
class QAResponse(BaseModel):
    question: str
    answer: str
    sources: List[str]
    confidence: float
    needs_human_review: bool

guard15 = Guard.for_pydantic(QAResponse)
res15 = guard15(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Answer: 'What is the capital of France?' Return JSON with question, answer, sources, confidence, and needs_human_review."}],
)
print(res15.validated_output)

# ── 16. Structured output for code generation ────────────────────────────────
class CodeSolution(BaseModel):
    language: str
    code: str
    explanation: str
    time_complexity: str
    space_complexity: str

guard16 = Guard.for_pydantic(CodeSolution)
res16 = guard16(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Implement binary search in Python and return as JSON with code, explanation, time_complexity, space_complexity."}],
)
solution: CodeSolution = res16.validated_output
print(solution.code)
print(f"Time: {solution.time_complexity}, Space: {solution.space_complexity}")

# ── 17. Structured output for product recommendations ────────────────────────
class ProductRecommendation(BaseModel):
    product_id: str
    product_name: str
    reason: str
    price: float
    match_score: float

class RecommendationList(BaseModel):
    user_query: str
    recommendations: List[ProductRecommendation]
    total_count: int

guard17 = Guard.for_pydantic(RecommendationList)
res17 = guard17(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Recommend 3 laptops for a programmer. Return JSON."}],
)
recs: RecommendationList = res17.validated_output
for r in recs.recommendations:
    print(f"{r.product_name}: ${r.price} (score: {r.match_score})")

# ── 18. Structured output for data transformation ────────────────────────────
class TransformedRecord(BaseModel):
    original: str
    normalized: str
    category: str
    is_valid: bool

guard18 = Guard.for_pydantic(TransformedRecord)

def transform_with_llm(raw_value: str) -> TransformedRecord:
    res = guard18(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Normalize this value: '{raw_value}'. Return JSON with original, normalized, category, is_valid.",
        }],
    )
    return res.validated_output

# ── 19. Structured output for chatbot with action routing ─────────────────────
class ChatbotIntent(BaseModel):
    user_message: str
    intent: Literal["faq", "complaint", "order_status", "refund", "other"]
    sentiment: Literal["positive", "negative", "neutral"]
    entities: dict
    escalate_to_human: bool

guard19 = Guard.for_pydantic(ChatbotIntent)

def classify_chat_intent(message: str) -> ChatbotIntent:
    res = guard19(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Classify this customer message: '{message}'. Return JSON with intent, sentiment, entities, escalate_to_human.",
        }],
    )
    return res.validated_output

# ── 20. Structured output for medical triage ─────────────────────────────────
class TriageAssessment(BaseModel):
    symptoms: List[str]
    urgency_level: Literal["emergency", "urgent", "routine", "self_care"]
    recommended_action: str
    disclaimer: str = "This is not medical advice. Please consult a doctor."

guard20 = Guard.for_pydantic(TriageAssessment)
res20 = guard20(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Patient reports mild headache and fatigue. Triage as JSON."}],
)
print(res20.validated_output)

# ── 21. Structured output for financial analysis ──────────────────────────────
class FinancialMetrics(BaseModel):
    company: str
    revenue_usd_millions: float
    ebitda_margin_percent: float
    debt_to_equity: float
    growth_rate_percent: float
    investment_rating: Literal["strong_buy", "buy", "hold", "sell", "strong_sell"]

guard21 = Guard.for_pydantic(FinancialMetrics)
res21 = guard21(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Analyze Apple Inc. financials and return structured JSON."}],
)
print(res21.validated_output)

# ── 22. Structured output for SEO analysis ───────────────────────────────────
class SEOAnalysis(BaseModel):
    page_title: str
    meta_description: str
    primary_keyword: str
    secondary_keywords: List[str]
    readability_score: float
    seo_score: int
    recommendations: List[str]

guard22 = Guard.for_pydantic(SEOAnalysis)
res22 = guard22(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Analyze SEO for a blog post about 'Python best practices' and return JSON."}],
)
print(res22.validated_output)

# ── 23. Structured output for event extraction ────────────────────────────────
class CalendarEvent(BaseModel):
    title: str
    date: str       # YYYY-MM-DD
    start_time: str  # HH:MM
    end_time: str
    location: Optional[str]
    attendees: List[str]
    description: Optional[str]

guard23 = Guard.for_pydantic(CalendarEvent)

def extract_event_from_email(email_text: str) -> CalendarEvent:
    res = guard23(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Extract calendar event from this email and return JSON:\n\n{email_text}",
        }],
    )
    return res.validated_output

# ── 24. Structured output for resume parsing ─────────────────────────────────
class WorkExperience(BaseModel):
    company: str
    role: str
    start_date: str
    end_date: Optional[str]
    description: str

class ResumeData(BaseModel):
    name: str
    email: str
    phone: Optional[str]
    skills: List[str]
    work_experience: List[WorkExperience]
    education: List[str]

guard24 = Guard.for_pydantic(ResumeData)

def parse_resume(resume_text: str) -> ResumeData:
    res = guard24(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Parse this resume and return structured JSON:\n\n{resume_text}",
        }],
        num_reasks=2,
    )
    return res.validated_output

# ── 25. Structured output with guardrails validators on fields ────────────────
from guardrails import Guard
from guardrails.hub import ToxicLanguage

class SafeProductDescription(BaseModel):
    product_name: str
    description: str
    price: float
    category: str

# Apply guardrails validators on top of pydantic
guard25 = Guard.for_pydantic(SafeProductDescription).use(
    ToxicLanguage, on_fail="exception"
)
res25 = guard25(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Generate a product description for eco-friendly water bottles as JSON."}],
)
print(res25.validated_output)

# ── 26. Structured output — batch processing ─────────────────────────────────
class CustomerFeedback(BaseModel):
    customer_id: str
    rating: int
    category: Literal["product", "service", "shipping", "other"]
    summary: str

guard26 = Guard.for_pydantic(CustomerFeedback)

raw_feedbacks = [
    "Customer 101: The shipping took forever. 2/5",
    "Customer 102: Amazing product quality! 5/5",
    "Customer 103: Support was unhelpful. 1/5",
]

def batch_parse_feedback(feedbacks: list[str]) -> list[CustomerFeedback]:
    results = []
    for fb in feedbacks:
        res = guard26(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"Parse this feedback as JSON with customer_id, rating (int), category, summary:\n{fb}",
            }],
        )
        results.append(res.validated_output)
    return results

parsed = batch_parse_feedback(raw_feedbacks)
for fb in parsed:
    print(f"{fb.customer_id}: {fb.rating}/5 [{fb.category}]")

# ── 27. Async structured output ───────────────────────────────────────────────
import asyncio
from guardrails import AsyncGuard

class NewsArticle(BaseModel):
    headline: str
    summary: str
    category: Literal["politics", "tech", "sports", "business", "entertainment"]
    sentiment: Literal["positive", "negative", "neutral"]

async def async_parse_news(raw_text: str) -> NewsArticle:
    aguard = AsyncGuard.for_pydantic(NewsArticle)
    res = await aguard(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Parse this news into JSON:\n\n{raw_text}"}],
    )
    return res.validated_output

asyncio.run(async_parse_news("Apple unveils new M4 chip, stocks rise 3%."))

# ── 28. Structured output from pre-existing LLM response ─────────────────────
class WeatherForecast(BaseModel):
    city: str
    date: str
    high_temp_c: float
    low_temp_c: float
    condition: Literal["sunny", "cloudy", "rainy", "snowy", "windy"]
    humidity_percent: int

raw_response = '{"city": "London", "date": "2024-01-15", "high_temp_c": 8.0, "low_temp_c": 3.0, "condition": "cloudy", "humidity_percent": 75}'

guard28 = Guard.for_pydantic(WeatherForecast)
res28 = guard28.parse(llm_output=raw_response)
weather: WeatherForecast = res28.validated_output
print(f"{weather.city}: {weather.high_temp_c}°C, {weather.condition}")

# ── 29. Streaming + Pydantic structured output ───────────────────────────────
# Guardrails collects the stream and validates the full JSON at the end
class TranslationResult(BaseModel):
    source_language: str
    target_language: str
    original_text: str
    translated_text: str
    confidence: float

guard29 = Guard.for_pydantic(TranslationResult)
res29 = guard29(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Translate 'Hello World' to Spanish and return JSON with source_language, target_language, original_text, translated_text, confidence."}],
)
print(res29.validated_output)

# ── 30. Model with custom serialization ───────────────────────────────────────
from pydantic import model_serializer

class APIResponse(BaseModel):
    success: bool
    data: dict
    error_message: Optional[str] = None
    request_id: str

guard30 = Guard.for_pydantic(APIResponse)
res30 = guard30(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Generate a mock successful API response JSON with success, data, error_message (null), request_id."}],
)
api_resp: APIResponse = res30.validated_output
print(api_resp.model_dump_json(indent=2))

# ── 31. Chain pydantic guard with safety validators ───────────────────────────
from guardrails.hub import DetectPII

class UserGeneratedContent(BaseModel):
    content: str
    author: str
    timestamp: str

ugc_guard = Guard.for_pydantic(UserGeneratedContent).use_many(
    ToxicLanguage(threshold=0.5, on_fail="exception"),
    DetectPII(on_fail="exception"),
)
res31 = ugc_guard(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Generate sample user content as JSON with content, author, timestamp."}],
    metadata={"pii_entities": ["EMAIL_ADDRESS", "PHONE_NUMBER"]},
)
print(res31.validated_output)
