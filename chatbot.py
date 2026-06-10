"""
Chatbot FSM (Finite State Machine) conversation handler.

States:
  idle           → greeting, ask language
  lang_select    → user picks language
  menu           → main menu: check eligibility / ask question / get documents
  eligibility    → step through 4 questions
  results        → show eligible schemes, offer document checklists
  docs           → show document checklist for a specific scheme
  freeform       → open Q&A via LLM (RAG-grounded)
"""

from data.schemes import ELIGIBILITY_QUESTIONS, SCHEMES
from utils.helpers import (
    detect_language,
    retrieve_relevant_schemes,
    compute_eligibility,
    format_document_checklist,
    format_eligibility_result,
    build_rag_system_prompt,
)
from utils.session import UserSession
from utils.llm_client import call_llm


# ── Static message strings ────────────────────────────────────────────────────

GREET = {
    "en": (
        "🙏 Welcome to *Welfare Scheme Assistant*!\n\n"
        "I can help you find government schemes you qualify for.\n\n"
        "Choose your language:\n"
        "1️⃣  English\n"
        "2️⃣  हिंदी (Hindi)\n\n"
        "Type 1 or 2"
    ),
    "hi": (
        "🙏 *सरकारी योजना सहायक* में आपका स्वागत है!\n\n"
        "मैं आपको सरकारी योजनाएं ढूंढने में मदद कर सकता हूं।\n\n"
        "अपनी भाषा चुनें:\n"
        "1️⃣  English\n"
        "2️⃣  हिंदी (Hindi)\n\n"
        "1 या 2 टाइप करें"
    ),
}

MAIN_MENU = {
    "en": (
        "What would you like to do?\n\n"
        "1️⃣  Check which schemes I qualify for\n"
        "2️⃣  Learn about PM-KISAN\n"
        "3️⃣  Learn about Ayushman Bharat\n"
        "4️⃣  Get document checklist\n"
        "5️⃣  Ask a question\n\n"
        "Type a number, or just ask your question directly."
    ),
    "hi": (
        "आप क्या जानना चाहते हैं?\n\n"
        "1️⃣  देखें कि मैं किन योजनाओं के लिए पात्र हूं\n"
        "2️⃣  पीएम-किसान के बारे में जानें\n"
        "3️⃣  आयुष्मान भारत के बारे में जानें\n"
        "4️⃣  जरूरी दस्तावेज़ की सूची\n"
        "5️⃣  कोई सवाल पूछें\n\n"
        "नंबर टाइप करें, या सीधे सवाल पूछें।"
    ),
}

DOC_MENU = {
    "en": "Which scheme's documents do you need?\n1️⃣  PM-KISAN\n2️⃣  Ayushman Bharat",
    "hi": "किस योजना के दस्तावेज़ चाहिए?\n1️⃣  पीएम-किसान\n2️⃣  आयुष्मान भारत",
}

RESTART_HINT = {
    "en": "\n\n_(Type *menu* to go back to main menu, or *restart* to start over)_",
    "hi": "\n\n_(वापस जाने के लिए *menu* टाइप करें, या दोबारा शुरू करने के लिए *restart*)_",
}


# ── Main handler ──────────────────────────────────────────────────────────────

async def handle_message(session: UserSession, user_text: str) -> str:
    """
    Main entry point. Takes current session + user message, returns bot response.
    Mutates session state in place.
    """
    text = user_text.strip()
    text_lower = text.lower()

    # Global commands — work from any state
    if text_lower in ("restart", "reset", "/start", "शुरू", "दोबारा"):
        session.state = "idle"
        session.eligibility_answers = {}
        session.eligibility_step = 0
        session.eligible_schemes = []
        return GREET["en"]

    if text_lower in ("menu", "मेनू", "back", "वापस"):
        session.state = "menu"
        return MAIN_MENU[session.lang]

    # Auto-detect language from user input (handles code-mixing)
    detected = detect_language(text)
    if session.state not in ("idle",) and detected == "hi" and session.lang == "en":
        # Silently switch if user writes in Hindi
        session.lang = "hi"

    # ── FSM routing ───────────────────────────────────────────────────────────

    if session.state == "idle":
        session.state = "lang_select"
        return GREET["en"]

    if session.state == "lang_select":
        return _handle_lang_select(session, text)

    if session.state == "menu":
        return await _handle_menu(session, text)

    if session.state == "eligibility":
        return _handle_eligibility(session, text)

    if session.state == "results":
        return await _handle_results(session, text)

    if session.state == "docs":
        return _handle_docs(session, text)

    if session.state == "freeform":
        return await _handle_freeform(session, text)

    # Fallback
    session.state = "menu"
    return MAIN_MENU[session.lang]


# ── State handlers ─────────────────────────────────────────────────────────────

def _handle_lang_select(session: UserSession, text: str) -> str:
    if text.strip() in ("2", "2️⃣", "hindi", "हिंदी", "hi"):
        session.lang = "hi"
    else:
        session.lang = "en"
    session.state = "menu"
    return MAIN_MENU[session.lang]


async def _handle_menu(session: UserSession, text: str) -> str:
    lang = session.lang
    t = text.strip()

    if t in ("1", "1️⃣"):
        session.state = "eligibility"
        session.eligibility_step = 0
        session.eligibility_answers = {}
        q = ELIGIBILITY_QUESTIONS[lang][0]["question"]
        return ("Let's check your eligibility. Answer with the number.\n\n" + q
                if lang == "en"
                else "आइए पात्रता जांचते हैं। नंबर से जवाब दें।\n\n" + q)

    if t in ("2", "2️⃣"):
        scheme = SCHEMES["pm_kisan"]
        resp = await _llm_scheme_info(session, "Tell me about PM-KISAN scheme briefly", [scheme])
        return resp + RESTART_HINT[lang]

    if t in ("3", "3️⃣"):
        scheme = SCHEMES["ayushman_bharat"]
        resp = await _llm_scheme_info(session, "Tell me about Ayushman Bharat scheme briefly", [scheme])
        return resp + RESTART_HINT[lang]

    if t in ("4", "4️⃣"):
        session.state = "docs"
        return DOC_MENU[lang]

    if t in ("5", "5️⃣"):
        session.state = "freeform"
        return ("Ask me anything about PM-KISAN or Ayushman Bharat!" + RESTART_HINT[lang]
                if lang == "en"
                else "पीएम-किसान या आयुष्मान भारत के बारे में कुछ भी पूछें!" + RESTART_HINT[lang])

    # Free text — try to route intelligently
    session.state = "freeform"
    return await _handle_freeform(session, text)


def _handle_eligibility(session: UserSession, text: str) -> str:
    lang = session.lang
    questions = ELIGIBILITY_QUESTIONS[lang]
    step = session.eligibility_step
    current_q = questions[step]

    # Validate answer
    valid = current_q["options"]
    ans = text.strip()
    if ans not in valid:
        return (f"Please reply with a number: {', '.join(valid)}\n\n{current_q['question']}"
                if lang == "en"
                else f"कृपया नंबर से जवाब दें: {', '.join(valid)}\n\n{current_q['question']}")

    # Save answer
    session.eligibility_answers[current_q["id"]] = ans
    session.eligibility_step += 1

    # More questions?
    if session.eligibility_step < len(questions):
        next_q = questions[session.eligibility_step]
        return next_q["question"]

    # All done — compute eligibility
    eligible = compute_eligibility(session.eligibility_answers)
    session.eligible_schemes = eligible
    session.state = "results"

    result_text = format_eligibility_result(eligible, lang)

    if eligible:
        if lang == "en":
            follow = "\n\nType the scheme number to get document checklist:\n"
            for i, s in enumerate(eligible, 1):
                follow += f"{i}. {s['name_en']}\n"
        else:
            follow = "\n\nदस्तावेज़ सूची के लिए योजना का नंबर टाइप करें:\n"
            for i, s in enumerate(eligible, 1):
                follow += f"{i}. {s['name_hi']}\n"
        return result_text + follow
    else:
        return result_text + RESTART_HINT[lang]


async def _handle_results(session: UserSession, text: str) -> str:
    lang = session.lang
    t = text.strip()
    schemes = session.eligible_schemes

    # User picks a scheme number to get checklist
    if t.isdigit():
        idx = int(t) - 1
        if 0 <= idx < len(schemes):
            checklist = format_document_checklist(schemes[idx], lang)
            session.state = "menu"
            return checklist + RESTART_HINT[lang]

    # Otherwise freeform
    session.state = "freeform"
    return await _handle_freeform(session, text)


def _handle_docs(session: UserSession, text: str) -> str:
    lang = session.lang
    t = text.strip()

    if t in ("1", "1️⃣"):
        return format_document_checklist(SCHEMES["pm_kisan"], lang) + RESTART_HINT[lang]
    if t in ("2", "2️⃣"):
        return format_document_checklist(SCHEMES["ayushman_bharat"], lang) + RESTART_HINT[lang]

    return DOC_MENU[lang]


async def _handle_freeform(session: UserSession, text: str) -> str:
    lang = session.lang
    relevant = retrieve_relevant_schemes(text)
    system_prompt = build_rag_system_prompt(relevant, lang)

    session.add_message("user", text)
    reply = await call_llm(system_prompt, session.chat_history, max_tokens=250)
    session.add_message("assistant", reply)

    return reply + RESTART_HINT[lang]


async def _llm_scheme_info(session: UserSession, query: str, schemes: list) -> str:
    lang = session.lang
    system_prompt = build_rag_system_prompt(schemes, lang)
    return await call_llm(system_prompt, [{"role": "user", "content": query}], max_tokens=200)