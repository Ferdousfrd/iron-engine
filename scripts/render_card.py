#!/usr/bin/env python3
"""
Module: render_card.py
Description: Scans data/incoming for user-dropped images (named <topic_id>.* or <uuid>.*),
             composites a standard 1080x1350 card with a gold divider and text overlay,
             saves to data/dispatches, and updates PostgreSQL status to 'rendered'.
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

INCOMING_DIR = os.path.expanduser("~/iron-engine/data/incoming")
RAW_DIR = os.path.expanduser("~/iron-engine/data/raw")
OUTPUT_DIR = os.path.expanduser("~/iron-engine/data/dispatches")
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

os.makedirs(INCOMING_DIR, exist_ok=True)
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


def render_dispatch_card(dispatch_id: str, overlay_text: str, base_image_path: str) -> str:
    """Builds a 1080x1350 vertical social card with centered cropping and gold divider."""
    canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color=(15, 15, 15))

    with Image.open(base_image_path) as raw_img:
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

    # Gold accent line divider
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([(0, IMAGE_HEIGHT - 4), (CANVAS_WIDTH, IMAGE_HEIGHT)], fill=(212, 160, 23))

    # Load font
    try:
        font = ImageFont.truetype(FONT_PATH, size=40)
    except IOError:
        font = ImageFont.load_default()

    wrapped_lines = textwrap.wrap(overlay_text.upper(), width=32)
    full_text = "\n".join(wrapped_lines)

    # Center-align text in bottom footer box
    bbox = draw.multiline_textbbox((0, 0), full_text, font=font, spacing=15, align="center")
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    text_x = (CANVAS_WIDTH - text_width) // 2
    text_y = IMAGE_HEIGHT + ((FOOTER_HEIGHT - text_height) // 2)

    draw.multiline_text((text_x, text_y), full_text, font=font, fill=(250, 250, 250), spacing=15, align="center")

    output_path = os.path.join(OUTPUT_DIR, f"{dispatch_id}.jpg")
    canvas.save(output_path, "JPEG", quality=95)
    return output_path


def process_incoming_renders():
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT d.id, d.topic_id, d.overlay_text 
        FROM dispatches d
        WHERE d.status IN ('awaiting_image', 'pending_render', 'pending');
    """)
    pending_records = cur.fetchall()

    if not pending_records:
        print("[INFO] No dispatches waiting for renders.")
        cur.close()
        conn.close()
        return

    processed = 0
    for record in pending_records:
        d_id = str(record["id"])
        t_id = str(record["topic_id"])

        found_file = None
        for ext in [".jpg", ".jpeg", ".png", ".webp"]:
            cand_topic = os.path.join(INCOMING_DIR, f"{t_id}{ext}")
            cand_uuid = os.path.join(INCOMING_DIR, f"{d_id}{ext}")
            if os.path.exists(cand_topic):
                found_file = cand_topic
                break
            elif os.path.exists(cand_uuid):
                found_file = cand_uuid
                break

        if found_file:
            print(f"[FOUND] Matched image for Topic #{t_id} ({os.path.basename(found_file)})")
            raw_dest = os.path.join(RAW_DIR, f"{d_id}_raw.jpg")

            with Image.open(found_file) as im:
                im.convert("RGB").save(raw_dest, "JPEG", quality=95)
            os.remove(found_file)

            output_card = render_dispatch_card(d_id, record["overlay_text"], raw_dest)

            cur.execute("""
                UPDATE dispatches
                SET status = 'rendered', image_path = %s
                WHERE id = %s;
            """, (output_card, d_id))
            conn.commit()
            print(f"[SUCCESS] Card saved: {output_card}")
            processed += 1

    if processed == 0:
        print(f"[WAITING] No matching files for pending topics found in {INCOMING_DIR}")
    else:
        print(f"[DONE] Rendered {processed} new dispatch card(s).")

    cur.close()
    conn.close()


if __name__ == "__main__":
    process_incoming_renders()
