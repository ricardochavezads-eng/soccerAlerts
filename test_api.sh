#!/bin/bash

# Transfer Bot API Test Script
# Usage: ./test_api.sh [local|production] [command]

BASE_URL="${1:-http://localhost:8000}"
COMMAND="${2:-health}"

echo "🚀 Testing Transfer Bot API"
echo "Base URL: $BASE_URL"
echo "---"

case $COMMAND in
  health)
    echo "📋 Health Check..."
    curl -s "$BASE_URL/health" | jq .
    ;;
  
  test-alert)
    echo "📱 Sending test alert..."
    curl -s -X POST "$BASE_URL/test-alert" | jq .
    ;;
  
  run-aggregation)
    echo "🔄 Running aggregation job..."
    curl -s -X POST "$BASE_URL/run-aggregation" | jq .
    ;;
  
  get-transfers)
    echo "📊 Getting recent transfers..."
    curl -s "$BASE_URL/transfers?days=7" | jq .
    ;;
  
  get-premier)
    echo "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Getting Premier League transfers..."
    curl -s "$BASE_URL/transfers?league=premier_league" | jq .
    ;;
  
  get-liga-mx)
    echo "🇲🇽 Getting Liga MX transfers..."
    curl -s "$BASE_URL/transfers?league=liga_mx" | jq .
    ;;
  
  search-player)
    PLAYER="${3:-Haaland}"
    echo "🔍 Searching for: $PLAYER"
    curl -s "$BASE_URL/transfers?player=$PLAYER" | jq .
    ;;
  
  init-db)
    echo "🗄️  Initializing database..."
    curl -s -X POST "$BASE_URL/init-db" | jq .
    ;;
  
  *)
    echo "Available commands:"
    echo "  health              - Check if API is running"
    echo "  test-alert          - Send a test Telegram alert"
    echo "  run-aggregation     - Manually trigger transfer aggregation"
    echo "  get-transfers       - Get all recent transfers"
    echo "  get-premier         - Get Premier League transfers"
    echo "  get-liga-mx         - Get Liga MX transfers"
    echo "  search-player NAME  - Search for a player"
    echo "  init-db             - Initialize database schema"
    echo ""
    echo "Usage: $0 [base_url] [command]"
    echo ""
    echo "Examples:"
    echo "  $0 http://localhost:8000 health"
    echo "  $0 https://your-app.railway.app test-alert"
    echo "  $0 http://localhost:8000 search-player Mbappé"
    ;;
esac

echo ""
