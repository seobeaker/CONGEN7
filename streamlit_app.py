import streamlit as st
import openai
import re

# --- Brand tone dictionary ---
brand_tones = {
    "Cotton On": "At Cotton On, we’re casual and informal—just like the fashion we’re known for...",
    "Cotton On Kids": "Cotton On Kids is the go-to for baby and kids clothing essentials and trends...",
    "Cotton On Body": "Cotton On Body empowers women to show up for themselves and each other...",
    "Factorie": "Factorie is the go-to youth street fashion brand...",
    "Rubi": "Rubi believes no outfit is complete without the finishing touches...",
    "Typo": "Typo breaks the rules—where creativity and contradictions collide...",
    "Supre": "Supre is your go-to for trend-driven fashion, denim and amazing basics...",
    "Ceres Life": "Ceres Life makes everyday outfitting effortless..."
}

# --- Helper: convert markdown to HTML ---
def markdown_to_html(text):
    lines = text.splitlines()
    html_lines = []
    paragraph_lines = []

    def flush_paragraph():
        nonlocal paragraph_lines
        if paragraph_lines:
            html_lines.append("<p>" + "<br>\n".join(paragraph_lines) + "</p>")
            paragraph_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            continue
        m_h2 = re.match(r"^## (.+)$", stripped)
        m_h3 = re.match(r"^### (.+)$", stripped)
        m_h4 = re.match(r"^#### (.+)$", stripped)
        if m_h2:
            flush_paragraph()
            html_lines.append(f"<h2>{m_h2.group(1)}</h2>")
            continue
        if m_h3:
            flush_paragraph()
            html_lines.append(f"<h3>{m_h3.group(1)}</h3>")
            continue
        if m_h4:
            flush_paragraph()
            html_lines.append(f"<h4>{m_h4.group(1)}</h4>")
            continue
        paragraph_lines.append(stripped)
    flush_paragraph()
    return "<html><body>\n" + "\n".join(html_lines) + "\n</body></html>"

# --- Streamlit UI ---
st.title("SEO Content Generator")

api_key = st.text_input("OpenAI API Key", type="password")
primary = st.text_input("Primary Keyword")
secondary = st.text_input("Secondary Keywords (comma separated)")
category = st.text_input("Page Category")

# Dynamic topics via session state
if 'topics' not in st.session_state:
    st.session_state.topics = ["", "", ""]

if st.button("+ Add Topic"):
    st.session_state.topics.append("")

for idx in range(len(st.session_state.topics)):
    st.session_state.topics[idx] = st.text_input(f"Topic {idx+1}", st.session_state.topics[idx])

brand = st.selectbox("Brand", list(brand_tones.keys()))
length_option = st.selectbox("Length", ["Short (~750 words)", "Medium (~1000 words)", "Long (~1500 words)"])
length_map = {"Short (~750 words)": 750, "Medium (~1000 words)": 1000, "Long (~1500 words)": 1500}
word_limit = length_map[length_option]

model = st.selectbox(
    "Model", ["gpt-4o", "gpt-4.1", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
)

if st.button("Generate Content"):
    if not api_key or not primary or not category:
        st.error("Please fill in the API key, primary keyword, and category.")
    else:
        client = openai.OpenAI(api_key=api_key)
        topics = [t for t in st.session_state.topics if t.strip()]
        tone = brand_tones.get(brand, "")

        # Build prompt
        prompt = (
            f"{tone}\n\n"
            f"Write SEO content for the page category '{category}' for the brand '{brand}'.\n"
            f"Use primary keyword: '{primary}'. Secondary keywords: {secondary}.\n"
            f"Your task:\n"
            f"1. Create a punchy, SEO-optimized **Page Title** using the primary keyword.\n"
            f"2. Generate a compelling **Meta Description** under 160 characters that includes secondary keywords.\n"
            f"3. Write the main body content of at least {word_limit} words.\n"
            f"4. Use normal paragraphs and headings only (no bullet points).\n"
        )
        if topics:
            prompt += "Structure:\n- Intro paragraph\n"
            headings = ["##", "###", "####"]
            for i, top in enumerate(topics):
                h = headings[i] if i < len(headings) else "####"
                prompt += f"{h} {top}\n"

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content

        # Extract title and meta description
        title_match = re.search(r"(?i)title\s*[:\-]\s*(.*)", content)
        meta_match = re.search(r"(?i)meta description\s*[:\-]\s*(.*)", content)

        page_title = title_match.group(1).strip() if title_match else "Not Found"
        meta_description = meta_match.group(1).strip() if meta_match else "Not Found"

        # ✅ Show Page Title and Meta Description FIRST in a grey box
        st.markdown(
            f"""
            <div style="border: 1px solid #ccc; background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h4 style="margin-bottom: 5px;">Page Title</h4>
                <p style="margin-top: 0;"><strong>{page_title}</strong></p>
                <h4 style="margin-bottom: 5px;">Meta Description</h4>
                <p style="margin-top: 0;">{meta_description}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ✅ Remove duplicate lines from body content
        cleaned_body = re.sub(r"(?i)(title|meta description)\s*[:\-].*", "", content).strip()

        # ✅ Show cleaned body content in a grey box
        st.markdown(
            """
            <h4>Generated Body Content</h4>
            <div style="border: 1px solid #ccc; background-color: #f9f9f9; padding: 15px; border-radius: 5px;">
            """
            + cleaned_body.replace("\n", "<br>")
            + "</div>",
            unsafe_allow_html=True
        )

        # ✅ Word count (excluding title/meta)
        word_count = len(re.findall(r"\b\w+\b", cleaned_body))
        st.info(f"Total Word Count (excluding title/meta): {word_count}")

        # ✅ HTML download (uses original full markdown)
        html_out = markdown_to_html(content)
        st.download_button(
            label="Download as HTML",
            data=html_out,
            file_name="generated_content.html",
            mime="text/html"
        )
