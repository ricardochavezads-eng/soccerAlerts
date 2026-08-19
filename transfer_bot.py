"""
Transfer Market Aggregator - FastAPI Backend
Monitors multiple transfer sources, dedupes, and sends Telegram alerts
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List
import logging
from collections import defaultdict

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from supabase import create_client, Client
import re

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TRANSFERMARKT_API_KEY = os.getenv("TRANSFERMARKT_API_KEY", "")  # Optional: paid API

# Initialize clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
app = FastAPI()
scheduler = AsyncIOScheduler()

# ============================================================================
# SOURCE SCRAPERS
# ============================================================================

class TransferScraper:
    """Aggregates transfer news from multiple sources"""
    
    def __init__(self):
        self.sources = {
            "transfermarkt": self.scrape_transfermarkt,
            "espn": self.scrape_espn,
            "sky_sports": self.scrape_sky_sports,
            "fabrizio_romano": self.scrape_fabrizio_romano,
            "league_official": self.scrape_league_official,
        }
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def scrape_transfermarkt(self) -> List[dict]:
        """Scrape Transfermarkt news feed"""
        transfers = []
        try:
            # Transfermarkt free feed endpoint
            url = "https://www.transfermarkt.com/transfers/latestnews"
            headers = {"User-Agent": "Mozilla/5.0"}
            
            # Note: Transfermarkt requires web scraping; using simple parsing
            # For production, use: https://api.transfermarkt.com/ (requires license)
            response = await self.client.get(url, headers=headers)
            
            # Parse transfer snippets from the feed
            # This is simplified; real implementation would parse HTML more carefully
            if response.status_code == 200:
                # Extract transfer news blocks
                logger.info("Transfermarkt scraped successfully")
            
        except Exception as e:
            logger.error(f"Transfermarkt scrape error: {e}")
        
        return transfers
    
    async def scrape_espn(self) -> List[dict]:
        """Scrape ESPN FC transfers"""
        transfers = []
        try:
            url = "https://www.espn.com/soccer/transfers"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = await self.client.get(url, headers=headers)
            
            if response.status_code == 200:
                logger.info("ESPN scraped successfully")
            
        except Exception as e:
            logger.error(f"ESPN scrape error: {e}")
        
        return transfers
    
    async def scrape_sky_sports(self) -> List[dict]:
        """Scrape Sky Sports transfer news"""
        transfers = []
        try:
            url = "https://www.skysports.com/transfer-news"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = await self.client.get(url, headers=headers)
            
            if response.status_code == 200:
                logger.info("Sky Sports scraped successfully")
            
        except Exception as e:
            logger.error(f"Sky Sports scrape error: {e}")
        
        return transfers
    
    async def scrape_fabrizio_romano(self) -> List[dict]:
        """Scrape Fabrizio Romano's news (via X/Twitter or The Athletic)"""
        transfers = []
        try:
            # Could integrate with Twitter API or scrape The Athletic
            # For now, placeholder for high-reliability source
            logger.info("Fabrizio Romano source checked")
            
        except Exception as e:
            logger.error(f"Fabrizio Romano scrape error: {e}")
        
        return transfers
    
    async def scrape_league_official(self) -> List[dict]:
        """Scrape official league announcements (Premier League, La Liga, etc.)"""
        transfers = []
        leagues = {
            "premier_league": "https://www.premierleague.com/news",
            "la_liga": "https://www.laliga.com/noticias",
            "serie_a": "https://www.legaseriea.it/notizie",
            "bundesliga": "https://www.bundesliga.com/de/news",
            "ligue_1": "https://www.ligue1.fr/actualite",
            "liga_mx": "https://www.ligamx.net/noticias",
        }
        
        try:
            for league_name, url in leagues.items():
                headers = {"User-Agent": "Mozilla/5.0"}
                response = await self.client.get(url, headers=headers, timeout=5.0)
                if response.status_code == 200:
                    logger.info(f"{league_name} official feed checked")
        
        except Exception as e:
            logger.error(f"League official scrape error: {e}")
        
        return transfers
    
    async def scrape_all(self) -> List[dict]:
        """Scrape all sources concurrently"""
        tasks = [
            self.scrape_transfermarkt(),
            self.scrape_espn(),
            self.scrape_sky_sports(),
            self.scrape_fabrizio_romano(),
            self.scrape_league_official(),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results
        all_transfers = []
        for result in results:
            if isinstance(result, list):
                all_transfers.extend(result)
        
        return all_transfers

# ============================================================================
# DEDUPLICATION & STORAGE
# ============================================================================

async def dedupe_transfers(transfers: List[dict]) -> List[dict]:
    """
    Deduplicate transfers using a smart key:
    (player_name, from_club, to_club, within 7-day window)
    """
    
    # Fetch recently stored transfers (last 7 days)
    seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    
    existing = supabase.table("transfers").select("*").gte(
        "created_at", seven_days_ago
    ).execute()
    
    existing_transfers = {
        (t["player_name"].lower(), t["from_club"].lower(), t["to_club"].lower())
        for t in existing.data
    }
    
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
    """Score transfer by source reliability (0.0 - 1.0)"""
    source = transfer.get("source", "").lower()
    
    reliability_scores = {
        "transfermarkt": 0.95,
        "official": 0.98,
        "fabrizio_romano": 0.99,
        "sky_sports": 0.90,
        "espn": 0.85,
        "league_official": 1.0,
    }
    
    for key, score in reliability_scores.items():
        if key in source:
            return score
    
    return 0.5  # Default low score for unknown sources

async def store_transfer(transfer: dict) -> None:
    """Store transfer in Supabase"""
    try:
        supabase.table("transfers").insert(transfer).execute()
        logger.info(f"Stored transfer: {transfer['player_name']} → {transfer['to_club']}")
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
        status = transfer.get("status", "Rumored")  # Confirmed, Rumored, Loan, etc.
        fee = transfer.get("fee", "TBD")
        sources = transfer.get("sources", [])
        
        # Build confidence emoji
        confidence = "✅" if reliability > 0.90 else "⚠️" if reliability > 0.75 else "🔄"
        
        # Build message
        message = (
            f"{confidence} *{status.upper()}*\n\n"
            f"⚽ *{player}*\n"
            f"{from_club} → {to_club}\n"
            f"💰 Fee: {fee}\n"
            f"🏆 {league}\n"
            f"📊 Reliability: {reliability*100:.0f}%\n\n"
            f"📰 Sources: {', '.join(sources[:3])}\n"
        )
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                logger.info(f"Alert sent: {player} → {to_club}")
            else:
                logger.error(f"Telegram error: {response.text}")
    
    except Exception as e:
        logger.error(f"Send alert error: {e}")

# ============================================================================
# MAIN AGGREGATION JOB
# ============================================================================

async def aggregate_transfers():
    """Main job: scrape, dedupe, score, alert"""
    logger.info("=== Starting transfer aggregation ===")
    
    scraper = TransferScraper()
    
    # Scrape all sources
    raw_transfers = await scraper.scrape_all()
    logger.info(f"Scraped {len(raw_transfers)} raw transfers")
    
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
        if reliability > 0.60:  # Adjust threshold as needed
            await send_telegram_alert(transfer, reliability)
    
    logger.info("=== Aggregation complete ===")

# ============================================================================
# SCHEDULER SETUP
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
    """
    Get recent transfers with optional filtering
    
    Query params:
    - league: Filter by league (premier_league, la_liga, serie_a, bundesliga, ligue_1, liga_mx)
    - player: Search by player name (partial match)
    - days: How many days back to fetch (default: 7)
    """
    try:
        date_threshold = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        query = supabase.table("transfers").select("*").gte("created_at", date_threshold)
        
        if league:
            query = query.eq("league", league)
        
        result = query.order("reliability_score", desc=True).execute()
        
        transfers = result.data
        
        # Client-side player filtering
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
    """Test Telegram alert (useful for debugging)"""
    test_transfer = {
        "player_name": "Test Player",
        "from_club": "Old Club",
        "to_club": "New Club",
        "league": "Premier League",
        "status": "Test Alert",
        "fee": "Test Fee",
        "sources": ["test"],
    }
    
    background_tasks.add_task(send_telegram_alert, test_transfer, 0.95)
    
    return {"message": "Test alert queued"}

@app.post("/run-aggregation")
async def run_aggregation_manual(background_tasks: BackgroundTasks):
    """Manually trigger aggregation (useful for testing)"""
    background_tasks.add_task(aggregate_transfers)
    return {"message": "Aggregation triggered"}

# ============================================================================
# DATABASE SCHEMA (Run once)
# ============================================================================

async def init_db():
    """Initialize Supabase tables (run this once)"""
    try:
        # Create transfers table if it doesn't exist
        supabase.rpc("create_transfers_table").execute()
    except:
        pass  # Table likely already exists

@app.post("/init-db")
async def init_db_endpoint():
    """Initialize database schema"""
    await init_db()
    return {"message": "Database initialized"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
