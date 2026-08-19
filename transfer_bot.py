"""
Transfer Market Aggregator - FastAPI Backend with Real Scrapers
Monitors Transfermarkt, ESPN, Sky Sports, and official league feeds
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List
import logging
from collections import defaultdict
import re

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from supabase import create_client, Client
from bs4 import BeautifulSoup

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FOOTBALL_DATA_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY", "")

# football-data.org competition codes for our tracked European leagues (no Liga MX on the free tier)
FOOTBALL_DATA_COMPETITIONS = "PL,PD,SA,BL1,FL1"

# Initialize clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
app = FastAPI()
scheduler = AsyncIOScheduler()

# ============================================================================
# REAL WEB SCRAPERS
# ============================================================================

LEAGUE_CLUBS = {
    "Premier League": ['arsenal', 'man city', 'manchester city', 'man united', 'manchester united',
                        'liverpool', 'chelsea', 'tottenham'],
    "La Liga": ['barcelona', 'real madrid', 'atletico', 'atletico madrid'],
    "Serie A": ['juventus', 'milan', 'inter', 'napoli', 'roma', 'lazio', 'fiorentina'],
    "Bundesliga": ['bayern', 'dortmund', 'hamburg', 'cologne', 'leverkusen'],
    "Ligue 1": ['lyon', 'marseille', 'psg', 'paris saint-germain', 'monaco', 'lille'],
    "Liga MX": ['monterrey', 'america', 'américa', 'cruz azul', 'toluca', 'chivas', 'guadalajara',
                'pumas', 'necaxa'],
}


class TransferScraper:
    """Aggregates transfer news from multiple real sources"""

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def _infer_league(self, *club_names) -> str:
        """Infer which of our 6 tracked leagues a transfer belongs to based on club names"""
        haystack = " ".join(c.lower() for c in club_names if c)
        for league, keywords in LEAGUE_CLUBS.items():
            if any(kw in haystack for kw in keywords):
                return league
        return "Unknown"

    async def scrape_transfermarkt_news(self) -> List[dict]:
        """Scrape Transfermarkt's structured 'latest transfers' table (real transfer data)"""
        transfers = []
        try:
            url = "https://www.transfermarkt.com/statistik/neuestetransfers"
            response = await self.client.get(url)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                rows = soup.select('tr.odd, tr.even')

                for row in rows:
                    try:
                        tds = row.find_all('td', recursive=False)
                        if len(tds) < 6:
                            continue

                        name_link = tds[0].select_one('td.hauptlink a')
                        from_link = tds[3].select_one('td.hauptlink a')
                        to_link = tds[4].select_one('td.hauptlink a')
                        if not (name_link and from_link and to_link):
                            continue

                        from_club = from_link.get('title') or from_link.get_text(strip=True)
                        to_club = to_link.get('title') or to_link.get_text(strip=True)

                        # Only keep transfers involving our 6 tracked leagues
                        league = self._infer_league(from_club, to_club)
                        if league == "Unknown":
                            continue

                        fee = tds[5].get_text(strip=True) or "TBD"
                        status = "Loan" if "loan" in fee.lower() else "Confirmed"

                        transfers.append({
                            "player_name": name_link.get('title') or name_link.get_text(strip=True),
                            "from_club": from_club,
                            "to_club": to_club,
                            "league": league,
                            "status": status,
                            "fee": fee,
                            "sources": ["Transfermarkt"],
                            "source_urls": [url],
                            "transfer_date": None,
                            "announced_date": datetime.utcnow().isoformat(),
                        })
                    except Exception as e:
                        logger.error(f"Error parsing Transfermarkt row: {e}")
                        continue

                logger.info(f"Transfermarkt: Found {len(transfers)} transfers")

        except Exception as e:
            logger.error(f"Transfermarkt scrape error: {e}")

        return transfers

    async def scrape_espn_transfers(self) -> List[dict]:
        """
        Scrape ESPN's transfer headlines.
        ESPN's transfers page renders client-side from a JSON blob embedded in the page
        (window.__espnfitt__), not static HTML elements, so we pull headline strings out
        of that JSON directly rather than looking for <article> tags that don't exist server-side.
        """
        transfers = []
        try:
            url = "https://www.espn.com/soccer/transfers"
            response = await self.client.get(url)

            if response.status_code == 200:
                html = response.text
                raw_headlines = re.findall(r'"headline":"((?:[^"\\]|\\.)*)"', html)

                seen = set()
                for raw in raw_headlines:
                    try:
                        title = json.loads('"' + raw + '"')
                    except Exception:
                        title = raw

                    if title in seen:
                        continue
                    seen.add(title)

                    transfer = self._parse_transfer_title(title, "ESPN", "Recent")
                    if transfer:
                        transfers.append(transfer)

                logger.info(f"ESPN: Found {len(transfers)} transfers")

        except Exception as e:
            logger.error(f"ESPN scrape error: {e}")

        return transfers
    
    async def scrape_sky_sports(self) -> List[dict]:
        """Scrape Sky Sports transfer news"""
        transfers = []
        try:
            url = "https://www.skysports.com/transfer-centre"
            response = await self.client.get(url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for news stories
                stories = soup.find_all('a', class_='sdc-site-tile__headline-link')
                
                for story in stories[:10]:
                    try:
                        title = story.get_text(strip=True)
                        transfer = self._parse_transfer_title(title, "Sky Sports", "Recent")
                        if transfer:
                            transfers.append(transfer)
                    except Exception as e:
                        logger.error(f"Error parsing Sky Sports story: {e}")
                        continue
                
                logger.info(f"Sky Sports: Found {len(transfers)} transfers")
            
        except Exception as e:
            logger.error(f"Sky Sports scrape error: {e}")
        
        return transfers
    
    async def scrape_official_announcements(self) -> List[dict]:
        """Scrape official club and league announcements"""
        transfers = []
        
        # Premier League
        try:
            url = "https://www.premierleague.com/news"
            response = await self.client.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                articles = soup.find_all('h3')[:5]
                for article in articles:
                    title = article.get_text(strip=True)
                    if any(word in title.lower() for word in ['sign', 'transfer', 'join', 'loan', 'move']):
                        transfer = self._parse_transfer_title(title, "Premier League Official", "Recent")
                        if transfer:
                            transfers.append(transfer)
        except Exception as e:
            logger.error(f"Premier League scrape error: {e}")
        
        # La Liga
        try:
            url = "https://www.laliga.com/noticias"
            response = await self.client.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                articles = soup.find_all('h3')[:5]
                for article in articles:
                    title = article.get_text(strip=True)
                    if any(word in title.lower() for word in ['fichaje', 'transfer', 'llega', 'firma']):
                        transfer = self._parse_transfer_title(title, "La Liga Official", "Recent")
                        if transfer:
                            transfers.append(transfer)
        except Exception as e:
            logger.error(f"La Liga scrape error: {e}")
        
        logger.info(f"Official announcements: Found {len(transfers)} transfers")
        return transfers
    
    def _parse_transfer_title(self, title: str, source: str, date: str) -> Optional[dict]:
        """Parse transfer info from a title string"""
        title_lower = title.lower()
        
        # Skip non-transfer content
        if not any(word in title_lower for word in ['sign', 'transfer', 'join', 'move', 'loan', 'fichaje', 'llega', 'firma']):
            return None
        
        # Try to extract player name and clubs
        # Common patterns:
        # "Player Name joins Club from Former Club"
        # "Player Name signs for Club"
        # "Club sign Player Name"

        # This is simplified - real implementation would be more sophisticated
        clubs_keywords = [club for keywords in LEAGUE_CLUBS.values() for club in keywords]

        # Extract clubs from title
        found_clubs = [club for club in clubs_keywords if club in title_lower]

        if len(found_clubs) < 2:
            return None
        
        # Try to find fee if mentioned
        fee = "TBD"
        fee_match = re.search(r'€[\d.]+[MKB]?|£[\d.]+[MKB]?|\$[\d.]+[MKB]?|[\d.]+\s*(?:million|billion|thousand)', title)
        if fee_match:
            fee = fee_match.group(0)
        
        # Determine status
        status = "Confirmed" if "official" in source.lower() else "Rumored"
        if "loan" in title_lower:
            status = "Loan"
        
        # Determine league
        league = self._infer_league(*found_clubs)

        return {
            "player_name": title[:50],  # Simplified - take first 50 chars as "player"
            "from_club": found_clubs[0].title() if len(found_clubs) > 0 else "Unknown",
            "to_club": found_clubs[1].title() if len(found_clubs) > 1 else "Unknown",
            "league": league,
            "status": status,
            "fee": fee,
            "sources": [source],
            "source_urls": [],
            "transfer_date": None,
            "announced_date": datetime.utcnow().isoformat(),
        }
    
    async def scrape_all(self) -> List[dict]:
        """Scrape all sources concurrently"""
        tasks = [
            self.scrape_transfermarkt_news(),
            self.scrape_espn_transfers(),
            self.scrape_sky_sports(),
            self.scrape_official_announcements(),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results
        all_transfers = []
        for result in results:
            if isinstance(result, list):
                all_transfers.extend(result)
        
        logger.info(f"Total transfers scraped: {len(all_transfers)}")
        return all_transfers

# ============================================================================
# DEDUPLICATION & STORAGE
# ============================================================================

async def dedupe_transfers(transfers: List[dict]) -> List[dict]:
    """Deduplicate transfers using smart key"""
    
    seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    
    try:
        existing = supabase.table("transfers").select("*").gte(
            "created_at", seven_days_ago
        ).execute()
        
        existing_transfers = {
            (t["player_name"].lower(), t["from_club"].lower(), t["to_club"].lower())
            for t in existing.data
        }
    except:
        existing_transfers = set()
    
    new_transfers = []
    for transfer in transfers:
        key = (
            transfer.get("player_name", "").lower(),
            transfer.get("from_club", "").lower(),
            transfer.get("to_club", "").lower(),
        )
        
        if key not in existing_transfers:
            new_transfers.append(transfer)
    
    return new_transfers

async def score_transfer_reliability(transfer: dict) -> float:
    """Score transfer by source reliability"""
    source = transfer.get("sources", [None])[0] if transfer.get("sources") else ""
    if not source:
        source = ""
    
    source_lower = source.lower()
    
    reliability_scores = {
        "official": 0.99,
        "premier league": 0.98,
        "la liga": 0.98,
        "serie a": 0.98,
        "bundesliga": 0.98,
        "ligue 1": 0.98,
        "liga mx": 0.98,
        "transfermarkt": 0.95,
        "sky sports": 0.90,
        "espn": 0.85,
    }
    
    for key, score in reliability_scores.items():
        if key in source_lower:
            return score
    
    return 0.70

async def store_transfer(transfer: dict) -> None:
    """Store transfer in Supabase"""
    try:
        supabase.table("transfers").insert(transfer).execute()
        logger.info(f"Stored: {transfer.get('player_name', 'Unknown')} → {transfer.get('to_club', 'Unknown')}")
    except Exception as e:
        logger.error(f"Storage error: {e}")

# ============================================================================
# TELEGRAM NOTIFICATIONS
# ============================================================================

async def send_telegram_alert(transfer: dict, reliability: float) -> None:
    """Send transfer alert via Telegram"""
    try:
        player = transfer.get("player_name", "Unknown")
        from_club = transfer.get("from_club", "Unknown")
        to_club = transfer.get("to_club", "Unknown")
        league = transfer.get("league", "Unknown League")
        status = transfer.get("status", "Rumored")
        fee = transfer.get("fee", "TBD")
        sources = transfer.get("sources", [])
        
        # Confidence emoji
        confidence = "✅" if reliability > 0.90 else "⚠️" if reliability > 0.75 else "🔄"
        
        # Build message
        message = (
            f"{confidence} *{status.upper()}*\n\n"
            f"⚽ *{player}*\n"
            f"{from_club} → {to_club}\n"
            f"💰 Fee: {fee}\n"
            f"🏆 {league}\n"
            f"📊 Reliability: {reliability*100:.0f}%\n\n"
            f"📰 Sources: {', '.join(sources[:3])}"
        )
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"Alert sent: {player} → {to_club}")
            else:
                logger.error(f"Telegram error: {response.text}")
    
    except Exception as e:
        logger.error(f"Send alert error: {e}")

# ============================================================================
# LIVE SCORES (football-data.org)
# ============================================================================

async def send_score_alert(competition: str, home: str, away: str, home_score: int, away_score: int, status: str) -> None:
    """Send a live score update via Telegram"""
    try:
        status_label = {
            "IN_PLAY": "⏱️ LIVE",
            "PAUSED": "⏸️ HALF-TIME",
            "FINISHED": "✅ FULL-TIME",
        }.get(status, status)

        message = (
            f"⚽ {status_label}\n\n"
            f"{home} {home_score} - {away_score} {away}\n"
            f"🏆 {competition}"
        )

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"Score alert sent: {home} {home_score}-{away_score} {away}")
            else:
                logger.error(f"Telegram score alert error: {response.text}")

    except Exception as e:
        logger.error(f"Send score alert error: {e}")

async def check_live_scores() -> None:
    """
    Poll football-data.org for live matches and alert on score/status changes.
    Note: the free tier only exposes aggregate scores, not individual goal scorers.
    """
    if not FOOTBALL_DATA_API_KEY:
        return

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://api.football-data.org/v4/matches",
                headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
                params={"status": "LIVE", "competitions": FOOTBALL_DATA_COMPETITIONS},
            )

        if response.status_code != 200:
            logger.error(f"football-data.org error: {response.status_code} {response.text}")
            return

        matches = response.json().get("matches", [])
        logger.info(f"Live scores: {len(matches)} matches in play")

        for match in matches:
            try:
                match_id = match["id"]
                competition = match["competition"]["name"]
                home = match["homeTeam"].get("shortName") or match["homeTeam"]["name"]
                away = match["awayTeam"].get("shortName") or match["awayTeam"]["name"]
                home_score = match["score"]["fullTime"]["home"]
                away_score = match["score"]["fullTime"]["away"]
                status = match["status"]

                existing = supabase.table("live_scores").select("*").eq("match_id", match_id).execute()
                prev = existing.data[0] if existing.data else None

                changed = (
                    prev is None
                    or prev["home_score"] != home_score
                    or prev["away_score"] != away_score
                    or prev["status"] != status
                )

                if not changed:
                    continue

                await send_score_alert(competition, home, away, home_score, away_score, status)

                row = {
                    "match_id": match_id,
                    "competition": competition,
                    "home_team": home,
                    "away_team": away,
                    "home_score": home_score,
                    "away_score": away_score,
                    "status": status,
                    "updated_at": datetime.utcnow().isoformat(),
                }
                if prev:
                    supabase.table("live_scores").update(row).eq("match_id", match_id).execute()
                else:
                    supabase.table("live_scores").insert(row).execute()

            except Exception as e:
                logger.error(f"Error processing live match: {e}")
                continue

    except Exception as e:
        logger.error(f"check_live_scores error: {e}")

# ============================================================================
# AGGREGATION JOB
# ============================================================================

async def aggregate_transfers():
    """Main job: scrape, dedupe, score, alert"""
    logger.info("=== Starting transfer aggregation ===")
    
    scraper = TransferScraper()
    
    # Scrape all sources
    raw_transfers = await scraper.scrape_all()
    logger.info(f"Scraped {len(raw_transfers)} raw transfers")
    
    if len(raw_transfers) == 0:
        logger.warning("No transfers found in this aggregation run")
        return
    
    # Deduplicate
    new_transfers = await dedupe_transfers(raw_transfers)
    logger.info(f"Found {len(new_transfers)} new transfers after dedup")
    
    # Score and alert
    for transfer in new_transfers:
        reliability = await score_transfer_reliability(transfer)
        transfer["reliability_score"] = reliability
        transfer["created_at"] = datetime.utcnow().isoformat()
        
        # Store in DB
        await store_transfer(transfer)
        
        # Send alert if reliable enough
        if reliability > 0.65:
            await send_telegram_alert(transfer, reliability)
    
    logger.info("=== Aggregation complete ===")

# ============================================================================
# SCHEDULER
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Start scheduler on app startup"""
    # Run transfer aggregation every 4 hours
    scheduler.add_job(
        aggregate_transfers,
        IntervalTrigger(hours=4),
        id="transfer_aggregation",
    )

    # Poll live scores every 3 minutes (10 req/min quota on football-data.org's free tier)
    scheduler.add_job(
        check_live_scores,
        IntervalTrigger(minutes=3),
        id="live_scores",
    )

    # Also run immediately on startup
    await aggregate_transfers()
    await check_live_scores()

    scheduler.start()
    logger.info("Scheduler started - transfers every 4h, live scores every 3min")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduler on app shutdown"""
    scheduler.shutdown()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/transfers")
async def get_transfers(
    league: Optional[str] = None,
    player: Optional[str] = None,
    days: int = 7,
):
    """Get recent transfers with optional filtering"""
    try:
        date_threshold = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        query = supabase.table("transfers").select("*").gte("created_at", date_threshold)
        
        if league:
            query = query.eq("league", league)
        
        result = query.order("reliability_score", desc=True).execute()
        
        transfers = result.data
        
        if player:
            transfers = [
                t for t in transfers
                if player.lower() in t.get("player_name", "").lower()
            ]
        
        return {
            "count": len(transfers),
            "transfers": transfers,
            "fetched_at": datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Get transfers error: {e}")
        return {"error": str(e), "count": 0, "transfers": []}

@app.post("/test-alert")
async def test_alert(background_tasks: BackgroundTasks):
    """Test Telegram alert"""
    test_transfer = {
        "player_name": "Kylian Mbappé",
        "from_club": "PSG",
        "to_club": "Real Madrid",
        "league": "La Liga",
        "status": "Confirmed",
        "fee": "€180M",
        "sources": ["Official", "Sky Sports"],
    }
    
    background_tasks.add_task(send_telegram_alert, test_transfer, 0.99)
    return {"message": "Test alert queued"}

@app.post("/run-aggregation")
async def run_aggregation_manual(background_tasks: BackgroundTasks):
    """Manually trigger aggregation"""
    background_tasks.add_task(aggregate_transfers)
    return {"message": "Aggregation triggered"}

@app.get("/scores")
async def get_scores():
    """Get current tracked live/recent match scores"""
    try:
        result = supabase.table("live_scores").select("*").order("updated_at", desc=True).execute()
        return {
            "count": len(result.data),
            "matches": result.data,
            "fetched_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Get scores error: {e}")
        return {"error": str(e), "count": 0, "matches": []}

@app.post("/check-scores")
async def check_scores_manual(background_tasks: BackgroundTasks):
    """Manually trigger a live scores poll"""
    background_tasks.add_task(check_live_scores)
    return {"message": "Score check triggered"}

@app.post("/init-db")
async def init_db_endpoint():
    """Initialize database (verify connection)"""
    try:
        result = supabase.table("transfers").select("*").limit(1).execute()
        return {"message": "Database connected", "status": "ok"}
    except Exception as e:
        return {"message": f"Database error: {e}", "status": "error"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
