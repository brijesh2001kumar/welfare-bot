"""
Helper utilities:
- Language detection (Hindi vs English, handles code-mixing)
- Eligibility scoring from user answers
- Document checklist formatter
"""

import re
from data.schemes import SCHEMES


# ── Language Detection ──────────────────────────────────────────────────────

HINDI_UNICODE_RANGE = re.compile(r'[\u0900-\u097F]')

def detect_language(text: str) -> str:
    # 1. Pure Devanagari script always wins
    if HINDI_UNICODE_RANGE.search(text):
        return "hi"
        
    # 2. Look for operational Romanized Hindi structural verbs/pronouns instead of nouns
    roman_hindi_signals = ["kya", "hai", "mera", "meri", "batao", "kab", "kaise", "he", "rhna"]
    lower = text.lower()
    if any(word in lower for word in roman_hindi_signals):
        return "hi"
        
    return "en"


# ── Scheme Retrieval ─────────────────────────────────────────────────────────

def retrieve_relevant_schemes(query: str) -> list[dict]:
    """
    Simple keyword-based retrieval over the scheme catalogue.
    Returns list of matching scheme dicts. Used as RAG context for LLM.
    """
    query_lower = query.lower()
    results = []
    for scheme in SCHEMES.values():
        for kw in scheme["keywords"]:
            if kw.lower() in query_lower:
                results.append(scheme)
                break
    # If nothing matched, return all (better to give context than nothing)
    return results if results else list(SCHEMES.values())


def get_scheme_by_id(scheme_id: str) -> dict | None:
    return SCHEMES.get(scheme_id)


# ── Eligibility Scoring ──────────────────────────────────────────────────────

def compute_eligibility(answers: dict) -> list[dict]:
    """
    Given answers dict {occupation, ration_card, family_income, aadhaar},
    returns list of eligible scheme dicts with a 'confidence' field.
    """
    eligible = []

    occupation = answers.get("occupation", "")
    ration_card = answers.get("ration_card", "")
    aadhaar = answers.get("aadhaar", "")

    # PM-KISAN: must be farmer (option 1)
    if occupation == "1" and aadhaar in ("1", "2"):
        eligible.append({**SCHEMES["pm_kisan"], "confidence": "high"})

    # Ayushman Bharat: BPL ration card (option 1) OR low income
    if ration_card == "1" or answers.get("family_income", "") == "1":
        eligible.append({**SCHEMES["ayushman_bharat"], "confidence": "high"})
    elif ration_card == "2" and answers.get("family_income", "") == "2":
        eligible.append({**SCHEMES["ayushman_bharat"], "confidence": "medium"})

    return eligible


# ── Document Checklist ───────────────────────────────────────────────────────

def format_document_checklist(scheme: dict, lang: str) -> str:
    """
    Returns a formatted document checklist string for the given scheme.
    """
    docs = scheme["documents_hi"] if lang == "hi" else scheme["documents_en"]
    name = scheme["name_hi"] if lang == "hi" else scheme["name_en"]
    apply_info = scheme["apply_hi"] if lang == "hi" else scheme["apply_en"]
    helpline = scheme["helpline"]

    if lang == "hi":
        lines = [f"📋 {name} — जरूरी दस्तावेज़:", ""]
        for i, doc in enumerate(docs, 1):
            lines.append(f"{i}. {doc}")
        lines += ["", f"📍 {apply_info}", f"📞 {helpline}"]
    else:
        lines = [f"📋 {name} — Required Documents:", ""]
        for i, doc in enumerate(docs, 1):
            lines.append(f"{i}. {doc}")
        lines += ["", f"📍 {apply_info}", f"📞 {helpline}"]

    return "\n".join(lines)


def format_eligibility_result(eligible_schemes: list[dict], lang: str) -> str:
    """
    Returns a human-readable eligibility summary in the chosen language.
    """
    if not eligible_schemes:
        if lang == "hi":
            return ("❌ आपके जवाबों के आधार पर, इस समय आप इन 2 योजनाओं के पात्र नहीं लगते।\n"
                    "लेकिन सुनिश्चित करने के लिए नजदीकी CSC या ग्राम पंचायत से मिलें।")
        return ("❌ Based on your answers, you may not be eligible for these 2 schemes right now.\n"
                "Please visit your nearest CSC or Gram Panchayat to confirm.")

    if lang == "hi":
        lines = ["✅ आप इन योजनाओं के लिए पात्र हो सकते हैं:\n"]
        for s in eligible_schemes:
            conf_label = "उच्च संभावना" if s["confidence"] == "high" else "संभावित"
            lines.append(f"🟢 {s['name_hi']}  ({conf_label})")
            lines.append(f"   लाभ: {s['benefit_hi']}\n")
    else:
        lines = ["✅ You may be eligible for these schemes:\n"]
        for s in eligible_schemes:
            conf_label = "High likelihood" if s["confidence"] == "high" else "Possible"
            lines.append(f"🟢 {s['name_en']}  ({conf_label})")
            lines.append(f"   Benefit: {s['benefit_en']}\n")

    return "\n".join(lines)


# ── Prompt Builder for LLM ───────────────────────────────────────────────────

def build_rag_system_prompt(retrieved_schemes: list[dict], lang: str) -> str:
    """
    Builds a grounded system prompt for the LLM with scheme data injected.
    This is the RAG layer — the LLM can ONLY use the facts provided here.
    """
    scheme_context = ""
    for s in retrieved_schemes:
        scheme_context += f"""
--- SCHEME: {s['name_en']} ---
Benefit: {s['benefit_en']}
Eligibility: {s['eligibility'].get('income_limit_en', '')}
Excluded: {s['eligibility'].get('excluded_en', '')}
Documents required: {', '.join(s['documents_en'])}
How to apply: {s['apply_en']}
Helpline: {s['helpline']}
"""

    lang_instruction = (
        "IMPORTANT: Respond in Hindi (Devanagari script). You may include English words for scheme names or technical terms."
        if lang == "hi"
        else "Respond in clear, simple English. Use short sentences."
    )

    return f"""You are a helpful government welfare scheme assistant for rural users in India.
You ONLY know about the following schemes. Do NOT make up any scheme, benefit, or eligibility rule.
If you don't know something, say "Please visit your nearest CSC or call the helpline."

{lang_instruction}

KNOWN SCHEMES:
{scheme_context}

Rules:
- Keep responses SHORT (3-5 sentences max) to save bandwidth
- Always end with the relevant helpline number if giving scheme info
- Never guess eligibility — use the eligibility flow for that
- If asked about any other scheme, say you only cover PM-KISAN and Ayushman Bharat right now
"""