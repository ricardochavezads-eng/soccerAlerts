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
from fastapi import FastAPI, BackgroundTasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from supabase import create_client, Client
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Initialize clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
app = FastAPI()
scheduler = AsyncIOScheduler()

# ============================================================================
# REAL WEB SCRAPERS
# ============================================================================

class TransferScraper:
    """Aggregates transfer news from multiple real sources"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=15.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
    
    async def scrape_transfermarkt_news(self) -> List[dict]:
        """Scrape latest transfer news from Transfermarkt"""
        transfers = []
        try:
            url = "https://www.transfermarkt.com/transfers/latestnews/1"
            response = await self.client.get(url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for transfer news items
                news_items = soup.find_all('div', class_='news-item')
                
                for item in news_items[:10]:  # Get top 10
                    try:
                        # Extract title (usually contains player name and clubs)
                        title_elem = item.find('a', class_='news-link')
                        if not title_elem:
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        
                        # Extract date
                        date_elem = item.find('span', class_='date')
                        date_str = date_elem.get_text(strip=True) if date_elem else "Today"
                        
                        # Parse title for transfer info
                        # Typical format: "Player Name joins Club from Former Club"
                        transfer = self._parse_transfer_title(title, "Transfermarkt", date_str)
                        if transfer:
                            transfers.append(transfer)
                    except Exception as e:
                        logger.error(f"Error parsing Transfermarkt item: {e}")
                        continue
                
                logger.info(f"Transfermarkt: Found {len(transfers)} transfers")
            
        except Exception as e:
            logger.error(f"Transfermarkt scrape error: {e}")
        
        return transfers
    
    async def scrape_espn_transfers(self) -> List[dict]:
        """Scrape transfer news from ESPN FC"""
        transfers = []
        try:
            url = "https://www.espn.com/soccer/transfers"
            response = await self.client.get(url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for transfer stories
                articles = soup.find_all('article', class_='contentItem')
                
                for article in articles[:8]:
                    try:
                        headline = article.find('h2')
                        if headline:
                            title = headline.get_text(strip=True)
                            transfer = self._parse_transfer_title(title, "ESPN", "Recent")
                            if transfer:
                                transfers.append(transfer)
                    except Exception as e:
                        logger.error(f"Error parsing ESPN article: {e}")
                        continue
                
                logger.info(f"ESPN: Found {len(transfers)} transfers")
            
        except Exception as e:
            logger.error(f"ESPN scrape error: {e}")
        
        return transfers
    
    async def scrape_sky_sports(self) -> List[dict]:
        """Scrape Sky Sports transfer news"""
        transfers = []
        try:
            url = "https://www.skysports.com/transfer-news"
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
        clubs_keywords = ['arsenal', 'man city', 'manchester city', 'man united', 'manchester united', 'liverpool', 
                         'chelsea', 'tottenham', 'barcelona', 'real madrid', 'atletico', 'psg', 'paris',
                         'juventus', 'milan', 'inter', 'napoli', 'roma', 'lazio', 'fiorentina',
                         'bayern', 'dortmund', 'hamburg', 'cologne', 'leverkusen',
                         'lyon', 'marseille', 'psg', 'monaco', 'lille',
                         'ajax', 'psv', 'feyenoord', 'az', 'twente',
                         'benfica', 'porto', 'sporting',
                         'monterrey', 'america', 'cruz azul', 'toluca', 'chivas', 'pumas', 'necaxa']
        
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
        league = "Unknown"
        if any(club in found_clubs for club in ['arsenal', 'manchester city', 'man city', 'liverpool', 'chelsea', 'tottenham', 'man united', 'manchester united']):
            league = "Premier League"
        elif any(club in found_clubs for club in ['barcelona', 'real madrid', 'atletico']):
            league = "La Liga"
        elif any(club in found_clubs for club in ['juventus', 'milan', 'inter', 'napoli', 'roma', 'lazio']):
            league = "Serie A"
        elif any(club in found_clubs for club in ['bayern', 'dortmund', 'hamburg', 'cologne', 'leverkusen']):
            league = "Bundesliga"
        elif any(club in found_clubs for club in ['lyon', 'marseille', 'psg', 'paris', 'monaco', 'lille']):
            league = "Ligue 1"
        elif any(club in found_clubs for club in ['monterrey', 'america', 'cruz azul', 'toluca', 'chivas', 'pumas', 'necaxa']):
            league = "Liga MX"
        
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
    # Run aggregation every 4 hours
    scheduler.add_job(
        aggregate_transfers,
        IntervalTrigger(hours=4),
        id="transfer_aggregation",
    )
    
    # Also run immediately on startup
    await aggregate_transfers()
    
    scheduler.start()
    logger.info("Scheduler started - running every 4 hours")

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
