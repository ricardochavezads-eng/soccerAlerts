-- Transfer Market Aggregator Schema
-- Run this in Supabase SQL editor

-- Main transfers table
CREATE TABLE IF NOT EXISTS transfers (
  id BIGSERIAL PRIMARY KEY,
  player_name TEXT NOT NULL,
  from_club TEXT NOT NULL,
  to_club TEXT NOT NULL,
  league TEXT NOT NULL, -- e.g., "Premier League", "La Liga", "Liga MX"
  status TEXT DEFAULT 'Rumored', -- Confirmed, Rumored, Loan, Free Agent, etc.
  fee TEXT, -- e.g., "€50M", "Loan", "Free", "TBD"
  fee_numeric NUMERIC, -- For sorting/filtering
  reliability_score NUMERIC DEFAULT 0.5, -- 0.0 - 1.0
  sources JSONB DEFAULT '[]'::jsonb, -- Array of source names
  source_urls JSONB DEFAULT '[]'::jsonb, -- Array of URLs where found
  transfer_date TIMESTAMP, -- When the transfer is expected/completed
  announced_date TIMESTAMP, -- When first announced
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  -- Indexes for faster queries
  CONSTRAINT player_from_to_unique UNIQUE (
    LOWER(player_name),
    LOWER(from_club),
    LOWER(to_club),
    DATE(created_at)
  )
);

CREATE INDEX idx_transfers_league ON transfers(league);
CREATE INDEX idx_transfers_player ON transfers USING GIN (to_tsvector('english', player_name));
CREATE INDEX idx_transfers_reliability ON transfers(reliability_score DESC);
CREATE INDEX idx_transfers_created ON transfers(created_at DESC);
CREATE INDEX idx_transfers_status ON transfers(status);

-- User preferences table (for future multi-user support)
CREATE TABLE IF NOT EXISTS user_preferences (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT UNIQUE NOT NULL,
  preferred_leagues TEXT[] DEFAULT '{Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Liga MX}'::text[],
  alert_min_reliability NUMERIC DEFAULT 0.6, -- Only alert transfers > this reliability
  enable_unconfirmed BOOLEAN DEFAULT FALSE, -- Alert on rumors?
  enable_loans BOOLEAN DEFAULT FALSE, -- Alert on loan transfers?
  followed_players TEXT[] DEFAULT ARRAY[]::text[], -- Specific player names to follow
  blocked_clubs TEXT[] DEFAULT ARRAY[]::text[], -- Clubs to ignore
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Alert log (track what's been sent)
CREATE TABLE IF NOT EXISTS alert_log (
  id BIGSERIAL PRIMARY KEY,
  transfer_id BIGINT REFERENCES transfers(id) ON DELETE CASCADE,
  user_id TEXT,
  sent_at TIMESTAMP DEFAULT NOW(),
  telegram_message_id INTEGER,
  reliability_score NUMERIC
);

CREATE INDEX idx_alert_log_sent ON alert_log(sent_at DESC);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_transfers_updated_at BEFORE UPDATE ON transfers
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- RLS (Row Level Security) - Optional, for multi-user setup
ALTER TABLE transfers ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Allow public read on transfers (authenticated users can read all)
CREATE POLICY "Transfers are readable by authenticated users"
  ON transfers FOR SELECT
  USING (auth.role() = 'authenticated');

-- Users can only read/modify their own preferences
CREATE POLICY "Users can read own preferences"
  ON user_preferences FOR SELECT
  USING (auth.uid()::text = user_id);

CREATE POLICY "Users can update own preferences"
  ON user_preferences FOR UPDATE
  USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own preferences"
  ON user_preferences FOR INSERT
  WITH CHECK (auth.uid()::text = user_id);
