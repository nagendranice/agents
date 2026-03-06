import os
import sys
from dotenv import load_dotenv
from typing import Any
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
import re
import logging
from html import unescape
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables (Railway injects them directly)
load_dotenv()

# Validate required environment variables
required_vars = ["EMAIL_SENDER", "EMAIL_PASSWORD"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing required environment variables: {missing_vars}")
    logger.error("Please set them in your Railway dashboard: Settings → Variables")
else:
    logger.info("All required environment variables are set")

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
    {"name": "ESPNCricinfo - Cricket", "url": "https://www.espncricinfo.com/rss/content/story/feeds/0.xml", "category": "Sports"},
    {"name": "BBC Sport", "url": "https://feeds.bbci.co.uk/sport/rss.xml?edition=uk", "category": "Sports"},
    {"name": "ESPN - Top Sports", "url": "https://www.espn.com/espn/rss/news", "category": "Sports"},
    {"name": "NDTV Sports", "url": "https://feeds.feedburner.com/ndtvsports-latest", "category": "Sports"},
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

DIGEST_ENGINE = "deterministic-digest-v1"
FEED_TIMEOUT_SECONDS = 6
FEED_MAX_WORKERS = 8

TARGET_SECTIONS = [
    ("World", "### 🌍 World"),
    ("Politics", "### 🏛️ Politics"),
    ("Sports", "### ⚽ Sports"),
    ("Business", "### 💼 Business"),
    ("Technology", "### 💻 Technology"),
    ("Entertainment", "### 🎬 Entertainment"),
]

KEYWORDS = {
    "World": ["world", "global", "international", "ukraine", "gaza", "israel", "china", "europe", "asia", "middle east"],
    "Politics": ["election", "parliament", "government", "minister", "policy", "bill", "congress", "bjp", "senate", "president"],
    "Sports": [
        "cricket", "ipl", "t20", "odi", "test", "bcci", "icc", "wicket", "innings", "bowler", "batsman", "cricinfo",
        "football", "soccer", "tennis", "f1", "formula 1", "nba", "olympics", "grand prix",
    ],
    "Business": ["market", "stock", "economy", "business", "finance", "trade", "inflation", "gdp", "revenue", "company"],
    "Technology": ["tech", "technology", "ai", "software", "app", "cyber", "chip", "startup", "iphone", "android"],
    "Entertainment": ["movie", "film", "bollywood", "hollywood", "actor", "actress", "music", "series", "celebrity", "trailer"],
}

PROMO_PATTERNS = [
    r"\bcoupon\b",
    r"\bcoupons\b",
    r"\bpromo\b",
    r"\bpromo code\b",
    r"\bdiscount\b",
    r"\bdeal\b",
    r"\bdeals\b",
    r"\bsave up to\b",
    r"\b%\s*off\b",
    r"\bservice code\b",
]


class SendNewsRequest(BaseModel):
    email: str = Field(..., description="Receiver email id")
    hours_back: int = Field(default=24, ge=1, le=168, description="Only include last N hours")
    name: str = Field(default="Reader", description="Recipient display name")


def fetch_latest_news(hours_back: int = 24) -> list[dict[str, Any]]:
    """Fetch RSS articles and prefer requested window, with older fallback if needed."""
    cutoff = datetime.utcnow() - timedelta(hours=hours_back)
    articles = []

    def _fetch_single_feed(feed: dict[str, str]) -> list[dict[str, Any]]:
        feed_articles: list[dict[str, Any]] = []
        try:
            logger.info("Fetching feed: %s", feed["name"])
            req = Request(
                feed["url"],
                headers={
                    "User-Agent": "NewsMailerBot/1.0 (+https://example.local)",
                    "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
                },
            )
            with urlopen(req, timeout=FEED_TIMEOUT_SECONDS) as resp:
                content = resp.read()

            parsed = feedparser.parse(content)
            if parsed.bozo:
                bozo_name = type(parsed.bozo_exception).__name__
                if bozo_name == "CharacterEncodingOverride":
                    logger.info("Non-fatal encoding override on %s; continuing parse", feed["name"])
                else:
                    logger.warning("Bozo flag on %s: %s", feed["name"], parsed.bozo_exception)

            logger.info("Feed %s: %d entries found", feed["name"], len(parsed.entries))

            for entry in parsed.entries[:60]:
                pub_date = entry.get("published_parsed") or entry.get("updated_parsed") or entry.get("date_parsed")
                pub_dt = datetime(*pub_date[:6]) if pub_date else None
                summary_raw = (entry.get("summary") or entry.get("description") or "").strip()
                summary = summary_raw[:250] + ("..." if len(summary_raw) > 250 else "")
                feed_articles.append({
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", "#"),
                    "source": feed["name"],
                    "category": feed["category"],
                    "summary": summary,
                    "published": pub_dt.isoformat() if pub_dt else "",
                    "is_recent": bool(pub_dt and pub_dt > cutoff),
                })
        except (HTTPError, URLError, socket.timeout) as e:
            logger.warning("Feed %s timed out/failed network request: %s", feed["name"], str(e))
        except Exception as e:
            logger.warning("Feed %s failed: %s", feed["name"], str(e))
        return feed_articles

    with ThreadPoolExecutor(max_workers=FEED_MAX_WORKERS) as pool:
        futures = [pool.submit(_fetch_single_feed, feed) for feed in RSS_FEEDS]
        for future in as_completed(futures):
            try:
                articles.extend(future.result())
            except Exception as e:
                logger.warning("Feed worker failed unexpectedly: %s", str(e))

    articles.sort(key=lambda x: x.get("published") or "", reverse=True)
    seen = set()
    unique = [a for a in articles if (a["title"], a["link"]) not in seen and not seen.add((a["title"], a["link"]))]

    recent = [a for a in unique if a["is_recent"]]
    older = [a for a in unique if not a["is_recent"]]
    combined = recent + older

    logger.info("Recent articles in %sh window: %d", hours_back, len(recent))
    logger.info("Total usable articles with fallback: %d", len(combined))
    return combined[:180]


def _clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _short_summary(article: dict[str, Any]) -> str:
    summary = _clean_text(article.get("summary", ""))
    if not summary:
        summary = "Quick update from the source."
    if len(summary) > 150:
        summary = summary[:147].rstrip() + "..."
    if summary and summary[-1] not in ".!?":
        summary += "."
    return summary


def _classify_article(article: dict[str, Any]) -> set[str]:
    tags: set[str] = set()
    source_category = (article.get("category") or "").lower()
    haystack = f"{article.get('title', '')} {article.get('summary', '')} {article.get('source', '')}".lower()

    if "sport" in source_category:
        tags.add("Sports")
    if "tech" in source_category:
        tags.add("Technology")
    if "entertain" in source_category:
        tags.add("Entertainment")
    if "world" in source_category:
        tags.add("World")
    # Do not auto-map all India stories to Politics; rely on content keywords.

    for section, words in KEYWORDS.items():
        if any(word in haystack for word in words):
            tags.add(section)

    return tags


def _section_score(article: dict[str, Any], section: str) -> int:
    haystack = f"{article.get('title', '')} {article.get('summary', '')} {article.get('source', '')}".lower()
    source_category = (article.get("category") or "").lower()
    score = 0

    def _matches_keyword(text: str, keyword: str) -> bool:
        # Use exact phrase/word matching to avoid substring collisions.
        pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
        return re.search(pattern, text) is not None

    def _is_promotional(text: str) -> bool:
        return any(re.search(pattern, text) is not None for pattern in PROMO_PATTERNS)

    # Keep strongly typed feeds in their own sections.
    if "sport" in source_category and section != "Sports":
        return 0
    if "tech" in source_category and section != "Technology":
        return 0
    if "entertain" in source_category and section != "Entertainment":
        return 0

    # Keep Technology focused on news, not affiliate deals/coupon posts.
    if section == "Technology" and _is_promotional(haystack):
        return 0

    # Source/category affinity
    if section == "Sports" and "sport" in source_category:
        score += 4
    if section == "Technology" and "tech" in source_category:
        score += 4
    if section == "Entertainment" and "entertain" in source_category:
        score += 4
    if section == "World" and "world" in source_category:
        score += 3

    # Content keyword affinity
    for word in KEYWORDS.get(section, []):
        if _matches_keyword(haystack, word):
            score += 2

    # Cricket boost inside sports so it appears before generic sports.
    if section == "Sports":
        cricket_terms = ["cricket", "ipl", "t20", "odi", "test", "bcci", "icc", "wicket", "innings", "cricinfo"]
        if any(_matches_keyword(haystack, term) for term in cricket_terms):
            score += 5

    # Recency preference only after section relevance is established.
    if score > 0 and article.get("is_recent"):
        score += 1

    return score


def _pick_section_articles(
    articles: list[dict[str, Any]],
    section: str,
    per_section: int = 5,
    used_links: set[str] | None = None,
) -> list[dict[str, Any]]:
    if used_links is None:
        used_links = set()

    # Keep only relevant items for this section, sorted by score.
    candidates = []
    for article in articles:
        score = _section_score(article, section)
        if score > 0:
            candidates.append((score, article))

    candidates.sort(key=lambda item: (item[0], item[1].get("published") or ""), reverse=True)

    chosen: list[dict[str, Any]] = []
    seen_links: set[str] = set()
    for _, article in candidates:
        link = article.get("link", "")
        if not link or link in seen_links or link in used_links:
            continue
        chosen.append(article)
        seen_links.add(link)
        used_links.add(link)
        if len(chosen) == per_section:
            return chosen

    return chosen


def generate_digest_markdown(articles: list[dict[str, Any]], hours_back: int, name: str) -> tuple[str, str]:
    if not articles:
        return "", DIGEST_ENGINE
    lines = [f"- Curated for {name}. Time requested: last {hours_back} hours (with older fallback when needed).", ""]
    used_links: set[str] = set()
    for section, heading in TARGET_SECTIONS:
        lines.append(heading)
        selected = _pick_section_articles(articles, section, per_section=5, used_links=used_links)
        for article in selected:
            title = _clean_text(article.get("title", "No title")) or "No title"
            summary = _short_summary(article)
            link = article.get("link") or "#"
            source = _clean_text(article.get("source", "Unknown Source")) or "Unknown Source"
            lines.append(f"- **{title}** — {summary} — [Read more]({link}) — {source}")
        if len(selected) < 5:
            for _ in range(5 - len(selected)):
                lines.append("- **Update pending** — Not enough source items yet; this slot will auto-fill as fresh stories arrive. — [Read more](#) — News Mailer")
        lines.append("")
    return "\n".join(lines).strip(), DIGEST_ENGINE


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


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 News Mailer API starting up...")
    logger.info(f"Static files directory: {os.path.abspath('static')}")
    logger.info(f"Environment check: EMAIL_SENDER={'✓' if os.getenv('EMAIL_SENDER') else '✗'}")
    logger.info(f"Environment check: EMAIL_PASSWORD={'✓' if os.getenv('EMAIL_PASSWORD') else '✗'}")
    logger.info("✅ Application startup complete")


@app.get("/")
async def root():
    """Serve the main HTML form."""
    return FileResponse("static/index.html")


@app.get("/health")
def health() -> dict[str, str]:
    logger.info("Health check requested")
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


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

    port = int(os.getenv("PORT", 8000))
    logger.info(f"🚀 Starting News Mailer API on port {port}")
    logger.info(f"📡 Health check endpoint: http://0.0.0.0:{port}/health")
    logger.info(f"🌐 Web interface: http://0.0.0.0:{port}/")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port, 
        reload=False,
        log_level="info"
    )