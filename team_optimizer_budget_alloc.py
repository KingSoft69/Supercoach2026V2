"""
Team optimization module using constraint-based optimization - Fixed version
"""
import numpy as np
import pandas as pd
from scipy.optimize import linprog
import config


class TeamOptimizer:
    """Optimizes team selection based on predicted performance and constraints"""
    
    def __init__(self):
        self.selected_team = None
        self.optimization_result = None
        
    def optimize_team(self, players_df, strategy='balanced'):
        """
        Optimize team selection with guaranteed budget compliance
        
        Parameters:
        - players_df: DataFrame with player data including predicted_score and value_score
        - strategy: 'balanced', 'value', or 'high_score'
        """
        print("\n" + "="*60)
        print("OPTIMIZING TEAM SELECTION")
        print("="*60)
        
        # Prepare data
        df = players_df.copy()
        
        # Choose objective based on strategy
        if strategy == 'value':
            df['objective'] = df['adjusted_value']
        elif strategy == 'high_score':
            df['objective'] = df['predicted_score']
        else:  # balanced
            df['objective'] = df['predicted_score'] * 0.7 + df['adjusted_value'] * 0.3
        
        # Calculate budget allocation to ensure all positions can be filled
        min_prices = {}
        for pos in ['DEF', 'MID', 'RUC', 'FWD']:
            required = config.POSITION_REQUIREMENTS[pos]['min']
            pos_players = df[df['position'] == pos].nsmallest(required, 'price')
            min_prices[pos] = pos_players['price'].sum()
        
        # Reserve for bench
        bench_needed = config.POSITION_REQUIREMENTS['BENCH']['min']
        min_prices['BENCH'] = df.nsmallest(bench_needed, 'price')['price'].sum()
        
        total_min = sum(min_prices.values())
        buffer = config.SALARY_CAP - total_min
        
        # Allocate budget proportionally
        position_budgets = {
            'MID': min_prices['MID'] + buffer * 0.35,
            'DEF': min_prices['DEF'] + buffer * 0.25,
            'FWD': min_prices['FWD'] + buffer * 0.20,
            'RUC': min_prices['RUC'] + buffer * 0.15,
            'BENCH': min_prices['BENCH'] + buffer * 0.05
        }
        
        selected_players = []
        position_counts = {pos: 0 for pos in config.POSITION_REQUIREMENTS.keys()}
        total_spent = 0
        
        # Phase 1: Fill each position within allocated budget
        for position in ['MID', 'DEF', 'FWD', 'RUC']:
            pos_df = df[df['position'] == position].sort_values('objective', ascending=False).copy()
            required = config.POSITION_REQUIREMENTS[position]['min']
            budget_for_position = position_budgets[position]
            
            count = 0
            spent = 0
            
            for _, player in pos_df.iterrows():
                if count < required and spent + player['price'] <= budget_for_position:
                    selected_players.append(player.to_dict())
                    spent += player['price']
                    total_spent += player['price']
                    position_counts[position] += 1
                    count += 1
                if count >= required:
                    break
            
            # If couldn't fill within position budget, use remaining global budget
            if count < required:
                remaining_budget = config.SALARY_CAP - total_spent
                cheaper_df = pos_df.sort_values('price')
                for _, player in cheaper_df.iterrows():
                    if player['player_id'] not in [p['player_id'] for p in selected_players]:
                        if count < required and player['price'] <= remaining_budget:
                            selected_players.append(player.to_dict())
                            total_spent += player['price']
                            remaining_budget -= player['price']
                            position_counts[position] += 1
                            count += 1
                        if count >= required:
                            break
        
        # Phase 2: Fill bench with remaining budget
        bench_budget = config.SALARY_CAP - total_spent
        selected_ids = [p['player_id'] for p in selected_players]
        remaining_df = df[~df['player_id'].isin(selected_ids)].sort_values('adjusted_value', ascending=False)
        
        bench_count = 0
        for _, player in remaining_df.iterrows():
            if bench_count < bench_needed and player['price'] <= bench_budget:
                selected_players.append(player.to_dict())
                bench_budget -= player['price']
                total_spent += player['price']
                position_counts['BENCH'] += 1
                bench_count += 1
        
        # If still short on bench, get absolute cheapest
        if bench_count < bench_needed:
            remaining_ids = [p['player_id'] for p in selected_players]
            cheapest_df = df[~df['player_id'].isin(remaining_ids)].sort_values('price')
            for _, player in cheapest_df.iterrows():
                if bench_count < bench_needed and player['price'] <= bench_budget:
                    selected_players.append(player.to_dict())
                    bench_budget -= player['price']
                    total_spent += player['price']
                    position_counts['BENCH'] += 1
                    bench_count += 1
                if bench_count >= bench_needed:
                    break
        
        # Create team DataFrame
        self.selected_team = pd.DataFrame(selected_players)
        
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
        """Get the starting 22 players (on-field)"""
        if self.selected_team is None:
            raise ValueError("No team selected. Call optimize_team() first.")
        
        starting_lineup = []
        
        for position in ['DEF', 'MID', 'RUC', 'FWD']:
            pos_players = self.selected_team[self.selected_team['position'] == position]
            on_field = config.POSITION_REQUIREMENTS[position]['on_field']
            
            # Select top players by predicted score
            top_players = pos_players.nlargest(on_field, 'predicted_score')
            starting_lineup.append(top_players)
        
        starting_df = pd.concat(starting_lineup)
        return starting_df
    
    def get_bench_players(self):
        """Get bench players"""
        if self.selected_team is None:
            raise ValueError("No team selected. Call optimize_team() first.")
        
        starting = self.get_starting_lineup()
        bench = self.selected_team[~self.selected_team['player_id'].isin(starting['player_id'])]
        return bench
    
    def display_team(self):
        """Display formatted team selection"""
        if self.selected_team is None:
            raise ValueError("No team selected. Call optimize_team() first.")
        
        print("\n" + "="*80)
        print("2026 AFL SUPERCOACH OPTIMAL TEAM")
        print("="*80)
        
        # Starting lineup
        print("\n--- STARTING LINEUP ---")
        starting = self.get_starting_lineup()
        
        for position in ['DEF', 'MID', 'RUC', 'FWD']:
            print(f"\n{position}:")
            pos_players = starting[starting['position'] == position]
            for _, player in pos_players.iterrows():
                print(f"  {player['name']:25s} ({player['team']:15s}) - "
                      f"${player['price']:7,} - Score: {player['predicted_score']:6.2f} - "
                      f"Value: {player['adjusted_value']:5.2f}")
        
        # Bench
        print("\n--- BENCH ---")
        bench = self.get_bench_players()
        for _, player in bench.iterrows():
            print(f"  {player['name']:25s} ({player['team']:15s}) - "
                  f"${player['price']:7,} - Score: {player['predicted_score']:6.2f}")
        
        # Summary
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
        """Analyze team composition and balance"""
        if self.selected_team is None:
            raise ValueError("No team selected.")
        
        print("\n--- TEAM ANALYSIS ---")
        
        # Age distribution
        avg_age = self.selected_team['age'].mean()
        print(f"Average Age: {avg_age:.1f}")
        
        # Team diversity
        team_counts = self.selected_team['team'].value_counts()
        print(f"\nTeam Diversity: {len(team_counts)} different AFL teams")
        print("Players per team:")
        for team, count in team_counts.head(5).items():
            print(f"  {team}: {count}")
        
        # Price distribution
        print(f"\nPrice Range: ${self.selected_team['price'].min():,} - "
              f"${self.selected_team['price'].max():,}")
        print(f"Average Price: ${self.selected_team['price'].mean():,.0f}")
        
        # Risk assessment
        avg_injury = self.selected_team['injury_history'].mean()
        print(f"\nAverage Injury History: {avg_injury:.2f}")
        
        return {
            'avg_age': avg_age,
            'team_diversity': len(team_counts),
            'avg_price': self.selected_team['price'].mean(),
            'avg_injury_risk': avg_injury
        }
