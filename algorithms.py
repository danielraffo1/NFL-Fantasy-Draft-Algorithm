#!/usr/bin/env python3
"""
Fantasy Football Draft Algorithms
Contains both Greedy and Regret-based draft algorithms
"""

import numpy as np
from typing import List, Dict, Optional
from models import Player, Team, DRAFT_CONFIG

class GreedyDraftAlgorithm:
    """
    Simple greedy algorithm that picks best available player by ADP
    
    Time Complexity: O(n log n) - initial sort + O(n) per pick
    Space Complexity: O(n) - storing player list
    """
    
    def __init__(self, players: List[Player]):
        # Create a deep copy to avoid modifying original
        self.available_players = [Player(
            name=p.name,
            position=p.position,
            team=p.team,
            adp_rank=p.adp_rank,
            auction_value=p.auction_value,
            actual_points=p.actual_points
        ) for p in players]
        
        # Sort by ADP rank (lower is better)
        self.available_players.sort(key=lambda p: p.adp_rank)
        self.drafted_players = set()
    
    def draft_player(self, team: Team) -> Optional[Player]:
        """Draft best available player for team needs"""
        needs = team.get_needs()
        
        if not needs:
            return None
        
        # Find best available player for any needed position
        for player in self.available_players:
            if player.name in self.drafted_players:
                continue
            
            # Check if player fits a direct need
            if player.position in needs:
                self.drafted_players.add(player.name)
                return player
            
            # Check if player can fill FLEX position
            if 'FLEX' in needs and player.position in ['RB', 'WR', 'TE']:
                self.drafted_players.add(player.name)
                return player
        
        # Fallback: draft best available player regardless of position
        for player in self.available_players:
            if player.name not in self.drafted_players:
                self.drafted_players.add(player.name)
                return player
        
        return None

class RegretDraftAlgorithm:
    """
    Advanced algorithm that calculates regret scores based on:
    - Player value (auction value as proxy for projected points)
    - Positional scarcity (fewer good players = higher urgency)
    - Pick distance (how long until next pick)
    
    Time Complexity: O(n²) per pick due to scarcity calculations
    Space Complexity: O(n) - storing player list
    """
    
    def __init__(self, players: List[Player]):
        # Create a deep copy to avoid modifying original
        self.all_players = [Player(
            name=p.name,
            position=p.position,
            team=p.team,
            adp_rank=p.adp_rank,
            auction_value=p.auction_value,
            actual_points=p.actual_points
        ) for p in players]
        
        self.drafted_players = set()
        self._cache_max_values()
    
    def _cache_max_values(self):
        """Cache maximum values for normalization"""
        self.max_auction = max([p.auction_value for p in self.all_players], default=1)
        self.position_counts = {}
        
        for player in self.all_players:
            pos = player.position
            if pos not in self.position_counts:
                self.position_counts[pos] = []
            self.position_counts[pos].append(player.auction_value)
        
        # Sort position values for quick access
        for pos in self.position_counts:
            self.position_counts[pos].sort(reverse=True)
    
    def get_available_players(self) -> List[Player]:
        """Get list of available (undrafted) players"""
        return [p for p in self.all_players if p.name not in self.drafted_players]
    
    def calculate_positional_scarcity(self, position: str) -> float:
        """
        Calculate how scarce a position is
        Higher scarcity = fewer quality players remaining
        """
        available_at_position = [
            p for p in self.all_players 
            if p.position == position and p.name not in self.drafted_players
        ]
        
        if not available_at_position:
            return 0.0
        
        if len(available_at_position) == 1:
            return 1.0
        
        # Calculate scarcity based on quality players remaining
        auction_values = [p.auction_value for p in available_at_position]
        
        if len(auction_values) < 2:
            return 1.0
        
        # Use top 25% as "quality" threshold
        threshold = np.percentile(auction_values, 75)
        quality_players = len([v for v in auction_values if v >= threshold])
        
        # Higher scarcity when fewer quality players remain
        # Scale between 0.1 and 1.0
        scarcity = max(0.1, 1.0 / max(1, quality_players))
        return min(1.0, scarcity)
    
    def calculate_value_dropoff(self, position: str) -> float:
        """ 
        Calculate value dropoff between best and next best player at position
        Higher dropoff = more urgent to draft now
        """
        available_at_position = [
            p for p in self.all_players 
            if p.position == position and p.name not in self.drafted_players
        ]
        
        if len(available_at_position) < 2:
            return 0.0
        
        # Sort by auction value (descending)
        available_at_position.sort(key=lambda p: p.auction_value, reverse=True)
        
        best_value = available_at_position[0].auction_value
        second_best_value = available_at_position[1].auction_value
        
        if best_value <= 0:
            return 0.0
        
        # Calculate normalized dropoff
        dropoff = max(0, best_value - second_best_value)
        normalized_dropoff = dropoff / best_value
        
        return min(1.0, normalized_dropoff)
    
    def calculate_pick_urgency(self, picks_until_next: int) -> float:
        """
        Calculate urgency based on picks until next turn
        More picks = higher urgency to draft now
        """
        # Normalize picks until next turn (typical range 1-19 in snake draft)
        normalized_picks = min(19, max(1, picks_until_next))
        
        # Higher urgency for more picks until next turn
        urgency = normalized_picks / 19.0
        
        return urgency
    
    def calculate_regret_score(self, player: Player, team: Team, picks_until_next: int = 11) -> float:
        """
        Calculate regret score for a player
        
        Formula components:
        1. Value score: normalized auction value (0-1)
        2. Scarcity component: position scarcity × value dropoff
        3. Urgency component: based on picks until next turn
        4. Bye week penalty: small penalty for stacking same bye weeks
        """
        
        # 1. Base value score (normalized auction value)
        value_score = player.auction_value / self.max_auction if self.max_auction > 0 else 0
        
        # 2. Positional scarcity and dropoff
        scarcity = self.calculate_positional_scarcity(player.position)
        dropoff = self.calculate_value_dropoff(player.position)
        
        # 3. Pick urgency
        urgency = self.calculate_pick_urgency(picks_until_next)
        
        # 4. Bye week penalty (optional)
        bye_penalty = 0.0
        team_bye_weeks = []
        for pos_players in team.roster.values():
            team_bye_weeks.extend([p.bye_week for p in pos_players if hasattr(p, 'bye_week')])
        
        if hasattr(player, 'bye_week') and player.bye_week in team_bye_weeks:
            bye_penalty = 0.05  # Small penalty for same bye week
        
        # Combine components with weights
        scarcity_component = scarcity * dropoff * 0.4  # Weight: 40%
        urgency_component = urgency * 0.3              # Weight: 30%
        value_component = value_score * 0.3            # Weight: 30%
        
        # Final regret score
        regret_score = value_component + scarcity_component + urgency_component - bye_penalty
        
        return max(0.0, regret_score)  # Ensure non-negative
    
    def draft_player(self, team: Team, picks_until_next: int = 11) -> Optional[Player]:
        """
        Draft player with highest regret score that fills team need
        """
        needs = team.get_needs()
        if not needs:
            return None
        
        available_players = self.get_available_players()
        if not available_players:
            return None
        
        # Calculate regret scores for all available players that fill needs
        candidates = []
        
        for player in available_players:
            # Check if player fills a need
            fills_need = False
            
            if player.position in needs:
                fills_need = True
            elif 'FLEX' in needs and player.position in ['RB', 'WR', 'TE']:
                fills_need = True
            
            if fills_need:
                regret_score = self.calculate_regret_score(player, team, picks_until_next)
                candidates.append((regret_score, player))
        
        if not candidates:
            # Fallback: draft any available player
            for player in available_players:
                regret_score = self.calculate_regret_score(player, team, picks_until_next)
                candidates.append((regret_score, player))
        
        if not candidates:
            return None
        
        # Sort by regret score (descending) and pick best
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        best_player = candidates[0][1]
        self.drafted_players.add(best_player.name)
        
        return best_player
    
    def update_available_players(self):
        """Update any internal state after a pick (placeholder for future optimizations)"""
        pass