#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

CONFIG_PATH = os.path.expanduser("~/iron-engine/config/.env")
load_dotenv(CONFIG_PATH)

token = os.getenv("HF_TOKEN")
client = InferenceClient(token=token)

PROMPT = (
    "Early 10th-century Welsh rulers meeting representatives of King Æthelstan near the borderlands of England and Wales, "
    "historically grounded royal gathering around a timber hall, Welsh rulers in period-appropriate wool clothing and cloaks, "
    "English royal representatives carrying simple standards, guarded but diplomatic atmosphere, horses and small retinue outside, "
    "rugged Welsh hills in the background, cinematic historical documentary realism, overcast natural light, "
    "realistic early medieval clothing and architecture, photorealistic 35mm film grain, "
    "no fantasy, no modern objects, no text"
)

output_path = os.path.expanduser("~/iron-engine/data/raw/hf_test.jpg")
os.makedirs(os.path.dirname(output_path), exist_ok=True)

print("[INFO] Generating image via Hugging Face InferenceClient...")
image = client.text_to_image(
    prompt=PROMPT,
    model="black-forest-labs/FLUX.1-schnell"
)

image.save(output_path)
print(f"[SUCCESS] Image written to: {output_path}")
