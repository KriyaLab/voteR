# prompt_31.py – FINAL WORKING VERSION (Safe, Schema-Compliant, GUI-Compatible)

import os
import sqlite3
import json
from datetime import datetime
from generate_pitch_deck_pdf_fixed import generate_pitch_deck_pdf

DB_PATH = "voter_data/voter_data.db"
SLOGAN_PATH = "voter_data/pitch_decks/slogans.json"

def get_constituency_code_from_name(name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM constituencies WHERE LOWER(name) = LOWER(?)", (name.lower(),))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def load_candidate_context(constituency_code):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM constituencies WHERE code = ?", (constituency_code,))
    row = cursor.fetchone()
    constituency_name = row[0] if row else "Unknown"

    cursor.execute("SELECT avg_sentiment_score, positive_pct, negative_pct FROM constituency_sentiment WHERE constituency = ?", (constituency_code,))
    sentiment = cursor.fetchone()

    cursor.execute("SELECT issue FROM constituency_issue_sentiment WHERE constituency = ? ORDER BY post_count DESC LIMIT 1", (constituency_name,))
    issue_row = cursor.fetchone()

    cursor.execute("""
        SELECT name, actual_party, caste, religion, age, gender, photo, symbol, swot, education, profession
        FROM candidates
        WHERE LOWER(constituency) = LOWER(?) AND is_opponent = 0
    """, (constituency_name,))
    candidate = cursor.fetchone()

    conn.close()

    if not candidate:
        raise ValueError(f"❌ No candidate found for constituency: {constituency_name}")

    return {
        "constituency_code": constituency_code,
        "constituency_name": constituency_name,
        "candidate_name": candidate[0],
        "party_name": candidate[1],
        "caste": candidate[2],
        "religion": candidate[3],
        "age": candidate[4],
        "gender": candidate[5],
        "photo": candidate[6],
        "symbol": candidate[7],
        "swot": candidate[8],
        "education": candidate[9],
        "profession": candidate[10],
        "issue": issue_row[0] if issue_row else "development",
        "avg_sentiment_score": round(sentiment[0], 2) if sentiment else 0.0,
        "positive_pct": round(sentiment[1]*100, 1) if sentiment else 0.0,
        "negative_pct": round(sentiment[2]*100, 1) if sentiment else 0.0
    }

def load_slogan_for_constituency(name):
    try:
        with open(SLOGAN_PATH, "r") as f:
            data = json.load(f)
        return data.get(name, {}).get("slogan")
    except Exception as e:
        print(f"⚠️ Could not load slogans.json: {e}")
        return None

def show_rationale(ctx, slogan):
    print("\n📊 Pitch Deck Generation: Strategic Rationale\n")
    print(f"🎯 For: **{ctx['candidate_name']}** ({ctx['party_name']}, {ctx['constituency_name']})")
    print(f"🧠 SWOT & Identity → caste: {ctx['caste']}, religion: {ctx['religion']}")
    print(f"📈 Sentiment says top issue is: **{ctx['issue']}**")
    print("👥 Empowerment focus: Women, Youth, BPL families")
    print(f"🪧 Slogan to be used: **{slogan}**")
    print("\n✅ Deck will combine emotion + vision + performance framing.\n")

# === MAIN ===
if __name__ == "__main__":
    constituency = os.environ.get("CONSTITUENCY_NAME", "Mandya")
    if not constituency:
        print("❌ CONSTITUENCY_NAME not provided via environment.")
        exit(1)

    selected_raw = os.environ.get("SELECTED_SLIDES", "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20")
    selected_slides = [s.strip() for s in selected_raw.split(",") if s.strip().isdigit() and 1 <= int(s.strip()) <= 20]
    print(f"📊 Slides selected: {', '.join(selected_slides)}")

    constituency_code = get_constituency_code_from_name(constituency)
    if not constituency_code:
        print(f"❌ Constituency '{constituency}' not found.")
        exit(1)

    ctx = load_candidate_context(constituency_code)
    slogan = load_slogan_for_constituency(ctx["constituency_name"]) or "Your Voice, Your Power, Your Future."

    show_rationale(ctx, slogan)

    rationale_text = f"""📊 Pitch Deck Generation: Strategic Rationale

To craft this deck for **{ctx['candidate_name']}** ({ctx['party_name']}, {ctx['constituency_name']}), we analyzed:
- 🔍 Voter sentiment & top issues: **{ctx['issue']}**
- 🧠 Candidate SWOT & identity: caste={ctx['caste']}, religion={ctx['religion']}
- 👩‍🎓 Empowerment themes for women, youth, and BPL households
- 🪧 Messaging from 101 proven campaign themes

The final pitch deck will:
✅ Position the candidate strongly on emotional + logical grounds
✅ Provide ready-made campaign content for speeches and outreach
✅ Highlight inclusive vision, performance, and slogan-led appeal

🎯 Generating deck now..."""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ✅ Fetch candidate_id using correct column
    cursor.execute("""
        SELECT candidate_id FROM candidates
        WHERE LOWER(name) = LOWER(?) AND LOWER(constituency) = LOWER(?) AND is_opponent = 0
    """, (ctx["candidate_name"], ctx["constituency_name"]))
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"❌ Could not find candidate_id for {ctx['candidate_name']} in {ctx['constituency_name']}")
    candidate_id = row[0]

    # ✅ Delete previous prompt_31 entry for this constituency
    cursor.execute("DELETE FROM prompt_outputs WHERE prompt_id = 31 AND LOWER(constituency) = LOWER(?)", (ctx["constituency_name"].lower(),))

    # ✅ Insert dummy variant + text + rationale to meet schema
    cursor.execute("""
        INSERT INTO prompt_outputs (
            prompt_id, constituency, candidate_id,
            variant_number, generated_text, rationale, created_at, source_script
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        31,
        ctx["constituency_name"],
        candidate_id,
        0,
        "__rationale_only__",
        rationale_text,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "prompt_31.py"
    ))

    conn.commit()
    conn.close()

    print("\n" + rationale_text + "\n")
    print("✅ Generating PDF pitch deck...")

    photo_path = f"voter_data/photos/{ctx['photo']}"
    symbol_path = f"voter_data/symbols/{ctx['symbol'].replace('.png', '_flat.png')}"
    bg_path = "assets/bg_bjp.jpg" if ctx["party_name"].lower() == "bjp" else "assets/bg_congress.jpg"
    footer_text = "Bharat Mata Ki Jai" if ctx["party_name"].lower() == "bjp" else "Jai Hind, Jai Jawan, Jai Kisan"
    theme_color = "#F26522" if ctx["party_name"].lower() == "bjp" else "#2E7D32"

    date_tag = datetime.now().strftime("%Y%m%d")
    candidate_slug = ctx["candidate_name"].lower().replace(" ", "_")
    constituency_slug = ctx["constituency_name"].lower().replace(" ", "_")
    output_file = f"voter_data/pitch_decks/pd_{candidate_slug}_{constituency_slug}_{date_tag}.pdf"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    generate_pitch_deck_pdf(
        output_path=output_file,
        candidate_name=ctx["candidate_name"],
        constituency_name=ctx["constituency_name"],
        party_name=ctx["party_name"],
        top_issue=ctx["issue"],
        swot=ctx["swot"],
        caste=ctx["caste"],
        religion=ctx["religion"],
        age=ctx["age"],
        gender=ctx["gender"],
        education=ctx["education"],
        profession=ctx["profession"],
        photo_path=photo_path,
        symbol_path=symbol_path,
        background_path=bg_path,
        footer_text=footer_text,
        theme_color=theme_color,
        slogan_text=slogan,
        selected_slides=selected_slides
    )

    print(f"\n✅ Pitch deck saved to {output_file}")

