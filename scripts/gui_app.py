import streamlit as st
import sqlite3
import os
import glob
import time
from datetime import datetime

DB_PATH = "voter_data/voter_data.db"

# === Custom Styling ===
st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    .stRadio > div { padding: 5px 0; }
    .stButton > button { margin-top: 10px; }
    .stDownloadButton > button {
        background-color: #0a2540;
        color: white;
    }
    .stExpander { background-color: #f5f5f5; padding: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# === Shared DB Helpers ===
def get_constituencies():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT name FROM constituencies ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_prompt_variants(prompt_id, constituency):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT variant_number, generated_text FROM prompt_outputs
        WHERE prompt_id = ? AND LOWER(constituency) = LOWER(?)
        ORDER BY variant_number
    """, (prompt_id, constituency.lower()))
    variants = cursor.fetchall()
    conn.close()
    return variants

def get_prompt_rationale(prompt_id, constituency):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT rationale FROM prompt_outputs
        WHERE prompt_id = ? AND LOWER(constituency) = LOWER(?)
        ORDER BY created_at DESC LIMIT 1
    """, (prompt_id, constituency.lower()))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

# === Streamlit App ===
st.set_page_config(page_title="voteR - AI Political Toolkit", layout="wide")
st.title("\U0001F5F3 voteR — AI Political Analysis Engine")

tab1, tab2, tab3 = st.tabs(["\U0001F4E3 Sentimental", "\U0001F464 Voter Enrich", "\U0001F4CA Strategy Tools"])

# === TAB 1 ===
with tab1:
    st.subheader("\U0001F4E3 Sentimental")
    constituency = st.selectbox("Select Constituency", get_constituencies(), key="campaign_constituency")
    use_identity = st.toggle("Include Caste & Religion in Messaging", value=False)

    campaign_prompts = [
        (1, "Campaign Flyer (PDF)"),
        (2, "Local Issue Messaging"),
        (3, "Youth & Jobs Appeal"),
        (4, "Call to Action to Vote"),
        (5, "Rebuttal to Opponent"),
        (6, "Slogan Generator"),
        (7, "First-Time Voter Appeal"),
        (8, "Gender Equality Messaging"),
        (9, "Rural Development Messaging"),
        (10, "Infrastructure & Growth Push")
    ]

    selected_campaign = st.selectbox("Choose Campaign Asset to Generate", campaign_prompts, format_func=lambda x: f"{x[0]}. {x[1]}")
    prompt_id = selected_campaign[0]

    if st.button("\U0001F680 Generate Asset"):
        os.environ['CONSTITUENCY_NAME'] = constituency
        os.environ['USE_IDENTITY_TAGS'] = 'y' if use_identity else 'n'
        os.environ['VARIANT_CHOICE'] = 'r'
        os.system(f"python3 prompt_{prompt_id}.py")
        st.rerun()

    rationale = get_prompt_rationale(prompt_id, constituency)
    variants = get_prompt_variants(prompt_id, constituency)

    if rationale:
        st.markdown(f"### \U0001F9E0 Rationale:\n{rationale}")

    if variants:
        st.markdown("### ✨ Choose your preferred flyer variant:")
        variant_map = {f"{v[0]}. {v[1][:500].replace('\n', ' ')}": v[0] for v in variants}
        refresh_key = f"variant_select_{prompt_id}_{constituency}_{len(variants)}_{int(time.time() // 60)}"
        selected_label = st.radio("Select a variant", list(variant_map.keys()), key=refresh_key)
        selected_variant = variant_map[selected_label]

        if st.button("♻️ Regenerate Variants"):
            os.environ['CONSTITUENCY_NAME'] = constituency
            os.environ['USE_IDENTITY_TAGS'] = 'y' if use_identity else 'n'
            os.environ['VARIANT_CHOICE'] = 'r'
            os.system(f"python3 prompt_{prompt_id}.py")
            st.rerun()

        if st.button("\U0001F4C4 Export PDF" if prompt_id == 1 else "\u2705 Finalize Variant"):
            os.environ['CONSTITUENCY_NAME'] = constituency
            os.environ['USE_IDENTITY_TAGS'] = 'y' if use_identity else 'n'
            os.environ['VARIANT_CHOICE'] = str(selected_variant)
            os.system(f"python3 prompt_{prompt_id}.py")
            st.success("✅ Variant finalized and saved.")

            if prompt_id == 1:
                flyer_files = glob.glob(f"voter_data/flyers/flyer_*{constituency.lower()}*.pdf")
                flyer_files.sort(reverse=True)
                if flyer_files:
                    with open(flyer_files[0], "rb") as f:
                        st.download_button("\U0001F4E5 Download Flyer", data=f, file_name=os.path.basename(flyer_files[0]), mime="application/pdf")

# === TAB 2 ===
with tab2:
    st.subheader("\U0001F464 Voter Enrich")
    voter_id = st.text_input("Enter Voter ID", value="", help="Enter full Voter ID (e.g., KA123456)")

    diagnostic_prompts = [
        (11, "Voter Profile Summary"),
        (12, "Caste-Religion Analysis"),
        (13, "Education & Profession Analysis"),
        (14, "Language & Location Insights"),
        (15, "Political Inclination Breakdown"),
        (16, "Influence Estimation"),
        (17, "Sentiment Polarity from Posts"),
        (18, "Group Admin & Follower Activity"),
        (19, "Family Network Influence"),
        (20, "Booth-Level Demographics"),
        (21, "Voting Pattern Likelihood (Model-Based)")
    ]

    selected_diag = st.selectbox("Choose Diagnostic Tool", diagnostic_prompts, format_func=lambda x: f"{x[0]}. {x[1]}")
    diag_id = selected_diag[0]

    if st.button("\U0001F4AC Generate Insight"):
        os.environ['VOTER_ID'] = voter_id
        result = os.popen(f"python3 prompt_{diag_id}.py").read()
        with st.expander("View Output"):
            st.code(result)

# === TAB 3 ===
with tab3:
    st.subheader("📊 Strategy Tools (Constituency Level)")
    constituency = st.selectbox("Select Constituency", get_constituencies(), key="strategy_constituency")

    strategy_prompts = [
        (22, "Top Influencers in Constituency"),
        (23, "Candidate SWOT using Sentiment"),
        (24, "Top Issues"),
        (25, "Opponent Influence Summary"),
        (26, "Top Influencers "),
        (27, "Boothwise Influencers"),
        (28, "Swing Booths"),
        (29, "SM Buzz Areas"),
        (30, "Trend on Healthcare"),
        (31, "Pitch Deck Generator (PDF)"),
        (32, "Campaign Video Generator (MP4)")
    ]

    selected_strategy = st.selectbox("Choose Strategy Tool", strategy_prompts, format_func=lambda x: f"{x[0]}. {x[1]}")
    strategy_id = selected_strategy[0]

    # Slide selection UI for Prompt 31
    if strategy_id == 31:
        st.markdown("#### 🎯 Select Slides to Include in the Pitch Deck")
        slide_options = [
            (1, "Cover with Slogan & Symbol"),
            (2, "Who Am I?"),
            (3, "Top Priority"),
            (4, "Vision for the Future"),
            (5, "Jobs & Youth"),
            (6, "Women First"),
            (7, "Support for Vulnerable"),
            (8, "Why Me?"),
            (9, "Vote Appeal"),
            (10, "Electoral History"),
            (11, "Reputation (SWOT)"),
            (12, "Public Quotes"),
            (13, "Digital Campaign Reach"),
            (14, "Sentiment Overview"),
            (15, "9 Key Promises"),
            (16, "Campaign Timeline"),
            (17, "Brand Framework"),
            (18, "Candidate Profile"),
            (19, "Final Slogan + Contact"),
            (20, "Thank You Slide")
        ]
        slide_dict = {f"{sid}. {title}": str(sid) for sid, title in slide_options}

        select_all = st.checkbox("✅ Select All Slides", value=True)
        selected_slide_labels = list(slide_dict.keys()) if select_all else st.multiselect(
            "Pick slides to include", options=list(slide_dict.keys()), default=list(slide_dict.keys())[:10]
        )
        selected_slide_ids = [slide_dict[label] for label in selected_slide_labels]

    if st.button("📋 Generate Asset"):
        os.environ['CONSTITUENCY_NAME'] = constituency
        os.environ['VARIANT_CHOICE'] = 'r'
        if strategy_id == 31:
            os.environ['SELECTED_SLIDES'] = ",".join(selected_slide_ids)

        if strategy_id in [31, 32]:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM candidates WHERE LOWER(constituency) = LOWER(?) AND is_opponent = 0 LIMIT 1", (constituency.lower(),))
            row = cursor.fetchone()
            os.environ['CANDIDATE_NAME'] = row[0] if row else "unknown"

        # ✅ Show rationale block for Prompt 31
        if strategy_id == 31:
            rationale = get_prompt_rationale(31, constituency)
            if rationale:
                st.markdown(f"### 🧠 Rationale:\n{rationale}")

        output = os.popen(f"python3 prompt_{strategy_id}.py").read()
        st.markdown("### 🧠 Output:")
        st.code(output)

        if strategy_id == 31:
            constituency_slug = constituency.lower().replace(" ", "_")
            files = glob.glob(f"voter_data/pitch_decks/pd_*_{constituency_slug}_*.pdf")
            files.sort(reverse=True)
            
            if files:
                with open(files[0], "rb") as f:
                    st.download_button("📥 Download Pitch Deck", data=f, file_name=os.path.basename(files[0]), mime="application/pdf")

        elif strategy_id == 32:
            files = glob.glob("voter_data/videos/cv_*.mp4")
            files.sort(reverse=True)
            if files:
                with open(files[0], "rb") as f:
                    st.download_button("🎬 Download Campaign Video", data=f, file_name=os.path.basename(files[0]), mime="video/mp4")


# === Bilingual Disclaimer Footer ===
st.markdown("---")
st.markdown("""
<p style='font-size: 12px; color: black; text-align: center;'>
<b>Disclaimer:</b><br>
This demonstration uses simulated data for illustrative purposes only.<br>
No real candidate, party, or voter information has been used.<br>
The system can be customized with actual data under formal engagement and compliance review.
</p>

<p style='font-size: 12px; color: black; text-align: center;'>
<b>ಜವಾಬ್ದಾರಿಯ ನಿರಾಕರಣೆ (Disclaimer):</b><br>
ಈ ಪ್ರదర్శನೆ ಮಾತ್ರ ಚಿತ್ರಣ ಉದ್ದೇಶಕ್ಕಾಗಿ ಸಂಯೋಜಿತ ಡೇಟಾವನ್ನು ಬಳಸುತ್ತದೆ.<br>
ಯಾವುದೇ ನಿಜವಾದ ಅಭ್ಯರ್ಥಿ, ಪಕ್ಷ ಅಥವಾ ಮತದಾರರ ಮಾಹಿತಿಯನ್ನು ಬಳಸಲಾಗಿಲ್ಲ.<br>
ನೈಜ ಡೇಟಾವನ್ನು ಬಳಸಿ ವೈಯಕ್ತಿಕೀಕೃತ ಪದ್ದತಿಗೆ, ಒಪ್ಪಂದದ ಆಧಾರದ ಮೇಲೆ ವ್ಯವಸ್ಥೆ ರೂಪಿಸಬಹುದು.
</p>
""", unsafe_allow_html=True)
