# ✅ Deployment Checklist

Quick reference for getting transfers alerts live in 10 minutes.

## 🎬 Setup (Do This First)

- [ ] **Create Telegram Bot**
  - Message @BotFather on Telegram
  - `/newbot` → follow prompts
  - Copy token → save as `TELEGRAM_BOT_TOKEN`
  - Message @userinfobot → copy chat ID → save as `TELEGRAM_CHAT_ID`

- [ ] **Setup Supabase**
  - Sign up free at supabase.com
  - Create new project
  - SQL Editor → paste `schema.sql` → run
  - Copy `SUPABASE_URL` and `SUPABASE_KEY` from settings

- [ ] **Gather Environment Variables**
  ```
  SUPABASE_URL=https://...
  SUPABASE_KEY=...
  TELEGRAM_BOT_TOKEN=...
  TELEGRAM_CHAT_ID=...
  ```

## 🚀 Deploy to Railway

**Option 1: GitHub (Easiest)**
- [ ] Push code to GitHub
- [ ] Go to railway.app → login
- [ ] New Project → select repo
- [ ] Add env variables
- [ ] Deploy ✅

**Option 2: Railway CLI**
- [ ] `railway login`
- [ ] `railway init`
- [ ] `railway variables set KEY=VALUE` (for each variable)
- [ ] `railway up`
- [ ] Copy public URL

**Option 3: Local Docker (Test First)**
- [ ] Create `.env` file from `.env.example`
- [ ] `docker-compose up`
- [ ] Test at http://localhost:8000/health

## 🧪 Testing

- [ ] Health check: `curl -X GET http://YOUR_URL/health`
- [ ] Test alert: `curl -X POST http://YOUR_URL/test-alert`
- [ ] Check Telegram for message
- [ ] Init DB: `curl -X POST http://YOUR_URL/init-db`

## 📊 First Run

- [ ] Wait for first aggregation (runs automatically every 4 hours)
- [ ] Or trigger manually: `curl -X POST http://YOUR_URL/run-aggregation`
- [ ] Check Telegram for transfer alerts 📱
- [ ] View transfers: `curl "http://YOUR_URL/transfers"`

## 📈 Monitoring

- [ ] Check Railway logs: Project → Deployments → View Logs
- [ ] Monitor aggregation runs
- [ ] Verify Telegram messages arriving

## 🎯 Customization (Optional)

- [ ] Adjust aggregation frequency (transfer_bot.py, line ~250)
- [ ] Change alert threshold (transfer_bot.py, line ~270)
- [ ] Add/remove leagues (schema.sql, user_preferences)
- [ ] Customize Telegram message format (send_telegram_alert function)

## 📋 Environment Variables Reference

| Variable | Example | Where to Get |
|----------|---------|--------------|
| `SUPABASE_URL` | `https://abc123.supabase.co` | Supabase dashboard |
| `SUPABASE_KEY` | `eyJhbGc...` | Supabase settings |
| `TELEGRAM_BOT_TOKEN` | `123456:ABCdef...` | @BotFather |
| `TELEGRAM_CHAT_ID` | `-987654321` | @userinfobot |

## 🔗 Quick Links

- Railway: https://railway.app
- Supabase: https://supabase.com
- Telegram BotFather: https://t.me/botfather
- User Info Bot: https://t.me/userinfobot

## 📞 If Stuck

**No alerts appearing:**
1. Test endpoint: `curl -X POST http://YOUR_URL/test-alert`
2. Check Railway logs
3. Verify Telegram chat ID is correct
4. Manually run: `curl -X POST http://YOUR_URL/run-aggregation`

**Database errors:**
1. Re-run schema.sql in Supabase
2. Verify SUPABASE_KEY is correct
3. Check Supabase project is active

**Scraper not working:**
1. Check logs for specific errors
2. Trigger manual run
3. Wait for next scheduled run (4 hours)

---

**You're all set!** Once deployed, you'll get transfer alerts on Telegram immediately. 🎉

Next: Build the React dashboard to browse all transfers by league. Let me know when it's live!
