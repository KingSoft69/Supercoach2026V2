"""
Team optimization module using constraint-based optimization
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
        Optimize team selection using budget-constrained greedy algorithm
        
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
        
        # Total players needed
        total_players_needed = config.TEAM_SIZE
        
        # Average budget per player (conservative)
        avg_price_per_player = config.SALARY_CAP / total_players_needed  # ~333k per player
        
        selected_players = []
        remaining_budget = config.SALARY_CAP
        position_counts = {pos: 0 for pos in config.POSITION_REQUIREMENTS.keys()}
        
        # Phase 1: Fill required positions with quality players (balanced budget approach)
        for position in ['MID', 'DEF', 'FWD', 'RUC']:  # Order by importance
            pos_df = df[df['position'] == position].sort_values('objective', ascending=False).copy()
            required = config.POSITION_REQUIREMENTS[position]['min']
            
            # How much budget do we have left per remaining player?
            remaining_players_needed = total_players_needed - len(selected_players)
            budget_per_remaining_player = remaining_budget / remaining_players_needed if remaining_players_needed > 0 else 0
            
            # Calculate minimum price we need to reserve for future positions
            # Estimate cheapest players for each remaining position
            future_positions = ['MID', 'DEF', 'FWD', 'RUC'][['MID', 'DEF', 'FWD', 'RUC'].index(position)+1:]
            min_budget_to_reserve = 0
            for future_pos in future_positions:
                future_required = config.POSITION_REQUIREMENTS[future_pos]['min']
                # Get cheapest players for that position
                future_df = df[df['position'] == future_pos].nsmallest(future_required, 'price')
                min_budget_to_reserve += future_df['price'].sum()
            
            # Also reserve for bench (cheapest 8 players)
            if position == 'RUC':  # Last position, so add bench reserve
                bench_needed = config.POSITION_REQUIREMENTS['BENCH']['min']
                selected_ids = [p['player_id'] for p in selected_players]
                remaining_for_bench = df[~df['player_id'].isin(selected_ids)].nsmallest(bench_needed, 'price')
                min_budget_to_reserve += remaining_for_bench['price'].sum()
            
            # Available budget for this position
            available_for_position = remaining_budget - min_budget_to_reserve
            max_price_per_player = available_for_position / required if required > 0 else 0
            max_price_per_player = max(max_price_per_player, 150000)  # At least 150k
            
            count = 0
            for _, player in pos_df.iterrows():
                if count < required:
                    # Can we afford this player?
                    if player['price'] <= remaining_budget and player['price'] <= max_price_per_player:
                        selected_players.append(player.to_dict())
                        remaining_budget -= player['price']
                        position_counts[position] += 1
                        count += 1
                if count >= required:
                    break
            
            # Fallback: if we couldn't fill the position, get cheaper players
            if count < required:
                cheaper_players = pos_df[pos_df['price'] <= remaining_budget].sort_values('price')
                for _, player in cheaper_players.iterrows():
                    player_id = player['player_id']
                    if player_id not in [p['player_id'] for p in selected_players]:
                        if count < required and player['price'] <= remaining_budget:
                            selected_players.append(player.to_dict())
                            remaining_budget -= player['price']
                            position_counts[position] += 1
                            count += 1
                        if count >= required:
                            break
        
        # Phase 2: Fill any missing position requirements with cheapest available
        # Check if all required positions are filled
        for position in ['DEF', 'MID', 'RUC', 'FWD']:
            required = config.POSITION_REQUIREMENTS[position]['min']
            current_count = position_counts[position]
            
            if current_count < required:
                print(f"\nFilling remaining {position} positions ({current_count}/{required})...")
                pos_df = df[df['position'] == position].copy()
                selected_ids = [p['player_id'] for p in selected_players]
                available = pos_df[~pos_df['player_id'].isin(selected_ids)].sort_values('price')
                
                for _, player in available.iterrows():
                    if current_count < required and player['price'] <= remaining_budget:
                        selected_players.append(player.to_dict())
                        remaining_budget -= player['price']
                        position_counts[position] += 1
                        current_count += 1
                        print(f"  ✓ Added {player['name']} for ${player['price']:,}")
                    if current_count >= required:
                        break
        
        # Phase 3: Fill bench with best available value players
        bench_needed = config.POSITION_REQUIREMENTS['BENCH']['min']
        
        print(f"\nFilling bench ({bench_needed} players needed, ${remaining_budget:,} remaining)...")
        
        # Get remaining players not already selected
        selected_ids = [p['player_id'] for p in selected_players]
        remaining_df = df[~df['player_id'].isin(selected_ids)].copy()
        
        # Sort by value (want good bench players for low price)
        remaining_df = remaining_df.sort_values('adjusted_value', ascending=False)
        
        bench_count = 0
        for _, player in remaining_df.iterrows():
            if bench_count < bench_needed:
                if player['price'] <= remaining_budget:
                    selected_players.append(player.to_dict())
                    remaining_budget -= player['price']
                    position_counts['BENCH'] += 1
                    bench_count += 1
        
        # Final fallback: if still missing bench players, get absolute cheapest
        if bench_count < bench_needed:
            remaining_ids = [p['player_id'] for p in selected_players]
            remaining_df = df[~df['player_id'].isin(remaining_ids)].sort_values('price')
            
            for _, player in remaining_df.iterrows():
                if bench_count < bench_needed and player['price'] <= remaining_budget:
                    selected_players.append(player.to_dict())
                    remaining_budget -= player['price']
                    position_counts['BENCH'] += 1
                    bench_count += 1
                if bench_count >= bench_needed:
                    break
        
        # Create team DataFrame
        self.selected_team = pd.DataFrame(selected_players)
        
        # Calculate team statistics
        total_cost = self.selected_team['price'].sum()
        total_predicted_score = self.selected_team['predicted_score'].sum()
        avg_value = self.selected_team['adjusted_value'].mean()
        
        print(f"\nTeam Selection Complete!")
        print(f"Total Players: {len(self.selected_team)}/{config.TEAM_SIZE}")
        print(f"Total Cost: ${total_cost:,} / ${config.SALARY_CAP:,}")
        print(f"Budget Status: {'✓ WITHIN BUDGET' if total_cost <= config.SALARY_CAP else '✗ OVER BUDGET'}")
        print(f"Remaining Budget: ${config.SALARY_CAP - total_cost:,}")
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
