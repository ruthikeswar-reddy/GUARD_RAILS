#!/bin/bash
# Install all Guardrails Hub validators used across the notebooks
# Run from the GUARD_RAILS directory after activating .venv

set -e

echo "Installing Guardrails Hub validators..."

# Content Safety
guardrails hub install hub://guardrails/toxic_language --quiet
guardrails hub install hub://guardrails/profanity_free --quiet
guardrails hub install hub://guardrails/detect_jailbreak --quiet
guardrails hub install hub://guardrails/prompt_injection --quiet
guardrails hub install hub://guardrails/detect_pii --quiet
guardrails hub install hub://guardrails/nsfw_text --quiet
guardrails hub install hub://guardrails/secrets_present --quiet
guardrails hub install hub://guardrails/sensitive_topic --quiet
guardrails hub install hub://guardrails/mentions_drugs --quiet

# Format & Structure
guardrails hub install hub://guardrails/valid_json --quiet
guardrails hub install hub://guardrails/valid_python --quiet
guardrails hub install hub://guardrails/valid_sql --quiet
guardrails hub install hub://guardrails/valid_html --quiet
guardrails hub install hub://guardrails/valid_url --quiet
guardrails hub install hub://guardrails/valid_address --quiet
guardrails hub install hub://guardrails/regex_match --quiet
guardrails hub install hub://guardrails/valid_length --quiet
guardrails hub install hub://guardrails/valid_range --quiet
guardrails hub install hub://guardrails/contains_string --quiet
guardrails hub install hub://guardrails/ends_with --quiet
guardrails hub install hub://guardrails/one_line --quiet
guardrails hub install hub://guardrails/valid_choices --quiet

# Factuality & Hallucination
guardrails hub install hub://guardrails/provenance_llm --quiet
guardrails hub install hub://guardrails/provenance_embeddings --quiet
guardrails hub install hub://guardrails/grounded_ai_hallucination --quiet
guardrails hub install hub://guardrails/bespoke_minicheck --quiet
guardrails hub install hub://guardrails/llm_rag_evaluator --quiet
guardrails hub install hub://guardrails/wiki_provenance --quiet

# Text Quality
guardrails hub install hub://guardrails/reading_level --quiet
guardrails hub install hub://guardrails/reading_time --quiet
guardrails hub install hub://guardrails/gibberish_text --quiet
guardrails hub install hub://guardrails/redundant_sentences --quiet
guardrails hub install hub://guardrails/saliency_check --quiet
guardrails hub install hub://guardrails/extracted_summary_sentences_match --quiet
guardrails hub install hub://guardrails/similar_to_document --quiet
guardrails hub install hub://guardrails/relevancy_evaluator --quiet

# Business Logic
guardrails hub install hub://guardrails/competitor_check --quiet
guardrails hub install hub://guardrails/restrict_to_topic --quiet
guardrails hub install hub://guardrails/quotes_price --quiet
guardrails hub install hub://guardrails/financial_tone --quiet
guardrails hub install hub://guardrails/politeness_check --quiet
guardrails hub install hub://guardrails/ban_list --quiet
guardrails hub install hub://guardrails/unusual_prompt --quiet
guardrails hub install hub://guardrails/responsiveness_check --quiet

echo "All validators installed successfully."
