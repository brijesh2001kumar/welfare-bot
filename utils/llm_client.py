"""
LLM client using Groq API (free, fast — llama3-8b-8192).
Falls back gracefully with a sorry message if API key not set.
"""

import os
import httpx
import json
from pathlib import Path
from dotenv import load_dotenv

# Explicitly locate and load the .env file from the project root
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"   # fast, free on Groq


async def call_llm(
    system_prompt: str,
    messages: list[dict],
    max_tokens: int = 300,
) -> str:
    """
    Call LLM with system prompt + conversation history.
    Returns assistant text response.
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return (
            "⚠️ LLM not configured. Set GROQ_API_KEY in .env file.\n"
            "For demo, eligibility flow and document checklists still work without it."
        )

    # Reconstruct history defensively to prevent malformed nested list schemas
    formatted_messages = []
    
    # 1. Inject System Prompt
    if system_prompt:
        formatted_messages.append({"role": "system", "content": system_prompt})
        
    # 2. Append Chat History safely 
    for msg in messages:
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            formatted_messages.append({"role": msg["role"], "content": msg["content"]})

    payload = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": formatted_messages,
        "temperature": 0.2,   # Lowered slightly for strict rule compliance
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            
            # Print explicit debugging info if it still encounters an error
            if resp.status_code != 200:
                return f"⚠️ API error {resp.status_code}: {resp.text}"
                
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

    except httpx.TimeoutException:
        return "⏱️ Response took too long. Please try again. / कृपया दोबारा कोशिश करें।"
    except Exception as e:
        return f"⚠️ Unexpected Connection Error: {str(e)}"