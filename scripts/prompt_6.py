# prompt_6.py — Slogan Generator from pool (GUI-Safe, CPU-Efficient)

import sqlite3
import json
import random
import os
from datetime import datetime
from difflib import SequenceMatcher

DB_PATH = "voter_data/voter_data.db"
SLOGAN_FILE = "voter_data/slogan_pool.json"
PROMPT_ID = 6
THEME = "Slogan Generator"

def get_constituency_code(name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM constituencies WHERE LOWER(name) = LOWER(?)", (name.lower(),))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def load_context(code):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM constituencies WHERE code = ?", (code,))
    cname = cursor.fetchone()[0]

    cursor.execute("SELECT candidate_id, name, actual_party, caste, religion FROM candidates WHERE constituency = ?", (cname,))
    candidate = cursor.fetchone()

    cursor.execute("SELECT issue FROM constituency_issue_sentiment WHERE constituency = ? ORDER BY post_count DESC LIMIT 1", (code,))
    issue = cursor.fetchone()
    conn.close()

    return {
        "candidate_id": candidate[0],
        "constituency": cname,
        "candidate_name": candidate[1] if candidate else "Candidate X",
        "party": candidate[2] if candidate else "Party X",
        "caste": candidate[3] if candidate else "General",
        "religion": candidate[4] if candidate else "Hindu",
        "top_issue": issue[0] if issue else "development"
    }

def load_slogan_pool():
    with open(SLOGAN_FILE, "r") as f:
        return json.load(f)

def is_similar(s1, s2, threshold=0.6):
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio() > threshold

def pick_unique_slogans(pool, count=3):
    selected = []
    attempts = 0
    while len(selected) < count and attempts < 100:
        s_dict = random.choice(pool)
        slogan = s_dict.get("text", "").strip()
        if slogan and all(not is_similar(slogan, exist) for exist in selected):
            selected.append(slogan)
        attempts += 1
    return selected

# === MAIN ===
if __name__ == "__main__":
    constituency = os.environ.get("CONSTITUENCY_NAME", "Mandya").strip()
    choice = os.environ.get("VARIANT_CHOICE", "r").strip().lower()

    if choice not in ["1", "2", "3", "r"]:
        print("❌ Invalid VARIANT_CHOICE")
        exit(1)

    code = get_constituency_code(constituency)
    if not code:
        print(f"❌ Constituency '{constituency}' not found.")
        exit(1)

    ctx = load_context(code)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rationale = f"Slogans selected from curated pool based on uniqueness and top issue: {ctx['top_issue']}."

    slogan_pool = load_slogan_pool()

    if choice == "r":
        print("🔁 Generating 3 slogans from pool...")
        slogans = pick_unique_slogans(slogan_pool, count=3)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM prompt_outputs WHERE prompt_id = ? AND LOWER(constituency) = LOWER(?)", (PROMPT_ID, constituency.lower()))
        for i, slogan in enumerate(slogans, 1):
            print(f"\n📝 Variant {i}: {slogan}\n")
            cursor.execute("""
                INSERT INTO prompt_outputs (prompt_id, candidate_id, constituency, theme, variant_number,
                    generated_text, created_at, source_script, rationale)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                PROMPT_ID,
                ctx["candidate_id"],
                ctx["constituency"],
                THEME,
                i,
                slogan,
                now,
                "prompt_6.py",
                rationale
            ))
        conn.commit()
        conn.close()
        print("✅ Slogans stored in DB.")
        exit(0)

    # Finalize: fetch selected slogan
    index = int(choice)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT generated_text FROM prompt_outputs
        WHERE prompt_id = ? AND LOWER(constituency) = LOWER(?) AND variant_number = ?
        LIMIT 1
    """, (PROMPT_ID, constituency.lower(), index))
    row = cursor.fetchone()

    if not row:
        print("❌ Variant not found. Run with VARIANT_CHOICE='r' first.")
        exit(1)

    final_text = row[0]

    # Reinsert final selection
    cursor.execute("DELETE FROM prompt_outputs WHERE prompt_id = ? AND LOWER(constituency) = LOWER(?) AND variant_number = ?", (PROMPT_ID, constituency.lower(), index))
    cursor.execute("""
        INSERT INTO prompt_outputs (prompt_id, candidate_id, constituency, theme, variant_number,
            generated_text, created_at, source_script, rationale)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        PROMPT_ID,
        ctx["candidate_id"],
        ctx["constituency"],
        THEME,
        index,
        final_text,
        now,
        "prompt_6.py",
        rationale
    ))
    conn.commit()
    conn.close()

    print("✅ Finalized successfully.")

