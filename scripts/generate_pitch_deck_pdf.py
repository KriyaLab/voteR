from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF
import os
import sqlite3

DB_PATH = "voter_data/voter_data.db"

def generate_pitch_deck_pdf(
    output_path,
    candidate_name,
    constituency_name,
    party_name,
    swot,
    caste,
    religion,
    age,
    gender,
    education,
    profession,
    photo_path,
    symbol_path,
    background_path,
    footer_text,
    theme_color,
    top_issue=None,
    slogan_text=None,
    selected_slides=None
):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    selected_slides = set(selected_slides or [])

    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))

    rgb = hex_to_rgb(theme_color)

    def draw_footer():
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.black)
        c.drawCentredString(width / 2.0, 0.5 * inch, footer_text)

    def draw_bottom_color_bar():
        c.setFillColorRGB(*rgb)
        c.rect(0, 0.75 * inch, width, 3, stroke=0, fill=1)

    def draw_shadowed_title(text, y):
        c.setFont("Helvetica-Bold", 22)
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.drawCentredString(width / 2 + 1, y - 1, text)
        c.setFillColor(colors.black)
        c.drawCentredString(width / 2, y, text)

    content_style = ParagraphStyle(name='content', fontSize=14, textColor=colors.black, leading=20)

    def draw_slide(title, text, source_note=None):
        c.showPage()
        draw_footer()
        draw_bottom_color_bar()
        draw_shadowed_title(title, height - 1.3 * inch)
        frame = Frame(inch, 1.2 * inch, width - 2 * inch, height - 3 * inch, showBoundary=0)
        elements = [Paragraph(text, content_style)]
        frame.addFromList(elements, c)
        if source_note:
            c.setFont("Helvetica-Oblique", 8)
            c.setFillColor(colors.grey)
            c.drawCentredString(width / 2.0, 1.05 * inch, f"*{source_note}")

    def draw_bar_chart(title, labels, values):
        d = Drawing(480, 300)
        bc = VerticalBarChart()
        bc.x = 50
        bc.y = 50
        bc.height = 200
        bc.width = 400
        bc.data = [values]
        bc.categoryAxis.categoryNames = labels
        bc.barWidth = 20
        bc.groupSpacing = 10
        bc.barSpacing = 5
        bc.valueAxis.valueMin = 0
        bc.valueAxis.valueMax = max(values + [100])
        bc.valueAxis.valueStep = int(bc.valueAxis.valueMax / 5)
        d.add(bc)
        d.add(String(180, 270, title, fontSize=14))
        c.showPage()
        draw_footer()
        draw_bottom_color_bar()
        renderPDF.draw(d, c, inch, 1.5 * inch)
    
    def draw_pie_chart(title, pos_pct, neg_pct):
        c.showPage()
        draw_footer()
        draw_bottom_color_bar()

        # Heading above chart
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2.0, height - 1.2 * inch, title)

        # Pie chart setup
        d = Drawing(300, 300)
        pie = Pie()
        pie.x = 100  # center pie inside Drawing
        pie.y = 50
        pie.width = 150
        pie.height = 150
        pie.data = [pos_pct, neg_pct, max(0, 100 - pos_pct - neg_pct)]
        pie.labels = ['Positive', 'Negative', 'Neutral']
        pie.slices.strokeWidth = 0.5
        pie.slices[0].fillColor = colors.green
        pie.slices[1].fillColor = colors.red
        pie.slices[2].fillColor = colors.lightgrey
        d.add(pie)

        # Draw centered on page
        x_offset = (width - 300) / 2
        y_offset = (height - 300) / 2.5
        renderPDF.draw(d, c, x_offset, y_offset)


    # Slide 1: Cover
    if '1' in selected_slides:
        if os.path.exists(photo_path):
            c.drawImage(photo_path, width/2 - 2*inch, height/2 - 1.5*inch, width=4*inch, height=4*inch, preserveAspectRatio=True)
        if os.path.exists(symbol_path):
            c.setFillColor(colors.white)
            c.rect(width - 1.52 * inch, height - 1.52 * inch, 1.14 * inch, 1.14 * inch, fill=True, stroke=False)
            c.drawImage(symbol_path, width - 1.5*inch, height - 1.5*inch, width=1.1*inch, height=1.1*inch)
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(colors.black)
        c.drawCentredString(width/2.0, height/2 - 2.2*inch, slogan_text or "Your Voice, Your Power, Your Future.")
        draw_footer()
        draw_bottom_color_bar()

    # Slides 2–9: Identity, Vision, Youth, Women, Vulnerable, etc.
    if '2' in selected_slides:
        draw_slide("Who Am I?", f"""
        <b>{candidate_name}</b> is contesting from <b>{constituency_name}</b> as a proud member of the <b>{party_name}</b>.<br/>
        Identity: Caste – <b>{caste}</b>, Religion – <b>{religion}</b>
        """)
    if '3' in selected_slides:
        draw_slide("Top Priority: " + top_issue, f"""
        The top concern in <b>{constituency_name}</b> is <b>{top_issue}</b>.<br/>
        Our action plan targets root causes with data-driven governance.
        """)
    if '4' in selected_slides:
        draw_slide("Vision for the Future", "We envision smart roads, clean water, safe neighborhoods, and economic dignity for all.")
    if '5' in selected_slides:
        draw_slide("Jobs & Youth", "Skill centers, startup zones, internships, and education-to-employment pipelines.")
    if '6' in selected_slides:
        draw_slide("Women First", "Safety, self-help groups, leadership, health, financial literacy, opportunity.")
    if '7' in selected_slides:
        draw_slide("Support for Vulnerable", "Housing, food, medicine, pensions, and fast-track social inclusion.")
    if '8' in selected_slides:
        draw_slide("Why Me?", f"I’ve served {constituency_name} through crises and campaigns. I’m not just your leader — I’m one of you.")
    if '9' in selected_slides:
        draw_slide("Vote Appeal", f"A vote for <b>{candidate_name}</b> is a vote for dignity, development, and decisive leadership.")

    # Slide 10: Electoral History (bar chart)
    if '10' in selected_slides:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT year, party, vote_share FROM eci_election_history WHERE constituency = ? ORDER BY year ASC", (constituency_name,))
        rows = cursor.fetchall()
        conn.close()
        if rows:
            labels = [f"{r[0]}-{r[1]}" for r in rows]
            shares = [r[2] for r in rows]
            draw_bar_chart("Electoral History (Vote %)", labels, shares)
            c.setFont("Helvetica-Oblique", 8)
            c.setFillColor(colors.grey)
            c.drawCentredString(width / 2.0, 1.25 * inch, "*source: ECI website")

        else:
            draw_slide("Electoral History", "No ECI data available.", source_note="Based on ECI trends")

    # Slide 11: Reputation SWOT
    if '11' in selected_slides:
        draw_slide("Reputation Snapshot", swot or "No SWOT data available.")

    # Slide 12: Public Quotes
    if '12' in selected_slides:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT quote, source_type, sentiment FROM campaign_quotes WHERE constituency = ? LIMIT 5", (constituency_name,))
        rows = cursor.fetchall()
        conn.close()
        if rows:
            text = "".join([f"• <i>{q[0]}</i> ({q[1]}, {q[2]})<br/>" for q in rows])
            draw_slide("What People Are Saying", text)
        else:
            draw_slide("Public Sentiment", "No quotes found.")

    # Slide 13: Digital Campaign (bar chart)
    if '13' in selected_slides:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT platform, followers FROM digital_campaigns WHERE constituency = ?", (constituency_name,))
        rows = cursor.fetchall()
        conn.close()
        if rows:
            platforms = [r[0] for r in rows]
            followers = [r[1] for r in rows]
            draw_bar_chart("Digital Reach (Followers)", platforms, followers)
        else:
            draw_slide("Digital Presence", "No platform data found.")

    # Slide 14: Sentiment (pie chart)
    if '14' in selected_slides:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT positive_pct, negative_pct FROM constituency_sentiment WHERE constituency = ?", (constituency_name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            pos_pct, neg_pct = round(row[0]*100, 1), round(row[1]*100, 1)
            draw_pie_chart("Public Sentiment Breakdown", pos_pct, neg_pct)
        else:
            draw_slide("Constituency Sentiment", "No data available.")

    # Slide 15–17: Promises, Timeline, Brand
    if '15' in selected_slides:
        draw_slide("9 Key Promises", """
        • Job portals<br/>• Women-led SHGs<br/>• Skill cards<br/>• Rural digitization<br/>• Smart rationing<br/>• Pensions<br/>• Irrigation<br/>• Transparency<br/>• Farmer Insurance
        """)
    if '16' in selected_slides:
        draw_slide("Campaign Timeline", "Jan–Apr: Outreach • May: Booth Mapping • Jun: Rallies • Jul: Poll Push • Aug: Victory.")
    if '17' in selected_slides:
        draw_slide("Our Brand Framework", "Trust • Action • Clarity • Unity • Decency • Development")

    # Slide 18: Candidate Profile
    if '18' in selected_slides:
        draw_slide("Candidate Profile", f"""
        Age: <b>{age}</b><br/>
        Gender: <b>{gender}</b><br/>
        Education: <b>{education}</b><br/>
        Profession: <b>{profession}</b>
        """)

    # Slide 19: Final Slogan + Contact
    if '19' in selected_slides:
        c.showPage()
        draw_footer()
        draw_bottom_color_bar()
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width/2.0, height - 1.5 * inch, slogan_text or "Your Voice, Your Power, Your Future.")
        if os.path.exists(symbol_path):
            c.drawImage(symbol_path, width/2 - 0.55*inch, height - 3.1*inch, width=1.1*inch, height=1.1*inch)
        slug = candidate_name.lower().replace(" ", "")
        links = [f"📧 {slug}@email.com", f"🌐 www.{slug}.com", f"X: twitter.com/{slug}"]
        c.setFont("Helvetica", 11)
        y = height - 4.2 * inch
        for line in links:
            c.drawCentredString(width/2.0, y, line)
            y -= 0.3 * inch

    # Slide 20: Thank You
    if '20' in selected_slides:
        draw_slide("Thank You", f"Together, let's transform {constituency_name} — one vote at a time.")

    c.save()
    print(f"✅ Pitch deck saved to {output_path}")

