# prompt_4.py — Call to Action to Vote (GUI-Safe, CPU-Efficient)

import sqlite3
import os
from datetime import datetime
from kalpana_llm_bridge import call_llama

DB_PATH = "voter_data/voter_data.db"
PROMPT_ID = 4
THEME = "Call to Vote"

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
    constituency = cursor.fetchone()[0]

    cursor.execute("SELECT avg_sentiment_score, positive_pct, negative_pct FROM constituency_sentiment WHERE constituency = ?", (code,))
    sentiment = cursor.fetchone()

    cursor.execute("SELECT candidate_id, name, actual_party, swot FROM candidates WHERE constituency = ?", (constituency,))
    candidate = cursor.fetchone()
    conn.close()

    return {
        "candidate_id": candidate[0],
        "constituency": constituency,
        "candidate_name": candidate[1] if candidate else "Candidate X",
        "party_name": candidate[2] if candidate else "Party X",
        "swot": candidate[3] if candidate else "Trusted and visionary.",
        "sentiment": f"{round(sentiment[0], 3)} ({round(sentiment[1] * 100, 1)}% 👍, {round(sentiment[2] * 100, 1)}% 👎)" if sentiment else "Neutral"
    }

def render_prompt(ctx):
    return f"""
Write a motivating call-to-action campaign message for voters in {ctx['constituency']}.
It should inspire them to vote and support {ctx['candidate_name']} from {ctx['party_name']}.
Use the following format:
- Campaign Slogan
- 3–4 line paragraph
- 3 bullet points (why voting matters)
- Powerful closing vote appeal
Candidate SWOT: {ctx['swot']}
Sentiment: {ctx['sentiment']}
"""

def clean(text):
    return "\n".join([line.strip() for line in text.strip().splitlines() if line.strip()])

# === MAIN ===
if __name__ == "__main__":
    constituency = os.environ.get("CONSTITUENCY_NAME", "Mandya").strip()
    choice = os.environ.get("VARIANT_CHOICE", "r").strip().lower()

    if choice not in ["1", "2", "3", "r"]:
        print("❌ Invalid VARIANT_CHOICE")
        exit(1)

    code = get_constituency_code(constituency)
    if not code:
        print(f"❌ Invalid constituency: {constituency}")
        exit(1)

    ctx = load_context(code)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rationale = (
        f"Call to action for voters in {ctx['constituency']} — urging participation and civic duty. "
        f"Sentiment: {ctx['sentiment']}. SWOT: {ctx['swot']}."
    )

    if choice == "r":
        print("🔁 Generating 3 voter appeal variants...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM prompt_outputs WHERE prompt_id = ? AND LOWER(constituency) = LOWER(?)", (PROMPT_ID, constituency.lower()))

        for i in range(3):
            prompt = render_prompt(ctx)
            raw = call_llama(prompt)
            cleaned = clean(raw)
            print(f"\n📝 Variant {i+1} generated.\n")
            cursor.execute("""
                INSERT INTO prompt_outputs (prompt_id, candidate_id, constituency, theme, variant_number,
                    generated_text, created_at, source_script, rationale)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                PROMPT_ID,
                ctx["candidate_id"],
                ctx["constituency"],
                THEME,
                i + 1,
                cleaned,
                now,
                "prompt_4.py",
                rationale
            ))
        conn.commit()
        conn.close()
        print("✅ Variants stored in DB.")
        exit(0)

    # Finalize: fetch selected variant from DB
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

    # Optional reconfirmation insert
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
        "prompt_4.py",
        rationale
    ))
    conn.commit()
    conn.close()

    print("✅ Finalized successfully.")

