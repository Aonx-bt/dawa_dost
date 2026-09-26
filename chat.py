import os
from pathlib import Path

from sarvamai import SarvamAI

for line in Path(".env").read_text().splitlines():
    if line.strip() and not line.startswith("#") and "=" in line:
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())

api_key = os.environ["SARVAM_API_KEY"]

client = SarvamAI(api_subscription_key=api_key)

response = client.chat.completions(
    messages=[{"role": "user", "content": "Hello, who are you?"}],
    model="sarvam-105b-conversations",
)

print(response.choices[0].message.content)
