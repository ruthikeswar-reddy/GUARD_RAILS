# Guardrails AI — Practical Examples

**320+ practical, LLM-integrated code examples** covering every major feature of the [guardrails-ai](https://github.com/guardrails-ai/guardrails) library, organized into 10 Jupyter notebooks.

All examples use real LLM API calls (OpenAI / Anthropic). Each notebook is self-contained and can be run independently.

---

## What is guardrails-ai?

Guardrails AI is a Python framework that adds **input/output validation** to LLM applications. It lets you:

- Detect and block toxic, harmful, or off-brand content
- Enforce structured output schemas (Pydantic models)
- Validate format, length, language, and factual grounding
- Automatically **REASK** the LLM when output fails validation
- Chain multiple validators into composable pipelines

```python
from guardrails import Guard, OnFailAction
from guardrails.hub import ToxicLanguage, ValidLength

guard = (
    Guard()
    .use(ToxicLanguage(on_fail=OnFailAction.EXCEPTION))
    .use(ValidLength(min=20, max=500, on_fail=OnFailAction.REASK))
)

outcome = guard(
    openai_client.chat.completions.create,
    prompt="Describe quantum computing.",
    model="gpt-4o-mini",
    num_reasks=2
)
print(outcome.validated_output)
```

---

## Setup

### 1. Activate the virtual environment

```bash
cd GUARD_RAILS
source .venv/bin/activate
```

### 2. Install Python dependencies

```bash
pip install -r guard_rails_ai_research/requirements.txt
```

| Package | Purpose |
|---------|---------|
| `guardrails-ai>=0.6.0` | Core framework |
| `openai>=1.0.0` | OpenAI LLM integration |
| `anthropic>=0.20.0` | Anthropic Claude integration |
| `python-dotenv` | Load `.env` API keys |
| `pydantic>=2.0.0` | Structured output schemas |
| `langdetect` | Language detection (Notebook 08) |
| `textblob` | Text analysis utilities |
| `aiohttp` | Async HTTP for custom validators |
| `litellm` | Universal LLM adapter (Notebook 10) |

### 3. Install Hub validators

```bash
bash guard_rails_ai_research/install_hubs.sh
```

This installs all 40+ validators used across the notebooks from [Guardrails Hub](https://hub.guardrailsai.com).

### 4. Configure API keys

Ensure `.env` (at `GUARD_RAILS/.env`) contains:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GUARDRAILS_API_KEY=...
```

Run once to configure guardrails CLI:

```bash
guardrails configure
```

---

## Notebooks

### 01 — Core Guards Fundamentals
**File:** `notebooks/01_core_guards_fundamentals.ipynb` | **32 examples**

The foundation. Everything else in the library builds on these concepts.

| Concept | What it does |
|---------|-------------|
| `Guard()` | Creates a guard with no validators — a starting point |
| `OnFailAction.EXCEPTION` | Raises `ValidationError` immediately on failure |
| `OnFailAction.REASK` | Re-prompts the LLM to fix the failing output |
| `OnFailAction.FIX` | Auto-corrects the value using the validator's `fix_value` |
| `OnFailAction.FILTER` | Removes the failing field from the output dict |
| `OnFailAction.REFRAIN` | Suppresses the entire response → returns `None` |
| `OnFailAction.NOOP` | Records failure but passes value through unchanged |
| `OnFailAction.FIX_REASK` | Tries FIX first; reasks LLM only if fix is insufficient |
| `OnFailAction.CUSTOM` | Calls a user-supplied function on failure |
| `ValidationOutcome` | Return object with `.validated_output`, `.validation_passed`, `.error` |
| `guard.history` | Full audit trail of every LLM call and validation attempt |
| `num_reasks` | Controls how many retry iterations are allowed |
| `guard.to_dict()` / `Guard.from_dict()` | Serialize and restore a guard |

**Key pattern:**
```python
guard = Guard().use(ValidLength(min=50, max=500, on_fail=OnFailAction.REASK))
outcome = guard(openai_client.chat.completions.create, prompt="...", model="gpt-4o-mini", num_reasks=2)
print(outcome.validated_output)
```

---

### 02 — Content Safety Validators
**File:** `notebooks/02_content_safety_validators.ipynb` | **33 examples**

Protect users and brand from harmful, sensitive, or unsafe content.

| Validator | Detects | Install |
|-----------|---------|---------|
| `ToxicLanguage` | Hate speech, insults, harassment | `hub://guardrails/toxic_language` |
| `ProfanityFree` | Explicit profanity and offensive words | `hub://guardrails/profanity_free` |
| `DetectJailbreak` | Jailbreak attempts ("ignore instructions", DAN) | `hub://guardrails/detect_jailbreak` |
| `PromptInjection` | Hidden instructions injected in user content | `hub://guardrails/prompt_injection` |
| `DetectPII` | SSN, email, phone, credit card, address | `hub://guardrails/detect_pii` |
| `NSFWText` | Sexual or violent content | `hub://guardrails/nsfw_text` |
| `SecretsPresent` | AWS keys, API tokens, credentials in code | `hub://guardrails/secrets_present` |
| `SensitiveTopic` | Politics, medical advice, religion | `hub://guardrails/sensitive_topic` |
| `MentionsDrugs` | Drug references (recreational vs clinical) | `hub://guardrails/mentions_drugs` |

**Covers:**
- Threshold tuning (e.g. `ToxicLanguage(threshold=0.7)`)
- Auto-redaction via `OnFailAction.FIX`
- Multi-paragraph injection scenarios (travel text, banking, HR)
- Combined ToxicLanguage + ProfanityFree safety chain

---

### 03 — Format & Structure Validators
**File:** `notebooks/03_format_structure_validators.ipynb` | **33 examples**

Ensure LLM outputs are correctly formatted, syntactically valid, and within expected ranges.

| Validator | Validates | Install |
|-----------|-----------|---------|
| `ValidJson` | JSON parseable | `hub://guardrails/valid_json` |
| `ValidPython` | Python syntax | `hub://guardrails/valid_python` |
| `ValidSql` | SQL syntax | `hub://guardrails/valid_sql` |
| `ValidHtml` | HTML structure | `hub://guardrails/valid_html` |
| `ValidUrl` | URL format | `hub://guardrails/valid_url` |
| `ValidAddress` | Real postal address | `hub://guardrails/valid_address` |
| `RegexMatch` | Custom regex pattern | `hub://guardrails/regex_match` |
| `ValidLength` | Min/max character count | `hub://guardrails/valid_length` |
| `ValidRange` | Numeric min/max | `hub://guardrails/valid_range` |
| `ContainsString` | Required substring present | `hub://guardrails/contains_string` |
| `EndsWith` | Required ending character/string | `hub://guardrails/ends_with` |
| `OneLine` | Exactly one line (no newlines) | `hub://guardrails/one_line` |
| `ValidChoices` | Value is in an allowed set | `hub://guardrails/valid_choices` |

**Covers:**
- Pass + fail cases for every validator
- REASK loop for `ValidChoices` until LLM picks a valid option
- FIX for `ValidJson` (attempts JSON repair)

---

### 04 — Factuality & Hallucination Detection
**File:** `notebooks/04_factuality_hallucination.ipynb` | **32 examples**

Prevent LLMs from generating claims that contradict or are unsupported by source documents.

| Validator | Method | Install |
|-----------|--------|---------|
| `ProvenanceLlm` | Uses an LLM to judge if claim is grounded in sources | `hub://guardrails/provenance_llm` |
| `ProvenanceEmbeddings` | Cosine similarity between claim and source embeddings | `hub://guardrails/provenance_embeddings` |
| `GroundedAIHallucination` | Grounded AI model detects invented facts | `hub://guardrails/grounded_ai_hallucination` |
| `BespokeMinicheck` | Lightweight fact-checking model | `hub://guardrails/bespoke_minicheck` |
| `LlmRagEvaluator` | Evaluates RAG answer against retrieved chunks | `hub://guardrails/llm_rag_evaluator` |
| `WikiProvenance` | Verifies claim against Wikipedia | `hub://guardrails/wiki_provenance` |

**Covers:**
- `metadata={'sources': [...]}` pattern for all provenance validators
- Threshold sweeps (0.3 / 0.5 / 0.7)
- ProvenanceLLM vs ProvenanceEmbeddings — side-by-side comparison
- Medical claim and financial earnings hallucination detection
- REASK loop until grounded answer is produced
- Dual-layer guard: ProvenanceLLM + BespokeMiniCheck

---

### 05 — Text Quality & Relevance
**File:** `notebooks/05_text_quality_relevance.ipynb` | **32 examples**

Enforce readability, coherence, and topical relevance of LLM-generated text.

| Validator | What it checks | Install |
|-----------|----------------|---------|
| `ReadingLevel` | Flesch-Kincaid grade level (e.g. grade 5, college) | `hub://guardrails/reading_level` |
| `ReadingTime` | Max reading time in minutes at given WPM | `hub://guardrails/reading_time` |
| `GibberishText` | Random characters, keyboard smash, token artifacts | `hub://guardrails/gibberish_text` |
| `RedundantSentences` | Same idea stated multiple times | `hub://guardrails/redundant_sentences` |
| `SaliencyCheck` | Off-topic sentences in summary | `hub://guardrails/saliency_check` |
| `ExtractedSummarySentencesMatch` | Extractive summary uses only source sentences | `hub://guardrails/extracted_summary_sentences_match` |
| `SimilarToDocument` | Semantic similarity to a reference document | `hub://guardrails/similar_to_document` |
| `RelevancyEvaluator` | Response actually addresses the question | `hub://guardrails/relevancy_evaluator` |

**Covers:**
- Children's app (grade 3) vs developer docs (college level) reading level
- FAQ redundancy detection
- Brand voice enforcement with `SimilarToDocument`
- Full 4-validator quality pipeline: GibberishText + ReadingLevel + RedundantSentences + ReadingTime

---

### 06 — Business Logic Validators
**File:** `notebooks/06_business_logic_validators.ipynb` | **32 examples**

Enforce company-specific rules: brand safety, topic restrictions, financial compliance, tone.

| Validator | Enforces | Install |
|-----------|----------|---------|
| `CompetitorCheck` | No competitor names in response | `hub://guardrails/competitor_check` |
| `RestrictToTopic` | Response stays within allowed topics | `hub://guardrails/restrict_to_topic` |
| `QuotesPrice` | No unsolicited price quotes | `hub://guardrails/quotes_price` |
| `FinancialTone` | No speculative investment advice | `hub://guardrails/financial_tone` |
| `PolitenessCheck` | Professional, courteous tone | `hub://guardrails/politeness_check` |
| `BanList` | Custom forbidden word/phrase list | `hub://guardrails/ban_list` |
| `ValidChoices` | Output is one of allowed values | `hub://guardrails/valid_choices` |
| `UnusualPrompt` | Statistically anomalous inputs | `hub://guardrails/unusual_prompt` |
| `ResponsivenessCheck` | Response actually answers the question | `hub://guardrails/responsiveness_check` |

**Covers:**
- CompetitorCheck with FIX (auto-redacts competitor name)
- FinancialTone hedging detection
- BanList for internal codename leak prevention
- End-to-end: financial chatbot pipeline + customer support gate

---

### 07 — Structured Output with Pydantic
**File:** `notebooks/07_structured_output_pydantic.ipynb` | **32 examples**

Force LLMs to return typed, validated data structures instead of free-form text.

**Covers:**

| Topic | Examples |
|-------|----------|
| `Guard.for_pydantic(output_class=MyModel)` | Wrap any Pydantic model in a Guard |
| Nested models | `Address` inside `User` |
| List fields | `items: List[LineItem]` |
| Optional fields | `bio: Optional[str] = None` |
| Enum / Literal | `status: Literal['open', 'closed']` |
| `@field_validator` | Pydantic v2 field-level validation |
| Annotated constraints | `age: Annotated[int, Field(ge=0, le=120)]` |
| Cross-field validator | `@model_validator` (start_date < end_date) |
| Guard validators on fields | Attach `ToxicLanguage` to a `feedback: str` field |
| LLM structured output | Full pipeline: prompt → validated Pydantic object |
| REASK with partial output | LLM returns 3/5 fields, guard reasks for the rest |
| `response_format={'type': 'json_object'}` | OpenAI structured outputs mode |
| `guard.json_schema` | Inspect the generated JSON schema |

```python
class BookRecommendation(BaseModel):
    title: str
    author: str
    rating: float

guard = Guard.for_pydantic(output_class=BookRecommendation)
outcome = guard(openai_client.chat.completions.create, prompt="Recommend a sci-fi book.", model="gpt-4o-mini")
print(outcome.validated_output)  # BookRecommendation(title=..., author=..., rating=...)
```

---

### 08 — Custom Validators
**File:** `notebooks/08_custom_validators.ipynb` | **32 examples**

Build your own validators for domain-specific rules not covered by the Hub.

**Two approaches:**

```python
# Class-based (recommended)
@register_validator(name='no-numbers', data_type='string')
class NoNumbers(Validator):
    def validate(self, value: str, metadata: dict) -> ValidationResult:
        if any(c.isdigit() for c in value):
            return FailResult(error_message='Must not contain digits')
        return PassResult()
```

**Covers:**

| Pattern | Description |
|---------|-------------|
| `PassResult` / `FailResult` | Signal pass or fail with optional `fix_value` |
| `FailResult(fix_value=...)` | Provide an auto-corrected value for `OnFailAction.FIX` |
| Parameterized validators | `__init__(self, keyword: str, **kwargs)` |
| Async validators | `async def validate(...)` + `AsyncGuard` |
| Metadata access | Read `metadata['source_doc']` inside `validate()` |
| External API call | HTTP request to moderation service inside validator |
| LRU caching | Cache expensive validation calls with `@lru_cache` |
| Language detection | English-only enforcement via `langdetect` |
| Custom PII | Domain-specific ID patterns (employee IDs: `EMP-XXXXX`) |
| `ErrorSpan` | Mark partial failure regions within a string |
| Stateful validator | Track call count / rate limiting per instance |
| Unit testing | Call `validator.validate(value, {})` directly |
| Hub-compatible structure | `pyproject.toml` layout for publishing to Hub |

---

### 09 — Pipeline Chaining & Multi-Validator Guards
**File:** `notebooks/09_pipeline_chaining.ipynb` | **32 examples**

Combine multiple validators into composable, ordered pipelines.

**Core API:**

```python
# Method 1: Chained .use()
guard = Guard().use(ValidatorA(...)).use(ValidatorB(...)).use(ValidatorC(...))

# Method 2: .use_many() with a list
guard = Guard().use_many(ValidatorA(...), ValidatorB(...), ValidatorC(...))
```

**Covers:**

| Topic | Key insight |
|-------|-------------|
| Execution order | First validator in chain runs first |
| Short-circuit with EXCEPTION | If validator 1 raises, validator 2 never runs |
| NOOP collects all failures | All validators run; errors aggregated for inspection |
| Mixed OnFailActions | Validator A uses FIX, Validator B uses EXCEPTION |
| Input vs output guards | Separate guards for user prompt and LLM response |
| Dynamic pipeline from config | Build validator list from a config dict at runtime |
| Conditional pipeline | Choose validators based on user role |
| Async pipeline | `AsyncGuard().use_many(...)` with async LLM |
| Pipeline benchmarking | `time.perf_counter()` around validation loop |
| Batch processing | Same guard validates list of texts |
| Healthcare pipeline | ToxicLanguage + ValidLength + ContainsString('consult') |
| Financial chatbot pipeline | ToxicLanguage + ProfanityFree + ValidLength |

---

### 10 — LLM Integration & Async
**File:** `notebooks/10_llm_integration_async.ipynb` | **32 examples**

Production patterns for integrating guards with real LLM providers.

**Covers:**

| Topic | What it shows |
|-------|---------------|
| OpenAI ChatCompletion | `guard(oai.chat.completions.create, prompt=..., model=...)` |
| Messages API format | system + user message dict format |
| Anthropic Claude | Call Anthropic, then `guard.validate(response)` |
| `AsyncGuard` | `AsyncGuard()` for async/await contexts |
| `guard.async_validate()` | Await a single validation |
| `asyncio.gather()` | Parallel validation of multiple outputs |
| Streaming | `guard(..., stream=True)` → iterate chunks |
| OpenAI function calling | Validate function call arguments as Pydantic model |
| Structured outputs mode | `response_format={'type': 'json_object'}` + guard |
| Error recovery | Catch `ValidationError`, retry with fallback prompt |
| Custom LLM callable | Wrap Ollama / vLLM / any model in guardrails |
| Anthropic streaming | Collect streamed text, then validate the full response |
| Exponential backoff | Retry on rate limit with `2 ** attempt` wait |
| Multi-turn conversation | Validate both user input and assistant response each turn |
| FastAPI async endpoint | `async def endpoint()` with `AsyncGuard` |
| Token budget | `guard.history[0].tokens_consumed` |
| Batch async processing | `asyncio.gather()` for N texts in parallel |
| Timeout handling | `asyncio.wait_for(guard(...), timeout=30)` |
| Provider switching | Same guard → OpenAI, then Anthropic |
| litellm adapter | `litellm.completion()` as universal LLM interface |
| Input guard + Output guard | Two separate guards in a single request pipeline |
| Metrics collection | Latency, token counts, iteration count from `guard.history` |
| Guard-per-request vs reuse | Stateless (new per call) vs shared instance trade-offs |
| Logging integration | `logging.info/warning` based on `outcome.validation_passed` |
| aiohttp external validator | Async HTTP call inside a custom async validator |

---

## OnFailAction Reference

| Action | What happens on validation failure |
|--------|------------------------------------|
| `EXCEPTION` | Raises `ValidationError` immediately — stops the pipeline |
| `REASK` | Re-prompts the LLM with the failing output and a correction request |
| `FIX` | Uses `FailResult.fix_value` to auto-correct the output |
| `FIX_REASK` | Tries FIX first; only reasks LLM if fix is not sufficient |
| `FILTER` | Removes the failing field from the output dict |
| `REFRAIN` | Suppresses the entire response — returns `None` |
| `NOOP` | Records the failure in history but passes value through unchanged |
| `CUSTOM` | Calls your own Python function with the value and fail results |

---

## Project Structure

```
guard_rails_ai_research/
├── notebooks/
│   ├── 01_core_guards_fundamentals.ipynb       # Guard API, OnFailActions, history
│   ├── 02_content_safety_validators.ipynb      # ToxicLanguage, DetectPII, Jailbreak...
│   ├── 03_format_structure_validators.ipynb    # ValidJSON, ValidSQL, RegexMatch...
│   ├── 04_factuality_hallucination.ipynb       # ProvenanceLLM, GroundedAI, RAG...
│   ├── 05_text_quality_relevance.ipynb         # ReadingLevel, GibberishText...
│   ├── 06_business_logic_validators.ipynb      # CompetitorCheck, BanList...
│   ├── 07_structured_output_pydantic.ipynb     # Guard.for_pydantic(), schemas...
│   ├── 08_custom_validators.ipynb              # @register_validator, async...
│   ├── 09_pipeline_chaining.ipynb              # .use(), .use_many(), pipelines...
│   └── 10_llm_integration_async.ipynb          # AsyncGuard, streaming, FastAPI...
├── requirements.txt                            # Python dependencies
├── install_hubs.sh                             # guardrails hub install commands
└── README.md                                   # This file
```

---

## Quick Start

```bash
# 1. Activate environment
cd GUARD_RAILS && source .venv/bin/activate

# 2. Install dependencies
pip install -r guard_rails_ai_research/requirements.txt

# 3. Install Hub validators
bash guard_rails_ai_research/install_hubs.sh

# 4. Launch Jupyter
jupyter notebook guard_rails_ai_research/notebooks/

# 5. Open any notebook and run all cells
```

**Recommended order:** 01 → 08 → 02 → 03 → 04 → 05 → 06 → 07 → 09 → 10

Start with 01 (core concepts) and 08 (custom validators) before the topic-specific notebooks.

---

## Environment Variables

```env
# GUARD_RAILS/.env
OPENAI_API_KEY=sk-...             # Required for all OpenAI examples
ANTHROPIC_API_KEY=sk-ant-...      # Required for notebooks 04, 10
GUARDRAILS_API_KEY=...            # Required for some Hub validators
```

---

## Key Concepts Summary

```
Guard             — The main object that wraps validators and LLM calls
Validator         — A single validation rule (from Hub or custom)
ValidationOutcome — Result object returned by guard.validate() or guard(llm_api, ...)
OnFailAction      — What to do when a validator fails (8 options)
PassResult        — Returned by a validator to signal success
FailResult        — Returned by a validator to signal failure (with optional fix_value)
guard.history     — Full audit trail: raw output, validated output, token counts
AsyncGuard        — Async version of Guard for use with async/await and FastAPI
```

---

## References

- [Guardrails AI GitHub](https://github.com/guardrails-ai/guardrails)
- [Guardrails Hub](https://hub.guardrailsai.com) — Browse all 70+ validators
- [Documentation](https://www.guardrailsai.com/docs)
