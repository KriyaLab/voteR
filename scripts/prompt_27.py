
if __name__ == '__main__':
    # prompt_27.py — Heatmap of top influencer zones with detailed info
    import sqlite3
    from datetime import datetime
    from common import get_context, db_connect, clear_prompt_output
    
    PROMPT_ID = 27
    SCRIPT_NAME = 'prompt_27.py'
    THEME = 'Constituency Intelligence'
    TITLE = 'Heatmap of top influencer zones'
    MENU_LABEL = 'Influencer Heatmap'
    CLI_ORDER = 27
    
    # 🔌 DB + Context
    ctx = get_context()
    constituency = ctx["constituency_name"]
    conn, cursor = db_connect()
    clear_prompt_output(cursor, PROMPT_ID, ctx["constituency_name"])
    
    # 🎯 Input
    #conn = sqlite3.connect("voter_data/voter_data.db")
    #cursor = conn.cursor()
    
    # 🧹 Clean old output
    #cursor.execute("DELETE FROM prompt_outputs WHERE prompt_id = ?", (PROMPT_ID,))
    
    # 🔍 Top influencer booths by followers
    cursor.execute("""
    SELECT booth_location, COUNT(*) AS influencer_count, SUM(followers_estimated) AS total_followers
    FROM voter_enriched_demo
    WHERE LOWER(constituency) = LOWER(?)
      AND is_group_admin = 1
    GROUP BY booth_location
    ORDER BY total_followers DESC
    LIMIT 10
    """, (constituency,))
    
    rows = cursor.fetchall()
    if not rows:
        print("❌ No influencer data found for this constituency.")
        exit()
    
    output = f"📍 Top Influencer Booths in {constituency}\n\n"
    for booth, count, total in rows:
        booth_name = booth if booth else "Local Outreach Center"
        output += f"• Booth: {booth_name} — {count} influencers, {total} followers\n"
    
        # 🎯 Detailed influencer list
        cursor.execute("""
        SELECT voter_id, name, followers_estimated, political_inclination
        FROM voter_enriched_demo
        WHERE LOWER(constituency) = LOWER(?)
          AND is_group_admin = 1
          AND booth_location = ?
        ORDER BY followers_estimated DESC
        LIMIT 10
        """, (constituency, booth))
    
        influencers = cursor.fetchall()
        for voter_id, name, followers, inclination in influencers:
            label = inclination if inclination else "Neutral"
    print("\n📊 Influencer Heatmap:\n")
    print(output)
    
    # 💾 Save to prompt_outputs
    cursor.execute("""
    INSERT INTO prompt_outputs
    (prompt_id, candidate_id, constituency, theme, variant_number, generated_text, created_at, source_script, rationale)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        PROMPT_ID,
        'influencer_heatmap',
        constituency,
        THEME,
        1,
        output,
        datetime.now().isoformat(timespec='seconds'),
        SCRIPT_NAME,
        "Top influencer booths with voter_id, follower count, and political inclination"
    ))
    
    conn.commit()
    conn.close()
    
    print("\n📊 Influencer Heatmap:\n")
    print(output)
