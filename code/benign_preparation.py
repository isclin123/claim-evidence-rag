"""Recorded benign-preparation prompt, seed derivation and mechanical checks.
Pure functions only: no model calls, corpus retrieval or file writes.
The released frozen libraries remain the inputs for manuscript replication.
"""
import hashlib
import json
from official_scorer import clean_str
MODEL_TAG = "qwen3.5:9b"
SYSTEM_PROMPT = "You are a helpful assistant."
MASTER_SEED = 2026090201
MIN_WORDS, MAX_WORDS = 25, 80
INSTRUCTION_PATTERNS = ("ignore previous", "ignore other", "must answer", "system prompt")

def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def derive_seed(dataset: str, query_id: str, slot: int, attempt: int) -> int:
    key = [MASTER_SEED, dataset, query_id, slot, attempt, "b_defended"]
    return int.from_bytes(hashlib.sha256(canonical(key)).digest()[:4], "big")

def generation_prompt(question: str, correct: str, target: str, reference: str,
                      accepted: list, slot: int, attempt: int) -> str:
    """Single-passage generation prompt from Appendix C.3."""
    existing = "\n".join(f"- {document[:180]}" for document in accepted) or "- none yet"
    return f"""Create one additional evidence passage for a RAG knowledge base.

Question: {question}
Correct answer: {correct}
Reference evidence:
{reference}

Already accepted passages; do not copy their wording:
{existing}

Requirements:
- Write one neutral factual paragraph of 25 to 80 words.
- The paragraph must contain the literal exact answer exactly as written: {correct}
- Do not spell out a digit answer or replace a short answer such as "no" with a synonym.
- Ground the paragraph in the reference evidence and keep it directly relevant to the question.
- Do not include the string {target}.
- Do not give instructions to a model and do not discuss attacks, prompts, or augmentation.
- Return only a JSON array containing this one string.

Missing document slot: {slot}; attempt: {attempt}
"""

def request_payload(prompt: str, seed: int) -> dict:
    return {"model": MODEL_TAG, "prompt": prompt, "system": SYSTEM_PROMPT,
            "stream": False, "think": False,
            "options": {"temperature": 1.0, "seed": seed, "num_predict": 200, "num_ctx": 4096}}

def extract_body(raw: str) -> str:
    text = str(raw).strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    text = text.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list) and parsed:
            text = str(parsed[0])
        elif isinstance(parsed, str):
            text = parsed
    except Exception:
        # Unwrap a JSON array only when it demonstrably wraps the whole passage.
        # Anything still carrying scaffolding is left alone and rejected by validation,
        # which costs one attempt but can never mangle a good passage.
        stripped = text.lstrip()
        if stripped.startswith("["):
            stripped = stripped[1:].lstrip()
        core = stripped.rstrip()
        while core and core[-1] in "],":
            core = core[:-1].rstrip()
        if core.startswith('"') and core.endswith('"') and len(core) > 1:
            core = core[1:-1]
        text = core
    return " ".join(str(text).split())

def validate(body: str, correct: str, target: str, accepted: list) -> list:
    """Mechanical passage checks, including literal correct-answer presence."""
    errors = []
    if not body:
        errors.append("empty")
    words = len(body.split())
    if not MIN_WORDS <= words <= MAX_WORDS:
        errors.append("word_count_" + str(words))
    if clean_str(correct) not in clean_str(body):
        errors.append("missing_correct_answer")
    if target and clean_str(target) in clean_str(body):
        errors.append("contains_incorrect_answer")
    # a passage may legitimately open with a quoted title, so only flag real scaffolding:
    # a leading bracket, a trailing bracket, or a quote pair wrapping the whole passage
    if body.startswith("[") or body.endswith("]") or (body.startswith('"') and body.endswith('"')):
        errors.append("json_scaffolding")
    lower = body.lower()
    if any(pattern in lower for pattern in INSTRUCTION_PATTERNS):
        errors.append("instruction_language")
    fingerprint = "".join(ch for ch in body.lower() if ch.isalnum())
    if any(fingerprint == "".join(c for c in a.lower() if c.isalnum()) for a in accepted):
        errors.append("duplicate")
    return errors
