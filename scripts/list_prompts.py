#!/usr/bin/env python3
"""
Module: list_prompts.py
Description: Dumps pending topics and their image prompts to the terminal
             so you can copy-paste them directly into Gemini.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/iron-engine/config/.env"))

def list_pending():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT d.id, t.id AS topic_id, t.title, d.overlay_text, d.image_prompt 
            FROM dispatches d
            JOIN topics t ON d.topic_id = t.id
            WHERE d.status IN ('awaiting_image', 'pending_render')
            ORDER BY t.id ASC;
        """)
        rows = cur.fetchall()

    if not rows:
        print("\n[INFO] No dispatches are currently awaiting images.\n")
        return

    print(f"\n{'=' * 80}")
    print(f"IRON NORTH: PENDING IMAGE GENERATION BATCH ({len(rows)} ITEMS)")
    print(f"{'=' * 80}\n")

    for r in rows:
        print(f"DROP AS:   ~/iron-engine/data/incoming/{r['topic_id']}.jpg")
        print(f"TOPIC #{r['topic_id']}:  {r['title']}")
        print(f"HEADER:    {r['overlay_text']}")
        print(f"PROMPT:\n{r['image_prompt']}")
        print(f"\n{'-' * 80}\n")

    conn.close()

if __name__ == "__main__":
    list_pending()
