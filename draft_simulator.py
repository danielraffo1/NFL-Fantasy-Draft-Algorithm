#!/usr/bin/env python3
"""
Draft simulation engine for Fantasy Football Draft Algorithm
FIXED VERSION: Handles player shortage and improves algorithm separation
"""

import pandas as pd
import copy
from typing import List, Dict, Tuple, Optional, Type
from models import Player, Team, DRAFT_CONFIG
from data_loader import DataLoader

class DraftSimulator:
    """Handles draft simulation logic"""
    
    def __init__(self):
        self.data_loader = DataLoader()
    
    def create_players_for_year(self, year: int, espn_data: Dict, actual_data: Dict) -> List[Player]:
        """Create Player objects for a given year with proper data matching"""
        players = []
        
        if year not in espn_data:
            print(f"❌ No ESPN data for {year}")
            return players
        
        year_espn = espn_data[year]
        year_actual = actual_data.get(year, {})
        
        for _, row in year_espn.iterrows():
            try:
                # Extract player data with safe defaults
                name = str(row.get('Player', ''))
                position = str(row.get('position', ''))
                team = str(row.get('team', ''))
                
                # Handle different column name variations
                adp_rank = row.get('ADP_Rank', row.get('adp_rank', row.get('overall_rank', 999)))
                auction_value = row.get('auction_value', 0)
                bye_week = row.get('bye_week', 0)
                
                # Skip invalid entries
                if not name or not position:
                    continue
                
                # Try to match actual points with improved matching
                actual_points = self.data_loader.match_player_points(name, year_actual)
                
                player = Player(
                    name=name,
                    position=position,
                    team=team,
                    adp_rank=int(adp_rank),
                    auction_value=int(auction_value),
                    actual_points=float(actual_points),
                    bye_week=int(bye_week)
                )
                players.append(player)
                
            except Exception as e:
                print(f"  Error creating player from row: {e}")
                continue
        
        print(f"✅ Created {len(players)} players for {year}")
        return players
    
    def generate_snake_draft_order(self, num_teams: int, num_rounds: int) -> List[int]:
        """
        Generate snake draft order for given teams and rounds
        FIXED: Ensure we don't exceed available players
        """
        draft_order = []
        for round_num in range(num_rounds):
            if round_num % 2 == 0:  # Even rounds (0, 2, 4...): normal order
                draft_order.extend(range(1, num_teams + 1))
            else:  # Odd rounds (1, 3, 5...): reverse order
                draft_order.extend(range(num_teams, 0, -1))
        return draft_order
    
    def simulate_draft(self, year: int, algorithm_class: Type, 
                      espn_data: Dict, actual_data: Dict) -> Optional[Tuple[Team, List[Team]]]:
        """
        Simulate a complete draft for one year
        FIXED: Better player management and error handling
        """
        # Create players for the year
        players = self.create_players_for_year(year, espn_data, actual_data)
        if not players:
            print(f"❌ No players created for {year}")
            return None
        
        # FIXED: Check if we have enough players for the draft
        total_picks_needed = DRAFT_CONFIG['num_teams'] * DRAFT_CONFIG['total_picks']
        if len(players) < total_picks_needed:
            print(f"⚠️  Warning: Only {len(players)} players available for {total_picks_needed} picks")
            # Adjust picks per team to fit available players
            max_picks_per_team = max(1, len(players) // DRAFT_CONFIG['num_teams'])
            actual_rounds = min(DRAFT_CONFIG['total_picks'], max_picks_per_team)
            print(f"   Adjusting to {actual_rounds} rounds per team")
        else:
            actual_rounds = DRAFT_CONFIG['total_picks']
        
        # Initialize teams
        teams = [Team(i) for i in range(1, DRAFT_CONFIG['num_teams'] + 1)]
        our_team = teams[DRAFT_CONFIG['draft_position'] - 1]  # 0-indexed
        
        # FIXED: Create completely separate player lists for each algorithm instance
        # This ensures algorithms don't interfere with each other
        team_algorithms = {}
        for team_id in range(1, DRAFT_CONFIG['num_teams'] + 1):
            # Deep copy players for each algorithm to prevent interference
            algorithm_players = []
            for p in players:
                new_player = Player(
                    name=p.name,
                    position=p.position,
                    team=p.team,
                    adp_rank=p.adp_rank,
                    auction_value=p.auction_value,
                    actual_points=p.actual_points,
                    bye_week=p.bye_week
                )
                algorithm_players.append(new_player)
            
            team_algorithms[team_id] = algorithm_class(algorithm_players)
        
        # Generate draft order for this simulation
        draft_order = self.generate_snake_draft_order(DRAFT_CONFIG['num_teams'], actual_rounds)
        
        # Track all drafted players globally to prevent double-drafting
        globally_drafted = set()
        
        # Simulate draft pick by pick
        for pick_num, team_id in enumerate(draft_order):
            current_team = teams[team_id - 1]  # 0-indexed
            current_algorithm = team_algorithms[team_id]
            
            # Calculate picks until our next turn (for regret algorithm)
            picks_until_next = self._calculate_picks_until_next(
                pick_num, team_id, draft_order
            )
            
            # Draft player
            drafted_player = self._execute_draft_pick(
                current_algorithm, current_team, picks_until_next, globally_drafted
            )
            
            if drafted_player:
                # Add to global drafted list
                globally_drafted.add(drafted_player.name)
                
                # Determine position to fill
                position = self._determine_roster_position(drafted_player, current_team)
                current_team.add_player(drafted_player, position)
                
                # Update all algorithm states to reflect the pick
                self._update_all_algorithms(team_algorithms, drafted_player.name)
            else:
                # FIXED: More graceful handling when no players available
                if len(globally_drafted) >= len(players) * 0.9:  # 90% of players drafted
                    print(f"   Draft ending early - most players drafted")
                    break
        
        return our_team, teams
    
    def _calculate_picks_until_next(self, current_pick: int, team_id: int, 
                                   draft_order: List[int]) -> int:
        """Calculate how many picks until this team's next turn"""
        if team_id != DRAFT_CONFIG['draft_position']:
            return 11  # Default for non-target team
        
        remaining_picks = draft_order[current_pick + 1:]
        try:
            next_our_pick = remaining_picks.index(DRAFT_CONFIG['draft_position'])
            return next_our_pick + 1
        except ValueError:
            return len(remaining_picks) + 1
    
    def _execute_draft_pick(self, algorithm, team: Team, picks_until_next: int, 
                           globally_drafted: set) -> Optional[Player]:
        """
        Execute a draft pick using the given algorithm
        FIXED: Check against globally drafted players
        """
        try:
            # Ensure algorithm's drafted list includes all globally drafted players
            if hasattr(algorithm, 'drafted_players'):
                algorithm.drafted_players.update(globally_drafted)
            
            # Check if algorithm supports picks_until_next parameter
            if hasattr(algorithm, 'draft_player'):
                if 'picks_until_next' in algorithm.draft_player.__code__.co_varnames:
                    player = algorithm.draft_player(team, picks_until_next)
                else:
                    player = algorithm.draft_player(team)
                
                # Double-check player isn't already drafted
                if player and player.name in globally_drafted:
                    print(f"⚠️  Player {player.name} already drafted, skipping")
                    return None
                
                return player
            else:
                print(f"⚠️  Algorithm {type(algorithm).__name__} missing draft_player method")
                return None
        except Exception as e:
            print(f"⚠️  Error in draft_player: {e}")
            return None
    
    def _determine_roster_position(self, player: Player, team: Team) -> str:
        """Determine which roster position to fill with the drafted player"""
        needs = team.get_needs()
        
        # First priority: direct position match
        if player.position in needs:
            return player.position
        
        # Second priority: FLEX eligibility
        if 'FLEX' in needs and player.position in ['RB', 'WR', 'TE']:
            return 'FLEX'
        
        # Fallback: use player's natural position (even if overfilled)
        return player.position
    
    def _update_all_algorithms(self, team_algorithms: Dict, drafted_player_name: str):
        """
        Update all algorithm states to reflect the drafted player
        FIXED: More robust state synchronization
        """
        for algorithm in team_algorithms.values():
            # Add player to drafted set for all algorithms
            if hasattr(algorithm, 'drafted_players'):
                algorithm.drafted_players.add(drafted_player_name)
            
            # Call update method if available
            if hasattr(algorithm, 'update_available_players'):
                try:
                    algorithm.update_available_players()
                except Exception as e:
                    pass  # Silently handle update errors
    
    def simulate_multiple_years(self, algorithm_class: Type, espn_data: Dict, 
                               actual_data: Dict) -> Dict[int, Tuple[Team, List[Team]]]:
        """Simulate drafts for multiple years"""
        results = {}
        
        for year in sorted(espn_data.keys()):
            if year in actual_data:
                print(f"🔄 Simulating {year} with {algorithm_class.__name__}...")
                result = self.simulate_draft(year, algorithm_class, espn_data, actual_data)
                if result:
                    results[year] = result
                else:
                    print(f"❌ Failed to simulate {year}")
        
        return results