import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("ANTHROPIC_API_KEY")
print(f"Key found: {key is not None}")
print(f"Key starts with: {key[:20] if key else 'NONE'}")
print(f"Key length: {len(key) if key else 0}")