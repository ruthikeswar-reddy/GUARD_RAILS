"""
TOPIC 10: Production Deployment & Advanced Patterns — 30+ practical examples
Covers: Guardrails server, REST API, async guards, streaming, LangChain,
        LlamaIndex, OpenAI compatibility, batching, telemetry, config

Install:
  pip install guardrails-ai flask gunicorn aiohttp langchain
"""

import asyncio
import json
import logging
import os
import time
from typing import Any, Optional

import openai
from guardrails import AsyncGuard, Guard
from guardrails.hub import (
    CompetitorCheck,
    DetectPII,
    ToxicLanguage,
    ValidJson,
    ValidPython,
)

# ──────────────────────────────────────────────────────────────────────────────
# GUARDRAILS SERVER CONFIG
# ──────────────────────────────────────────────────────────────────────────────

# ── 1. config.py for guardrails server ───────────────────────────────────────
# Run with: guardrails start --config config.py --port 8000
CONFIG_PY_CONTENT = """
from guardrails import Guard
from guardrails.hub import ToxicLanguage, DetectPII, ValidJson

guards = [
    Guard(name="toxicity")
        .use(ToxicLanguage, threshold=0.5, on_fail="exception"),

    Guard(name="pii-filter")
        .use(DetectPII, on_fail="fix"),

    Guard(name="json-validator")
        .use(ValidJson, on_fail="exception"),
]
"""

# ── 2. Call the guardrails REST API (POST /guards/{name}/validate) ────────────
import requests

def call_guard_api(text: str, guard_name: str = "toxicity", base_url: str = "http://localhost:8000") -> dict:
    resp = requests.post(
        f"{base_url}/guards/{guard_name}/validate",
        json={"llmOutput": text},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()

# ── 3. Call guard API with LLM pass-through ────────────────────────────────
def api_llm_validate(prompt: str, guard_name: str = "toxicity") -> str:
    resp = requests.post(
        f"http://localhost:8000/guards/{guard_name}/openai/v1/chat/completions",
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    return resp.json()["choices"][0]["message"]["content"]

# ──────────────────────────────────────────────────────────────────────────────
# ASYNC GUARDS
# ──────────────────────────────────────────────────────────────────────────────

# ── 4. Basic async guard ─────────────────────────────────────────────────────
async def async_example():
    aguard = AsyncGuard().use(ToxicLanguage, on_fail="exception")
    res = await aguard(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Tell me a fun science fact."}],
    )
    return res.validated_output

asyncio.run(async_example())

# ── 5. Concurrent async guards ────────────────────────────────────────────────
async def parallel_validation(texts: list[str]) -> list[str]:
    aguard = AsyncGuard().use(ToxicLanguage, on_fail="filter")
    tasks = [aguard.parse(text) for text in texts]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [
        r.validated_output if not isinstance(r, Exception) else None
        for r in results
    ]

asyncio.run(parallel_validation(["Great product!", "Terrible service.", "It was okay."]))

# ── 6. Async input + output guard pipeline ────────────────────────────────────
async def async_full_pipeline(user_msg: str) -> str:
    from guardrails.hub import PromptInjectionDetector, SecretsPresent

    input_guard = AsyncGuard().use(PromptInjectionDetector, on_fail="exception")
    await input_guard.parse(user_msg)

    output_guard = AsyncGuard().use_many(
        ToxicLanguage(threshold=0.5, on_fail="exception"),
        SecretsPresent(on_fail="exception"),
    )
    res = await output_guard(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_msg}],
    )
    return res.validated_output

# ──────────────────────────────────────────────────────────────────────────────
# STREAMING
# ──────────────────────────────────────────────────────────────────────────────

# ── 7. Streaming guard — validate after stream completes ─────────────────────
def streaming_with_guard(prompt: str) -> str:
    buffer = ""
    for chunk in openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    ):
        delta = chunk.choices[0].delta.content or ""
        print(delta, end="", flush=True)
        buffer += delta
    print()

    guard = Guard().use(ToxicLanguage, on_fail="exception")
    return guard.parse(buffer).validated_output

# ── 8. Streaming guard with interim checks ────────────────────────────────────
def streaming_with_chunked_checks(prompt: str, check_every: int = 100) -> str:
    guard = Guard().use(ToxicLanguage, on_fail="noop")
    buffer = ""
    for chunk in openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    ):
        buffer += chunk.choices[0].delta.content or ""
        if len(buffer) % check_every < 5:
            res = guard.parse(buffer)
            if not res.validation_passed:
                logging.warning("Interim check failed at %d chars", len(buffer))
    return buffer

# ──────────────────────────────────────────────────────────────────────────────
# LANGCHAIN INTEGRATION
# ──────────────────────────────────────────────────────────────────────────────

# ── 9. Guardrails as LangChain output parser ─────────────────────────────────
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

def guardrails_langchain_chain(question: str) -> str:
    guard = Guard().use(ToxicLanguage, on_fail="exception")

    llm = ChatOpenAI(model="gpt-4o-mini")
    prompt = ChatPromptTemplate.from_messages([("user", "{question}")])
    chain = prompt | llm | StrOutputParser()

    raw = chain.invoke({"question": question})
    return guard.parse(raw).validated_output

# ── 10. LangChain RAG with guardrails factuality check ────────────────────────
from langchain_core.runnables import RunnableLambda

def make_safe_rag_chain(retriever, embed_func):
    from guardrails.hub import ProvenanceLLM

    llm = ChatOpenAI(model="gpt-4o-mini")
    guard = Guard().use(ProvenanceLLM, validation_method="sentence", on_fail="filter")

    def guarded_generate(input_dict):
        docs = retriever.invoke(input_dict["question"])
        context = "\n".join(doc.page_content for doc in docs)
        raw = llm.invoke(f"Context:\n{context}\n\nQ: {input_dict['question']}").content
        return guard.parse(
            raw,
            metadata={"sources": [context], "embed_function": embed_func},
        ).validated_output

    return RunnableLambda(guarded_generate)

# ──────────────────────────────────────────────────────────────────────────────
# FLASK MIDDLEWARE
# ──────────────────────────────────────────────────────────────────────────────

# ── 11. Flask middleware for LLM output sanitization ─────────────────────────
from flask import Flask, request, jsonify, g

app = Flask(__name__)
OUTPUT_GUARD = Guard().use_many(
    ToxicLanguage(threshold=0.5, on_fail="filter"),
    DetectPII(on_fail="fix"),
)

@app.before_request
def validate_input():
    if request.json and "message" in request.json:
        from guardrails.hub import PromptInjectionDetector
        input_guard = Guard().use(PromptInjectionDetector, on_fail="exception")
        try:
            input_guard.parse(request.json["message"])
        except Exception as e:
            return jsonify({"error": f"Input blocked: {e}"}), 400

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "")
    raw = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_msg}],
    ).choices[0].message.content

    res = OUTPUT_GUARD.parse(
        raw,
        metadata={"pii_entities": ["EMAIL_ADDRESS", "PHONE_NUMBER"]},
    )
    return jsonify({"response": res.validated_output})

# ──────────────────────────────────────────────────────────────────────────────
# BATCHING
# ──────────────────────────────────────────────────────────────────────────────

# ── 12. Batch validation (sync) ───────────────────────────────────────────────
def batch_validate(texts: list[str], guard: Guard) -> list[dict]:
    results = []
    for text in texts:
        res = guard.parse(text)
        results.append({
            "text": text[:50],
            "passed": res.validation_passed,
            "output": res.validated_output,
        })
    return results

guard_tox = Guard().use(ToxicLanguage, on_fail="noop")
batch_results = batch_validate(
    ["Great!", "Terrible service!", "Could be better."],
    guard_tox,
)
for r in batch_results:
    print(r)

# ── 13. Async batch validation ────────────────────────────────────────────────
async def async_batch_validate(texts: list[str]) -> list[dict]:
    aguard = AsyncGuard().use(ToxicLanguage, on_fail="noop")
    tasks = [aguard.parse(t) for t in texts]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [
        {"text": t[:50], "passed": r.validation_passed if not isinstance(r, Exception) else None}
        for t, r in zip(texts, results)
    ]

# ──────────────────────────────────────────────────────────────────────────────
# TELEMETRY & LOGGING
# ──────────────────────────────────────────────────────────────────────────────

# ── 14. Validation metrics tracker ───────────────────────────────────────────
class GuardMetrics:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.latencies: list[float] = []

    def record(self, passed: bool, latency: float):
        self.total += 1
        self.passed += passed
        self.failed += not passed
        self.latencies.append(latency)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0

    @property
    def avg_latency(self) -> float:
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0

    def report(self) -> dict:
        return {
            "total": self.total, "passed": self.passed, "failed": self.failed,
            "pass_rate": f"{self.pass_rate:.1%}",
            "avg_latency_ms": f"{self.avg_latency * 1000:.1f}",
        }

metrics = GuardMetrics()
guard_m = Guard().use(ToxicLanguage, on_fail="noop")

for text in ["Good text.", "Bad text!", "Neutral text."]:
    t0 = time.time()
    res = guard_m.parse(text)
    metrics.record(res.validation_passed, time.time() - t0)

print(metrics.report())

# ──────────────────────────────────────────────────────────────────────────────
# CACHING GUARDS
# ──────────────────────────────────────────────────────────────────────────────

# ── 15. Cache guard instances (avoid re-instantiation) ───────────────────────
from functools import lru_cache

@lru_cache(maxsize=None)
def get_toxicity_guard() -> Guard:
    return Guard().use(ToxicLanguage, threshold=0.5, on_fail="exception")

@lru_cache(maxsize=None)
def get_pii_guard() -> Guard:
    return Guard().use(DetectPII, on_fail="fix")

# Reuse cached guard instances
result = get_toxicity_guard().parse("This is fine.")
print(result.validation_passed)

# ──────────────────────────────────────────────────────────────────────────────
# ENVIRONMENT-BASED GUARD CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────

# ── 16. Dev vs prod guard strictness ─────────────────────────────────────────
def build_guard(env: str = None) -> Guard:
    env = env or os.getenv("APP_ENV", "development")
    if env == "production":
        return Guard(name="prod-guard").use_many(
            ToxicLanguage(threshold=0.3, on_fail="exception"),
            DetectPII(on_fail="exception"),
            CompetitorCheck(competitors=["RivalCorp"], on_fail="exception"),
        )
    else:
        return Guard(name="dev-guard").use(
            ToxicLanguage(threshold=0.7, on_fail="noop")
        )

guard16 = build_guard()
print(guard16.name)

# ──────────────────────────────────────────────────────────────────────────────
# RETRY / CIRCUIT BREAKER PATTERN
# ──────────────────────────────────────────────────────────────────────────────

# ── 17. Circuit breaker for repeated validation failures ─────────────────────
class CircuitBreaker:
    def __init__(self, threshold: int = 5, reset_after: float = 60.0):
        self._threshold = threshold
        self._failures = 0
        self._opened_at: Optional[float] = None

    def call(self, fn, *args, **kwargs):
        if self._opened_at:
            if time.time() - self._opened_at > 60:
                self._failures = 0
                self._opened_at = None
            else:
                raise RuntimeError("Circuit breaker open — too many validation failures.")
        try:
            result = fn(*args, **kwargs)
            self._failures = 0
            return result
        except Exception as e:
            self._failures += 1
            if self._failures >= self._threshold:
                self._opened_at = time.time()
                logging.error("Circuit breaker opened after %d failures.", self._failures)
            raise

cb = CircuitBreaker(threshold=3)
guard_cb = Guard().use(ToxicLanguage, on_fail="exception")

def safe_call(text: str) -> str:
    return cb.call(lambda: guard_cb.parse(text).validated_output, text)

# ──────────────────────────────────────────────────────────────────────────────
# OPENAI SDK COMPATIBILITY
# ──────────────────────────────────────────────────────────────────────────────

# ── 18. Wrap OpenAI client with guardrails ───────────────────────────────────
class GuardedOpenAI:
    def __init__(self, guard: Guard):
        self._client = openai.OpenAI()
        self._guard = guard

    def chat(self, messages: list[dict], model: str = "gpt-4o-mini") -> str:
        raw = self._client.chat.completions.create(
            model=model, messages=messages
        ).choices[0].message.content
        return self._guard.parse(raw).validated_output

safe_openai = GuardedOpenAI(Guard().use(ToxicLanguage, on_fail="exception"))
reply = safe_openai.chat([{"role": "user", "content": "Tell me a joke."}])
print(reply)

# ── 19. Async OpenAI wrapper with guard ──────────────────────────────────────
class AsyncGuardedOpenAI:
    def __init__(self, guard: AsyncGuard):
        self._client = openai.AsyncOpenAI()
        self._guard = guard

    async def chat(self, messages: list[dict], model: str = "gpt-4o-mini") -> str:
        raw = (await self._client.chat.completions.create(
            model=model, messages=messages
        )).choices[0].message.content
        res = await self._guard.parse(raw)
        return res.validated_output

# ──────────────────────────────────────────────────────────────────────────────
# LLAMA-INDEX INTEGRATION
# ──────────────────────────────────────────────────────────────────────────────

# ── 20. LlamaIndex query engine with guardrails ──────────────────────────────
def make_guarded_llama_engine(index):
    from llama_index.core.query_engine import BaseQueryEngine

    guard = Guard().use(ToxicLanguage, on_fail="exception")

    class GuardedQueryEngine(BaseQueryEngine):
        def _query(self, query_str):
            response = index.as_query_engine().query(query_str)
            guard.parse(str(response))
            return response

    return GuardedQueryEngine()

# ──────────────────────────────────────────────────────────────────────────────
# MULTI-GUARD ORCHESTRATION
# ──────────────────────────────────────────────────────────────────────────────

# ── 21. Guard router: pick guard based on content type ───────────────────────
class GuardRouter:
    def __init__(self):
        self._guards: dict[str, Guard] = {
            "code": Guard().use(ValidPython, on_fail="exception"),
            "json": Guard().use(ValidJson, on_fail="exception"),
            "text": Guard().use(ToxicLanguage, on_fail="exception"),
        }

    def route(self, content: str, content_type: str = "text") -> str:
        guard = self._guards.get(content_type, self._guards["text"])
        return guard.parse(content).validated_output

router = GuardRouter()
print(router.route('{"key": "value"}', "json"))
print(router.route("def foo(): pass", "code"))

# ── 22. Guard middleware chain (decorator pattern) ────────────────────────────
def guarded(input_guard: Optional[Guard] = None, output_guard: Optional[Guard] = None):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            if input_guard and args:
                input_guard.parse(args[0])
            result = fn(*args, **kwargs)
            if output_guard:
                result = output_guard.parse(result).validated_output
            return result
        return wrapper
    return decorator

@guarded(
    input_guard=Guard().use(ToxicLanguage, on_fail="exception"),
    output_guard=Guard().use(ToxicLanguage, on_fail="filter"),
)
def process_text(text: str) -> str:
    return openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": text}],
    ).choices[0].message.content

# ──────────────────────────────────────────────────────────────────────────────
# MONITORING & OBSERVABILITY
# ──────────────────────────────────────────────────────────────────────────────

# ── 23. Guard with OpenTelemetry tracing ─────────────────────────────────────
def guarded_with_tracing(text: str, guard: Guard, span_name: str = "guardrails.validate") -> str:
    try:
        from opentelemetry import trace
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(span_name) as span:
            span.set_attribute("input.length", len(text))
            res = guard.parse(text)
            span.set_attribute("validation.passed", res.validation_passed)
            return res.validated_output
    except ImportError:
        return guard.parse(text).validated_output   # fallback if OTel not installed

# ── 24. Prometheus metrics exporter for guard results ────────────────────────
class PrometheusGuardExporter:
    def __init__(self, guard: Guard, prefix: str = "guardrails"):
        self._guard = guard
        self._prefix = prefix
        self._counters = {"total": 0, "passed": 0, "failed": 0}

    def validate(self, text: str) -> str:
        self._counters["total"] += 1
        res = self._guard.parse(text)
        key = "passed" if res.validation_passed else "failed"
        self._counters[key] += 1
        return res.validated_output

    def metrics(self) -> str:
        p = self._prefix
        lines = []
        for k, v in self._counters.items():
            lines.append(f"# TYPE {p}_{k}_total counter")
            lines.append(f"{p}_{k}_total {v}")
        return "\n".join(lines)

exporter = PrometheusGuardExporter(Guard().use(ToxicLanguage, on_fail="noop"))
exporter.validate("Great text!")
exporter.validate("Terrible!")
print(exporter.metrics())

# ──────────────────────────────────────────────────────────────────────────────
# TESTING GUARDS
# ──────────────────────────────────────────────────────────────────────────────

# ── 25. Unit test for custom validator ────────────────────────────────────────
import unittest

class TestToxicityGuard(unittest.TestCase):
    def setUp(self):
        self.guard = Guard().use(ToxicLanguage, threshold=0.5, on_fail="exception")

    def test_clean_text_passes(self):
        res = self.guard.parse("The weather is nice today.")
        self.assertTrue(res.validation_passed)

    def test_toxic_text_raises(self):
        with self.assertRaises(Exception):
            self.guard.parse("You are a complete idiot and I hate you.")

    def test_validation_outcome_type(self):
        from guardrails.classes import ValidationOutcome
        res = self.guard.parse("Hello, world.")
        self.assertIsInstance(res, ValidationOutcome)

# Run tests
suite = unittest.TestLoader().loadTestsFromTestCase(TestToxicityGuard)
unittest.TextTestRunner(verbosity=0).run(suite)

# ── 26. Guard mock for testing downstream systems ─────────────────────────────
from unittest.mock import MagicMock, patch

def test_with_mock_guard():
    mock_guard = MagicMock()
    mock_guard.parse.return_value = MagicMock(
        validated_output="Safe output",
        validation_passed=True,
    )
    result = mock_guard.parse("Any input").validated_output
    assert result == "Safe output"

test_with_mock_guard()

# ──────────────────────────────────────────────────────────────────────────────
# ADVANCED PATTERNS
# ──────────────────────────────────────────────────────────────────────────────

# ── 27. Guard with fallback on exception ──────────────────────────────────────
def guarded_with_fallback(text: str, fallback: str = "Content unavailable.") -> str:
    guard = Guard().use(ToxicLanguage, on_fail="exception")
    try:
        return guard.parse(text).validated_output
    except Exception:
        return fallback

# ── 28. A/B testing guards ────────────────────────────────────────────────────
import random

def ab_test_guard(text: str) -> str:
    guard_a = Guard().use(ToxicLanguage, threshold=0.5, on_fail="filter")
    guard_b = Guard().use(ToxicLanguage, threshold=0.3, on_fail="filter")

    guard = guard_a if random.random() < 0.5 else guard_b
    return guard.parse(text).validated_output

# ── 29. Guard with retry logic ────────────────────────────────────────────────
def guarded_llm_with_retry(prompt: str, max_retries: int = 3) -> str:
    guard = Guard().use(ToxicLanguage, on_fail="exception")
    for attempt in range(max_retries):
        try:
            raw = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
            ).choices[0].message.content
            return guard.parse(raw).validated_output
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            logging.warning("Guard attempt %d failed: %s", attempt + 1, e)
            time.sleep(2 ** attempt)
    return ""

# ── 30. Guard in a FastAPI app ────────────────────────────────────────────────
# pip install fastapi uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel as PydanticBaseModel

fastapi_app = FastAPI()
fastapi_guard = Guard().use_many(
    ToxicLanguage(threshold=0.5, on_fail="exception"),
    DetectPII(on_fail="fix"),
)

class ChatRequest(PydanticBaseModel):
    message: str

class ChatResponse(PydanticBaseModel):
    reply: str
    safe: bool

@fastapi_app.post("/chat", response_model=ChatResponse)
async def fastapi_chat(req: ChatRequest):
    raw = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": req.message}],
    ).choices[0].message.content
    try:
        res = fastapi_guard.parse(
            raw,
            metadata={"pii_entities": ["EMAIL_ADDRESS", "PHONE_NUMBER"]},
        )
        return ChatResponse(reply=res.validated_output, safe=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ── 31. Multi-step agent guard ────────────────────────────────────────────────
class GuardedAgent:
    def __init__(self):
        self._input_guard = Guard().use(ToxicLanguage, on_fail="exception")
        self._step_guard = Guard().use(ValidJson, on_fail="reask")
        self._output_guard = Guard().use_many(
            ToxicLanguage(threshold=0.5, on_fail="filter"),
            DetectPII(on_fail="fix"),
        )

    def run(self, task: str) -> str:
        self._input_guard.parse(task)

        # Step 1: Plan
        plan = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Return a JSON plan with 'steps' array."},
                {"role": "user", "content": f"Plan how to: {task}"},
            ],
        ).choices[0].message.content
        self._step_guard.parse(plan)

        # Step 2: Execute
        result = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": f"Execute this plan and summarize:\n\n{plan}"},
            ],
        ).choices[0].message.content

        res = self._output_guard.parse(
            result,
            metadata={"pii_entities": ["EMAIL_ADDRESS", "PHONE_NUMBER"]},
        )
        return res.validated_output

agent = GuardedAgent()
# output = agent.run("Write a summary of renewable energy benefits.")

# ── 32. Guard persistence: save/load guard config ────────────────────────────
import yaml

def save_guard_config(guard: Guard, path: str):
    config = guard.to_dict()
    with open(path, "w") as f:
        yaml.dump(config, f)

def load_guard_config(path: str) -> Guard:
    with open(path) as f:
        config = yaml.safe_load(f)
    return Guard.from_dict(config)

guard32 = Guard(name="persisted-guard").use(ToxicLanguage, on_fail="exception")
# save_guard_config(guard32, "/tmp/guard_config.yaml")
# loaded = load_guard_config("/tmp/guard_config.yaml")
