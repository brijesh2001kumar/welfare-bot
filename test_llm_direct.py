# test_llm_direct.py
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# 1. Explicitly locate and load the .env file
root_dir = Path(__file__).resolve().parent
env_path = root_dir / '.env'
load_dotenv(dotenv_path=env_path)

print("=" * 50)
print("DIAGNOSTIC PATH CHECK")
print(f"Project Root Directory: {root_dir}")
print(f"Looking for .env file at: {env_path}")
print(f"Does .env file exist? {env_path.exists()}")
print("=" * 50)

# 2. Check if the environment variable is visible to Python
api_key = os.getenv("GROQ_API_KEY", "")
print("ENVIRONMENT VARIABLE CHECK")
if api_key:
    print(f"✅ Success! GROQ_API_KEY found in Python.")
    print(f"   Key starts with: {api_key[:7]}...")
else:
    print("❌ Failure: GROQ_API_KEY is completely empty inside Python.")
print("=" * 50)

# 3. Test the actual integration module asynchronously
from utils.llm_client import call_llm

async def run_live_test():
    print("LIVE API PIPELINE TEST")
    if not api_key:
        print("⏭️ Skipping live API call because API key is missing.")
        return

    print("Sending request to Groq (Llama 3)... Please wait...")
    
    test_system_prompt = "You are a helpful assistant."
    test_messages = [{"role": "user", "content": "Respond with exactly the phrase: 'Pipeline is 100% operational!'"}]
    
    response = await call_llm(test_system_prompt, test_messages)
    print(f"Response from LLM Client:\n{response}")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(run_live_test())