#!/usr/bin/env python3
"""
Data loading utilities for Fantasy Football Draft Algorithm
Handles loading ESPN rankings and actual performance data
"""

import pandas as pd
import os
from typing import Dict, Any

class DataLoader:
    """Handles loading and preprocessing of fantasy football data"""
    
    def __init__(self):
        self.years = [2020, 2021, 2022, 2023, 2024]
    
    def load_espn_rankings(self) -> Dict[int, pd.DataFrame]:
        """Load ESPN draft rankings for all years"""
        espn_data = {}
        
        for year in self.years:
            try:
                filename = f'data/fantasy_rankings_{year}.xlsx'
                if not os.path.exists(filename):
                    print(f"❌ File not found: {filename}")
                    continue
                
                df = pd.read_excel(filename)
                
                # Standardize column names if needed
                column_mapping = {
                    'player_name': 'Player',
                    'overall_rank': 'ADP_Rank',
                    'position_rank': 'Position_Rank'
                }
                
                for old_col, new_col in column_mapping.items():
                    if old_col in df.columns and new_col not in df.columns:
                        df = df.rename(columns={old_col: new_col})
                
                # Ensure required columns exist
                required_cols = ['Player', 'position', 'team', 'ADP_Rank', 'auction_value']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    print(f"  Missing columns in {filename}: {missing_cols}")
                    # Try alternative column names
                    if 'adp_rank' in df.columns and 'ADP_Rank' not in df.columns:
                        df['ADP_Rank'] = df['adp_rank']
                    if 'overall_rank' in df.columns and 'ADP_Rank' not in df.columns:
                        df['ADP_Rank'] = df['overall_rank']
                
                espn_data[year] = df
                print(f"✅ Loaded {year} ESPN rankings: {len(df)} players")
                
            except Exception as e:
                print(f"❌ Error loading {filename}: {str(e)}")
        
        return espn_data
    
    def load_actual_points(self) -> Dict[int, Dict[str, float]]:
        """Load actual fantasy points for all years"""
        actual_data = {}
        
        for year in self.years:
            try:
                filename = f'data/{year}.xlsx'
                if not os.path.exists(filename):
                    print(f"❌ File not found: {filename}")
                    continue
                
                # Skip first row which often contains merged headers
                df = pd.read_excel(filename, skiprows=1)
                
                # Clean player names (remove asterisks, plus signs)
                if 'Player' in df.columns:
                    df['Player_Clean'] = (df['Player']
                                        .str.replace('*', '', regex=False)
                                        .str.replace('+', '', regex=False)
                                        .str.strip())
                else:
                    print(f"❌ No 'Player' column found in {filename}")
                    continue
                
                # Find fantasy points column
                points_col = None
                possible_cols = ['PPR', 'FantPt', 'Fantasy Points', 'FPTS', 'Points']
                
                for col in possible_cols:
                    if col in df.columns:
                        points_col = col
                        break
                
                if not points_col:
                    print(f"❌ No fantasy points column found in {filename}")
                    print(f"   Available columns: {df.columns.tolist()}")
                    continue
                
                # Create player-to-points mapping
                player_points = {}
                for _, row in df.iterrows():
                    player_name = row.get('Player_Clean')
                    points = row.get(points_col)
                    
                    if pd.notna(player_name) and pd.notna(points):
                        try:
                            player_points[player_name] = float(points)
                        except (ValueError, TypeError):
                            continue
                
                actual_data[year] = player_points
                print(f"✅ Loaded {year} actual points: {len(player_points)} players")
                
            except Exception as e:
                print(f"❌ Error loading {filename}: {str(e)}")
        
        return actual_data
    
    def match_player_points(self, player_name: str, actual_data: Dict[str, float]) -> float:
        """Match player name to actual points with fuzzy matching"""
        # Direct match
        if player_name in actual_data:
            return actual_data[player_name]
        
        # Fuzzy matching for name variations
        player_lower = player_name.lower()
        
        for actual_name, points in actual_data.items():
            actual_lower = actual_name.lower()
            
            # Check if names contain each other
            if (player_lower in actual_lower or 
                actual_lower in player_lower or
                self._names_similar(player_lower, actual_lower)):
                return points
        
        return 0.0
    
    def _names_similar(self, name1: str, name2: str) -> bool:
        """Check if two names are similar (basic similarity check)"""
        # Split names and check for common parts
        parts1 = set(name1.split())
        parts2 = set(name2.split())
        
        # If they share at least 2 name parts, consider them similar
        common_parts = parts1.intersection(parts2)
        return len(common_parts) >= 2 or (len(common_parts) >= 1 and 
                                         (len(parts1) <= 2 or len(parts2) <= 2))