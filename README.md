# 📰 News Mailer - Personalized News Digest Service

A beautiful web application that fetches curated news from multiple trusted sources and delivers personalized email digests with automatic LLM summarization.

![News Mailer Demo](https://via.placeholder.com/800x400.png?text=News+Mailer+Demo)

## ✨ Features

- 🌐 **Beautiful Web UI** - Simple form to request news digests
- 📧 **Email Delivery** - HTML-formatted emails with context-aware GIFs
- 🤖 **AI-Powered** - LLM-curated summaries organized by category
- 🔄 **Multi-Source** - Aggregates from 20+ RSS feeds (India, World, Tech, Entertainment)
- 🛡️ **Auto-Fallback** - Smart model switching on rate limits
- 🎨 **Responsive Design** - Works on desktop and mobile
- ⚡ **Fast & Lightweight** - Built with FastAPI

## 🚀 Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/news-mailer.git
cd news-mailer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your credentials

# Run the server
python news_agent_copy.py

# Open browser
http://localhost:8000
```

### Using Docker

```bash
# Build image
docker build -t news-mailer .

# Run container
docker run -p 8000:8000 --env-file .env news-mailer
```

## 📝 Configuration

Create a `.env` file with:

```env
EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
GROQ_API_KEY=gsk_your_groq_api_key
```

**Getting Credentials:**
- **Gmail App Password:** [Google Account Security](https://myaccount.google.com/security) → 2-Step Verification → App Passwords
- **Groq API Key:** [Groq Console](https://console.groq.com)

## 🌐 Deployment

Deploy to your favorite platform in minutes:

### Railway (Recommended)
```bash
# Push to GitHub first, then:
# 1. Go to railway.app
# 2. New Project → Deploy from GitHub
# 3. Add environment variables
# 4. Generate domain
```

### Render
```bash
# Push to GitHub, then:
# 1. Go to render.com
# 2. New Web Service → Connect repo
# 3. Add environment variables
# 4. Deploy
```

### Fly.io
```bash
flyctl launch
flyctl secrets set EMAIL_SENDER=your@email.com
flyctl secrets set EMAIL_PASSWORD=your-password
flyctl secrets set GROQ_API_KEY=your-key
flyctl deploy
```

📖 **[Full Deployment Guide →](DEPLOYMENT.md)**

## 📊 Architecture

```
┌─────────────┐
│  Web UI     │  ← User enters email + preferences
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  FastAPI    │  ← Handles requests
└──────┬──────┘
       │
       ├──→ Fetch RSS feeds (20+ sources)
       │
       ├──→ LLM Summarization (Groq + fallbacks)
       │
       └──→ Send HTML Email (Gmail SMTP)
```

## 🛠️ Tech Stack

- **Backend:** FastAPI (Python 3.11)
- **LLM:** Groq (Llama 4 Scout, Llama 4 Maverick, Llama 3.3, Qwen3)
- **Email:** SMTP (Gmail)
- **Feeds:** feedparser
- **Deployment:** Docker, Railway, Render, Fly.io

## 📡 API Reference

### Web Interface
- `GET /` - Main form UI

### API Endpoints

#### Health Check
```bash
GET /health
```

#### Send News Digest
```bash
POST /send-news
Content-Type: application/json

{
  "email": "receiver@example.com",
  "hours_back": 24,
  "name": "John Doe"
}
```

**Response:**
```json
{
  "status": "sent",
  "email": "receiver@example.com",
  "hours_back": 24,
  "articles_considered": 42,
  "model_used": "meta-llama/llama-4-scout-17b-16e-instruct"
}
```

## 🎨 Customization

### Add News Sources
Edit `RSS_FEEDS` in `news_agent_copy.py`:
```python
RSS_FEEDS.append({
    "name": "Your Source",
    "url": "https://example.com/feed",
    "category": "Tech"
})
```

### Modify Email Template
Update `build_email_html()` function for custom styling.

### Change LLM Models
Edit `MODEL_FALLBACKS` list to use different Groq models.

## 🧪 Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test news sending
curl -X POST http://localhost:8000/send-news \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "hours_back": 24,
    "name": "Test User"
  }'
```

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - feel free to use this project for personal or commercial purposes.

## 🙏 Acknowledgments

- News sources: Times of India, The Hindu, BBC, Reuters, TechCrunch, and more
- LLM: Groq (amazing free tier!)
- Icons: Emoji masterrace 🎉

---

**Made with ❤️ for staying informed**

⭐ Star this repo if you find it useful!
