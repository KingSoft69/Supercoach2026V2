# AFL Supercoach 2026 - Machine Learning Team Optimizer

An intelligent machine learning system that optimizes your AFL Supercoach team selection for the 2026 season to maximize your chances of winning the overall rank.

## Features

- **Machine Learning Predictions**: Uses Gradient Boosting models to predict player performance based on historical statistics
- **Intelligent Team Selection**: Optimizes team composition considering:
  - Salary cap constraints ($10M)
  - Position requirements (DEF, MID, RUC, FWD)
  - Player value (points per dollar)
  - Risk factors (injury history, form)
- **Multiple Optimization Strategies**: 
  - Balanced: Mix of performance and value
  - Value: Maximum points per dollar
  - High Score: Maximum predicted score
- **Comprehensive Analysis**: Detailed team analysis including age distribution, team diversity, and risk assessment

## Installation

1. Clone this repository:
```bash
git clone https://github.com/KingSoft69/Supercoach2026V2.git
cd Supercoach2026V2
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the optimizer:
```bash
python supercoach_optimizer.py
```

The program will:
1. Load/generate player data
2. Train machine learning models on player statistics
3. Predict player performance for 2026
4. Optimize team selection within constraints
5. Output the optimal team composition

## Output Files

- `optimal_team_2026.csv`: Your optimized 30-player team
- `all_players_analyzed.csv`: All players with ML predictions and value scores
- `player_data_2026.csv`: Raw player statistics
- `supercoach_model.pkl`: Trained ML model (can be reused)

## Configuration

Edit `config.py` to customize:
- Salary cap and team size
- Position requirements
- Scoring weights
- ML model parameters

## How It Works

### 1. Data Collection
The system collects AFL player statistics including:
- Disposals, kicks, handballs
- Marks, tackles, goals
- Hitouts (for ruckmen)
- Historical performance
- Current form and injury history

### 2. Machine Learning Model
Uses Gradient Boosting Regression to predict:
- Expected average score per game
- Player value (points per $)
- Risk-adjusted performance

Features used:
- Age and experience
- Historical averages
- Recent form (last 3-5 games)
- Position and team
- Injury history

### 3. Team Optimization
Applies constraint-based optimization to select 30 players:
- 6 Defenders
- 8 Midfielders  
- 2 Ruckmen
- 6 Forwards
- 8 Bench players

Optimizes for maximum predicted weekly score while staying under salary cap.

## Team Strategy

The optimizer considers multiple factors:
- **Performance**: Predicted fantasy points
- **Value**: Points per dollar spent
- **Balance**: Position coverage and team diversity
- **Risk**: Injury history and recent games played
- **Form**: Recent performance trends

## Requirements

- Python 3.8+
- pandas
- numpy
- scikit-learn
- scipy

See `requirements.txt` for complete list.

## Future Enhancements

- Real-time data integration with AFL statistics API
- Weekly team optimization and trade suggestions
- Captain selection optimization
- Historical validation against past seasons
- Web interface for easier interaction
- Multi-week optimization considering fixture difficulty

## Contributing

Feel free to contribute improvements, bug fixes, or additional features!

## License

MIT License - see LICENSE file for details

## Disclaimer

This tool is for entertainment and educational purposes. Player predictions are based on statistical models and may not reflect actual performance. Always do your own research before making fantasy team decisions.

## Author

Created for AFL Supercoach 2026 optimization