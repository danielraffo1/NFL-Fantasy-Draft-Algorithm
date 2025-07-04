#!/usr/bin/env python3
"""
Data models and configuration for Fantasy Football Draft Algorithm
"""

from typing import List, Dict

# Draft Configuration
DRAFT_CONFIG = {
    'num_teams': 10,
    'draft_position': 5,  # We draft from 5th position
    'roster_spots': {
        'QB': 1,
        'RB': 2, 
        'WR': 2,
        'TE': 1,
        'FLEX': 1,  # RB/WR/TE
        'K': 1
    },
    'total_picks': 8  # Total picks per team
}

class Player:
    """Represents a fantasy football player"""
    
    def __init__(self, name: str, position: str, team: str, adp_rank: int, 
                 auction_value: int = 0, actual_points: float = 0, bye_week: int = 0):
        self.name = name
        self.position = position
        self.team = team
        self.adp_rank = adp_rank
        self.auction_value = auction_value
        self.actual_points = actual_points
        self.bye_week = bye_week
    
    def __repr__(self):
        return f"{self.name} ({self.position}, {self.team}) - ADP: {self.adp_rank}, Points: {self.actual_points:.1f}"
    
    def __eq__(self, other):
        if not isinstance(other, Player):
            return False
        return self.name == other.name and self.position == other.position
    
    def __hash__(self):
        return hash((self.name, self.position))

class Team:
    """Represents a fantasy team's roster"""
    
    def __init__(self, team_id: int):
        self.team_id = team_id
        self.roster = {
            'QB': [],
            'RB': [],
            'WR': [],
            'TE': [],
            'FLEX': [],
            'K': []
        }
        self.total_points = 0.0
        self.draft_picks = []  # Track draft order
    
    def add_player(self, player: Player, position: str = None):
        """Add player to roster at specified position"""
        if position is None:
            position = player.position
        
        # Handle FLEX position
        if position == 'FLEX' and player.position in ['RB', 'WR', 'TE']:
            self.roster['FLEX'].append(player)
        elif position in self.roster:
            self.roster[position].append(player)
        else:
            # Fallback to player's natural position
            if player.position in self.roster:
                self.roster[player.position].append(player)
            else:
                # Last resort: add to FLEX if it's a skill position
                if player.position in ['RB', 'WR', 'TE']:
                    self.roster['FLEX'].append(player)
        
        self.total_points += player.actual_points
        self.draft_picks.append(player)
    
    def get_needs(self) -> List[str]:
        """Return positions that still need to be filled"""
        needs = []
        for pos, max_count in DRAFT_CONFIG['roster_spots'].items():
            if len(self.roster[pos]) < max_count:
                needs.append(pos)
        return needs
    
    def is_complete(self) -> bool:
        """Check if roster is complete"""
        return len(self.get_needs()) == 0
    
    def get_position_points(self, position: str) -> float:
        """Get total points for a specific position"""
        return sum(p.actual_points for p in self.roster.get(position, []))
    
    def get_roster_summary(self) -> Dict[str, Dict]:
        """Get summary of roster by position"""
        summary = {}
        for position, players in self.roster.items():
            if players:
                summary[position] = {
                    'players': [p.name for p in players],
                    'total_points': sum(p.actual_points for p in players),
                    'count': len(players)
                }
        return summary
    
    def __repr__(self):
        return f"Team {self.team_id}: {self.total_points:.1f} points ({len(self.draft_picks)} picks)"