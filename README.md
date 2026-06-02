# AI Guard Rails — Research Repository

A hands-on research project evaluating four major libraries for securing LLM applications. Each module covers a different layer of the AI safety stack — from input scanning and output validation, to conversation-level guardrails and automated red-teaming.

---

## Why This Exists

Production LLM systems need multiple overlapping defenses. This project maps out the landscape:

| Layer | Library | What it guards |
|-------|---------|---------------|
| Input/Output Scanning | `llm-guard` | PII, prompt injection, toxicity at the raw text level |
| Output Validation | `guardrails-ai` | Format, schema, content, and factuality of LLM responses |
| Conversation Control | `nemoguardrails` | Topic restrictions, jailbreaks, and policy enforcement at the dialogue level |
| Adversarial Testing | `PyRIT` | Automated red-teaming — finds what the defenders miss |

---

## Repository Structure

```
GUARD_RAILS/
├── llm_guard_research/          ← llm-guard: input/output scanners
├── guard_rails_ai_research/     ← guardrails-ai: validation framework (320+ examples)
├── nemo_guard_rails_research/   ← NVIDIA NeMo Guardrails: Colang-based conversation rails
├── pyrit_library_research/      ← Microsoft PyRIT: AI red-teaming toolkit
├── docs/                        ← Architecture diagrams, Excel evaluation sheets
├── requirements.txt             ← Unified dependency list for the full project
└── .env                         ← API keys (not committed)
```

---

## Module 1 — llm-guard

**Directory:** `llm_guard_research/`

[llm-guard](https://llm-guard.com) is a lightweight scanner that intercepts raw prompts and LLM responses to detect and block harmful content before it reaches or leaves the model.

```
llm_guard_research/
├── notebooks/
│   ├── prompt_injection_check.ipynb       ← Detecting injected instructions in user input
│   ├── sensitive_data_pii.ipynb           ← PII detection and redaction (SSN, email, phone...)
│   └── toxic_unsafe_content_check.ipynb   ← Toxicity and unsafe content scanning
├── prompt_injection/                      ← Test cases and raw results
├── PII/                                   ← PII scanner experiments
├── toxic_unsafe_content/                  ← Toxicity scanner experiments
└── create_excel.py                        ← Generates comparison Excel reports
```

**What's covered:**

| Scanner | Detects |
|---------|---------|
| Prompt Injection | Hidden instructions, role-play overrides, instruction injection |
| Sensitive Data / PII | SSN, email, phone, credit card, names, addresses |
| Toxic / Unsafe Content | Hate speech, violence, harassment, self-harm |

---

## Module 2 — guardrails-ai

**Directory:** `guard_rails_ai_research/`

[guardrails-ai](https://github.com/guardrails-ai/guardrails) is a Python framework that wraps LLM API calls with input/output validators. It can auto-fix, reask the LLM, filter, or raise exceptions when validation fails.

**320+ practical examples across 10 notebooks and matching Python scripts.**

```
guard_rails_ai_research/
├── notebooks/
│   ├── 01_core_guards_fundamentals.ipynb      ← Guard API, OnFailActions, history
│   ├── 02_content_safety_validators.ipynb     ← ToxicLanguage, DetectPII, Jailbreak, NSFW
│   ├── 03_format_structure_validators.ipynb   ← ValidJSON, ValidSQL, RegexMatch, ValidLength
│   ├── 04_factuality_hallucination.ipynb      ← ProvenanceLLM, GroundedAI, RAG evaluation
│   ├── 05_text_quality_relevance.ipynb        ← ReadingLevel, GibberishText, Saliency
│   ├── 06_business_logic_validators.ipynb     ← CompetitorCheck, BanList, FinancialTone
│   ├── 07_structured_output_pydantic.ipynb    ← Guard.for_pydantic(), nested models, enums
│   ├── 08_custom_validators.ipynb             ← @register_validator, async, ErrorSpan
│   ├── 09_pipeline_chaining.ipynb             ← .use(), .use_many(), mixed OnFailActions
│   └── 10_llm_integration_async.ipynb         ← AsyncGuard, streaming, FastAPI
├── 01_guard_basics.py  →  10_production_deployment.py   ← Standalone Python equivalents
├── install_hubs.sh                            ← Installs all 40+ Hub validators
└── requirements.txt
```

**Notebook quick-reference:**

| # | Topic | Key concepts |
|---|-------|-------------|
| 01 | Core Guards | `Guard()`, `OnFailAction`, `ValidationOutcome`, `guard.history` |
| 02 | Content Safety | ToxicLanguage, DetectPII, DetectJailbreak, PromptInjection |
| 03 | Format & Structure | ValidJSON, ValidSQL, ValidHTML, RegexMatch, ValidChoices |
| 04 | Factuality | ProvenanceLLM, ProvenanceEmbeddings, BespokeMinicheck, RAG evaluation |
| 05 | Text Quality | ReadingLevel, GibberishText, RedundantSentences, RelevancyEvaluator |
| 06 | Business Logic | CompetitorCheck, RestrictToTopic, FinancialTone, BanList |
| 07 | Structured Output | `Guard.for_pydantic()`, nested models, cross-field validators |
| 08 | Custom Validators | `@register_validator`, `PassResult`/`FailResult`, async validators |
| 09 | Pipelines | Chained validators, short-circuit, conditional pipelines, batch processing |
| 10 | LLM Integration | AsyncGuard, streaming, OpenAI + Anthropic, FastAPI endpoint |

---

## Module 3 — NeMo Guardrails

**Directory:** `nemo_guard_rails_research/`

[NVIDIA NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails) enforces conversation-level policies using **Colang** — a DSL that defines intents, bot responses, and flows. Rails fire before (input) or after (output) the main LLM call.

```
nemo_guard_rails_research/
├── notebooks/
│   └── nemo_guardrails_research.ipynb     ← Full walkthrough (6 sections)
├── configs/
│   ├── topical_rails/                     ← Restrict to allowed topics, block off-topic/jailbreak
│   ├── jailbreak_rails/                   ← LLM-as-judge self-check (generalizes to novel attacks)
│   ├── output_moderation/                 ← PII in input + financial advice blocking
│   └── custom_actions_rails/              ← Python functions registered as guardrail actions
└── run_research.py                        ← CLI runner (no Jupyter needed)
```

**Four mechanisms explored:**

| Approach | How it works | Trade-off |
|----------|-------------|-----------|
| Topical Rails | Colang intent matching against example utterances | Fast, but brittle — only catches known patterns |
| Self-Check Rails | Second LLM call evaluates input/output against policy | Generalizes to novel attacks; adds ~1–2s latency |
| Output Moderation | Colang output flows for PII and advice gating | Low latency; only works for structured, predictable violations |
| Custom Actions | Python functions called inline via `execute` | Fully flexible — plug in regex, ML classifiers, or external APIs |

---

## Module 4 — PyRIT (AI Red-Teaming)

**Directory:** `pyrit_library_research/`

[PyRIT](https://github.com/microsoft/PyRIT) (Python Risk Identification Toolkit) is Microsoft's open-source AI red-teaming framework. It **attacks** LLM systems automatically to find vulnerabilities the defensive libraries miss.

```
pyrit_library_research/
├── notebooks/
│   ├── 01_pyrit_intro_and_setup_1.ipynb   ← Architecture, components, first attack
│   ├── 02_single_turn_attacks.ipynb       ← Single-prompt adversarial testing
│   ├── 03_multi_turn_attacks.ipynb        ← Crescendo orchestrator (multi-step attacks)
│   └── 04_full_analysis.ipynb             ← Results analysis and visualization
├── targets/
│   └── fastapi_agent_target.py            ← Custom FastAPI target wrapping a guarded LLM
├── datasets/
│   └── test_prompts.json                  ← 102-prompt adversarial test set
├── results/                               ← Attack run outputs
├── single_turn_results.png                ← Single-turn attack results chart
├── multi_turn_results.png                 ← Crescendo multi-turn attack results chart
├── dataset_composition.png                ← Test dataset breakdown by harm category
└── requirements.txt
```

**Why PyRIT belongs here:**

The other three libraries are defenders. PyRIT is the attacker — it probes those defenses to surface gaps. Automated red-teaming that would take a human team weeks runs in hours.

| Capability | Detail |
|-----------|--------|
| Single-turn attacks | Sends adversarial prompts directly; scores each response |
| Multi-turn (Crescendo) | Gradually escalates a conversation to extract unsafe content |
| Custom targets | Wrap any guarded API as a PyRIT target (see `fastapi_agent_target.py`) |
| Scoring | Automated, reproducible harm scores across 20+ attack categories |
| Dataset | 102 curated prompts across jailbreaks, PII extraction, unsafe content |

---

## Documentation

**Directory:** `docs/`

```
docs/
├── images/
│   ├── responsible_ai_libraries.excalidraw.png   ← Library comparison diagram
│   ├── responsible_ai_attacks.excalidraw.png     ← Attack surface diagram
│   ├── data_understanding.excalidraw.png         ← Data flow overview
│   └── tool_flow_masking.excalidraw.png          ← Masking / redaction flow
└── excel_files/
    ├── guard_rails_ai_checks.xlsx                ← guardrails-ai evaluation matrix
    ├── nemo_guard_rails_checks.xlsx              ← NeMo evaluation matrix
    └── responsible_ai_checks.xlsx                ← Cross-library comparison
```

---

## Setup

### 1. Clone and activate the virtual environment

```bash
cd GUARD_RAILS
python -m venv .venv
source .venv/bin/activate
```

### 2. Install all dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API keys

Create a `.env` file in the root:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GUARDRAILS_API_KEY=...
```

### 4. Install guardrails-ai Hub validators (Module 2 only)

```bash
bash guard_rails_ai_research/install_hubs.sh
```

### 5. Launch Jupyter

```bash
jupyter notebook
```

---

## Reading Order

If you're new to this project, work through the modules in this order:

1. **llm_guard_research** — Start here for a low-friction introduction to input/output scanning. The three notebooks are self-contained and short.
2. **guard_rails_ai_research** — The most comprehensive module. Start with notebook `01` (core concepts) and `08` (custom validators), then pick topics as needed.
3. **nemo_guard_rails_research** — Read after guardrails-ai to see how conversation-level rails differ from per-call validation.
4. **pyrit_library_research** — Finish here to see the full picture: after understanding how each defense works, run attacks against them to find the gaps.

---

## Key Takeaways

- No single library covers every threat. A production system needs layered defenses.
- `llm-guard` is the fastest to integrate for basic input scanning.
- `guardrails-ai` offers the most flexibility for output validation and structured output enforcement.
- NeMo Guardrails is the right tool when you need policy enforcement at the conversation level, not just per-call.
- PyRIT should be a recurring part of the development cycle — not a one-time audit.
