"""
TOPIC 4: Factuality & RAG / Hallucination Validators — 30+ practical examples
Covers: ProvenanceLLM, ProvenanceEmbeddings, ExtractedSummarySentencesMatch,
        ExtractiveSummary, SaliencyCheck, LLMCritic, LLMRAGEvaluator,
        ResponsivenessCheck, GroundedAIHallucination, BespokeMiniCheck,
        WikiProvenance, ResponseEvaluator

Install:
  guardrails hub install hub://guardrails/provenance_llm
  guardrails hub install hub://guardrails/provenance_embeddings
  guardrails hub install hub://guardrails/extracted_summary_sentences_match
  guardrails hub install hub://guardrails/extractive_summary
  guardrails hub install hub://guardrails/saliency_check
  guardrails hub install hub://guardrails/llm_critic
  guardrails hub install hub://guardrails/llm_rag_evaluator
  guardrails hub install hub://guardrails/responsiveness_check
  guardrails hub install hub://guardrails/grounded_ai_hallucination
  guardrails hub install hub://guardrails/bespoke_minicheck
  guardrails hub install hub://guardrails/wiki_provenance
"""

import openai
from guardrails import Guard

# ── Helper: embedding function (reused throughout) ───────────────────────────
def embed_texts(texts: list[str]) -> list[list[float]]:
    resp = openai.embeddings.create(model="text-embedding-3-small", input=texts)
    return [e.embedding for e in resp.data]

# ──────────────────────────────────────────────────────────────────────────────
# PROVENANCE LLM
# ──────────────────────────────────────────────────────────────────────────────

# ── 1. Basic provenance check with LLM ───────────────────────────────────────
from guardrails.hub import ProvenanceLLM

guard1 = Guard().use(ProvenanceLLM, validation_method="sentence", on_fail="exception")
guard1.parse(
    "The Eiffel Tower is located in Paris, France.",
    metadata={
        "sources": ["The Eiffel Tower is a wrought-iron lattice tower in Paris, France."],
        "embed_function": embed_texts,
    },
)

# ── 2. Provenance — reject hallucinated facts ────────────────────────────────
guard2 = Guard().use(ProvenanceLLM, validation_method="sentence", on_fail="exception")
try:
    guard2.parse(
        "The Eiffel Tower is located in Berlin.",
        metadata={
            "sources": ["The Eiffel Tower is in Paris, France."],
            "embed_function": embed_texts,
        },
    )
except Exception as e:
    print(f"Hallucination caught: {e}")

# ── 3. Provenance — full text validation ─────────────────────────────────────
guard3 = Guard().use(ProvenanceLLM, validation_method="full", on_fail="exception")
guard3.parse(
    "Mount Everest is the tallest mountain on Earth.",
    metadata={
        "sources": ["Mount Everest, at 8,849 m, is Earth's highest mountain."],
        "embed_function": embed_texts,
    },
)

# ── 4. Multi-source provenance ────────────────────────────────────────────────
guard4 = Guard().use(ProvenanceLLM, validation_method="sentence", on_fail="filter")
res4 = guard4.parse(
    "Water boils at 100°C at sea level. Gold is heavier than water.",
    metadata={
        "sources": [
            "Water boils at 100 degrees Celsius (212°F) at standard atmospheric pressure.",
            "Gold has a density of 19.3 g/cm³, much denser than water at 1 g/cm³.",
        ],
        "embed_function": embed_texts,
    },
)
print(res4.validated_output)

# ── 5. Provenance — RAG pipeline answer validation ────────────────────────────
def rag_answer_with_check(question: str, context_docs: list[str]) -> str:
    raw = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Answer based only on the provided context."},
            {"role": "user", "content": f"Context:\n{chr(10).join(context_docs)}\n\nQuestion: {question}"},
        ],
    ).choices[0].message.content

    guard = Guard().use(ProvenanceLLM, validation_method="sentence", on_fail="filter")
    res = guard.parse(
        raw,
        metadata={"sources": context_docs, "embed_function": embed_texts},
    )
    return res.validated_output

# ──────────────────────────────────────────────────────────────────────────────
# PROVENANCE EMBEDDINGS
# ──────────────────────────────────────────────────────────────────────────────

# ── 6. Embedding-based provenance ────────────────────────────────────────────
from guardrails.hub import ProvenanceEmbeddings

guard6 = Guard().use(
    ProvenanceEmbeddings,
    validation_method="sentence",
    on_fail="exception",
)
guard6.parse(
    "Python was created by Guido van Rossum.",
    metadata={
        "sources": ["Python is a programming language created by Guido van Rossum in 1991."],
        "embed_function": embed_texts,
        "threshold": 0.7,
    },
)

# ── 7. Embedding provenance with custom threshold ────────────────────────────
guard7 = Guard().use(ProvenanceEmbeddings, validation_method="full", on_fail="exception")
guard7.parse(
    "The speed of light is approximately 300,000 km/s.",
    metadata={
        "sources": ["Light travels at approximately 299,792 km/s in a vacuum."],
        "embed_function": embed_texts,
        "threshold": 0.6,
    },
)

# ──────────────────────────────────────────────────────────────────────────────
# SUMMARY / EXTRACTIVE CHECKS
# ──────────────────────────────────────────────────────────────────────────────

# ── 8. Extracted summary sentences match ─────────────────────────────────────
from guardrails.hub import ExtractedSummarySentencesMatch

guard8 = Guard().use(
    ExtractedSummarySentencesMatch,
    threshold=0.85,
    on_fail="exception",
)

source_doc = (
    "The Amazon River is the largest river by discharge volume of water in the world. "
    "It is located in South America and flows into the Atlantic Ocean."
)
guard8.parse(
    "The Amazon River is the world's largest river by water volume, located in South America.",
    metadata={"sources": [source_doc], "embed_function": embed_texts},
)

# ── 9. Extractive summary — all sentences must come from source ───────────────
from guardrails.hub import ExtractiveSummary

guard9 = Guard().use(ExtractiveSummary, threshold=0.8, on_fail="filter")
res9 = guard9.parse(
    "Einstein won the Nobel Prize. He developed the theory of relativity.",
    metadata={
        "document": (
            "Albert Einstein won the Nobel Prize in Physics in 1921. "
            "He is best known for developing the theory of relativity."
        ),
        "embed_function": embed_texts,
    },
)
print(res9.validated_output)

# ── 10. Saliency check — key topics covered in summary ───────────────────────
from guardrails.hub import SaliencyCheck

guard10 = Guard().use(
    SaliencyCheck,
    docs_dir="./source_docs",
    on_fail="exception",
)
# Ensures the LLM summary covers salient topics from source documents

# ──────────────────────────────────────────────────────────────────────────────
# LLM CRITIC
# ──────────────────────────────────────────────────────────────────────────────

# ── 11. LLM as critic — basic ─────────────────────────────────────────────────
from guardrails.hub import LLMCritic

guard11 = Guard().use(
    LLMCritic,
    llm_callable="gpt-4o-mini",
    on_fail="exception",
)
guard11.parse(
    "The French Revolution began in 1789 and led to major political changes.",
    metadata={"prompt": "Verify the historical accuracy of this statement."},
)

# ── 12. LLM critic as quality gate ───────────────────────────────────────────
quality_guard = Guard().use(
    LLMCritic,
    llm_callable="gpt-4o-mini",
    on_fail="reask",
)
res12 = quality_guard(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Explain the water cycle in 3 sentences."}],
    num_reasks=2,
)
print(res12.validated_output)

# ──────────────────────────────────────────────────────────────────────────────
# RAG EVALUATORS
# ──────────────────────────────────────────────────────────────────────────────

# ── 13. LLM RAG evaluator — answer faithfulness ──────────────────────────────
from guardrails.hub import LLMRagEvaluator

context = "The Sahara is the world's largest hot desert, covering 9.2 million km²."
question = "What is the Sahara?"

guard13 = Guard().use(
    LLMRagEvaluator,
    llm_callable="gpt-4o-mini",
    on_fail="exception",
)
guard13.parse(
    "The Sahara is the largest hot desert in the world.",
    metadata={"query": question, "context": context},
)

# ── 14. RAG evaluator — detect off-context answers ───────────────────────────
try:
    guard13.parse(
        "The Sahara is located in Antarctica.",
        metadata={"query": question, "context": context},
    )
except Exception as e:
    print(f"Off-context answer blocked: {e}")

# ── 15. MLcube RAG context evaluator ─────────────────────────────────────────
from guardrails.hub import MLcubeRagContextEvaluator

guard15 = Guard().use(MLcubeRagContextEvaluator, on_fail="exception")
guard15.parse(
    "Photosynthesis converts sunlight into chemical energy.",
    metadata={
        "query": "What is photosynthesis?",
        "context": "Photosynthesis is the process by which plants convert light energy into chemical energy.",
    },
)

# ── 16. Responsiveness check ──────────────────────────────────────────────────
from guardrails.hub import ResponsivenessCheck

guard16 = Guard().use(
    ResponsivenessCheck,
    llm_callable="gpt-4o-mini",
    on_fail="reask",
)
res16 = guard16(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is photosynthesis? Be specific."}],
    num_reasks=2,
)
print(res16.validated_output)

# ──────────────────────────────────────────────────────────────────────────────
# GROUNDED AI / BESPOKE MINI-CHECK
# ──────────────────────────────────────────────────────────────────────────────

# ── 17. GroundedAI hallucination check ───────────────────────────────────────
from guardrails.hub import GroundedAIHallucination

guard17 = Guard().use(GroundedAIHallucination, on_fail="exception")
guard17.parse(
    "The Earth orbits the Sun once every 365.25 days.",
    metadata={
        "sources": ["Earth takes approximately 365.25 days to orbit the Sun."]
    },
)

# ── 18. BespokeMiniCheck — lightweight hallucination check ───────────────────
from guardrails.hub import BespokeMiniCheck

guard18 = Guard().use(BespokeMiniCheck, on_fail="exception")
guard18.parse(
    "DNA is a double helix molecule.",
    metadata={"context": "DNA (deoxyribonucleic acid) has a double helix structure discovered by Watson and Crick."},
)

# ── 19. Wiki provenance ───────────────────────────────────────────────────────
from guardrails.hub import WikiProvenance

guard19 = Guard().use(WikiProvenance, on_fail="exception")
guard19.parse(
    "The Great Wall of China was built over many centuries to protect Chinese states.",
)

# ──────────────────────────────────────────────────────────────────────────────
# RESPONSE EVALUATOR
# ──────────────────────────────────────────────────────────────────────────────

# ── 20. Response evaluator ────────────────────────────────────────────────────
from guardrails.hub import ResponseEvaluator

guard20 = Guard().use(
    ResponseEvaluator,
    llm_callable="gpt-4o-mini",
    on_fail="exception",
)
guard20.parse(
    "To reset your password, go to Settings > Account > Reset Password.",
    metadata={"query": "How do I reset my password?"},
)

# ──────────────────────────────────────────────────────────────────────────────
# COMPOSITE RAG PIPELINES
# ──────────────────────────────────────────────────────────────────────────────

# ── 21. Full RAG safety: provenance + responsiveness ─────────────────────────
rag_guard = Guard(name="rag-safety").use_many(
    ProvenanceLLM(validation_method="sentence", on_fail="filter"),
    ResponsivenessCheck(llm_callable="gpt-4o-mini", on_fail="reask"),
)

def safe_rag_response(question: str, contexts: list[str]) -> str:
    prompt = f"Answer the question using these contexts:\n{chr(10).join(contexts)}\n\nQ: {question}"
    raw = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    ).choices[0].message.content

    res = rag_guard.parse(
        raw,
        metadata={
            "sources": contexts,
            "query": question,
            "embed_function": embed_texts,
        },
    )
    return res.validated_output

# ── 22. Medical RAG — strict hallucination control ───────────────────────────
medical_guard = Guard(name="medical-rag").use_many(
    ProvenanceLLM(validation_method="sentence", on_fail="exception"),
    BespokeMiniCheck(on_fail="exception"),
)

def safe_medical_answer(question: str, docs: list[str]) -> str:
    raw = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Answer medical questions using only the given documents."},
            {"role": "user", "content": f"Docs:\n{chr(10).join(docs)}\n\nQ: {question}"},
        ],
    ).choices[0].message.content

    res = medical_guard.parse(
        raw,
        metadata={"sources": docs, "context": chr(10).join(docs), "embed_function": embed_texts},
    )
    return res.validated_output

# ── 23. Extractive summary in a document summarizer ──────────────────────────
from guardrails.hub import ExtractiveSummary

def summarize_document(text: str) -> str:
    raw = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": f"Summarize this in 3 sentences:\n\n{text}"}
        ],
    ).choices[0].message.content

    guard = Guard().use(ExtractiveSummary, threshold=0.75, on_fail="filter")
    res = guard.parse(
        raw,
        metadata={"document": text, "embed_function": embed_texts},
    )
    return res.validated_output

# ── 24. Chatbot answer quality gate ──────────────────────────────────────────
from guardrails.hub import LLMCritic, ResponsivenessCheck

quality_gate = Guard(name="quality-gate").use_many(
    LLMCritic(llm_callable="gpt-4o-mini", on_fail="reask"),
    ResponsivenessCheck(llm_callable="gpt-4o-mini", on_fail="reask"),
)

def high_quality_answer(question: str) -> str:
    res = quality_gate(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": question}],
        num_reasks=2,
    )
    return res.validated_output

# ── 25. Legal QA — provenance from statutes ──────────────────────────────────
statute_text = (
    "Under Section 230 of the Communications Decency Act, "
    "no provider of an interactive computer service shall be treated as the publisher "
    "of any information provided by another information content provider."
)

legal_guard = Guard().use(ProvenanceLLM, validation_method="sentence", on_fail="exception")

def legal_qa(question: str, statutes: list[str]) -> str:
    raw = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Answer only from the given statutes."},
            {"role": "user", "content": f"Statutes:\n{chr(10).join(statutes)}\n\nQ: {question}"},
        ],
    ).choices[0].message.content

    res = legal_guard.parse(
        raw,
        metadata={"sources": statutes, "embed_function": embed_texts},
    )
    return res.validated_output

# ── 26. Financial report — grounded claims ───────────────────────────────────
fin_context = "ACME Corp reported Q3 revenue of $5.2B, up 12% YoY, with net income of $1.1B."

fin_guard = Guard().use(GroundedAIHallucination, on_fail="exception")
fin_guard.parse(
    "ACME Corp had revenue of $5.2 billion in Q3.",
    metadata={"sources": [fin_context]},
)

# ── 27. Multi-hop provenance — chain of facts ────────────────────────────────
sources = [
    "Water (H2O) is composed of two hydrogen atoms and one oxygen atom.",
    "Hydrogen is the lightest and most abundant element in the universe.",
    "Oxygen is necessary for combustion and human respiration.",
]

guard27 = Guard().use(ProvenanceLLM, validation_method="sentence", on_fail="filter")
res27 = guard27.parse(
    "Water contains hydrogen, the most abundant element, and oxygen needed for respiration.",
    metadata={"sources": sources, "embed_function": embed_texts},
)
print(res27.validated_output)

# ── 28. Education app — verify historical facts ───────────────────────────────
history_sources = [
    "World War II lasted from 1939 to 1945.",
    "The war involved most of the world's nations, including all great powers.",
]

edu_guard = Guard().use(ProvenanceLLM, validation_method="sentence", on_fail="exception")
edu_guard.parse(
    "World War II, which lasted from 1939 to 1945, was a global conflict.",
    metadata={"sources": history_sources, "embed_function": embed_texts},
)

# ── 29. News summarizer with factuality gate ─────────────────────────────────
from guardrails.hub import ExtractedSummarySentencesMatch

news_article = """
Apple Inc. reported record quarterly revenue of $123.9 billion for Q1 FY2024,
a 2% increase year-over-year. Services revenue hit an all-time high of $23.1 billion.
CEO Tim Cook called it a strong start to the fiscal year.
"""

news_guard = Guard().use(
    ExtractedSummarySentencesMatch,
    threshold=0.8,
    on_fail="filter",
)

def safe_news_summary(article: str) -> str:
    raw = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Summarize this article in 2 sentences:\n\n{article}"}],
    ).choices[0].message.content

    res = news_guard.parse(
        raw,
        metadata={"sources": [article], "embed_function": embed_texts},
    )
    return res.validated_output

# ── 30. Async RAG validator ───────────────────────────────────────────────────
import asyncio
from guardrails import AsyncGuard
from guardrails.hub import ProvenanceLLM

async def async_rag_validate(text: str, sources: list[str]) -> str:
    aguard = AsyncGuard().use(ProvenanceLLM, validation_method="sentence", on_fail="filter")
    res = await aguard.parse(
        text,
        metadata={"sources": sources, "embed_function": embed_texts},
    )
    return res.validated_output

asyncio.run(async_rag_validate(
    "The speed of light is 300,000 km/s.",
    ["Light travels at approximately 299,792 km/s in a vacuum."],
))

# ── 31. Wikipedia-grounded encyclopedia bot ───────────────────────────────────
from guardrails.hub import WikiProvenance

wiki_guard = Guard().use(WikiProvenance, on_fail="exception")

def wiki_grounded_answer(topic: str) -> str:
    raw = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Tell me about {topic} in 2 sentences."}],
    ).choices[0].message.content

    res = wiki_guard.parse(raw)
    return res.validated_output
