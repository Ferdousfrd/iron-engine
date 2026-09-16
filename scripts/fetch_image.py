#!/usr/bin/env python3
"""
Module: fetch_image.py
Description: Generates authentic visual assets for dispatches using Hugging Face FLUX.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

CONFIG_PATH = os.path.expanduser("~/iron-engine/config/.env")
load_dotenv(CONFIG_PATH)

RAW_DIR = os.path.expanduser("~/iron-engine/data/raw")
os.makedirs(RAW_DIR, exist_ok=True)

def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def fetch_target_dispatch():
    conn = get_db()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT id, image_prompt 
            FROM dispatches 
            WHERE status = 'pending'
            ORDER BY created_at DESC 
            LIMIT 1;
        """)
        row = cur.fetchone()
        
        if not row:
            cur.execute("""
                SELECT id, image_prompt 
                FROM dispatches 
                ORDER BY created_at DESC 
                LIMIT 1;
            """)
            row = cur.fetchone()
    conn.close()
    return row

def generate_visual_hf(prompt: str, output_file: str) -> bool:
    token = os.getenv("HF_TOKEN")
    if not token:
        print("[ERROR] HF_TOKEN missing in environment configuration.")
        return False

    print("[INFO] Querying Hugging Face FLUX.1-schnell...")
    try:
        client = InferenceClient(token=token)
        image = client.text_to_image(
            prompt=prompt,
            model="black-forest-labs/FLUX.1-schnell"
        )
        image.save(output_file, quality=95)
        print(f"[SUCCESS] High-fidelity render written to: {output_file}")
        return True
    except Exception as e:
        print(f"[ERROR] Hugging Face inference failed: {e}")
        return False

if __name__ == "__main__":
    record = fetch_target_dispatch()
    if not record:
        print("[NOTICE] No dispatches found to process.")
        sys.exit(0)

    dispatch_id = str(record["id"])
    dest_path = os.path.join(RAW_DIR, f"{dispatch_id}_raw.jpg")

    print(f"[GENERATE] Processing visual for Dispatch UUID: {dispatch_id}...")
    success = generate_visual_hf(record["image_prompt"], dest_path)
    if not success:
        sys.exit(1)
