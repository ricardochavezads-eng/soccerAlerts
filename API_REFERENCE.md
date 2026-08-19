# 📡 Transfer Bot API Reference

Complete guide to all endpoints and their usage.

---

## Base URL

**Local (development):**
```
http://localhost:8000
```

**Production (Railway):**
```
https://your-app.railway.app
```

---

## Endpoints

### 1. Health Check ✅

Check if the API is running and responsive.

```http
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-08-18T15:32:45.123456"
}
```

**Example:**
```bash
curl http://localhost:8000/health | jq .
```

---

### 2. Get Transfers 📊

Retrieve recent transfers with optional filtering.

```http
GET /transfers?league=LEAGUE&player=PLAYER&days=DAYS
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `league` | string | - | Filter by league (optional). Values: `premier_league`, `la_liga`, `serie_a`, `bundesliga`, `ligue_1`, `liga_mx` |
| `player` | string | - | Search player name (partial/case-insensitive). Optional. |
| `days` | integer | 7 | How many days back to fetch transfers. Optional. |

**Response:**
```json
{
  "count": 3,
  "transfers": [
    {
      "id": 1,
      "player_name": "Kylian Mbappé",
      "from_club": "Paris Saint-Germain",
      "to_club": "Real Madrid",
      "league": "La Liga",
      "status": "Confirmed",
      "fee": "€180M",
      "fee_numeric": 180000000,
      "reliability_score": 0.99,
      "sources": ["Official", "Sky Sports", "Transfermarkt"],
      "source_urls": ["https://...", "https://..."],
      "transfer_date": "2024-07-15T00:00:00",
      "announced_date": "2024-07-14T18:30:00",
      "created_at": "2024-07-14T18:35:22.123456",
      "updated_at": "2024-07-14T18:35:22.123456"
    }
  ],
  "fetched_at": "2024-08-18T15:32:45.123456"
}
```

**Examples:**

Get all transfers from last 7 days:
```bash
curl "http://localhost:8000/transfers"
```

Get La Liga transfers:
```bash
curl "http://localhost:8000/transfers?league=la_liga"
```

Get Liga MX transfers from last 30 days:
```bash
curl "http://localhost:8000/transfers?league=liga_mx&days=30"
```

Search for Haaland across all leagues:
```bash
curl "http://localhost:8000/transfers?player=Haaland"
```

Search within a league:
```bash
curl "http://localhost:8000/transfers?league=premier_league&player=Saka"
```

Get only very reliable transfers:
```bash
# Note: filtering by reliability done client-side
curl "http://localhost:8000/transfers" | jq '.transfers[] | select(.reliability_score > 0.9)'
```

---

### 3. Test Alert 📱

Send a test Telegram alert to verify your bot is working.

```http
POST /test-alert
```

**Response:**
```json
{
  "message": "Test alert queued"
}
```

Check your Telegram chat for the test message!

**Example:**
```bash
curl -X POST http://localhost:8000/test-alert
```

**Expected Telegram message:**
```
✅ TEST ALERT

⚽ Test Player
Old Club → New Club
💰 Fee: Test Fee
🏆 Test League
📊 Reliability: 95%

📰 Sources: test
```

---

### 4. Run Aggregation 🔄

Manually trigger the transfer aggregation job (scrapes all sources).

```http
POST /run-aggregation
```

**Response:**
```json
{
  "message": "Aggregation triggered"
}
```

The aggregation runs asynchronously in the background. Check the logs to see progress.

**Example:**
```bash
curl -X POST http://localhost:8000/run-aggregation
```

**Note:** Aggregation normally runs every 4 hours automatically. This endpoint is useful for:
- Testing scrapers
- Getting fresh data immediately
- Debugging source issues

---

### 5. Initialize Database 🗄️

Set up database schema (run this once after deployment).

```http
POST /init-db
```

**Response:**
```json
{
  "message": "Database initialized"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/init-db
```

**Note:** Should only be called once. Safe to run multiple times (won't create duplicates).

---

## Response Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | Success | Request successful |
| 400 | Bad Request | Invalid query parameters |
| 404 | Not Found | Endpoint doesn't exist |
| 500 | Server Error | Internal error (check logs) |

---

## Data Types

### Transfer Object

```typescript
{
  id: number,                    // Database ID
  player_name: string,           // Player name
  from_club: string,             // Current club
  to_club: string,               // New club
  league: string,                // Destination league
  status: string,                // "Confirmed", "Rumored", "Loan", "Free Agent", etc.
  fee: string,                   // "€50M", "Free", "Loan", "TBD", etc.
  fee_numeric: number | null,    // Fee as number for sorting
  reliability_score: number,     // 0.0 - 1.0 (confidence level)
  sources: string[],             // ["Transfermarkt", "Sky Sports", ...]
  source_urls: string[],         // URLs where transfer was found
  transfer_date: ISO8601 | null, // When transfer happens/happened
  announced_date: ISO8601 | null,// When first announced
  created_at: ISO8601,           // When added to DB
  updated_at: ISO8601            // Last update time
}
```

### League Values

| Value | Name |
|-------|------|
| `premier_league` | Premier League (England) |
| `la_liga` | La Liga (Spain) |
| `serie_a` | Serie A (Italy) |
| `bundesliga` | Bundesliga (Germany) |
| `ligue_1` | Ligue 1 (France) |
| `liga_mx` | Liga MX (Mexico) |

### Status Values

- `Confirmed` — Official transfer completed
- `Rumored` — Being discussed/negotiated
- `Done Deal` — Agreement reached, waiting for official
- `Loan` — Temporary transfer
- `Free Agent` — Player available on free transfer
- `Released` — Player leaves club

---

## Reliability Scores

| Score | Source Tier | Examples |
|-------|-------------|----------|
| 0.95 - 1.0 | Official/Tier 1 | Transfermarkt Official, League Announcements, Fabrizio Romano |
| 0.85 - 0.94 | Major News | Sky Sports, ESPN, official club statements |
| 0.70 - 0.84 | Reputable Journalists | Secondary sports reporters |
| 0.50 - 0.69 | Mixed Sources | Aggregators, blogs |
| < 0.50 | Unverified | Reddit, forums, rumors |

---

## Error Handling

### Example Error Response

```json
{
  "error": "Database connection failed",
  "count": 0,
  "transfers": []
}
```

**Common errors:**

**"Database connection failed"**
- Supabase URL or key is wrong
- Supabase project is paused/down
- Check environment variables

**"Telegram authorization failed"**
- Bot token is expired or invalid
- Chat ID doesn't exist
- Bot hasn't been added to chat

**"No results"**
- Search criteria too specific
- Transfers older than 30 days
- Filter matches no transfers

---

## Rate Limiting

No official rate limits on free tier, but be respectful:

- Aggregation: Every 4 hours (configurable)
- API queries: No limit, but avoid hammering
- Telegram: 30 messages/second per bot (API limit)

---

## Pagination & Sorting

Current API doesn't support pagination (all results returned).

**Sorting tips (client-side):**

```bash
# Sort by reliability (highest first)
curl "http://localhost:8000/transfers" | jq '.transfers | sort_by(-.reliability_score)'

# Sort by date (newest first)
curl "http://localhost:8000/transfers" | jq '.transfers | sort_by(-.created_at)'

# Filter + sort
curl "http://localhost:8000/transfers" | \
  jq '.transfers | map(select(.league == "La Liga")) | sort_by(-.reliability_score)'
```

---

## Shell Script Helpers

Use `test_api.sh` for quick testing:

```bash
chmod +x test_api.sh

# Health check
./test_api.sh http://localhost:8000 health

# Send test alert
./test_api.sh http://localhost:8000 test-alert

# Get Premier League transfers
./test_api.sh http://localhost:8000 get-premier

# Search for player
./test_api.sh http://localhost:8000 search-player "Mbappé"

# Production endpoint
./test_api.sh https://your-app.railway.app transfers
```

---

## cURL Examples

### Get Latest Premier League Signings

```bash
curl -s "http://localhost:8000/transfers?league=premier_league" | jq '.transfers | .[:5]'
```

### Find All Transfers for a Player

```bash
curl -s "http://localhost:8000/transfers?player=Bellingham" | jq '.transfers[]'
```

### Only Show Confirmed Deals

```bash
curl -s "http://localhost:8000/transfers" | \
  jq '.transfers[] | select(.status == "Confirmed")'
```

### Export to CSV (quick)

```bash
curl -s "http://localhost:8000/transfers" | \
  jq -r '.transfers[] | [.player_name, .from_club, .to_club, .fee, .reliability_score] | @csv' > transfers.csv
```

### Monitor Real-time (every 1 minute)

```bash
watch -n 60 'curl -s "http://localhost:8000/transfers?days=1" | jq ".count"'
```

---

## Webhook Events (Future)

Planned enhancements:

```http
POST /webhooks/transfer-confirmed
POST /webhooks/transfer-rumored
POST /webhooks/player-followed
```

Subscribe to specific events and get POST payloads to your URL.

---

## Version Info

- **API Version:** 1.0
- **Last Updated:** Aug 2024
- **FastAPI:** 0.104+
- **Python:** 3.11+

---

## Support & Debugging

### Check logs
```bash
# Railway
railway logs -f

# Local Docker
docker-compose logs -f transfer-bot
```

### Test connectivity
```bash
# Health check
curl http://localhost:8000/health

# Database
curl "http://localhost:8000/transfers"

# Telegram
curl -X POST http://localhost:8000/test-alert
```

### Common Issues

**"No transfers found"**
- Aggregation hasn't run yet (runs every 4 hours)
- Manually trigger: `curl -X POST http://localhost:8000/run-aggregation`
- Check logs for scraper errors

**"Stale data"**
- Aggregation last ran X hours ago
- Sources may not have new transfers
- Try `/run-aggregation` to force refresh

**"Wrong reliability scores"**
- Adjust in `transfer_bot.py` → `score_transfer_reliability()`
- Rebuild and redeploy

---

That's it! You're ready to build the dashboard next. 🚀
