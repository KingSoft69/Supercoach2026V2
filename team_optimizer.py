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
        
    def optimize_team(self, players_df, strategy='max_score'):
        """
        Optimize team selection - follows Supercoach 2026 rules:
        - 22 onfield players (6 DEF, 8 MID, 2 RUC, 6 FWD)
        - 8 bench players (any position, for coverage)
        - Total 30 players within salary cap
        
        Strategies:
        - 'max_score': Maximize total predicted score (best for overall rank)
        - 'balanced': Balance between score and value
        - 'value': Maximize value (points per dollar)
        """
        print("\n" + "="*60)
        print("OPTIMIZING TEAM SELECTION - SUPERCOACH 2026 RULES")
        print(f"Strategy: {strategy.upper()} - Maximizing for Overall Rank Victory")
        print("="*60)
        
        df = players_df.copy()
        
        # Set optimization objective based on strategy
        if strategy == 'max_score':
            # For overall rank, use score that includes rookie upside
            df['objective'] = df['overall_rank_score']  # Predicted score * upside * risk
            print("\n🎯 Objective: MAXIMIZE SCORE with ROOKIE UPSIDE (Win Overall Rank)")
            print("   Factoring in young players getting better throughout the season")
        elif strategy == 'value':
            df['objective'] = df['adjusted_value']
            print("\n🎯 Objective: Maximize value (points per dollar)")
        else:  # balanced
            # Balanced approach: score * value
            df['objective'] = df['predicted_score'] * df['adjusted_value']
            print("\n🎯 Objective: Balance score and value")
        
        # Sort by objective
        df = df.sort_values('objective', ascending=False).reset_index(drop=True)
        
        selected = []
        remaining_budget = config.SALARY_CAP
        position_counts = {pos: 0 for pos in config.POSITION_REQUIREMENTS.keys()}
        
        # Calculate target budget per position based on requirements
        total_onfield = sum(config.POSITION_REQUIREMENTS[pos]['on_field'] for pos in ['DEF', 'MID', 'RUC', 'FWD'])
        avg_price_per_player = config.SALARY_CAP / config.TEAM_SIZE
        
        print(f"\nBudget Strategy:")
        print(f"  Total Budget: ${config.SALARY_CAP:,}")
        print(f"  Target Players: {config.TEAM_SIZE}")
        print(f"  Average Price Target: ${avg_price_per_player:,.0f} per player")
        
        # Phase 1: Fill onfield positions prioritizing high scorers
        print("\nPhase 1: Selecting starting 22 onfield players (highest scorers)...")
        for pos in ['DEF', 'MID', 'RUC', 'FWD']:
            onfield_needed = config.POSITION_REQUIREMENTS[pos]['on_field']
            pos_players = df[df['position'] == pos].copy()
            
            # Calculate budget for this position (more flexible for max_score strategy)
            if strategy == 'max_score':
                # For max score, allow spending more on high performers
                pos_budget_allocation = (onfield_needed / total_onfield) * config.SALARY_CAP * 0.85
            else:
                pos_budget_allocation = (onfield_needed / total_onfield) * config.SALARY_CAP * 0.7
                
            target_price = pos_budget_allocation / onfield_needed
            
            print(f"  Selecting {onfield_needed} {pos} (target ~${target_price:,.0f} each)...")
            
            # Select best players by objective
            selected_for_pos = 0
            for _, player in pos_players.iterrows():
                if selected_for_pos < onfield_needed and player['price'] <= remaining_budget:
                    # For max_score, be more aggressive with high scorers
                    if strategy == 'max_score':
                        accept = (player['predicted_score'] >= df[df['position'] == pos]['predicted_score'].quantile(0.6) or
                                 selected_for_pos >= onfield_needed - 2)  # Must fill last 2 slots
                    else:
                        accept = (player['price'] <= target_price * 1.5 or 
                                 selected_for_pos >= onfield_needed - 1)
                    
                    if accept or selected_for_pos >= onfield_needed - 1:  # Must fill last slots
                        player_dict = player.to_dict()
                        player_dict['onfield'] = True
                        selected.append(player_dict)
                        remaining_budget -= player['price']
                        position_counts[pos] += 1
                        selected_for_pos += 1
                        
                if selected_for_pos >= onfield_needed:
                    break
        
        # Phase 2: Fill bench (8 players) - cheaper backup options
        print(f"\nPhase 2: Selecting {config.BENCH_SIZE} bench players...")
        selected_ids = [s['player_id'] for s in selected]
        remaining_players = df[~df['player_id'].isin(selected_ids)].copy()
        
        # For bench, prioritize cheap players with decent scores
        remaining_players = remaining_players.sort_values('price', ascending=True)
        
        target_bench_price = remaining_budget / config.BENCH_SIZE if remaining_budget > 0 else 100000
        print(f"  Target bench price: ~${target_bench_price:,.0f} each (cheapest available)")
        
        bench_count = 0
        for _, player in remaining_players.iterrows():
            pos = player['position']
            # Check if we can add more of this position and afford it
            if (bench_count < config.BENCH_SIZE and 
                player['price'] <= remaining_budget and
                position_counts[pos] < config.POSITION_REQUIREMENTS[pos]['max']):
                player_dict = player.to_dict()
                player_dict['onfield'] = False
                selected.append(player_dict)
                remaining_budget -= player['price']
                position_counts[pos] += 1
                bench_count += 1
                
            if bench_count >= config.BENCH_SIZE:
                break
        
        # If we didn't fill all positions, warn the user
        if len(selected) < config.TEAM_SIZE:
            print(f"\n⚠ WARNING: Could only select {len(selected)}/{config.TEAM_SIZE} players within budget")
            print(f"  Remaining budget: ${remaining_budget:,}")
            print(f"  Consider adjusting strategy or checking data quality")
        
        # Create team DataFrame
        self.selected_team = pd.DataFrame(selected)
        
        # Calculate statistics
        total_cost = self.selected_team['price'].sum()
        onfield_players = self.selected_team[self.selected_team['onfield'] == True]
        onfield_score = onfield_players['predicted_score'].sum() if len(onfield_players) > 0 else 0
        avg_value = self.selected_team['adjusted_value'].mean()
        
        print(f"\nTeam Selection Complete!")
        print(f"Total Players: {len(self.selected_team)}/{config.TEAM_SIZE}")
            
            # Calculate budget for this position (proportional)
            pos_budget_allocation = (onfield_needed / total_onfield) * config.SALARY_CAP * 0.7  # Use 70% for starting lineup
            target_price = pos_budget_allocation / onfield_needed
            
            print(f"  Selecting {onfield_needed} {pos} (target ~${target_price:,.0f} each)...")
            
            # Try to fill with players close to target price
            selected_for_pos = 0
            for _, player in pos_players.iterrows():
                if selected_for_pos < onfield_needed and player['price'] <= remaining_budget:
                    # Accept if price is reasonable or we need to fill remaining slots
                    accept = (player['price'] <= target_price * 1.5 or 
                             selected_for_pos < onfield_needed and player['price'] <= remaining_budget * 0.5)
                    
                    if accept or selected_for_pos >= onfield_needed - 1:  # Must fill last slots
                        player_dict = player.to_dict()
                        player_dict['onfield'] = True
                        selected.append(player_dict)
                        remaining_budget -= player['price']
                        position_counts[pos] += 1
                        selected_for_pos += 1
                        
                if selected_for_pos >= onfield_needed:
                    break
        
        # Phase 2: Fill bench (8 players) with best remaining value
        print(f"\nPhase 2: Selecting {config.BENCH_SIZE} bench players...")
        selected_ids = [s['player_id'] for s in selected]
        remaining_players = df[~df['player_id'].isin(selected_ids)].copy()
        
        # Target cheaper bench players
        target_bench_price = remaining_budget / config.BENCH_SIZE if remaining_budget > 0 else 100000
        print(f"  Target bench price: ~${target_bench_price:,.0f} each")
        
        bench_count = 0
        for _, player in remaining_players.iterrows():
            pos = player['position']
            # Check if we can add more of this position and afford it
            if (bench_count < config.BENCH_SIZE and 
                player['price'] <= remaining_budget and
                position_counts[pos] < config.POSITION_REQUIREMENTS[pos]['max']):
                player_dict = player.to_dict()
                player_dict['onfield'] = False
                selected.append(player_dict)
                remaining_budget -= player['price']
                position_counts[pos] += 1
                bench_count += 1
                
            if bench_count >= config.BENCH_SIZE:
                break
        
        # If we didn't fill all positions, warn the user
        if len(selected) < config.TEAM_SIZE:
            print(f"\n⚠ WARNING: Could only select {len(selected)}/{config.TEAM_SIZE} players within budget")
            print(f"  Remaining budget: ${remaining_budget:,}")
            print(f"  Consider adjusting player valuations or increasing budget")
        
        # Create team DataFrame
        self.selected_team = pd.DataFrame(selected)
        
        # Calculate statistics
        total_cost = self.selected_team['price'].sum()
        onfield_players = self.selected_team[self.selected_team['onfield'] == True]
        onfield_score = onfield_players['predicted_score'].sum() if len(onfield_players) > 0 else 0
        avg_value = self.selected_team['adjusted_value'].mean()
        
        print(f"\nTeam Selection Complete!")
        print(f"Total Players: {len(self.selected_team)}/{config.TEAM_SIZE}")
        print(f"Total Cost: ${total_cost:,} / ${config.SALARY_CAP:,}")
        print(f"Budget Status: {'✓ WITHIN BUDGET' if total_cost <= config.SALARY_CAP else '✗ OVER BUDGET'}")
        print(f"Onfield (Starting 22) Predicted Score: {onfield_score:.2f}")
        print(f"Average Value Score: {avg_value:.2f}")
        print(f"\nPosition Breakdown:")
        for pos in ['DEF', 'MID', 'RUC', 'FWD']:
            count = position_counts[pos]
            req = config.POSITION_REQUIREMENTS[pos]
            onfield = config.POSITION_REQUIREMENTS[pos]['on_field']
            bench = count - onfield
            status = "✓" if count >= req['min'] and count <= req['max'] else "✗"
            print(f"  {status} {pos}: {count} total ({onfield} onfield + {bench} bench)")
        
        return self.selected_team
    
    def get_starting_lineup(self):
        """Get the starting 22 onfield players"""
        if self.selected_team is None:
            raise ValueError("No team selected.")
        
        # Return players marked as onfield
        return self.selected_team[self.selected_team['onfield'] == True].copy()
    
    def get_bench_players(self):
        """Get the 8 bench players"""
        if self.selected_team is None:
            raise ValueError("No team selected.")
        
        # Return players marked as bench
        return self.selected_team[self.selected_team['onfield'] == False].copy()
    
    def display_team(self):
        """Display formatted team selection following Supercoach 2026 rules"""
        if self.selected_team is None:
            raise ValueError("No team selected.")
        
        print("\n" + "="*80)
        print("2026 AFL SUPERCOACH OPTIMAL TEAM - SUPERCOACH RULES")
        print("="*80)
        
        starting = self.get_starting_lineup()
        
        print("\n--- STARTING LINEUP (22 ONFIELD PLAYERS) ---")
        for position in ['DEF', 'MID', 'RUC', 'FWD']:
            print(f"\n{position}:")
            pos_players = starting[starting['position'] == position]
            for _, player in pos_players.iterrows():
                print(f"  {player['name']:25s} ({player['team']:15s}) - "
                      f"${player['price']:7,} - Score: {player['predicted_score']:6.2f} - "
                      f"Value: {player['adjusted_value']:5.2f}")
        
        print("\n--- BENCH (8 EMERGENCY PLAYERS) ---")
        bench = self.get_bench_players()
        # Group bench by position for better display
        for position in ['DEF', 'MID', 'RUC', 'FWD']:
            pos_bench = bench[bench['position'] == position]
            if len(pos_bench) > 0:
                print(f"\n{position} Bench:")
                for _, player in pos_bench.iterrows():
                    print(f"  {player['name']:25s} ({player['team']:15s}) - "
                          f"${player['price']:7,} - Score: {player['predicted_score']:6.2f} - "
                          f"Value: {player['adjusted_value']:5.2f}")
        
        total_cost = self.selected_team['price'].sum()
        total_score = starting['predicted_score'].sum()
        
        print("\n" + "="*80)
        print(f"Total Squad Cost: ${total_cost:,} / ${config.SALARY_CAP:,}")
        print(f"Money Remaining: ${config.SALARY_CAP - total_cost:,}")
        print(f"Expected Weekly Score (Starting 22): {total_score:.2f}")
        print(f"Average Value: {self.selected_team['adjusted_value'].mean():.2f}")
        print(f"Team Composition: {len(starting)} onfield + {len(bench)} bench = {config.TEAM_SIZE} total")
        print("="*80)
    
    def save_team(self, filepath='optimal_team.csv'):
        """Save team to CSV"""
        if self.selected_team is None:
            raise ValueError("No team selected.")
        self.selected_team.to_csv(filepath, index=False)
        print(f"\nTeam saved to {filepath}")
    
    def save_team_excel(self, filepath='optimal_team_2026.xlsx'):
        """Save team to Excel with formatting following Supercoach 2026 rules"""
        if self.selected_team is None:
            raise ValueError("No team selected.")
        
        # Create Excel writer
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Starting lineup (22 onfield players)
            starting = self.get_starting_lineup()
            starting_sorted = starting.sort_values(['position', 'predicted_score'], ascending=[True, False])
            starting_sorted.to_excel(writer, sheet_name='Starting 22 (Onfield)', index=False)
            
            # Bench (8 players)
            bench = self.get_bench_players()
            bench_sorted = bench.sort_values(['position', 'predicted_score'], ascending=[True, False])
            bench_sorted.to_excel(writer, sheet_name='Bench (8 Emergency)', index=False)
            
            # Full team
            full_team_sorted = self.selected_team.sort_values(['onfield', 'position', 'predicted_score'], ascending=[False, True, False])
            full_team_sorted.to_excel(writer, sheet_name='Full Team', index=False)
            
            # Summary statistics
            summary_data = {
                'Metric': [
                    'Total Players',
                    'Onfield Players',
                    'Bench Players',
                    'Total Cost',
                    'Salary Cap',
                    'Remaining Budget',
                    'Starting 22 Predicted Score',
                    'Average Player Value',
                    'Average Age',
                    'Average Injury History'
                ],
                'Value': [
                    len(self.selected_team),
                    len(starting),
                    len(bench),
                    f"${self.selected_team['price'].sum():,}",
                    f"${config.SALARY_CAP:,}",
                    f"${config.SALARY_CAP - self.selected_team['price'].sum():,}",
                    f"{starting['predicted_score'].sum():.2f}",
                    f"{self.selected_team['adjusted_value'].mean():.2f}",
                    f"{self.selected_team['age'].mean():.1f}",
                    f"{self.selected_team['injury_history'].mean():.2f}"
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        print(f"\nTeam saved to Excel: {filepath}")
    
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
