import os
from dotenv import load_dotenv
import anthropic
import json

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

try:
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": """Analyse this company registration for a Ghanaian internship platform.
            
Company Name: Ecobank Ghana
Email: hr@ecobank.com.gh
Industry: Banking & Finance
Phone: 0302123456
Address: 19 Seventh Avenue, Ridge, Accra
Contact Person: Kwame Mensah
Description: Ecobank Ghana is a leading pan-African bank offering internship opportunities to students across Ghana.

Respond ONLY with this JSON:
{
    "confidence_score": <number 0-100>,
    "decision": "<AUTO_APPROVE or RECOMMEND_APPROVE or MANUAL_REVIEW>",
    "reasoning": "<2-3 sentences>",
    "flags": []
}"""
        }]
    )
    
    raw = message.content[0].text.strip()
    print(f"✅ Raw response: {raw}")
    result = json.loads(raw)
    print(f"✅ Parsed: {result}")

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"❌ Error: {e}")