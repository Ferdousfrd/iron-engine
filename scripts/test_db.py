#!/usr/bin/env python3
"""
Module: test_db.py
Description: Validates database connectivity, queries unprocessed topics,
             and prints structured output using psycopg2.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# 1. Load environment configuration from config/.env
CONFIG_PATH = os.path.expanduser("~/iron-engine/config/.env")
if not os.path.exists(CONFIG_PATH):
    print(f"[ERROR] Missing configuration file at: {CONFIG_PATH}")
    sys.exit(1)

load_dotenv(CONFIG_PATH)

def get_db_connection():
    """Establishes and returns a connection to the PostgreSQL database."""
    try:
        connection = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        return connection
    except psycopg2.OperationalError as err:
        print(f"[CRITICAL] Database connection failed: {err}")
        sys.exit(1)

def fetch_pending_topics():
    """Queries all records from 'topics' where is_processed is FALSE."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT id, title, year_event, region, core_conflict
        FROM topics
        WHERE is_processed = FALSE
        ORDER BY id ASC;
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    # Free up socket and connection resources
    cursor.close()
    conn.close()
    return rows

if __name__ == "__main__":
    print("[INFO] Attempting connection to PostgreSQL...")
    topics = fetch_pending_topics()
    
    print(f"[SUCCESS] Connected! Found {len(topics)} pending topics in database:\n")
    for topic in topics:
        print(f"  • ID {topic['id']}: {topic['title']} ({topic['year_event']}) - {topic['region']}")
        print(f"    Summary: {topic['core_conflict']}\n")
