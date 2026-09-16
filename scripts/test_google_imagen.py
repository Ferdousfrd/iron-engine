#!/usr/bin/env python3
import os
import io
from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(os.path.expanduser("~/iron-engine/config/.env"))

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

PROMPT = (
    "Early 10th-century Welsh rulers meeting representatives of King Æthelstan near the borderlands of England and Wales, "
    "historically grounded royal gathering around a timber hall, Welsh rulers in period-appropriate wool clothing and cloaks, "
    "English royal representatives carrying simple standards, guarded but diplomatic atmosphere, horses and small retinue outside, "
    "rugged Welsh hills in the background, cinematic historical documentary realism, overcast natural light, "
    "realistic early medieval clothing and architecture, no fantasy, no modern objects, no text"
)

output_path = os.path.expanduser("~/iron-engine/data/raw/google_test.jpg")
os.makedirs(os.path.dirname(output_path), exist_ok=True)

print("[INFO] Requesting visual from Gemini 2.5 Flash Image API...")

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=PROMPT,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="4:5"
            )
        )
    )

    image_saved = False
    for candidate in response.candidates:
        for part in candidate.content.parts:
            if part.inline_data is not None:
                img = Image.open(io.BytesIO(part.inline_data.data))
                img.save(output_path, "JPEG", quality=95)
                image_saved = True
                print(f"[SUCCESS] Authentic render saved to: {output_path}")
                break

    if not image_saved:
        print("[NOTICE] No image payload returned in candidates.")

except Exception as e:
    print(f"[FAILED] Error from Google API: {e}")
