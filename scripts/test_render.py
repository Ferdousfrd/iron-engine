#!/usr/bin/env python3
import os
import urllib.parse
import requests

PROMPT = (
    "Early 10th-century Welsh rulers meeting representatives of King Æthelstan near the borderlands of England and Wales, "
    "historically grounded royal gathering around a timber hall, Welsh rulers in period-appropriate wool clothing and cloaks, "
    "English royal representatives carrying simple standards, guarded but diplomatic atmosphere, horses and small retinue outside, "
    "rugged Welsh hills in the background, no exaggerated kneeling or humiliation, political recognition rather than conquest, "
    "cinematic historical documentary realism, overcast natural light, realistic early medieval clothing and architecture, "
    "no fantasy, no modern objects, no text"
)

output_path = os.path.expanduser("~/iron-engine/data/raw/welsh_test.jpg")
os.makedirs(os.path.dirname(output_path), exist_ok=True)

clean_prompt = urllib.parse.quote(PROMPT)
url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1080&height=1350&nologo=true&model=flux"

print("[INFO] Requesting test render from Flux...")
response = requests.get(url, timeout=90)

if response.status_code == 200 and len(response.content) > 5000:
    with open(output_path, "wb") as f:
        f.write(response.content)
    print(f"[SUCCESS] Image written to: {output_path}")
else:
    print(f"[ERROR] Generation failed. HTTP Status: {response.status_code}")
