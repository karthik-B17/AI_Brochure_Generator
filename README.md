# 🌐 AI Website Summarizer — Intelligent Company Brochure Generator

A powerful **Generative AI application** that converts any company website into a clean, structured **markdown brochure** using **Mistral AI**, **web scraping**, and a modern **Gradio UI**.

[![Live Demo](https://img.shields.io/badge/🤗%20HuggingFace-Live%20Demo-yellow)](https://huggingface.co/spaces/Karthikb87/AI_Brochure_Generator)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![Gradio](https://img.shields.io/badge/Gradio-Compatible-orange)](https://gradio.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 📸 Preview

> Clean dark UI that takes a company URL and generates a professional brochure in seconds with streaming output.

---

## 🚀 Features

* 🌍 **Website Scraping** — Extracts content from landing + important pages
* 🧠 **AI Link Selection** — Automatically selects relevant links (About, Careers, etc.)
* ✍️ **Brochure Generation** — Converts raw content into structured markdown
* ⚡ **Streaming Output** — Real-time response generation
* 🎨 **Modern UI** — Built with Gradio (dark theme + responsive layout)
* 🚫 **Rate Limiting** — Prevents API abuse (session-based control)

---

## 🗂 Project Structure

```
ai-website-summarizer/
├── app.py              # Main app (UI + logic + streaming)
├── scraper.py          # Website scraping utilities
├── requirements.txt    # Dependencies
├── .env                # Local secrets (DO NOT COMMIT)
├── .gitignore          # Ignore sensitive/system files
└── README.md           # Documentation
```

---

## ⚙️ How It Works

```
User inputs company name + URL
        │
        ▼
Gradio UI (Blocks + Chatbot)
        │
        ▼
fetch_website_links() → extracts all links
        │
        ▼
Mistral AI selects relevant links (About, Careers, etc.)
        │
        ▼
fetch_website_contents() → scrapes selected pages
        │
        ▼
Mistral generates structured brochure (markdown)
        │
        ▼
Streaming output → Chat UI
```

---

## 🛠 Local Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/ai-website-summarizer.git
cd ai-website-summarizer
```

---

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Setup environment variables

Create `.env` file:

```env
MISTRAL_API_KEY=your_api_key_here
```

---

### 5. Run the app

```bash
python app.py
```

Open:

```
http://localhost:7860
```

---

## 🌍 Example Usage

**Input:**

* Company: `HuggingFace`
* URL: `https://huggingface.co`

**Output:**

* About section
* Products/services
* Careers
* Company overview

All formatted in clean **markdown brochure style**.

---

## 🔑 Environment Variables

| Variable        | Description        | Required |
| --------------- | ------------------ | -------- |
| MISTRAL_API_KEY | Mistral AI API key | ✅ Yes    |

For deployment, add this in:
👉 HuggingFace Spaces → **Settings → Secrets**

---

## 🚢 Deployment (HuggingFace Spaces)

1. Push repo to GitHub
2. Create new Space
3. Select **Gradio SDK**
4. Connect GitHub repo
5. Add `MISTRAL_API_KEY` in Secrets
6. Deploy automatically 🚀

---

## 🔒 Security Notes

* ❌ Never commit `.env`
* 🔐 API keys loaded via environment variables
* 🚫 Rate limiting prevents misuse
* 🌐 Safe for public deployment

---

## 🧩 Tech Stack

| Layer      | Technology                     |
| ---------- | ------------------------------ |
| AI Model   | Mistral (`mistral-small-2603`) |
| UI         | Gradio                         |
| Scraping   | BeautifulSoup + Requests       |
| Backend    | Python                         |
| Deployment | HuggingFace Spaces             |

---

## 📈 Future Improvements

* ⚡ Async scraping (faster performance)
* 📊 Structured sections (About, Products, Careers)
* 📄 Export to PDF
* 🔍 Multi-company comparison

---

## 👤 Author

**Karthik B**
📧 [karthikb57m@gmail.com](mailto:karthikb57m@gmail.com)
🤗 HuggingFace: https://huggingface.co/Karthikb87

---

## 📜 License

This project is licensed under the MIT License.
