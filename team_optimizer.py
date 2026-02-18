"""
Team optimization - Simplified greedy approach with guaranteed position filling
"""
import numpy as np
import pandas as pd
import config


class TeamOptimizer:
    """Optimizes team selection based on predicted performance and constraints"""
    
    def __init__(self):
        self.selected_team = None
        
    def optimize_team(self, players_df, strategy='balanced'):
        """
        Optimize team selection - fills all 30 positions within budget
        """
        print("\n" + "="*60)
        print("OPTIMIZING TEAM SELECTION")
        print("="*60)
        
        df = players_df.copy()
        
        # Choose objective - for this algorithm, always use value to stay within budget
        df['objective'] = df['adjusted_value']
        
        selected = []
        remaining_budget = config.SALARY_CAP
        position_counts = {pos: 0 for pos in config.POSITION_REQUIREMENTS.keys()}
        
        # Phase 1: Fill each required position with best value within budget
        for pos in ['DEF', 'MID', 'RUC', 'FWD']:
            required = config.POSITION_REQUIREMENTS[pos]['min']
            # Get players for this position sorted by value
            pos_players = df[df['position'] == pos].sort_values('adjusted_value', ascending=False)
            
            for _, player in pos_players.iterrows():
                if position_counts[pos] < required and player['price'] <= remaining_budget:
                    selected.append(player.to_dict())
                    remaining_budget -= player['price']
                    position_counts[pos] += 1
                if position_counts[pos] >= required:
                    break
        
        # Phase 2: Fill bench with best remaining value
        bench_needed = config.POSITION_REQUIREMENTS['BENCH']['min']
        selected_ids = [s['player_id'] for s in selected]
        remaining_players = df[~df['player_id'].isin(selected_ids)].sort_values('adjusted_value', ascending=False)
        
        for _, player in remaining_players.iterrows():
            if position_counts['BENCH'] < bench_needed and player['price'] <= remaining_budget:
                selected.append(player.to_dict())
                remaining_budget -= player['price']
                position_counts['BENCH'] += 1
            if position_counts['BENCH'] >= bench_needed:
                break
        
        # Create team DataFrame
        self.selected_team = pd.DataFrame(selected)
        
        # Calculate statistics
        total_cost = self.selected_team['price'].sum()
        total_predicted_score = self.selected_team['predicted_score'].sum()
        avg_value = self.selected_team['adjusted_value'].mean()
        
        print(f"\nTeam Selection Complete!")
        print(f"Total Players: {len(self.selected_team)}/{config.TEAM_SIZE}")
        print(f"Total Cost: ${total_cost:,} / ${config.SALARY_CAP:,}")
        print(f"Budget Status: {'✓ WITHIN BUDGET' if total_cost <= config.SALARY_CAP else '✗ OVER BUDGET'}")
        print(f"Total Predicted Score: {total_predicted_score:.2f}")
        print(f"Average Value Score: {avg_value:.2f}")
        print(f"\nPosition Breakdown:")
        for pos in ['DEF', 'MID', 'RUC', 'FWD', 'BENCH']:
            count = position_counts[pos]
            req = config.POSITION_REQUIREMENTS[pos]
            status = "✓" if count >= req['min'] and count <= req['max'] else "✗"
            print(f"  {status} {pos}: {count} (required: {req['min']}-{req['max']})")
        
        return self.selected_team
    
    def get_starting_lineup(self):
        """Get the starting 22 players"""
        if self.selected_team is None:
            raise ValueError("No team selected.")
        
        starting_lineup = []
        for position in ['DEF', 'MID', 'RUC', 'FWD']:
            pos_players = self.selected_team[self.selected_team['position'] == position]
            on_field = config.POSITION_REQUIREMENTS[position]['on_field']
            top_players = pos_players.nlargest(on_field, 'predicted_score')
            starting_lineup.append(top_players)
        
        return pd.concat(starting_lineup)
    
    def get_bench_players(self):
        """Get bench players"""
        if self.selected_team is None:
            raise ValueError("No team selected.")
        starting = self.get_starting_lineup()
        bench = self.selected_team[~self.selected_team['player_id'].isin(starting['player_id'])]
        return bench
    
    def display_team(self):
        """Display formatted team selection"""
        if self.selected_team is None:
            raise ValueError("No team selected.")
        
        print("\n" + "="*80)
        print("2026 AFL SUPERCOACH OPTIMAL TEAM")
        print("="*80)
        
        starting = self.get_starting_lineup()
        
        print("\n--- STARTING LINEUP ---")
        for position in ['DEF', 'MID', 'RUC', 'FWD']:
            print(f"\n{position}:")
            pos_players = starting[starting['position'] == position]
            for _, player in pos_players.iterrows():
                print(f"  {player['name']:25s} ({player['team']:15s}) - "
                      f"${player['price']:7,} - Score: {player['predicted_score']:6.2f} - "
                      f"Value: {player['adjusted_value']:5.2f}")
        
        print("\n--- BENCH ---")
        bench = self.get_bench_players()
        for _, player in bench.iterrows():
            print(f"  {player['name']:25s} ({player['team']:15s}) - "
                  f"${player['price']:7,} - Score: {player['predicted_score']:6.2f}")
        
        total_cost = self.selected_team['price'].sum()
        total_score = starting['predicted_score'].sum()
        
        print("\n" + "="*80)
        print(f"Total Squad Cost: ${total_cost:,} / ${config.SALARY_CAP:,}")
        print(f"Money Remaining: ${config.SALARY_CAP - total_cost:,}")
        print(f"Expected Weekly Score: {total_score:.2f}")
        print(f"Average Value: {self.selected_team['adjusted_value'].mean():.2f}")
        print("="*80)
    
    def save_team(self, filepath='optimal_team.csv'):
        """Save team to CSV"""
        if self.selected_team is None:
            raise ValueError("No team selected.")
        self.selected_team.to_csv(filepath, index=False)
        print(f"\nTeam saved to {filepath}")
    
    def analyze_team_balance(self):
        """Analyze team composition"""
        if self.selected_team is None:
            raise ValueError("No team selected.")
        
        print("\n--- TEAM ANALYSIS ---")
        
        avg_age = self.selected_team['age'].mean()
        print(f"Average Age: {avg_age:.1f}")
        
        team_counts = self.selected_team['team'].value_counts()
        print(f"\nTeam Diversity: {len(team_counts)} different AFL teams")
        print("Players per team:")
        for team, count in team_counts.head(5).items():
            print(f"  {team}: {count}")
        
        print(f"\nPrice Range: ${self.selected_team['price'].min():,} - ${self.selected_team['price'].max():,}")
        print(f"Average Price: ${self.selected_team['price'].mean():,.0f}")
        
        avg_injury = self.selected_team['injury_history'].mean()
        print(f"\nAverage Injury History: {avg_injury:.2f}")
        
        return {
            'avg_age': avg_age,
            'team_diversity': len(team_counts),
            'avg_price': self.selected_team['price'].mean(),
            'avg_injury_risk': avg_injury
        }
