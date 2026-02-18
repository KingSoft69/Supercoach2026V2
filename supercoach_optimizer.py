"""
Main program for AFL Supercoach 2026 Team Optimizer
"""
import sys
import pandas as pd
from data_collector import AFLDataCollector
from ml_predictor import PlayerPerformancePredictor
from team_optimizer import TeamOptimizer
import config


def main():
    """Main execution function"""
    print("="*80)
    print("AFL SUPERCOACH 2026 - MACHINE LEARNING TEAM OPTIMIZER")
    print("="*80)
    print("\nThis program uses machine learning to select the optimal AFL Supercoach team")
    print("for the 2026 season, maximizing predicted performance within budget constraints.")
    print("\n" + "="*80 + "\n")
    
    # Step 1: Collect player data from FootyWire
    print("STEP 1: Collecting Real Player Data from FootyWire")
    print("-" * 40)
    collector = AFLDataCollector()
    
    # Load real data from FootyWire with detailed player information
    print("Fetching player data from FootyWire with detailed player information...")
    print("This may take a few minutes as we fetch details for each player...")
    players_df = collector.load_real_data(fetch_player_details=True)
    
    if players_df is None or len(players_df) == 0:
        print("\n❌ ERROR: Could not load real data from FootyWire!")
        print("Please check your internet connection and try again.")
        sys.exit(1)
    
    print(f"✓ Successfully loaded {len(players_df)} real players from FootyWire")
    print(f"Positions: {players_df['position'].value_counts().to_dict()}")
    
    # Save raw data
    collector.save_data('player_data_2026.csv')
    
    # Step 2: Train ML models
    print("\n" + "="*80)
    print("STEP 2: Training Machine Learning Models")
    print("-" * 40)
    predictor = PlayerPerformancePredictor()
    predictor.train_score_predictor(players_df)
    
    # Save model
    predictor.save_model('supercoach_model.pkl')
    
    # Step 3: Calculate value scores for all players
    print("\n" + "="*80)
    print("STEP 3: Calculating Player Values")
    print("-" * 40)
    players_df = predictor.calculate_value_scores(players_df)
    
    # Display top players by position
    print("\nTop 5 Players by Value Score (per position):")
    for position in ['DEF', 'MID', 'RUC', 'FWD']:
        print(f"\n{position}:")
        top_players = players_df[players_df['position'] == position].nlargest(5, 'adjusted_value')
        for _, player in top_players.iterrows():
            print(f"  {player['name']:25s} - "
                  f"Score: {player['predicted_score']:6.2f} - "
                  f"Price: ${player['price']:7,} - "
                  f"Value: {player['adjusted_value']:5.2f}")
    
    # Step 4: Optimize team selection for maximum score (overall rank victory)
    print("\n" + "="*80)
    print("STEP 4: Optimizing Team Selection for Overall Rank Victory")
    print("-" * 40)
    print("Strategy: Maximize predicted weekly score to win overall rank")
    optimizer = TeamOptimizer()
    
    # Use max_score strategy to win overall rank
    team = optimizer.optimize_team(players_df, strategy='max_score')
    
    # Step 5: Display and save results
    print("\n" + "="*80)
    print("STEP 5: Final Team Selection")
    print("="*80)
    optimizer.display_team()
    optimizer.analyze_team_balance()
    
    # Save team
    optimizer.save_team('optimal_team_2026.csv')
    
    # Save team to Excel
    optimizer.save_team_excel('optimal_team_2026.xlsx')
    
    # Save detailed analysis
    players_df.to_csv('all_players_analyzed.csv', index=False)
    
    print("\n" + "="*80)
    print("OPTIMIZATION COMPLETE!")
    print("="*80)
    print("\nOutput files created:")
    print("  - optimal_team_2026.xlsx: Your optimized team (Excel)")
    print("  - optimal_team_2026.csv: Your optimized team (CSV)")
    print("  - all_players_analyzed.csv: All players with predictions")
    print("  - player_data_2026.csv: Raw player data")
    print("  - supercoach_model.pkl: Trained ML model")
    print("\nUse this team to dominate Supercoach 2026!")
    print("="*80)
    
    return optimizer.selected_team


if __name__ == "__main__":
    try:
        team = main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
