"""
AI Website Summarizer — Gradio App
Converts a company name + URL into a polished markdown brochure
using Mistral AI and the existing scraper.py helpers.
"""

import os
import json
import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
from scraper import fetch_website_links, fetch_website_contents

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────
load_dotenv()

MAPI  = os.getenv("MISTRAL_API_KEY")
MODEL = "mistral-small-2603"

openai = OpenAI(
    api_key=MAPI,
    base_url="https://api.mistral.ai/v1",
)

# ──────────────────────────────────────────────
# Prompts  (kept exactly as in the notebook)
# ──────────────────────────────────────────────
link_system_prompt = """
You are provided with a list of links found on a webpage.
You are able to decide which of the links would be most relevant to include in a brochure about the company,
such as links to an About page, or a Company page, or Careers/Jobs pages.
You should respond in JSON as in this example:

{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page", "url": "https://another.full.url/careers"}
    ]
}
"""

brochure_system_prompt = """
You are an assistant that analyzes the contents of several relevant pages from a company website
and creates a short brochure about the company for prospective customers, investors and recruits.
Respond in markdown without code blocks.
Include details of company culture, customers and careers/jobs if you have the information.
"""

# ──────────────────────────────────────────────
# Core logic  (identical to notebook functions)
# ──────────────────────────────────────────────
def get_links_user_prompt(url: str) -> str:
    user_prompt = (
        f"Here is the list of links on the website {url} -\n"
        "Please decide which of these are relevant web links for a brochure about the company, "
        "respond with the full https URL in JSON format.\n"
        "Do not include Terms of Service, Privacy, email links.\n\n"
        "Links (some might be relative links):\n"
    )
    links = fetch_website_links(url)
    user_prompt += "\n".join(links)
    return user_prompt


def select_relevant_links(url: str) -> dict:
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user",   "content": get_links_user_prompt(url)},
        ],
        response_format={"type": "json_object"},
    )
    result = response.choices[0].message.content
    return json.loads(result)


def fetch_page_and_all_relevant_links(url: str) -> str:
    contents       = fetch_website_contents(url)
    relevant_links = select_relevant_links(url)

    result = f"## Landing Page:\n\n{contents}\n## Relevant Links:\n"

    for link in relevant_links.get("links", []):
        if isinstance(link, dict):
            link_type = link.get("type", "Unknown")
            link_url  = link.get("url")
        else:
            link_type = "Unknown"
            link_url  = link

        result += f"\n\n### Link: {link_type}\n"
        try:
            result += fetch_website_contents(link_url)
        except Exception as e:
            result += f"Error fetching {link_url}: {e}\n"

    return result


def get_brochure_user_prompt(company_name: str, url: str) -> str:
    user_prompt = (
        f"You are looking at a company called: {company_name}\n"
        "Here are the contents of its landing page and other relevant pages; "
        "use this information to build a short brochure of the company in markdown without code blocks.\n\n"
    )
    user_prompt += fetch_page_and_all_relevant_links(url)
    return user_prompt[:5_000]   # truncate as in notebook


# ──────────────────────────────────────────────
# Rate limiting
# ──────────────────────────────────────────────
MAX_REQUESTS_PER_SESSION = 2


def _limit_reached(count: int) -> bool:
    return count >= MAX_REQUESTS_PER_SESSION

# ──────────────────────────────────────────────
# Gradio streaming handler (FIXED for Gradio 6)
# ──────────────────────────────────────────────
def stream_brochure(company_name: str, url: str, history: list, request_count: int):

    company_name = company_name.strip()
    url = url.strip()

    if _limit_reached(request_count):
        return (
            history + [
                {"role": "assistant", "content": "🚫 Session limit reached. Refresh page."}
            ],
            request_count,
            _counter_html(request_count),
        )

    if not company_name:
        return (
            history + [{"role": "assistant", "content": "⚠️ Enter company name"}],
            request_count,
            _counter_html(request_count),
        )

    if not url.startswith("http"):
        return (
            history + [{"role": "assistant", "content": "⚠️ Enter valid URL"}],
            request_count,
            _counter_html(request_count),
        )

    new_count = request_count + 1
    user_turn = f"Summarise **{company_name}** — {url}"

    # Add initial messages
    messages = history + [
        {"role": "user", "content": user_turn},
        {"role": "assistant", "content": "🔍 Fetching website... please wait..."}
    ]

    yield (messages, new_count, _counter_html(new_count))

    try:
        user_prompt = get_brochure_user_prompt(company_name, url)
    except Exception as e:
        yield (
            history + [{"role": "assistant", "content": f"❌ Error: {e}"}],
            new_count,
            _counter_html(new_count),
        )
        return

    # Stream response
    stream = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": brochure_system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        stream=True,
    )

    # Update last assistant message instead of appending new ones
    messages[-1]["content"] = ""

    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        messages[-1]["content"] += delta

        yield (messages, new_count, _counter_html(new_count))
# ──────────────────────────────────────────────
# Counter badge HTML
# ──────────────────────────────────────────────
def _counter_html(count: int) -> str:
    remaining = MAX_REQUESTS_PER_SESSION - count
    if remaining > 0:
        color   = "#22c55e" if remaining == MAX_REQUESTS_PER_SESSION else "#f59e0b"
        label   = f"{remaining} generation{'s' if remaining != 1 else ''} remaining this session"
        icon    = "✅" if remaining == MAX_REQUESTS_PER_SESSION else "⚠️"
    else:
        color   = "#ef4444"
        label   = "Session limit reached — refresh the page to continue"
        icon    = "🚫"

    bar_pct = int((remaining / MAX_REQUESTS_PER_SESSION) * 100)

    return f"""
    <div id="rate-limit-badge">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
            <span style="font-size:1rem;">{icon}</span>
            <span style="color:{color}; font-weight:600; font-size:0.88rem;">{label}</span>
        </div>
        <div style="background:#1e293b; border-radius:6px; height:6px; overflow:hidden;">
            <div style="background:{color}; width:{bar_pct}%; height:100%;
                        border-radius:6px; transition:width 0.4s ease;"></div>
        </div>
    </div>
    """


# ──────────────────────────────────────────────
# UI helpers
# ──────────────────────────────────────────────
def clear_inputs():
    """Clears text fields and chat — does NOT reset the rate-limit counter."""
    return "", "", []


# ──────────────────────────────────────────────
# Custom CSS
# ──────────────────────────────────────────────
CUSTOM_CSS = """
/* ── Global ── */
body, .gradio-container {
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
    background: #0f1117 !important;
    color: #e2e8f0 !important;
}

/* ── Header banner ── */
#header-banner {
    background: linear-gradient(135deg, #1a1f36 0%, #0d1b2a 60%, #1a2744 100%);
    border: 1px solid #2d3a5a;
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 20px;
    text-align: center;
}
#header-banner h1 {
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(90deg, #60a5fa, #a78bfa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 6px 0;
}
#header-banner p {
    color: #94a3b8;
    font-size: 1rem;
    margin: 0;
}

/* ── Input panel ── */
#input-panel {
    background: #161b2e;
    border: 1px solid #2d3a5a;
    border-radius: 14px;
    padding: 20px;
}

/* ── Textboxes ── */
.gr-textbox textarea, .gr-textbox input {
    background: #0f1420 !important;
    border: 1px solid #3b4a6b !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-size: 0.95rem !important;
}
.gr-textbox textarea:focus, .gr-textbox input:focus {
    border-color: #60a5fa !important;
    box-shadow: 0 0 0 3px rgba(96,165,250,0.15) !important;
}

/* ── Buttons ── */
#generate-btn {
    background: linear-gradient(135deg, #3b82f6, #6366f1) !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: white !important;
    padding: 12px !important;
    transition: all 0.2s !important;
}
#generate-btn:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 25px rgba(99,102,241,0.4) !important;
}

#clear-btn {
    background: #1e2740 !important;
    border: 1px solid #3b4a6b !important;
    border-radius: 10px !important;
    color: #94a3b8 !important;
    font-size: 0.9rem !important;
}
#clear-btn:hover {
    border-color: #60a5fa !important;
    color: #60a5fa !important;
}

/* ── Chatbot ── */
#chatbot {
    background: #0f1420 !important;
    border: 1px solid #2d3a5a !important;
    border-radius: 14px !important;
}
.message.bot {
    background: #161b2e !important;
    border: 1px solid #2d3a5a !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
}
.message.user {
    background: #1e2d4a !important;
    border: 1px solid #3b5a8a !important;
    border-radius: 12px !important;
    color: #bfdbfe !important;
}

/* ── Tips accordion ── */
#tips-accordion {
    background: #161b2e !important;
    border: 1px solid #2d3a5a !important;
    border-radius: 12px !important;
    color: #94a3b8 !important;
}

/* ── Status bar ── */
#status-bar {
    background: #0d1117;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 0.85rem;
    color: #64748b;
    text-align: center;
}

/* ── Rate-limit badge ── */
#rate-limit-badge {
    background: #161b2e;
    border: 1px solid #2d3a5a;
    border-radius: 10px;
    padding: 10px 14px;
    margin-top: 12px;
}
"""

# ──────────────────────────────────────────────
# Build the Gradio UI
# ──────────────────────────────────────────────
with gr.Blocks(title="AI Website Summarizer") as demo:

    # ── Header ──
    gr.HTML("""
    <div id="header-banner">
        <h1>🌐 AI Website Summarizer</h1>
        <p>Enter a company name and website URL — get a professional brochure in seconds, powered by Mistral AI</p>
    </div>
    """)

    with gr.Row():
        # ── Left column: inputs ──
        with gr.Column(scale=1, min_width=320, elem_id="input-panel"):
            gr.Markdown("### 🏢 Company Details")

            company_input = gr.Textbox(
                label="Company Name",
                placeholder="e.g. HuggingFace",
                lines=1,
            )
            url_input = gr.Textbox(
                label="Website URL",
                placeholder="e.g. https://huggingface.co",
                lines=1,
            )

            generate_btn = gr.Button(
                "✨ Generate Brochure",
                variant="primary",
                elem_id="generate-btn",
            )
            clear_btn = gr.Button(
                "🗑️ Clear",
                variant="secondary",
                elem_id="clear-btn",
            )

            # ── Rate-limit counter badge (rendered after wiring below) ──
            counter_placeholder = gr.HTML(value=_counter_html(0), elem_id="counter-slot")

            with gr.Accordion("💡 Tips", open=False, elem_id="tips-accordion"):
                gr.Markdown("""
**How it works:**
1. Enter the company's display name.
2. Paste its primary homepage URL.
3. Hit **Generate Brochure** — the AI crawls the site, picks the most relevant pages, and writes a concise brochure for you.

**Examples to try:**
- `Anthropic` → `https://anthropic.com`
- `HuggingFace` → `https://huggingface.co`
- `Mistral AI` → `https://mistral.ai`

**Tips:**
- Use the main domain (avoid deep sub-pages).
- Processing usually takes 15–30 seconds.
- The brochure is rendered in **markdown** — headings, bullets and all!
                """)

        # ── Right column: chat output ──
        with gr.Column(scale=2):
            gr.Markdown("### 📄 Brochure Output")

            chatbot = gr.Chatbot(
                value=[],
                height=560,
                render_markdown=True,
                elem_id="chatbot",
            )

            gr.HTML("""
            <div id="status-bar">
                Powered by <strong>Mistral AI</strong> · Scraper: <strong>scraper.py</strong> ·
                Model: <strong>mistral-small-2603</strong>
            </div>
            """)

    # ── Chat state + rate-limit counter ──
    chat_state    = gr.State([])
    request_count = gr.State(0)          # per-session counter (0 → 2)

    # ── Wire up Generate button ──
    generate_btn.click(
        fn=stream_brochure,
        inputs=[company_input, url_input, chat_state, request_count],
        outputs=[chatbot, request_count, counter_placeholder],
    ).then(
        fn=lambda bot: bot,
        inputs=[chatbot],
        outputs=[chat_state],
    )

    # ── Wire up Clear button (resets text + chat, NOT the rate-limit counter) ──
    clear_btn.click(
        fn=clear_inputs,
        inputs=[],
        outputs=[company_input, url_input, chatbot],
    ).then(
        fn=lambda: [],
        inputs=[],
        outputs=[chat_state],
    )

# ──────────────────────────────────────────────
# Launch
# ──────────────────────────────────────────────
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        css=CUSTOM_CSS,
    )