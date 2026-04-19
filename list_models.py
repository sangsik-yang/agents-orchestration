import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise RuntimeError("Missing API Key: OPENROUTER_API_KEY must be set in .env")

request = urllib.request.Request(
    "https://openrouter.ai/api/v1/models",
    headers={"Authorization": f"Bearer {api_key}"},
)

with urllib.request.urlopen(request) as response:
    payload = json.load(response)

for model in payload.get("data", []):
    model_id = model.get("id", "")
    if model_id.endswith(":free"):
        print(model_id)
