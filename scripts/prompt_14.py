import sqlite3
import yaml

DB_PATH = "voter_data/voter_data.db"
PROMPT_ID = 14

def detect_political_inclination(voter_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get from enriched table
    cursor.execute("SELECT name, constituency, political_inclination FROM voter_enriched_demo WHERE voter_id = ?", (voter_id,))
    row = cursor.fetchone()

    if not row:
        print("❌ No data found for that EPIC No (voter_id).")
        return

    name, constituency, inclination = row

    # Optional fallback to social_posts hashtags
    cursor.execute("SELECT hashtags FROM social_posts WHERE voter_id = ?", (voter_id,))
    post_row = cursor.fetchone()
    hashtags = post_row[0] if post_row else ""

    # Decide label
    leaning = inclination if inclination else "Undeclared / Neutral"

    output = {
        "Name": name,
        "Constituency": constituency,
        "Political Inclination": leaning,
        "Hashtags (if any)": hashtags
    }

    rationale = (
        f"Political inclination was extracted from voter enrichment. "
        f"{'Hashtag activity in social posts supported this leaning.' if hashtags else 'No public hashtags found.'}"
    )

    print("\n🗳️ Political Inclination Detection:\n")
    print(yaml.dump(output, allow_unicode=True))
    print("🧠 Rationale:\n" + rationale)

if __name__ == "__main__":
# PATCH START
    import os
    voter_id = os.getenv('VOTER_ID')
    if not voter_id:
        voter_id = voter_id = input("🔍 Enter EPIC No (voter_id): ").strip()
# PATCH END
    detect_political_inclination(voter_id)

