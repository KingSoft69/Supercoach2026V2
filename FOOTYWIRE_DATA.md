# FootyWire Data Integration

## Overview
This optimizer is configured to fetch real-time AFL Supercoach player data from FootyWire.

## Data Source
- **URL**: https://www.footywire.com/afl/footy/supercoach_prices
- **Data Retrieved**: Player names, teams, positions, prices, average scores, and games played
- **Update Frequency**: Live data from FootyWire's current season

## How It Works

### 1. Data Fetching (`data_collector.py`)
The `AFLDataCollector.load_real_data()` method:
- Fetches the Supercoach prices page from FootyWire
- Parses the HTML table to extract player information
- Uses `fetch_player_details=False` for faster execution (estimates age/draft data from performance)
- Falls back to sample data only if FootyWire is unreachable

### 2. Real vs Sample Data
The optimizer indicates which data source is being used:
- **Real data**: `✓ Successfully loaded XXX REAL AFL players from FootyWire`
- **Sample data**: `⚠ Using XXX sample players (FootyWire data unavailable)`

Real player IDs start with 'FW' (e.g., FW0001), while sample IDs start with 'P' (e.g., P0001).

### 3. Data Fields
From FootyWire, we get:
- **Direct**: name, team, position, price, avg_score, games_played
- **Estimated**: age (from games played), draft_pick (from performance), injury history

## Running with Real Data

### Local Execution
```bash
# Requires internet connection to footywire.com
python supercoach_optimizer.py
```

### GitHub Actions
When a PR is merged to main, the GitHub Actions workflow automatically:
1. Fetches fresh data from FootyWire
2. Runs the optimizer with real players
3. Commits the results back to the repository

See `.github/workflows/run-model-on-pr.yml` for the automated workflow.

## Network Requirements
- Active internet connection
- Access to https://www.footywire.com (port 443)
- No proxy/firewall blocking FootyWire

## Fallback Behavior
If FootyWire cannot be reached:
- The system generates sample data for testing
- Sample players have realistic stats but fictional names
- This allows development/testing without internet access

##ネット環境での実行
This is the intended production behavior - always run with real FootyWire data when possible.
