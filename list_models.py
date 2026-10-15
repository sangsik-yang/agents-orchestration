import json
import urllib.request
from dotenv import load_dotenv
from config import OPENROUTER_BASE_URL, get_openrouter_api_key

load_dotenv()

request = urllib.request.Request(
    f"{OPENROUTER_BASE_URL}/models",
    headers={"Authorization": f"Bearer {get_openrouter_api_key()}"},
)

with urllib.request.urlopen(request) as response:
    payload = json.load(response)

for model in payload.get("data", []):
    model_id = model.get("id", "")
    if model_id.endswith(":free"):
        print(model_id)
