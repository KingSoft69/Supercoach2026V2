"""
Data collection module for AFL player statistics with real FootyWire data
"""
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time
import re


class AFLDataCollector:
    """Collects and manages AFL player data from FootyWire"""
    
    def __init__(self):
        self.players_data = None
        self.real_data_url = "https://www.footywire.com/afl/footy/supercoach_prices"
        self.base_url = "https://www.footywire.com"
    
    def calculate_potential(self, age):
        """
        Calculate player potential based on age
        Peak age for AFL is typically 24-28
        Young players (18-23) have high potential for growth
        Players 29+ are declining
        """
        if age < 18:
            return 0.5
        elif age <= 21:
            # Young players with high potential
            return 1.0 + (21 - age) * 0.1  # Up to 1.3 for 18 year olds
        elif age <= 24:
            # Developing players
            return 1.0 + (24 - age) * 0.05  # Up to 1.15 for 21 year olds
        elif age <= 28:
            # Peak performance age
            return 1.0
        elif age <= 32:
            # Slight decline
            return 1.0 - (age - 28) * 0.05  # Down to 0.8 for 32 year olds
        else:
            # Veterans
            return max(0.5, 1.0 - (age - 28) * 0.08)  # Declining rapidly
    
    def get_player_details(self, player_url):
        """
        Fetch detailed player information from individual player page
        Including: age, draft pick, injury history, career stats
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(player_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            details = {}
            
            # Try to extract age, draft info from player info table
            info_table = soup.find('table', {'class': 'playerno'})
            if info_table:
                rows = info_table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        label = cells[0].text.strip().lower()
                        value = cells[1].text.strip()
                        
                        if 'age' in label or 'born' in label:
                            # Extract age number
                            age_match = re.search(r'(\d+)', value)
                            if age_match:
                                details['age'] = int(age_match.group(1))
                        elif 'draft' in label:
                            # Extract draft pick number
                            draft_match = re.search(r'#(\d+)', value)
                            if draft_match:
                                details['draft_pick'] = int(draft_match.group(1))
                            elif 'rookie' in value.lower():
                                details['draft_pick'] = 999  # Rookie draft
                            elif 'undrafted' in value.lower():
                                details['draft_pick'] = 1000  # Undrafted
                        elif 'height' in label:
                            details['height'] = value
                        elif 'weight' in label:
                            details['weight'] = value
            
            # Try to extract career stats and injury info
            stats_table = soup.find('table', {'class': 'data'})
            if stats_table:
                # Get career totals or averages
                rows = stats_table.find_all('tr')
                for row in rows:
                    if 'Career' in row.text or 'Total' in row.text:
                        cells = row.find_all('td')
                        if len(cells) > 5:
                            try:
                                details['games_played'] = int(cells[1].text.strip())
                            except:
                                pass
                    
                    # Check for injury indicators in recent seasons (last 2 years)
                    # Look for low game counts or injury notes
                    if '2025' in row.text or '2024' in row.text:
                        cells = row.find_all('td')
                        if len(cells) > 1:
                            try:
                                games_in_season = int(cells[1].text.strip())
                                # If played very few games, likely injured
                                if games_in_season < 5:
                                    details['injured_last_year'] = True
                            except:
                                pass
            
            # Look for injury notes in the page text
            page_text = soup.get_text().lower()
            injury_keywords = ['injury', 'injured', 'suspension', 'suspended', 'out for season']
            for keyword in injury_keywords:
                if keyword in page_text:
                    details['injured_last_year'] = True
                    break
            
            return details
            
        except Exception as e:
            return {}
    
    def load_real_data(self, fetch_player_details=False):
        """
        Load real AFL Supercoach player data from FootyWire
        
        Parameters:
        - fetch_player_details: If True, fetches detailed info for each player (slow)
        """
        try:
            print("Fetching real player data from FootyWire...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(self.real_data_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the table with player data
            table = soup.find('table', {'class': 'data'})
            
            if not table:
                print("Could not find player data table. Using sample data instead.")
                return self.load_sample_data()
            
            # Extract table data
            players = []
            rows = table.find_all('tr')[1:]  # Skip header
            
            print(f"Processing {len(rows)} players...")
            
            for idx, row in enumerate(rows):
                cols = row.find_all('td')
                if len(cols) >= 7:
                    try:
                        # Extract player information
                        player_link = cols[0].find('a')
                        name = player_link.text.strip() if player_link else cols[0].text.strip()
                        player_url = None
                        if player_link and player_link.get('href'):
                            player_url = self.base_url + player_link.get('href')
                        
                        team = cols[1].text.strip()
                        position = cols[2].text.strip()
                        
                        # Parse price (remove $ and commas)
                        price_text = cols[3].text.strip().replace('$', '').replace(',', '')
                        price = int(price_text) if price_text.isdigit() else 0
                        
                        # Get average score if available
                        avg_score_text = cols[4].text.strip()
                        avg_score = float(avg_score_text) if avg_score_text and avg_score_text != '-' else 0.0
                        
                        # Get games played if available
                        games_text = cols[5].text.strip() if len(cols) > 5 else '0'
                        games_played = int(games_text) if games_text.isdigit() else 0
                        
                        # Fetch detailed player info from FootyWire links (for ALL players, no limit)
                        age = None
                        draft_pick = None
                        injured_last_year = False
                        
                        if fetch_player_details and player_url:
                            print(f"  Fetching details for {name} ({idx+1}/{len(rows)})...")
                            details = self.get_player_details(player_url)
                            age = details.get('age')
                            draft_pick = details.get('draft_pick')
                            injured_last_year = details.get('injured_last_year', False)
                            if 'games_played' in details:
                                games_played = details['games_played']
                            time.sleep(0.5)  # Be respectful to the server
                        
                        # Estimate age if not fetched
                        if age is None:
                            if games_played > 0:
                                # Estimate based on games: avg 2 years per 44 games
                                age = int(18 + (games_played / 22))
                                age = max(18, min(35, age))
                            else:
                                age = int(np.random.normal(25, 4))
                                age = max(18, min(35, age))
                        
                        # Estimate draft pick if not fetched
                        if draft_pick is None:
                            # Estimate based on performance and age
                            # Better players likely had earlier picks
                            if avg_score > 100:
                                draft_pick = int(np.random.uniform(1, 20))
                            elif avg_score > 80:
                                draft_pick = int(np.random.uniform(10, 40))
                            elif avg_score > 60:
                                draft_pick = int(np.random.uniform(20, 60))
                            else:
                                draft_pick = int(np.random.uniform(30, 100))
                        
                        # Calculate draft pick value (early picks more valuable)
                        draft_value = max(0, 100 - draft_pick) / 100  # 0-1 scale
                        
                        # Create player entry
                        if price > 0:  # Only include players with valid prices
                            player = {
                                'player_id': f'FW{len(players):04d}',
                                'name': name,
                                'team': team,
                                'position': self._normalize_position(position),
                                'age': age,
                                'games_played': games_played,
                                'avg_score': avg_score if avg_score > 0 else self._estimate_score(price),
                                'price': price,
                                'potential': self.calculate_potential(age),
                                'draft_pick': draft_pick,
                                'draft_value': draft_value,
                                'injured_last_year': 1 if injured_last_year else 0,
                                'injury_history': int(np.random.exponential(1)) + (2 if injured_last_year else 0),
                                'games_last_3': 0 if injured_last_year else min(3, int(np.random.uniform(0, 4))),
                                'form_last_5': avg_score * np.random.uniform(0.9, 1.1) if avg_score > 0 else self._estimate_score(price) * np.random.uniform(0.9, 1.1)
                            }
                            
                            # Add estimated stats based on position and score
                            player.update(self._estimate_stats(player))
                            
                            players.append(player)
                    except (ValueError, AttributeError, IndexError) as e:
                        continue  # Skip rows with parsing errors
            
            if players:
                self.players_data = pd.DataFrame(players)
                print(f"✓ Loaded {len(players)} real players from FootyWire")
                print(f"  Age range: {self.players_data['age'].min()}-{self.players_data['age'].max()}")
                print(f"  Potential range: {self.players_data['potential'].min():.2f}-{self.players_data['potential'].max():.2f}")
                return self.players_data
            else:
                print("No valid player data found. Using sample data instead.")
                return self.load_sample_data()
                
        except Exception as e:
            print(f"Error fetching real data: {e}")
            print("Falling back to sample data...")
            return self.load_sample_data()
    
    def _estimate_score(self, price):
        """Estimate average score from price"""
        # Rough approximation: $500k ~ 80 points
        return (price / 6000) + np.random.normal(0, 5)
    
    def _normalize_position(self, position):
        """Normalize position names to standard format"""
        position = position.upper().strip()
        
        # Map common position variations
        if 'DEF' in position or 'BACK' in position or position == 'D':
            return 'DEF'
        elif 'MID' in position or 'MIDFIELDER' in position or position == 'M':
            return 'MID'
        elif 'RUC' in position or 'RUCK' in position or position == 'R':
            return 'RUC'
        elif 'FWD' in position or 'FORWARD' in position or position == 'F':
            return 'FWD'
        else:
            # Default to MID for utility players
            return 'MID'
    
    def _estimate_stats(self, player):
        """Estimate detailed stats based on position and average score"""
        position = player['position']
        avg_score = player['avg_score']
        
        # Reverse engineer stats from supercoach scoring
        # Score = kicks*3 + handballs*2 + marks*3 + tackles*4 + goals*6 + behinds*1 + hitouts*1
        
        if position == 'MID':
            disposals = avg_score / 2.5
            kicks = disposals * 0.55
            handballs = disposals * 0.45
            marks = avg_score / 20
            tackles = avg_score / 25
            goals = avg_score / 120
            behinds = avg_score / 80
            hitouts = 0.5
        elif position == 'DEF':
            disposals = avg_score / 2.8
            kicks = disposals * 0.65
            handballs = disposals * 0.35
            marks = avg_score / 18
            tackles = avg_score / 30
            goals = avg_score / 200
            behinds = avg_score / 150
            hitouts = 0.2
        elif position == 'FWD':
            disposals = avg_score / 3.5
            kicks = disposals * 0.55
            handballs = disposals * 0.45
            marks = avg_score / 22
            tackles = avg_score / 35
            goals = avg_score / 40
            behinds = avg_score / 70
            hitouts = 0.3
        else:  # RUC
            disposals = avg_score / 4
            kicks = disposals * 0.5
            handballs = disposals * 0.5
            marks = avg_score / 25
            tackles = avg_score / 35
            goals = avg_score / 150
            behinds = avg_score / 120
            hitouts = avg_score / 4
        
        return {
            'avg_disposals': round(kicks + handballs, 2),
            'avg_kicks': round(kicks, 2),
            'avg_handballs': round(handballs, 2),
            'avg_marks': round(marks, 2),
            'avg_tackles': round(tackles, 2),
            'avg_goals': round(goals, 2),
            'avg_behinds': round(behinds, 2),
            'avg_hitouts': round(hitouts, 2)
        }
    
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
            injured_last_year = 1 if np.random.random() < 0.15 else 0  # 15% injury rate
            injury_history = int(np.random.exponential(1)) + (2 if injured_last_year else 0)
            games_last_3 = 0 if injured_last_year else min(3, int(np.random.uniform(0, 4)))
            form_last_5 = avg_score * np.random.uniform(0.8, 1.2)
            
            # Draft pick estimation (better players likely earlier picks)
            if avg_score > 100:
                draft_pick = int(np.random.uniform(1, 20))
            elif avg_score > 80:
                draft_pick = int(np.random.uniform(10, 40))
            elif avg_score > 60:
                draft_pick = int(np.random.uniform(20, 60))
            else:
                draft_pick = int(np.random.uniform(30, 100))
            
            draft_value = max(0, 100 - draft_pick) / 100
            potential = self.calculate_potential(age)
            
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
                'potential': potential,
                'draft_pick': draft_pick,
                'draft_value': draft_value,
                'injured_last_year': injured_last_year,
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
