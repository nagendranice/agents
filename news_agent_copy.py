import os
from dotenv import load_dotenv
from typing import Any
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import feedparser
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import json
import re

load_dotenv()

app = FastAPI(title="News Mailer API", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# === Updated RSS Sources (verified more reliable as of March 2026) ===
# RSS_FEEDS = [
#     {"name": "Times of India - Top Stories", "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "category": "India"},
#     {"name": "The Hindu - News", "url": "https://www.thehindu.com/news/feeder/default.rss", "category": "India"},  # Better than main feeder
#     {"name": "Indian Express - India", "url": "https://indianexpress.com/section/india/feed/", "category": "India"},
#     {"name": "Indian Express - World", "url": "https://indianexpress.com/section/world/feed/", "category": "World"},
#     {"name": "BBC News - World", "url": "http://feeds.bbci.co.uk/news/rss.xml", "category": "World"},
#     {"name": "Hindustan Times - India", "url": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml", "category": "India"},  # Reliable alternative
#     {"name": "Reuters - India", "url": "https://ir.thomsonreuters.com/rss/news-releases.xml", "category": "India/World"},
#     {"name": "Pinkvilla - Entertainment", "url": "https://www.pinkvilla.com/rss.xml", "category": "Entertainment"},
#     {"name": "AlJazeera - World", "url": "https://www.aljazeera.com/xml/rss/all.xml", "category": "World"},
# ]

RSS_FEEDS = [
    # Your current general / India / World feeds
    {"name": "Times of India - Top Stories", "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "category": "India"},
    {"name": "The Hindu - News", "url": "https://www.thehindu.com/news/feeder/default.rss", "category": "India"},
    {"name": "Indian Express - India", "url": "https://indianexpress.com/section/india/feed/", "category": "India"},
    {"name": "Indian Express - World", "url": "https://indianexpress.com/section/world/feed/", "category": "World"},
    {"name": "BBC News - World", "url": "http://feeds.bbci.co.uk/news/rss.xml", "category": "World"},
    {"name": "Hindustan Times - India", "url": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml", "category": "India"},
    {"name": "Reuters - India", "url": "https://ir.thomsonreuters.com/rss/news-releases.xml", "category": "India/World"},
    {"name": "Pinkvilla - Entertainment", "url": "https://www.pinkvilla.com/rss.xml", "category": "Entertainment"},
    {"name": "AlJazeera - World", "url": "https://www.aljazeera.com/xml/rss/all.xml", "category": "World"},

    # Additional Tech feeds (higher chance of recent updates)
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "category": "Tech"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "Tech"},
    {"name": "Wired", "url": "https://www.wired.com/feed/rss", "category": "Tech"},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "category": "Tech"},
    {"name": "Gadgets 360", "url": "https://feeds.feedburner.com/NDTV-Gadgets360-latest", "category": "Tech"},
    {"name": "YourStory", "url": "https://yourstory.com/feed", "category": "Tech"},

    # Additional Entertainment feeds
    # Bollywood
    {"name": "Bollywood Hungama News", "url": "https://www.bollywoodhungama.com/rss/news.xml", "category": "Entertainment"},
    {"name": "Bollywood Hungama Features", "url": "https://www.bollywoodhungama.com/rss/features.xml", "category": "Entertainment"},
    {"name": "Hindustan Times Bollywood", "url": "https://www.hindustantimes.com/feeds/rss/entertainment/bollywood/rssfeed.xml", "category": "Entertainment"},
    {"name": "Indian Express Bollywood", "url": "https://indianexpress.com/section/entertainment/bollywood/feed/", "category": "Entertainment"},
    {"name": "Filmibeat Bollywood", "url": "https://www.filmibeat.com/rss/feeds/bollywood-fb.xml", "category": "Entertainment"},

    # Tollywood
    {"name": "123Telugu", "url": "https://www.123telugu.com/feed", "category": "Entertainment"},
    {"name": "Filmy Focus", "url": "https://www.filmyfocus.com/feed/", "category": "Entertainment"},

    # Hollywood / General Entertainment
    {"name": "Variety", "url": "https://variety.com/feed/", "category": "Entertainment"},
    {"name": "Deadline Hollywood", "url": "https://deadline.com/feed/", "category": "Entertainment"},
]

MODEL_FALLBACKS = [
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "llama-3.3-70b-versatile",
    "qwen/qwen3-32b",
]


class SendNewsRequest(BaseModel):
    email: str = Field(..., description="Receiver email id")
    hours_back: int = Field(default=24, ge=1, le=168, description="Only include last N hours")
    name: str = Field(default="Reader", description="Recipient display name")


def fetch_latest_news(hours_back: int = 24) -> list[dict[str, Any]]:
    """Fetch and filter latest articles from all RSS feeds."""
    cutoff = datetime.utcnow() - timedelta(hours=hours_back)
    articles = []

    for feed in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed["url"])
            if parsed.bozo:
                print(f"Warning: Bozo flag on {feed['name']}: {parsed.bozo_exception}")
                continue

            print(f"Feed {feed['name']}: {len(parsed.entries)} entries found")

            for entry in parsed.entries[:20]:  # Limit per feed
                pub_date = entry.get("published_parsed") or entry.get("updated_parsed") or entry.get("date_parsed")
                if not pub_date:
                    continue

                pub_dt = datetime(*pub_date[:6])
                if pub_dt > cutoff:
                    articles.append({
                        "title": entry.get("title", "No title"),
                        "link": entry.get("link", "#"),
                        "source": feed["name"],
                        "category": feed["category"],
                        "summary": (entry.get("summary") or entry.get("description") or "")[:250] + "...",
                        "published": pub_dt.isoformat(),
                    })
        except Exception as e:
            print(f"Feed {feed['name']} failed: {str(e)}")
            continue

    articles.sort(key=lambda x: x.get("published", ""), reverse=True)
    seen = set()
    unique = [a for a in articles if (a["title"], a["link"]) not in seen and not seen.add((a["title"], a["link"]))]

    print(f"Total recent articles: {len(unique)}")
    return unique[:40]


def is_model_limit_error(error_message: str) -> bool:
    lowered = error_message.lower()
    tokens = ["rate limit", "limit", "429", "too many requests", "tokens per", "quota", "resource exhausted"]
    return any(token in lowered for token in tokens)


def normalize_markdown(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    normalized = []
    for line in lines:
        if line.startswith("###") or line.startswith("-"):
            normalized.append(line)
            continue
        if re.match(r"^\d+[\).]\s+", line):
            cleaned_line = re.sub(r"^\d+[\).]\s+", "", line)
            normalized.append(f"- {cleaned_line}")
            continue
        normalized.append(f"- {line}")
    return "\n".join(normalized)


def generate_digest_markdown(articles: list[dict[str, Any]], hours_back: int, name: str) -> tuple[str, str]:
    if not articles:
        return "", MODEL_FALLBACKS[0]

    payload = json.dumps(articles[:35], ensure_ascii=False)
    prompt = f"""
You are a concise news editor. Create a clean markdown digest for {name}.
Time window: last {hours_back} hours.

Rules:
- Output markdown only.
- Use section headings with exactly this style: ### 🌍 World, ### 🏛️ Politics, ### ⚽ Sports, ### 💼 Business, ### 💻 Technology, ### 🎬 Entertainment.
- Include only relevant sections that have stories.
- Under each section, add 3-5 bullets.
- Bullet format: - **Title** — one short summary sentence — [Read more](URL) — Source
- Do not output JSON, python lists, or code fences.

Articles:
{payload}
""".strip()

    last_error = None
    for model_name in MODEL_FALLBACKS:
        try:
            llm = ChatGroq(model=model_name, temperature=0.2)
            response = llm.invoke([HumanMessage(content=prompt)])
            content = (response.content or "").strip()
            if content and not content.startswith("[") and "Read more" in content:
                return normalize_markdown(content), model_name
            if content:
                return normalize_markdown(content), model_name
        except Exception as exc:
            last_error = str(exc)
            print(f"Model failed: {model_name} -> {last_error}")
            if not is_model_limit_error(last_error):
                continue
            continue

    raise RuntimeError(f"All models failed. Last error: {last_error}")


def markdown_to_html(markdown_text: str) -> str:
    lines = markdown_text.split('\n')
    result = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                result.append('</ul>')
                in_list = False
            continue
            
        # Section headings
        if line.startswith('###'):
            if in_list:
                result.append('</ul>')
                in_list = False
            heading = line.replace('###', '').strip()
            result.append(f'<h2 style="margin:22px 0 10px 0;font-size:20px;color:#1f2d3d;border-left:4px solid #5b8def;padding-left:10px;">{heading}</h2>')
            continue
            
        # List items
        if line.startswith('-'):
            content = line[1:].strip()
            # Apply bold
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color:#1f2d3d;">\1</strong>', content)
            # Apply links
            content = re.sub(
                r'\[(.*?)\]\((.*?)\)',
                r'<a href="\2" style="color:#3498db;text-decoration:none;font-weight:500;border-bottom:1px solid #bdc3c7;">\1</a>',
                content,
            )
            if not in_list:
                result.append('<ul style="list-style:none;padding:0;margin:12px 0;">')
                in_list = True
            result.append(f'<li style="margin:8px 0;padding:12px;background:#f7f9fc;border-radius:8px;border-left:3px solid #5b8def;">{content}</li>')
            continue
            
        # Regular text
        if in_list:
            result.append('</ul>')
            in_list = False
        result.append(f'<p style="margin:8px 0;">{line}</p>')
    
    if in_list:
        result.append('</ul>')
    
    return '\n'.join(result)


def pick_context_gif(markdown_digest: str) -> str:
    """Pick a relevant GIF based on digest content."""
    lower = markdown_digest.lower()
    
    # Sports keywords
    sports_terms = ['sports', 'cricket', 'football', 'soccer', 'tennis', 'basketball', 'match', 'tournament', 'championship']
    if any(term in lower for term in sports_terms):
        return "https://media.giphy.com/media/l0HlHJGHe3yAMhdQY/giphy.gif"
    
    # Business/Economy keywords
    business_terms = ['business', 'market', 'economy', 'stock', 'trade', 'finance', 'company', 'revenue']
    if any(term in lower for term in business_terms):
        return "https://media.giphy.com/media/67ThRZlYBvibtdF9JH/giphy.gif"
    
    # Technology keywords
    tech_terms = ['technology', 'tech', 'ai', 'software', 'app', 'digital', 'cyber', 'iphone', 'android']
    if any(term in lower for term in tech_terms):
        return "https://media.giphy.com/media/LaVp0AyqR5bGsC5Cbm/giphy.gif"
    
    # Politics keywords
    politics_terms = ['politics', 'election', 'government', 'minister', 'president', 'parliament', 'policy']
    if any(term in lower for term in politics_terms):
        return "https://media.giphy.com/media/l0IylOPCNkiqOgMyA/giphy.gif"
    
    # World/Breaking news default
    return "https://media.giphy.com/media/l0Iy69RBwtdmvwkIo/giphy.gif"


def build_email_html(name: str, hours_back: int, markdown_digest: str) -> str:
    hero_gif = pick_context_gif(markdown_digest)
    content_html = markdown_to_html(markdown_digest)
    now_str = datetime.now().strftime("%A, %d %b %Y • %I:%M %p IST")
    return f"""
    <html>
      <body style="margin:0;background:#eef2f7;font-family:Segoe UI,Arial,sans-serif;color:#2f3b4a;">
        <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #dde5ef;">
          <div style="padding:22px;background:linear-gradient(120deg,#4f73ff,#7a52c7);color:#fff;">
            <h1 style="margin:0 0 6px 0;font-size:26px;">📰 Your Personal News Brief</h1>
            <div style="font-size:14px;opacity:.95;">Hi {name}, here are updates from the last {hours_back} hours.</div>
            <div style="font-size:12px;opacity:.9;margin-top:6px;">{now_str}</div>
          </div>
          <img src="{hero_gif}" alt="news highlight" style="width:100%;max-height:220px;object-fit:cover;display:block;" />
          <div style="padding:20px 24px;line-height:1.6;">{content_html}</div>
          <div style="padding:14px 24px;background:#f7f9fc;color:#7a8797;font-size:12px;">
            Sent by News Mailer • You requested this digest for the last {hours_back} hours.
          </div>
        </div>
      </body>
    </html>
    """.strip()


def send_email(receiver_email: str, name: str, hours_back: int, markdown_digest: str) -> None:
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    if not sender or not password:
        raise RuntimeError("EMAIL_SENDER or EMAIL_PASSWORD is missing in environment.")

    html_email = build_email_html(name=name, hours_back=hours_back, markdown_digest=markdown_digest)
    subject = f"📰 News Digest ({hours_back}h) - {datetime.now().strftime('%d %b %Y')}"

    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr(("News Mailer", sender))
    msg["To"] = receiver_email
    msg["Subject"] = subject

    plain_fallback = markdown_digest or "No digest content generated."
    msg.attach(MIMEText(plain_fallback, "plain", "utf-8"))
    msg.attach(MIMEText(html_email, "html", "utf-8"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender, password)
    server.send_message(msg)
    server.quit()


@app.get("/")
async def root():
    """Serve the main HTML form."""
    return FileResponse("static/index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/send-news")
def send_news(req: SendNewsRequest) -> dict[str, Any]:
    try:
        articles = fetch_latest_news(hours_back=req.hours_back)
        if not articles:
            raise HTTPException(status_code=404, detail="No recent articles found for requested hours_back.")

        digest_markdown, model_used = generate_digest_markdown(
            articles=articles,
            hours_back=req.hours_back,
            name=req.name,
        )
        send_email(
            receiver_email=req.email,
            name=req.name,
            hours_back=req.hours_back,
            markdown_digest=digest_markdown,
        )
        return {
            "status": "sent",
            "email": req.email,
            "hours_back": req.hours_back,
            "articles_considered": len(articles),
            "model_used": model_used,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)