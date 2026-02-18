"""
Configuration for 2026 AFL Supercoach
"""

# Team constraints
SALARY_CAP = 10000000  # $10 million salary cap
TEAM_SIZE = 30  # Total players in team

# Position requirements
POSITION_REQUIREMENTS = {
    'DEF': {'min': 6, 'max': 6, 'on_field': 6},
    'MID': {'min': 8, 'max': 8, 'on_field': 8},
    'RUC': {'min': 2, 'max': 2, 'on_field': 2},
    'FWD': {'min': 6, 'max': 6, 'on_field': 6},
    'BENCH': {'min': 8, 'max': 8, 'on_field': 0}
}

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
    'injury_history',
    'games_last_3',
    'form_last_5'
]
