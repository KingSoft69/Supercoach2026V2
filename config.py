"""
Configuration for 2026 AFL Supercoach
"""

# Team constraints
SALARY_CAP = 10000000  # $10 million salary cap
TEAM_SIZE = 30  # Total players in team

# Position requirements
# Supercoach 2026 rules: 30 players total
# - 22 on-field players (6 DEF, 8 MID, 2 RUC, 6 FWD)
# - 8 bench players (any position mix, typically emergency coverage for each position)
# Max values allow flexibility for bench composition
POSITION_REQUIREMENTS = {
    'DEF': {'min': 6, 'max': 9, 'on_field': 6},   # 6 onfield, up to 3 bench
    'MID': {'min': 8, 'max': 11, 'on_field': 8},  # 8 onfield, up to 3 bench
    'RUC': {'min': 2, 'max': 4, 'on_field': 2},   # 2 onfield, up to 2 bench
    'FWD': {'min': 6, 'max': 9, 'on_field': 6},   # 6 onfield, up to 3 bench
}
# Total: 22 onfield + flexible 8 bench (max total = 33 but constrained to 30 by TEAM_SIZE)

# Total on-field: 22 players (6+8+2+6)
# Total bench: 8 players (flexible positioning)
STARTING_LINEUP_SIZE = 22
BENCH_SIZE = 8

# Scoring system weights
SCORING_WEIGHTS = {
    'kicks': 3,
    'handballs': 2,
    'marks': 3,
    'tackles': 4,
    'frees_for': 1,
    'frees_against': -3,
    'hitouts': 1,
    'goals': 6,
    'behinds': 1
}

# Data sources (placeholder - would need actual AFL stats API)
DATA_SOURCES = {
    'historical_stats': 'https://www.afl.com.au/stats',
    'player_prices': 'https://supercoach.heraldsun.com.au',
}

# Model parameters
MODEL_CONFIG = {
    'test_size': 0.2,
    'random_state': 42,
    'cv_folds': 5,
}

# Features for ML model
PLAYER_FEATURES = [
    'age',
    'potential',
    'games_played',
    'avg_disposals',
    'avg_kicks',
    'avg_handballs',
    'avg_marks',
    'avg_tackles',
    'avg_goals',
    'avg_behinds',
    'avg_hitouts',
    'avg_score',
    'price',
    'position_encoded',
    'team_encoded',
    'draft_pick',
    'draft_value',
    'injured_last_year',
    'injury_history',
    'games_last_3',
    'form_last_5'
]
