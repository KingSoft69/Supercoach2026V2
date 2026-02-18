"""
Data collection module for AFL player statistics
"""
import pandas as pd
import numpy as np
from datetime import datetime


class AFLDataCollector:
    """Collects and manages AFL player data"""
    
    def __init__(self):
        self.players_data = None
        
    def load_sample_data(self):
        """
        Generate sample player data for demonstration
        In production, this would scrape from AFL APIs or databases
        """
        np.random.seed(42)
        
        # AFL teams
        teams = [
            'Adelaide', 'Brisbane', 'Carlton', 'Collingwood', 'Essendon',
            'Fremantle', 'Geelong', 'Gold Coast', 'GWS', 'Hawthorn',
            'Melbourne', 'North Melbourne', 'Port Adelaide', 'Richmond',
            'St Kilda', 'Sydney', 'West Coast', 'Western Bulldogs'
        ]
        
        # Positions
        positions = ['DEF', 'MID', 'RUC', 'FWD']
        
        # Generate 400+ players
        num_players = 450
        players = []
        
        for i in range(num_players):
            position = np.random.choice(positions)
            team = np.random.choice(teams)
            
            # Age distribution (18-35)
            age = int(np.random.normal(25, 4))
            age = max(18, min(35, age))
            
            # Games played (influenced by age)
            games_played = int(np.random.exponential(50) * (age - 17) / 10)
            games_played = max(0, min(300, games_played))
            
            # Performance stats (position-dependent)
            if position == 'MID':
                avg_disposals = np.random.normal(25, 5)
                avg_kicks = avg_disposals * np.random.uniform(0.5, 0.6)
                avg_handballs = avg_disposals - avg_kicks
                avg_marks = np.random.normal(5, 2)
                avg_tackles = np.random.normal(5, 2)
                avg_goals = np.random.normal(0.8, 0.4)
                avg_hitouts = np.random.normal(0.5, 0.3)
            elif position == 'DEF':
                avg_disposals = np.random.normal(20, 4)
                avg_kicks = avg_disposals * np.random.uniform(0.6, 0.7)
                avg_handballs = avg_disposals - avg_kicks
                avg_marks = np.random.normal(6, 2)
                avg_tackles = np.random.normal(4, 2)
                avg_goals = np.random.normal(0.3, 0.2)
                avg_hitouts = np.random.normal(0.2, 0.2)
            elif position == 'FWD':
                avg_disposals = np.random.normal(18, 4)
                avg_kicks = avg_disposals * np.random.uniform(0.5, 0.6)
                avg_handballs = avg_disposals - avg_kicks
                avg_marks = np.random.normal(5, 2)
                avg_tackles = np.random.normal(3, 1.5)
                avg_goals = np.random.normal(2, 0.8)
                avg_hitouts = np.random.normal(0.3, 0.2)
            else:  # RUC
                avg_disposals = np.random.normal(15, 3)
                avg_kicks = avg_disposals * np.random.uniform(0.5, 0.6)
                avg_handballs = avg_disposals - avg_kicks
                avg_marks = np.random.normal(4, 1.5)
                avg_tackles = np.random.normal(3, 1.5)
                avg_goals = np.random.normal(0.5, 0.3)
                avg_hitouts = np.random.normal(30, 8)
            
            # Ensure non-negative values
            avg_disposals = max(0, avg_disposals)
            avg_kicks = max(0, avg_kicks)
            avg_handballs = max(0, avg_handballs)
            avg_marks = max(0, avg_marks)
            avg_tackles = max(0, avg_tackles)
            avg_goals = max(0, avg_goals)
            avg_hitouts = max(0, avg_hitouts)
            avg_behinds = max(0, np.random.normal(0.5, 0.3))
            
            # Calculate average score (Supercoach scoring)
            avg_score = (
                avg_kicks * 3 +
                avg_handballs * 2 +
                avg_marks * 3 +
                avg_tackles * 4 +
                avg_goals * 6 +
                avg_behinds * 1 +
                avg_hitouts * 1
            )
            
            # Price based on average score and some noise
            base_price = avg_score * 6000 + np.random.normal(50000, 30000)
            price = int(max(100000, min(800000, base_price)))
            
            # Additional features
            injury_history = int(np.random.exponential(1))
            games_last_3 = min(3, int(np.random.uniform(0, 4)))
            form_last_5 = avg_score * np.random.uniform(0.8, 1.2)
            
            player = {
                'player_id': f'P{i:04d}',
                'name': f'{np.random.choice(["Smith", "Jones", "Brown", "Wilson", "Taylor", "Johnson", "Williams", "Davis", "Miller", "Anderson"])} {np.random.choice(["Jack", "Tom", "Sam", "Luke", "Matt", "Josh", "Ben", "Dan", "Jake", "Alex"])}',
                'team': team,
                'position': position,
                'age': age,
                'games_played': games_played,
                'avg_disposals': round(avg_disposals, 2),
                'avg_kicks': round(avg_kicks, 2),
                'avg_handballs': round(avg_handballs, 2),
                'avg_marks': round(avg_marks, 2),
                'avg_tackles': round(avg_tackles, 2),
                'avg_goals': round(avg_goals, 2),
                'avg_behinds': round(avg_behinds, 2),
                'avg_hitouts': round(avg_hitouts, 2),
                'avg_score': round(avg_score, 2),
                'price': price,
                'injury_history': injury_history,
                'games_last_3': games_last_3,
                'form_last_5': round(form_last_5, 2)
            }
            
            players.append(player)
        
        self.players_data = pd.DataFrame(players)
        return self.players_data
    
    def get_players_by_position(self, position):
        """Get all players for a specific position"""
        if self.players_data is None:
            raise ValueError("No data loaded. Call load_sample_data() first.")
        return self.players_data[self.players_data['position'] == position]
    
    def save_data(self, filepath):
        """Save player data to CSV"""
        if self.players_data is not None:
            self.players_data.to_csv(filepath, index=False)
            print(f"Data saved to {filepath}")
    
    def load_data(self, filepath):
        """Load player data from CSV"""
        self.players_data = pd.read_csv(filepath)
        return self.players_data
