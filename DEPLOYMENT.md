# 📰 News Mailer API - Deployment Guide

A FastAPI service that fetches curated news from multiple sources and sends personalized email digests with a beautiful HTML UI.

## 🚀 Quick Start (Local)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python news_agent_copy.py

# Open browser
http://localhost:8000
```

## 🌐 Deployment Options

### Option 1: Railway (Recommended - Free Tier Available)

**Setup:**

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

2. **Deploy to Railway:**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect the Dockerfile and deploy

3. **Set Environment Variables:**
   In Railway dashboard, go to Variables and add:
   ```
   EMAIL_SENDER=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
   GROQ_API_KEY=your-groq-api-key
   ```

4. **Generate Domain:**
   - In Railway dashboard, go to Settings → Generate Domain
   - Your app will be live at `https://your-app.railway.app`

**GitHub Actions Setup (Optional):**
```bash
# Add Railway token to GitHub secrets
# Go to GitHub repo → Settings → Secrets → New repository secret
# Name: RAILWAY_TOKEN
# Value: Get from Railway account settings
```

---

### Option 2: Render (Free Tier)

1. **Create `render.yaml`:**
   ```yaml
   services:
     - type: web
       name: news-mailer
       env: docker
       plan: free
       envVars:
         - key: EMAIL_SENDER
           sync: false
         - key: EMAIL_PASSWORD
           sync: false
         - key: GROQ_API_KEY
           sync: false
   ```

2. **Deploy:**
   - Go to [render.com](https://render.com)
   - New → Web Service → Connect GitHub repository
   - Render auto-detects Dockerfile
   - Add environment variables
   - Deploy

3. **GitHub Actions:**
   - Get deploy hook URL from Render dashboard
   - Add to GitHub secrets as `RENDER_DEPLOY_HOOK_URL`

---

### Option 3: Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Create app
flyctl launch

# Set secrets
flyctl secrets set EMAIL_SENDER=your@email.com
flyctl secrets set EMAIL_PASSWORD=your-password
flyctl secrets set GROQ_API_KEY=your-key

# Deploy
flyctl deploy
```

---

### Option 4: Docker Compose (VPS/Cloud VM)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  news-mailer:
    build: .
    ports:
      - "8000:8000"
    environment:
      - EMAIL_SENDER=${EMAIL_SENDER}
      - EMAIL_PASSWORD=${EMAIL_PASSWORD}
      - GROQ_API_KEY=${GROQ_API_KEY}
    restart: unless-stopped
```

Deploy:
```bash
# On your VPS
git clone YOUR_REPO
cd YOUR_REPO
cp .env.example .env  # Edit with your credentials
docker-compose up -d
```

---

### Option 5: AWS/GCP/Azure

**Using Docker:**
1. Build and push to container registry
2. Deploy to:
   - **AWS:** ECS, App Runner, or Elastic Beanstalk
   - **GCP:** Cloud Run or App Engine
   - **Azure:** Container Instances or App Service

---

## 🔐 Environment Variables

Required variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `EMAIL_SENDER` | Gmail address to send from | `yourbot@gmail.com` |
| `EMAIL_PASSWORD` | Gmail app password | `abcd efgh ijkl mnop` |
| `GROQ_API_KEY` | Groq API key for LLM | `gsk_...` |

**Getting Gmail App Password:**
1. Enable 2FA on your Google account
2. Go to Google Account → Security → 2-Step Verification → App Passwords
3. Generate a password for "Mail"
4. Use that 16-character password (not your regular password)

---

## 📡 API Endpoints

### Web UI
- `GET /` - Main form interface

### API Endpoints
- `GET /health` - Health check
- `POST /send-news` - Send news digest
  ```json
  {
    "email": "receiver@example.com",
    "hours_back": 24,
    "name": "John Doe"
  }
  ```

---

## 🧪 Testing Locally

```bash
# Start server
python news_agent_copy.py

# Test API
curl -X POST http://localhost:8000/send-news \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","hours_back":24,"name":"Test User"}'
```

---

## 🔄 GitHub Actions Auto-Deploy

The workflow `.github/workflows/deploy.yml` automatically deploys on push to `main` branch.

**Setup:**
1. Add secrets to GitHub (Settings → Secrets):
   - `RAILWAY_TOKEN` (if using Railway)
   - `RENDER_DEPLOY_HOOK_URL` (if using Render)
   - `DOCKER_USERNAME` + `DOCKER_PASSWORD` (if using Docker Hub)

2. Push to main:
   ```bash
   git push origin main
   ```

---

## 🐛 Troubleshooting

**Email not sending:**
- Check Gmail app password is correct
- Ensure 2FA is enabled on Gmail account
- Check spam folder

**Groq API errors:**
- Verify API key is valid
- Check rate limits (model fallback should handle this)

**Static files not loading:**
- Ensure `static/` folder exists with `index.html`
- Check file paths in Dockerfile

---

## 📝 Customization

**Add more news sources:**
Edit `RSS_FEEDS` list in `news_agent_copy.py`:
```python
RSS_FEEDS.append({
    "name": "Your Source",
    "url": "https://example.com/rss",
    "category": "Tech"
})
```

**Modify email template:**
Edit `build_email_html()` function for custom styling.

**Change GIF selection:**
Update `pick_context_gif()` function with your logic.

---

## 📊 Monitoring

- Railway: Built-in logs and metrics
- Render: Logs tab in dashboard
- Fly.io: `flyctl logs`
- Docker: `docker logs <container-id>`

---

## 🎉 Done!

Your News Mailer API is now deployed and ready to send personalized news digests!

**Questions?** Open an issue on GitHub.
