#!/usr/bin/env python3
"""
Module: render_card.py
Description: Generates high-impact social media image cards by compositing
             base imagery with auto-wrapped text overlays using Pillow.
"""

import os
import sys
import textwrap
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

# ---------------- CONFIGURATION ----------------
CONFIG_PATH = os.path.expanduser("~/iron-engine/config/.env")
load_dotenv(CONFIG_PATH)

CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1350
IMAGE_HEIGHT = 900
FOOTER_HEIGHT = CANVAS_HEIGHT - IMAGE_HEIGHT  # 450px

OUTPUT_DIR = os.path.expanduser("~/iron-engine/data/dispatches")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def fetch_pending_render(cursor):
    """Pulls the latest pending dispatch that has not yet been rendered."""
    query = """
        SELECT id, overlay_text
        FROM dispatches
        WHERE status = 'pending'
        ORDER BY created_at ASC
        LIMIT 1;
    """
    cursor.execute(query)
    return cursor.fetchone()

def render_dispatch_card(dispatch_id: str, overlay_text: str, base_image_path: str) -> str:
    """Builds the 1080x1350 image card and saves it to disk."""
    # 1. Create a blank dark canvas
    canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color=(15, 15, 15))

    # 2. Process and paste the base artwork
    with Image.open(base_image_path) as raw_img:
        # Resize/crop to fill top frame (1080 x 900)
        img_ratio = raw_img.width / raw_img.height
        target_ratio = CANVAS_WIDTH / IMAGE_HEIGHT

        if img_ratio > target_ratio:
            new_width = int(IMAGE_HEIGHT * img_ratio)
            resized = raw_img.resize((new_width, IMAGE_HEIGHT), Image.Resampling.LANCZOS)
            left_crop = (new_width - CANVAS_WIDTH) // 2
            cropped = resized.crop((left_crop, 0, left_crop + CANVAS_WIDTH, IMAGE_HEIGHT))
        else:
            new_height = int(CANVAS_WIDTH / img_ratio)
            resized = raw_img.resize((CANVAS_WIDTH, new_height), Image.Resampling.LANCZOS)
            top_crop = (new_height - IMAGE_HEIGHT) // 2
            cropped = resized.crop((0, top_crop, CANVAS_WIDTH, top_crop + IMAGE_HEIGHT))

        canvas.paste(cropped, (0, 0))

    # 3. Add accent border line between image and footer
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([(0, IMAGE_HEIGHT - 4), (CANVAS_WIDTH, IMAGE_HEIGHT)], fill=(212, 160, 23))  # Gold accent

    # 4. Format and wrap text
    try:
        font = ImageFont.truetype(FONT_PATH, size=40)
    except IOError:
        font = ImageFont.load_default()

    wrapped_lines = textwrap.wrap(overlay_text.upper(), width=32)
    full_text = "\n".join(wrapped_lines)

    # 5. Measure and center text in footer
    bbox = draw.multiline_textbbox((0, 0), full_text, font=font, spacing=15, align="center")
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    text_x = (CANVAS_WIDTH - text_width) // 2
    text_y = IMAGE_HEIGHT + ((FOOTER_HEIGHT - text_height) // 2)

    draw.multiline_text((text_x, text_y), full_text, font=font, fill=(250, 250, 250), spacing=15, align="center")

    # 6. Save final composite
    output_path = os.path.join(OUTPUT_DIR, f"{dispatch_id}.jpg")
    canvas.save(output_path, "JPEG", quality=95)
    return output_path

def mark_as_rendered(conn, dispatch_id: str, file_path: str):
    """Updates database record status to rendered and sets image path."""
    with conn.cursor() as cursor:
        query = """
            UPDATE dispatches
            SET status = 'rendered',
                image_path = %s
            WHERE id = %s;
        """
        cursor.execute(query, (file_path, dispatch_id))
        conn.commit()

if __name__ == "__main__":
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    record = fetch_pending_render(cursor)
    if not record:
        print("[NOTICE] No pending dispatches found to render.")
        sys.exit(0)

    dispatch_id = str(record["id"])
    overlay_text = record["overlay_text"]
    test_image = os.path.expanduser("~/iron-engine/data/raw/viking_base.jpg")

    print(f"[RENDER] Generating social card for Dispatch UUID: {dispatch_id}...")
    saved_path = render_dispatch_card(dispatch_id, overlay_text, test_image)
    
    mark_as_rendered(conn, dispatch_id, saved_path)
    print(f"[SUCCESS] Card saved: {saved_path}")
    print(f"[SUCCESS] Database updated: status = 'rendered'")

    cursor.close()
    conn.close()
