# 🚀 Deployment Checklist

Use this checklist to deploy your News Mailer API to production.

## ✅ Pre-Deployment Checklist

### 1. Environment Setup
- [ ] Get Gmail App Password
  - Enable 2FA on your Gmail account
  - Go to Google Account → Security → 2-Step Verification → App Passwords
  - Generate password and save it
  
- [ ] Get Groq API Key
  - Sign up at https://console.groq.com
  - Create API key and save it

### 2. Test Locally
- [ ] Copy `.env.example` to `.env`
- [ ] Add your credentials to `.env`
- [ ] Run `python news_agent_copy.py`
- [ ] Open http://localhost:8000
- [ ] Test sending an email to yourself
- [ ] Verify email received with proper formatting

### 3. Prepare for Deployment
- [ ] Create GitHub repository (if not exists)
- [ ] Commit all files:
  ```bash
  git init
  git add .
  git commit -m "Initial deployment setup"
  ```
- [ ] Add `.env` to `.gitignore` (security!)
- [ ] Push to GitHub:
  ```bash
  git remote add origin YOUR_REPO_URL
  git push -u origin main
  ```

## 🌐 Deployment Options

Choose ONE platform below:

### Option A: Railway (Recommended)
- [ ] Go to https://railway.app
- [ ] Click "New Project" → "Deploy from GitHub repo"
- [ ] Select your repository
- [ ] Add environment variables:
  - `EMAIL_SENDER`
  - `EMAIL_PASSWORD`
  - `GROQ_API_KEY`
- [ ] Click "Deploy"
- [ ] Generate domain in Settings
- [ ] Test your endpoint: `https://your-app.railway.app`

### Option B: Render
- [ ] Go to https://render.com
- [ ] Click "New" → "Web Service"
- [ ] Connect GitHub repository
- [ ] Add environment variables (as above)
- [ ] Click "Create Web Service"
- [ ] Wait for deployment
- [ ] Test your endpoint: `https://your-app.onrender.com`

### Option C: Fly.io
- [ ] Install flyctl: `curl -L https://fly.io/install.sh | sh`
- [ ] Login: `flyctl auth login`
- [ ] Launch: `flyctl launch`
- [ ] Set secrets:
  ```bash
  flyctl secrets set EMAIL_SENDER=your@email.com
  flyctl secrets set EMAIL_PASSWORD=your-password
  flyctl secrets set GROQ_API_KEY=your-key
  ```
- [ ] Deploy: `flyctl deploy`

## 🎯 Post-Deployment

### 1. Test Production Endpoint
- [ ] Visit your deployed URL
- [ ] Fill out the form
- [ ] Send test email
- [ ] Verify email received

### 2. Setup GitHub Actions (Optional)
- [ ] Add deployment secrets to GitHub:
  - Go to repo Settings → Secrets → Actions
  - Add `RAILWAY_TOKEN` (Railway) or `RENDER_DEPLOY_HOOK_URL` (Render)
- [ ] Push to main branch to trigger auto-deploy
- [ ] Verify workflow runs successfully

### 3. Monitor
- [ ] Check application logs for errors
- [ ] Monitor email delivery rate
- [ ] Watch for Groq API rate limits

## 🔧 Troubleshooting

### Email Not Sending
- [ ] Verify Gmail App Password is correct
- [ ] Check 2FA is enabled on Gmail
- [ ] Look in spam folder
- [ ] Check application logs for SMTP errors

### Groq API Errors
- [ ] Verify API key is correct
- [ ] Check remaining credits/limits
- [ ] Review model fallback logs

### Static Files Not Loading
- [ ] Ensure `static/` directory is included in deployment
- [ ] Check Dockerfile copies static files
- [ ] Verify FastAPI static mount is configured

### Deployment Failed
- [ ] Check all environment variables are set
- [ ] Verify Dockerfile syntax
- [ ] Review platform-specific logs
- [ ] Ensure requirements.txt is complete

## 📊 Success Metrics

After deployment, you should see:
- ✅ Health endpoint returns `{"status": "ok"}`
- ✅ Root URL shows the web form
- ✅ Form submission sends email successfully
- ✅ Email arrives with proper HTML formatting
- ✅ No errors in application logs

## 🎉 You're Done!

Your News Mailer API is now live and ready to send personalized news digests!

**Share your deployment:** 
Tweet your deployed app with #NewsMailerAPI

**Need help?**
- 📖 Read [DEPLOYMENT.md](DEPLOYMENT.md)
- 🐛 Open an issue on GitHub
- 💬 Check existing issues for solutions

---

Made with ❤️ Happy Deploying!
