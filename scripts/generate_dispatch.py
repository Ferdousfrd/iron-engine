#!/usr/bin/env python3
"""
Module: generate_dispatch.py
Description: Ingests unprocessed topics from PostgreSQL, generates structured 
             social dispatches via Groq (Llama 3.3), validates the payload 
             with Pydantic, and records the output to PostgreSQL.
"""

import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv
from groq import Groq

# ---------------- CONFIGURATION & CLIENT INITIALIZATION ----------------
CONFIG_PATH = os.path.expanduser("~/iron-engine/config/.env")
if not os.path.exists(CONFIG_PATH):
    print(f"[CRITICAL] Missing configuration at {CONFIG_PATH}")
    sys.exit(1)

load_dotenv(CONFIG_PATH)

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key or groq_api_key.startswith("gsk_your_actual"):
    print("[CRITICAL] Please set a valid GROQ_API_KEY in ~/iron-engine/config/.env")
    sys.exit(1)

client = Groq(api_key=groq_api_key)

# ---------------- PYDANTIC CONTRACT ----------------
class DispatchContent(BaseModel):
    overlay_header: str = Field(
        ...,
        description="A punchy, capitalized summary/punchline for the image footer (max 25 words)."
    )
    caption_body: str = Field(
        ...,
        description="A gripping, historically accurate story (150-220 words) with narrative tension and a closing question."
    )
    image_prompt: str = Field(
        ...,
        description="A photorealistic, cinematic visual prompt describing warriors, gear, environment, and weather."
    )

# ---------------- DATABASE OPERATIONS ----------------
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def fetch_next_topic(conn):
    """Safely retrieves the next pending topic using row-level locking."""
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        query = """
            SELECT id, title, year_event, region, core_conflict
            FROM topics
            WHERE is_processed = FALSE
            ORDER BY id ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED;
        """
        cursor.execute(query)
        return cursor.fetchone()

# ---------------- LLM GENERATION ----------------
def generate_dispatch_payload(topic: dict) -> DispatchContent:
    """Prompts Llama 3 on Groq and validates the output strictly via Pydantic."""
    system_prompt = (
        "You are an expert military historian and content director for 'Iron North'. "
        "Create historically authentic, gritty, and engaging social posts. "
        "You must respond ONLY with a raw JSON object containing these exact keys: "
        "'overlay_header', 'caption_body', and 'image_prompt'. Do not include markdown code blocks."
    )

    user_prompt = f"""
    EVENT: {topic['title']} ({topic['year_event']})
    REGION: {topic['region']}
    HISTORICAL CONTEXT: {topic['core_conflict']}

    Instructions:
    1. overlay_header: In ALL-CAPS, summarize the historic punchline for an image footer (max 25 words).
    2. caption_body: Write a compelling 150-200 word story detailing the strategic clash, tactical reality, and finish with an open question prompting reader debate.
    3. image_prompt: A hyper-detailed visual prompt for an image generator. Detail accurate Norse/regional arms, armor, lighting, muddy or stormy atmosphere, cinematic 4:5 ratio.
    """

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        model="openai/gpt-oss-120b",
        temperature=0.7,
        response_format={"type": "json_object"}
    )

    raw_json = chat_completion.choices[0].message.content
    parsed_dict = json.loads(raw_json)
    
    # Validate dictionary against our Pydantic schema
    return DispatchContent(**parsed_dict)

def commit_dispatch(conn, topic_id: int, dispatch: DispatchContent):
    """Inserts the dispatch and updates the topic status in one atomic transaction."""
    with conn.cursor() as cursor:
        insert_sql = """
            INSERT INTO dispatches (topic_id, overlay_text, caption_body, image_prompt, status)
            VALUES (%s, %s, %s, %s, 'pending')
            RETURNING id;
        """
        cursor.execute(
            insert_sql,
            (topic_id, dispatch.overlay_header, dispatch.caption_body, dispatch.image_prompt)
        )
        dispatch_id = cursor.fetchone()[0]

        update_sql = """
            UPDATE topics
            SET is_processed = TRUE
            WHERE id = %s;
        """
        cursor.execute(update_sql, (topic_id,))

        conn.commit()
        return dispatch_id

# ---------------- MAIN RUNTIME ----------------
if __name__ == "__main__":
    conn = get_db_connection()
    print("[INFO] Checking for pending topics...")

    try:
        topic = fetch_next_topic(conn)
        if not topic:
            print("[NOTICE] No pending topics found. Run an insert to add more.")
            sys.exit(0)

        print(f"[PROCESS] Processing Topic #{topic['id']}: '{topic['title']}'...")
        dispatch = generate_dispatch_payload(topic)

        print("\n[VALIDATION SUCCESS] Pydantic validated output:")
        print(f"  • OVERLAY HEADER: {dispatch.overlay_header}")
        print(f"  • IMAGE PROMPT  : {dispatch.image_prompt[:90]}...")
        print(f"  • CAPTION LEAD  : {dispatch.caption_body[:100]}...\n")

        new_uuid = commit_dispatch(conn, topic['id'], dispatch)
        print(f"[DB SUCCESS] Saved dispatch with UUID: {new_uuid}")
        print(f"[DB SUCCESS] Marked Topic #{topic['id']} as processed.")

    except ValidationError as ve:
        conn.rollback()
        print(f"[VALIDATION FAILED] Schema error: {ve}")
    except Exception as e:
        conn.rollback()
        print(f"[CRITICAL ERROR] Pipeline failed: {e}")
    finally:
        conn.close()
