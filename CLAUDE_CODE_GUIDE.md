# 🤖 Claude Code Guide for Transfer Bot Setup

This guide explains how to use **Claude Code** to complete the remaining setup steps.

---

## 📋 What's Already Done

✅ **Complete backend written** (`transfer_bot.py`)
✅ **Database schema created** (`schema.sql`)
✅ **All dependencies listed** (`requirements.txt`)
✅ **Docker setup ready** (`Dockerfile`, `docker-compose.yml`)
✅ **Setup script created** (`setup.sh`)
✅ **Full documentation** (README, guides, API docs)

All files are in: `/home/claude/transfer-alerts/`

---

## 🚀 Next Steps (Use Claude Code Here)

### Step 1: Download the Project

**Option A: Download ZIP**
1. Go to `/home/claude/transfer-alerts/`
2. Zip all files
3. Download to your local machine

**Option B: Clone from GitHub** (easier if you have GitHub already)
1. Create GitHub repo
2. Push files
3. Clone on your machine

---

### Step 2: Run Setup with Claude Code

Open Claude Code in your terminal and navigate to the project:

```bash
cd path/to/transfer-alerts
```

Then let Claude Code handle it:

```
"Set up the transfer market bot for me"
```

Claude Code will:
1. ✅ Run `./setup.sh` (creates venv, installs dependencies)
2. ✅ Create `.env` file from `.env.example`
3. ✅ Initialize git repo
4. ✅ Test Python installation
5. ✅ Show you what to do next

---

### Step 3: Get Your Credentials

While Claude Code runs setup, gather these 4 things:

#### 🤖 Telegram Bot Token
1. Open Telegram
2. Message [@BotFather](https://t.me/botfather)
3. Send: `/newbot`
4. Follow prompts (name your bot)
5. Copy the token provided
6. Paste in `.env` as `TELEGRAM_BOT_TOKEN`

**Example:**
```
TELEGRAM_BOT_TOKEN=123456:ABCdefXYZ789
```

#### 💬 Telegram Chat ID
1. Message [@userinfobot](https://t.me/userinfobot)
2. It responds with your ID
3. Copy the number (usually starts with `-`)
4. Paste in `.env` as `TELEGRAM_CHAT_ID`

**Example:**
```
TELEGRAM_CHAT_ID=-987654321
```

#### 🗄️ Supabase URL & Key
1. Go to [supabase.com](https://supabase.com)
2. Sign up free (takes 1 minute)
3. Create new project
4. Go to **Settings** → **API**
5. Copy **Project URL** → `SUPABASE_URL`
6. Copy **anon public** key → `SUPABASE_KEY`

**Example:**
```
SUPABASE_URL=https://abc123.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

### Step 4: Add Credentials with Claude Code

Ask Claude Code:

```
"Add these environment variables to .env:
SUPABASE_URL=https://...
SUPABASE_KEY=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=..."
```

Claude Code will:
1. ✅ Update `.env` with your values
2. ✅ Verify format is correct
3. ✅ Create `.env.local` if needed

---

### Step 5: Test Locally with Claude Code

Ask Claude Code:

```
"Test the transfer bot locally using docker-compose"
```

Claude Code will:
1. ✅ Run `docker-compose up`
2. ✅ Wait for services to start
3. ✅ Call `/health` endpoint
4. ✅ Show you the results

You should see:
```json
{"status": "ok", "timestamp": "..."}
```

If it works → **Proceed to Step 6!**

---

### Step 6: Deploy to Railway with Claude Code

Ask Claude Code:

```
"Help me deploy this to Railway using GitHub"
```

Claude Code will guide you through:
1. ✅ Creating/using GitHub repo
2. ✅ Committing code to git
3. ✅ Pushing to GitHub
4. ✅ Setting up Railway project
5. ✅ Adding environment variables to Railway
6. ✅ Triggering deployment

Or if you prefer manual Railway setup, ask:

```
"Show me the Railway deployment steps"
```

---

### Step 7: Initialize Database

Once deployed to Railway, ask Claude Code:

```
"Initialize the Supabase database by running the schema"
```

Claude Code will:
1. ✅ Connect to your Supabase project
2. ✅ Run `schema.sql` in SQL editor
3. ✅ Verify tables created

---

### Step 8: Test Everything

Ask Claude Code:

```
"Test the transfer bot API on Railway"
```

Claude Code will:
1. ✅ Call `GET /health` → should return OK
2. ✅ Call `POST /init-db` → initializes database
3. ✅ Call `POST /test-alert` → sends test Telegram message
4. ✅ Check your Telegram for message

**You should get a Telegram message!** 🎉

---

## 📝 Claude Code Commands (Quick Reference)

### Setup
```
"Run setup.sh to initialize the project"
"Create and activate Python virtual environment"
"Install dependencies from requirements.txt"
```

### Testing
```
"Start docker-compose and test the API locally"
"Send a test alert to verify Telegram is working"
"Check if the database is connected"
```

### Deployment
```
"Push code to GitHub and deploy to Railway"
"Add environment variables to Railway"
"Initialize the Supabase database"
```

### Debugging
```
"Show me the logs from the running bot"
"Test the /health endpoint"
"Get the API response from /transfers"
```

---

## 🆘 If Something Goes Wrong

### "Setup failed"
Ask Claude Code:
```
"Troubleshoot the setup - check Python version and dependencies"
```

### "Can't connect to Supabase"
Ask Claude Code:
```
"Verify Supabase credentials in .env and test connection"
```

### "Telegram not sending"
Ask Claude Code:
```
"Test Telegram bot token and verify chat ID is correct"
```

### "Docker not working"
Ask Claude Code:
```
"Debug docker-compose - check if Docker is running"
```

---

## 💡 Pro Tips

1. **Save credentials securely**
   - Don't commit `.env` to GitHub
   - `.gitignore` already excludes it ✅

2. **Use Railway secrets**
   - Store production credentials in Railway, not GitHub
   - Claude Code will help you copy them over

3. **Check logs frequently**
   - Railway dashboard shows real-time logs
   - Docker logs show local testing
   - Ask Claude Code to "show me the logs"

4. **Test incremental**
   - Test locally first (`docker-compose`)
   - Then test on Railway
   - Test Telegram last (confirms everything works)

---

## 📊 Architecture Overview

```
Your Machine
├── Claude Code (orchestrates setup)
├── transfer_bot.py (FastAPI backend)
├── .env (your secrets)
├── Docker (tests locally)
└── Git (version control)

GitHub
└── transfer-alerts repo

Railway
├── transfer-bot service (FastAPI)
├── Environment variables
└── Auto-deploys on git push

Supabase
└── PostgreSQL database
    ├── transfers table
    ├── user_preferences table
    └── alert_log table

Telegram
└── Bot receives alerts
```

---

## 🎬 Example Claude Code Session

```
You: "Set up the transfer bot completely"

Claude Code:
✅ Running setup.sh...
✅ Python venv created
✅ Dependencies installed
✅ Git initialized
📋 Needs: .env credentials

You: "Add these to .env: [paste credentials]"

Claude Code:
✅ .env updated
✅ Testing connection to Supabase...
✅ Supabase working

You: "Test locally"

Claude Code:
✅ docker-compose up
✅ Waiting for services...
✅ Testing /health endpoint
✅ API responding

You: "Deploy to Railway"

Claude Code:
✅ Pushing to GitHub
✅ Creating Railway project
✅ Adding env variables
✅ Deploying...
✅ Live at: https://transfer-bot.railway.app

You: "Send a test alert"

Claude Code:
✅ Calling /test-alert endpoint
✅ Telegram message sent
📱 Check your Telegram!
```

---

## 🚀 Final Checklist (Use Claude Code for All!)

- [ ] Run `./setup.sh`
- [ ] Add credentials to `.env`
- [ ] Test locally with `docker-compose`
- [ ] Create GitHub repo + push
- [ ] Deploy to Railway
- [ ] Initialize Supabase database
- [ ] Send test alert
- [ ] **Verify Telegram receives message**
- [ ] Wait for first scheduled aggregation (4 hours)
- [ ] **Start getting transfer alerts!** 🎉

---

**Ready?** Open Claude Code and ask:

```
"Help me set up and deploy the transfer market bot"
```

Let Claude Code handle the heavy lifting while you grab your credentials! 🚀
