⚽ **Transfer Market Bot** — Real-time alerts across Liga MX & Europe's top 5 leagues

Get Telegram notifications the instant players move between clubs.

---

## 🎯 What This Does

Monitors **Transfermarkt, ESPN, Sky Sports, League Official feeds, Fabrizio Romano**, and more.

- **Aggregates** transfers from 6+ sources every 4 hours
- **Deduplicates** by player + clubs (no spam!)
- **Scores reliability** (0-100%) based on source tier
- **Sends Telegram alerts** instantly when transfers confirmed
- **Stores everything** in Supabase for browsing later

**Example alert:**
```
✅ CONFIRMED

⚽ Kylian Mbappé
PSG → Real Madrid
💰 Fee: €180M
🏆 La Liga
📊 Reliability: 99%

📰 Sources: Official, Sky Sports, Transfermarkt
```

Covers:
- 🇪🇬 **Premier League** (England)
- 🇪🇸 **La Liga** (Spain)
- 🇮🇹 **Serie A** (Italy)
- 🇩🇪 **Bundesliga** (Germany)
- 🇫🇷 **Ligue 1** (France)
- 🇲🇽 **Liga MX** (Mexico)

---

## ⚡ Quick Start (10 minutes)

### 1. Run automated setup
```bash
chmod +x setup.sh
./setup.sh
```

This:
- ✅ Creates Python virtual environment
- ✅ Installs dependencies
- ✅ Sets up git repo
- ✅ Creates `.env` file
- ✅ Checks everything works

### 2. Add your credentials
```bash
nano .env
```

You need 4 things (takes 5 minutes to gather):
- **Telegram Bot Token** — Message [@BotFather](https://t.me/botfather), `/newbot`
- **Telegram Chat ID** — Message [@userinfobot](https://t.me/userinfobot)
- **Supabase URL** — Create free account at [supabase.com](https://supabase.com), create project
- **Supabase Key** — Copy from Supabase project settings

### 3. Deploy to Railway
```bash
git remote add origin https://github.com/YOUR_USERNAME/transfer-alerts.git
git push origin main
```

Then:
- Go to [railway.app](https://railway.app)
- New Project → GitHub → select `transfer-alerts`
- Add environment variables (copy from `.env`)
- Railway auto-deploys ✅

### 4. Initialize & test
```bash
curl -X POST https://YOUR_RAILWAY_APP.railway.app/init-db
curl -X POST https://YOUR_RAILWAY_APP.railway.app/test-alert
```

You should get a test message on Telegram! 📱

---

## 📁 Project Structure

```
transfer-alerts/
├── transfer_bot.py              # FastAPI backend + scraper
├── schema.sql                   # Database schema (run in Supabase)
├── requirements.txt             # Python packages
├── Dockerfile                   # Container config
├── docker-compose.yml           # Local testing
├── setup.sh                     # Automated setup (run this!)
├── test_api.sh                  # API testing script
├── .env.example                 # Env vars template
├── .gitignore                   # Git ignore
├── SETUP.md                     # Full setup guide
├── API_REFERENCE.md             # Endpoint documentation
├── DEPLOYMENT_CHECKLIST.md      # Quick checklist
└── README.md                    # This file
```

---

## 🚀 Features

### Real-time Aggregation
- Runs every 4 hours (configurable)
- Scrapes 6+ sources in parallel
- Smart deduplication (same transfer = one alert)
- Reliability scoring (0-100%)

### Telegram Alerts
- Automatic daily transfer digest
- Instant alerts for big signings
- Source attribution (which journalist/site reported it?)
- Adjustable confidence threshold

### API Endpoints
```bash
# Health check
GET /health

# Get transfers by league
GET /transfers?league=premier_league&days=7

# Search player
GET /transfers?player=Haaland

# Manually run scraper
POST /run-aggregation

# Send test alert
POST /test-alert
```

See `API_REFERENCE.md` for full docs.

### Database
- Supabase PostgreSQL (free tier is plenty)
- Stores transfer history
- User preferences (future)
- Alert logs

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| `SETUP.md` | Detailed setup walkthrough |
| `API_REFERENCE.md` | All endpoints + examples |
| `DEPLOYMENT_CHECKLIST.md` | Quick reference checklist |
| `test_api.sh` | Test endpoints quickly |

---

## 🛠️ Local Development

### Test locally with Docker
```bash
docker-compose up
```

Then:
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/test-alert
```

### Run aggregation manually
```bash
curl -X POST http://localhost:8000/run-aggregation
```

### Check logs
```bash
docker-compose logs -f transfer-bot
```

---

## 🔧 Customization

### Change aggregation frequency
Edit `transfer_bot.py`, line ~250:
```python
scheduler.add_job(
    aggregate_transfers,
    IntervalTrigger(hours=4),  # Change to 2, 1, etc.
    id="transfer_aggregation",
)
```

### Adjust alert threshold
Edit `transfer_bot.py`, line ~270:
```python
if reliability > 0.60:  # Only alert for 60%+ confidence
    await send_telegram_alert(transfer, reliability)
```

### Add/remove leagues
Edit scraper in `transfer_bot.py`, function `scrape_league_official()`:
```python
leagues = {
    "premier_league": "https://...",
    # Add or remove leagues here
}
```

---

## 📊 Reliability Scores

| Score | Tier | Examples |
|-------|------|----------|
| 0.95-1.0 | Official | League announcements, Official club statements |
| 0.90-0.94 | Major News | Sky Sports, ESPN, Transfermarkt Official |
| 0.70-0.89 | Journalists | Fabrizio Romano, secondary reporters |
| 0.50-0.69 | Mixed | Aggregators, blogs |
| <0.50 | Unverified | Reddit, forums, rumors |

Default alert threshold: **0.60** (only "Mixed" tier and above)

---

## 🚨 Troubleshooting

### No alerts appearing?
1. Test locally: `docker-compose up`
2. Send test: `curl -X POST http://localhost:8000/test-alert`
3. Check logs for errors
4. Verify Telegram chat ID is correct (negative number for groups)

### Supabase connection error?
1. Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
2. Check Supabase project is active (not paused)
3. Re-run schema.sql if tables missing

### Scrapers not working?
1. Check Railway logs for specific errors
2. Try manual aggregation: `POST /run-aggregation`
3. Note: Website scraping can break if site HTML changes

### Database issues?
1. Go to Supabase SQL Editor
2. Run: `SELECT * FROM transfers LIMIT 1`
3. If no results, re-run `schema.sql`

---

## 🔗 Links

- **Railway**: https://railway.app (deployment)
- **Supabase**: https://supabase.com (database)
- **Telegram**: https://t.me/botfather (create bot)
- **GitHub**: https://github.com (code hosting)

---

## 📋 API Examples

### Get Premier League transfers
```bash
curl "http://localhost:8000/transfers?league=premier_league"
```

### Search for a player
```bash
curl "http://localhost:8000/transfers?player=Bellingham"
```

### Only confirmed deals
```bash
curl "http://localhost:8000/transfers" | jq '.transfers[] | select(.status=="Confirmed")'
```

### Export to CSV
```bash
curl "http://localhost:8000/transfers" | \
  jq -r '.transfers[] | [.player_name, .from_club, .to_club, .fee] | @csv' > transfers.csv
```

See `API_REFERENCE.md` for more examples.

---

## 🎯 Next Steps (After Deployment)

Once alerts are working:

1. **Build React Dashboard**
   - Browse transfers by league
   - Filter by status, reliability, date
   - Search players across all 6 leagues
   - See which sources reported first

2. **Add User Preferences**
   - Pick which leagues to follow
   - Set your own alert threshold
   - Favorite specific players
   - Mute certain clubs

3. **Enhance Scrapers**
   - Integrate Transfermarkt API (paid)
   - Monitor Twitter for real-time journalist posts
   - Parse official league JSON APIs
   - Track Reddit r/soccer early discussions

---

## 📝 Environment Variables

| Variable | Example | Where to Get |
|----------|---------|--------------|
| `SUPABASE_URL` | `https://abc123.supabase.co` | Supabase dashboard |
| `SUPABASE_KEY` | `eyJhbGc...` | Supabase settings |
| `TELEGRAM_BOT_TOKEN` | `123456:ABCdef...` | @BotFather on Telegram |
| `TELEGRAM_CHAT_ID` | `-987654321` | @userinfobot on Telegram |

---

## 💬 Questions?

Check the docs:
- Full setup? → `SETUP.md`
- API endpoints? → `API_REFERENCE.md`
- Quick checklist? → `DEPLOYMENT_CHECKLIST.md`

---

**Ready?** 🚀

```bash
./setup.sh
nano .env
git push
# Deploy to Railway
# 🎉 Profit!
```

Enjoy never missing a transfer again! ⚽
