# ⚽ Transfer Market Aggregator - Setup Guide

Real-time transfer alerts across Liga MX and Europe's top 5 leagues via Telegram + dashboard.

---

## 🚀 Quick Start (5 minutes)

### 1. **Create a Telegram Bot**

- Message [@BotFather](https://t.me/botfather) on Telegram
- Send `/newbot`
- Follow the prompts (name: "Transfer Alert Bot", username: "transfer_alerts_bot")
- Copy the token provided → save as `TELEGRAM_BOT_TOKEN`

Get your **Chat ID**:
- Message [@userinfobot](https://t.me/userinfobot) to get your user ID
- Or send any message to your bot and check updates at: `https://api.telegram.org/botTOKEN/getUpdates`
- Look for `message.chat.id` → save as `TELEGRAM_CHAT_ID`

### 2. **Set Up Supabase**

1. Create free account at [supabase.com](https://supabase.com)
2. Create a new project (free tier is plenty)
3. Go to **SQL Editor** → paste contents of `schema.sql` → run all
4. Copy your `SUPABASE_URL` and `SUPABASE_KEY` from settings → add to `.env`

### 3. **Deploy to Railway** ✨ (Recommended)

Railway is perfect for this because it's free tier is generous + integrates seamlessly.

#### Option A: Deploy directly from GitHub (easiest)

1. Push this code to a GitHub repo
2. Go to [railway.app](https://railway.app) → sign up
3. Click **New Project** → select your GitHub repo
4. Railway auto-detects FastAPI + sets up Python 3.11
5. Add environment variables:
   - Go to **Project Settings** → **Variables**
   - Paste all values from `.env`
6. Railway builds & deploys automatically ✅

#### Option B: Deploy from CLI (if you prefer local first)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create Railway project in this directory
railway init

# Set environment variables
railway variables set SUPABASE_URL=...
railway variables set SUPABASE_KEY=...
railway variables set TELEGRAM_BOT_TOKEN=...
railway variables set TELEGRAM_CHAT_ID=...

# Deploy
railway up
```

Railway gives you a public URL like: `https://your-app.railway.app`

### 4. **Initialize Database**

Call the init endpoint once to create tables:

```bash
curl -X POST https://your-app.railway.app/init-db
```

### 5. **Test It Out**

Send a test alert:

```bash
curl -X POST https://your-app.railway.app/test-alert
```

You should get a message on Telegram! ✅

---

## 📊 API Endpoints

### Health Check
```
GET /health
```

### Get Recent Transfers
```
GET /transfers?league=Premier League&days=7&player=Haaland
```

Query params:
- `league` (optional): Filter by league name
- `player` (optional): Search player name (partial match)
- `days` (optional): How far back to fetch (default: 7)

Example response:
```json
{
  "count": 5,
  "transfers": [
    {
      "player_name": "Kylian Mbappé",
      "from_club": "PSG",
      "to_club": "Real Madrid",
      "league": "La Liga",
      "status": "Confirmed",
      "fee": "€180M",
      "reliability_score": 0.99,
      "sources": ["Official", "Sky Sports", "Transfermarkt"],
      "created_at": "2024-08-15T12:34:56Z"
    }
  ],
  "fetched_at": "2024-08-18T10:15:22Z"
}
```

### Manual Aggregation Trigger
```
POST /run-aggregation
```

This runs the scraper immediately (useful for testing). Normally runs every 4 hours.

---

## 🔧 Configuration

### Change Aggregation Frequency

In `transfer_bot.py`, find this line:

```python
scheduler.add_job(
    aggregate_transfers,
    IntervalTrigger(hours=4),  # <-- Change this
    id="transfer_aggregation",
)
```

Options:
- `hours=2` — every 2 hours
- `hours=1` — every hour (be careful with free tiers)
- `minutes=30` — every 30 minutes

### Adjust Alert Threshold

Only alerts if reliability > threshold. In `aggregate_transfers()`:

```python
if reliability > 0.60:  # <-- Adjust this (0.0 - 1.0)
    await send_telegram_alert(transfer, reliability)
```

Higher = fewer alerts but more reliable.

### Add/Remove Leagues

In `scraper.scrape_league_official()`:

```python
leagues = {
    "premier_league": "...",
    "la_liga": "...",
    # Add more or remove...
}
```

---

## 📈 Understanding Reliability Scores

```
1.0 — Official league/club announcements
0.99 — Fabrizio Romano (best journalist)
0.95 — Transfermarkt official database
0.90 — Sky Sports, ESPN
0.75 — Secondary sources
0.50 — Unknown/unverified sources
```

Alerts only fire for transfers > `alert_min_reliability` (default: 0.60).

---

## 🔍 Monitoring & Logs

### Check live logs on Railway

1. Go to your Railway project
2. Click **Deployments** → most recent
3. Click **View Logs** tab
4. Watch real-time aggregation output

### Common issues:

**"Supabase connection error"**
- Verify `SUPABASE_URL` and `SUPABASE_KEY` are correct
- Check if Supabase project is active (not paused)

**"Telegram: 401 Unauthorized"**
- `TELEGRAM_BOT_TOKEN` is wrong or expired
- Re-create bot with @BotFather

**"No transfers found"**
- Web scrapers might need updates (websites change HTML)
- Check logs for scrape errors
- Can manually trigger with `/run-aggregation` endpoint

---

## 🎯 Next Steps (Phase 2)

Once you're getting alerts reliably:

### Build the React Dashboard
- Fetch transfers from `/transfers` endpoint
- Display by league with filtering
- Show reliability score + sources
- Search player across all 6 leagues

### Add User Preferences (multi-user)
- Let users pick which leagues to follow
- Set their own alert threshold
- Auto-mute certain clubs

### Enhance Scrapers
- Use **Transfermarkt API** (paid) for 100% accuracy
- Parse official league JSON feeds
- Integrate Twitter API for Fabrizio Romano
- Monitor Reddit r/soccer early discussions

### Build Alerts Dashboard
- History of sent alerts
- See which sources were first to report
- Track accuracy over time

---

## 📱 Telegram Bot Commands (Future)

```
/start — Subscribe to all leagues
/leagues — Pick which leagues to follow
/players — Follow specific players
/settings — Adjust alert threshold
/latest — See recent transfers
/search Player Name — Search a player
```

---

## 💾 Database Backups

Supabase has automatic daily backups on the free tier. To manually export:

1. Go to Supabase SQL Editor
2. Run: `SELECT * FROM transfers`
3. Click "Export" → CSV/JSON

Or use CLI:
```bash
supabase db dump -f transfers_backup.sql
```

---

## 🆘 Troubleshooting

### Bot not sending alerts?
1. Test endpoint: `POST /test-alert`
2. Check Railway logs for errors
3. Verify Telegram chat ID is correct (should be negative number for groups)

### Missing transfers?
1. Aggregation runs every 4 hours by default
2. Trigger manually: `POST /run-aggregation`
3. Check scraper logs — websites may have changed HTML

### Supabase table issues?
1. Re-run `schema.sql` in SQL Editor
2. Check table exists: `SELECT * FROM transfers LIMIT 1`
3. Verify RLS policies aren't blocking access

---

## 📞 Support

- Railway docs: https://docs.railway.app
- Supabase docs: https://supabase.com/docs
- FastAPI docs: https://fastapi.tiangolo.com

---

**You're all set!** 🎉 You should start receiving transfer alerts on Telegram immediately after deployment.

Let me know when it's live and we'll build out the dashboard next! 🚀
