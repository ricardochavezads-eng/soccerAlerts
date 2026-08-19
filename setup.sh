#!/bin/bash

# 🚀 Transfer Market Bot - Automated Setup Script
# Run this once to set up everything locally

set -e  # Exit on error

echo "================================================"
echo "⚽ Transfer Market Bot - Setup"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check prerequisites
echo -e "${BLUE}Step 1: Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠️  Python 3 not found. Please install Python 3.11+${NC}"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}⚠️  Git not found. Please install Git${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $(python3 --version)${NC}"
echo -e "${GREEN}✅ Git $(git --version | cut -d' ' -f3)${NC}"
echo ""

# Step 2: Create virtual environment
echo -e "${BLUE}Step 2: Creating Python virtual environment...${NC}"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate venv
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Step 3: Install dependencies
echo -e "${BLUE}Step 3: Installing Python dependencies...${NC}"
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 4: Create .env file
echo -e "${BLUE}Step 4: Setting up environment variables...${NC}"

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file${NC}"
    echo ""
    echo -e "${YELLOW}📝 IMPORTANT: Edit .env and add your credentials:${NC}"
    echo "   - SUPABASE_URL (from supabase.com)"
    echo "   - SUPABASE_KEY (from supabase.com)"
    echo "   - TELEGRAM_BOT_TOKEN (from @BotFather)"
    echo "   - TELEGRAM_CHAT_ID (from @userinfobot)"
    echo ""
    echo "   Run: nano .env  (or edit in your editor)"
    echo ""
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

echo ""

# Step 5: Show project structure
echo -e "${BLUE}Step 5: Project structure${NC}"
echo ""
echo "transfer-alerts/"
echo "├── transfer_bot.py          (FastAPI backend)"
echo "├── schema.sql               (Database schema)"
echo "├── requirements.txt         (Dependencies)"
echo "├── Dockerfile              (Container setup)"
echo "├── docker-compose.yml      (Local testing)"
echo "├── .env                    (Your secrets)"
echo "├── .env.example            (Template)"
echo "├── .gitignore              (Git ignore)"
echo "├── SETUP.md                (Full setup guide)"
echo "├── API_REFERENCE.md        (API docs)"
echo "├── DEPLOYMENT_CHECKLIST.md (Quick checklist)"
echo "└── venv/                   (Python environment)"
echo ""

# Step 6: Git setup (optional)
echo -e "${BLUE}Step 6: Git initialization${NC}"

if [ ! -d ".git" ]; then
    git init
    git config user.email "you@example.com"
    git config user.name "Your Name"
    git add .
    git commit -m "Initial commit: Transfer market bot" -q
    echo -e "${GREEN}✅ Git repository initialized${NC}"
else
    echo -e "${GREEN}✅ Git repository already exists${NC}"
fi

echo ""

# Step 7: Test local setup
echo -e "${BLUE}Step 7: Testing local setup...${NC}"
echo ""

if grep -q "SUPABASE_URL=https://" .env && grep -q "TELEGRAM_BOT_TOKEN=" .env; then
    echo -e "${GREEN}✅ Environment variables configured${NC}"
else
    echo -e "${YELLOW}⚠️  Environment variables not yet configured${NC}"
    echo "   Run: nano .env"
    echo ""
fi

echo ""

# Step 8: Display next steps
echo "================================================"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "================================================"
echo ""

echo -e "${YELLOW}📋 NEXT STEPS:${NC}"
echo ""
echo "1️⃣  Edit .env with your credentials:"
echo "   $ nano .env"
echo ""
echo "   You need:"
echo "   • Telegram Bot Token (from @BotFather)"
echo "   • Telegram Chat ID (from @userinfobot)"
echo "   • Supabase URL & Key (from supabase.com)"
echo ""
echo "2️⃣  Test locally (optional):"
echo "   $ docker-compose up"
echo "   Then: curl http://localhost:8000/health"
echo ""
echo "3️⃣  Create GitHub repository:"
echo "   $ git remote add origin https://github.com/YOUR_USERNAME/transfer-alerts.git"
echo "   $ git branch -M main"
echo "   $ git push -u origin main"
echo ""
echo "4️⃣  Deploy to Railway:"
echo "   • Go to https://railway.app"
echo "   • New Project → GitHub"
echo "   • Select transfer-alerts repo"
echo "   • Add environment variables"
echo "   • Deploy! 🚀"
echo ""
echo "5️⃣  Initialize database:"
echo "   $ curl -X POST https://YOUR_APP.railway.app/init-db"
echo ""
echo "6️⃣  Send test alert:"
echo "   $ curl -X POST https://YOUR_APP.railway.app/test-alert"
echo ""

echo -e "${GREEN}You're ready to go! 🎉${NC}"
echo ""
