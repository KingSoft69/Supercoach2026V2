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
The system collects AFL player statistics from FootyWire, including:
- **Basic Stats**: Disposals, kicks, handballs, marks, tackles, goals, hitouts
- **Performance**: Historical averages and current form
- **Demographics**: Age, team, position
- **Draft Information**: Draft pick number (earlier picks indicate higher talent)
- **Injury History**: Whether player was injured last year and career injury count
- **Availability**: Recent games played

### 2. Machine Learning Model
Uses Gradient Boosting Regression to predict player performance considering:
- **Age & Potential**: Young players (18-23) have growth potential, peak age is 24-28
- **Draft Pedigree**: Top 10 picks and first-round picks weighted higher
- **Injury Risk**: Players injured last year are downweighted
- **Historical Performance**: Career averages and recent form
- **Position-specific Patterns**: Different scoring patterns for DEF/MID/RUC/FWD

Advanced features:
- Age-squared and years-to-peak (non-linear age effects)
- Potential-adjusted scores (upside for young players)
- Injury risk scores (combining history and recent injuries)
- Draft value indicators (top 10, first round flags)
- Availability scores (games played recently)

### 3. Team Optimization
Applies constraint-based optimization to select 30 players:
- 6 Defenders
- 8 Midfielders  
- 2 Ruckmen
- 6 Forwards
- 8 Bench players

Optimizes for:
- **Maximum predicted weekly score** while staying under salary cap
- **Value**: Points per dollar spent
- **Balance**: Position coverage and team diversity
- **Risk**: Downweights injury-prone players
- **Upside**: Bonus for young players with high potential

## Team Strategy

The optimizer considers multiple factors:
- **Performance**: Predicted fantasy points based on historical data
- **Value**: Points per dollar spent (optimal budget allocation)
- **Balance**: Position coverage and AFL team diversity
- **Age & Potential**: Young players (18-23) with high upside get bonus weighting
- **Draft Pedigree**: Top draft picks historically perform better
- **Risk**: Injury history and recent injuries are heavily penalized
- **Availability**: Recent games played indicates current fitness
- **Form**: Recent performance trends weighted more than career averages

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