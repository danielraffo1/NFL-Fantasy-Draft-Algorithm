#!/usr/bin/env python3
"""
Performance analysis utilities for Fantasy Football Draft Algorithm
FIXED VERSION: Better error handling and timing precision
"""

import time
import sys
from typing import Dict, Any, Optional
from algorithms import GreedyDraftAlgorithm, RegretDraftAlgorithm
from draft_simulator import DraftSimulator
from models import Team

class PerformanceAnalyzer:
    """Handles performance analysis and benchmarking"""
    
    def __init__(self):
        self.simulator = DraftSimulator()
    
    def analyze_algorithms(self, espn_data: Dict, actual_data: Dict, 
                          test_year: int = 2022) -> Optional[Dict[str, Any]]:
        """
        Analyze runtime and memory performance of both algorithms
        FIXED: Better timing precision and error handling
        """
        if test_year not in espn_data or test_year not in actual_data:
            print(f"❌ No data available for performance testing in {test_year}")
            return None
        
        # Create test dataset
        players = self.simulator.create_players_for_year(test_year, espn_data, actual_data)
        if not players:
            print("❌ No players available for performance testing")
            return None
        
        print(f"📊 Performance testing with {len(players)} players")
        
        # Test Greedy Algorithm
        greedy_time, greedy_memory = self._benchmark_algorithm(
            GreedyDraftAlgorithm, players, "Greedy"
        )
        
        # Test Regret Algorithm
        regret_time, regret_memory = self._benchmark_algorithm(
            RegretDraftAlgorithm, players, "Regret"
        )
        
        # Calculate memory estimates
        player_memory = self._estimate_player_memory(players)
        team_memory = self._estimate_team_memory()
        total_memory = player_memory + (team_memory * 10)  # 10 teams
        
        # FIXED: Ensure greedy_time is never exactly zero for division
        if greedy_time <= 0:
            greedy_time = 0.0001  # Set minimum time to avoid division by zero
        
        results = {
            'greedy_time': greedy_time,
            'regret_time': regret_time,
            'greedy_memory': greedy_memory,
            'regret_memory': regret_memory,
            'player_memory': player_memory,
            'team_memory': team_memory,
            'memory_estimate': total_memory / 1024,  # Convert to KB
            'dataset_size': len(players),
            'performance_ratio': regret_time / greedy_time
        }
        
        return results
    
    def _benchmark_algorithm(self, algorithm_class, players: list, algorithm_name: str) -> tuple:
        """
        Benchmark a single algorithm's performance
        FIXED: Better timing measurement and multiple runs for accuracy
        Returns: (runtime_seconds, memory_bytes)
        """
        print(f"   Testing {algorithm_name} Algorithm...")
        
        # Run multiple times for better timing accuracy
        times = []
        
        for run in range(5):  # 5 runs for average
            # Create fresh copies for each run
            test_players = []
            for p in players:
                from models import Player
                new_player = Player(
                    name=p.name,
                    position=p.position,
                    team=p.team,
                    adp_rank=p.adp_rank,
                    auction_value=p.auction_value,
                    actual_points=p.actual_points,
                    bye_week=p.bye_week if hasattr(p, 'bye_week') else 0
                )
                test_players.append(new_player)
            
            # Measure runtime with higher precision
            start_time = time.perf_counter()  # Higher precision timer
            
            try:
                # Create algorithm instance
                algorithm = algorithm_class(test_players)
                test_team = Team(1)
                
                # Simulate 8 draft picks
                for pick_round in range(min(8, len(test_players))):
                    # Calculate mock picks until next turn
                    picks_until_next = max(1, 11 - pick_round)
                    
                    # Draft player
                    if hasattr(algorithm, 'draft_player'):
                        if algorithm_name == "Regret":
                            drafted_player = algorithm.draft_player(test_team, picks_until_next)
                        else:
                            drafted_player = algorithm.draft_player(test_team)
                        
                        if drafted_player:
                            # Add to team
                            needs = test_team.get_needs()
                            position = (drafted_player.position if drafted_player.position in needs 
                                      else needs[0] if needs else 'FLEX')
                            test_team.add_player(drafted_player, position)
                            
                            # Update algorithm state
                            if hasattr(algorithm, 'update_available_players'):
                                algorithm.update_available_players()
                        else:
                            break  # No more players available
                
                runtime = time.perf_counter() - start_time
                times.append(runtime)
                
            except Exception as e:
                print(f"      ⚠️  Error in run {run+1}: {e}")
                times.append(0.001)  # Default time for failed runs
        
        # Use average time from all runs
        avg_runtime = sum(times) / len(times) if times else 0.001
        
        # Estimate memory usage (do this once, not in loop)
        try:
            algorithm = algorithm_class(test_players)
            memory_usage = self._estimate_algorithm_memory(algorithm)
        except:
            memory_usage = 1024  # Default 1KB if estimation fails
        
        print(f"      Runtime: {avg_runtime*1000:.2f} ms (avg of {len(times)} runs)")
        print(f"      Memory: ~{memory_usage/1024:.1f} KB")
        
        return avg_runtime, memory_usage
    
    def _estimate_algorithm_memory(self, algorithm) -> int:
        """
        Estimate memory usage of algorithm instance
        FIXED: More robust error handling
        """
        try:
            # Basic size of algorithm object
            base_size = sys.getsizeof(algorithm)
            
            # Size of player list
            players_size = 0
            if hasattr(algorithm, 'all_players') and algorithm.all_players:
                players_size = sys.getsizeof(algorithm.all_players)
                # Sample a few players to estimate total size
                sample_size = min(5, len(algorithm.all_players))
                for player in algorithm.all_players[:sample_size]:
                    players_size += sys.getsizeof(player)
                # Scale up based on sample
                if sample_size > 0:
                    players_size = players_size * len(algorithm.all_players) // sample_size
                    
            elif hasattr(algorithm, 'available_players') and algorithm.available_players:
                players_size = sys.getsizeof(algorithm.available_players)
                sample_size = min(5, len(algorithm.available_players))
                for player in algorithm.available_players[:sample_size]:
                    players_size += sys.getsizeof(player)
                if sample_size > 0:
                    players_size = players_size * len(algorithm.available_players) // sample_size
            
            # Size of drafted players set
            drafted_size = 0
            if hasattr(algorithm, 'drafted_players'):
                drafted_size = sys.getsizeof(algorithm.drafted_players)
            
            total_size = base_size + players_size + drafted_size
            return max(1024, total_size)  # Minimum 1KB
            
        except Exception as e:
            print(f"      ⚠️  Memory estimation error: {e}")
            return 2048  # Default estimate: 2KB
    
    def _estimate_player_memory(self, players: list) -> int:
        """Estimate memory usage of player objects"""
        if not players:
            return 0
        
        try:
            # Sample first player to estimate size
            sample_size = sys.getsizeof(players[0])
            
            # Add size of string attributes (approximate)
            sample_size += len(getattr(players[0], 'name', '')) * 2  # Unicode
            sample_size += len(getattr(players[0], 'position', '')) * 2
            sample_size += len(getattr(players[0], 'team', '')) * 2
            
            return sample_size * len(players)
        except:
            return len(players) * 200  # Default 200 bytes per player
    
    def _estimate_team_memory(self) -> int:
        """Estimate memory usage of a team object"""
        try:
            test_team = Team(1)
            base_size = sys.getsizeof(test_team)
            
            # Add size of roster dictionary
            roster_size = sys.getsizeof(test_team.roster)
            for pos_list in test_team.roster.values():
                roster_size += sys.getsizeof(pos_list)
            
            return base_size + roster_size
        except:
            return 512  # Default 512 bytes per team
    
    def analyze_complexity(self) -> Dict[str, str]:
        """Return theoretical complexity analysis"""
        return {
            'greedy_time': "O(n log n) - initial sort + O(n) per pick",
            'greedy_space': "O(n) - storing player list",
            'regret_time': "O(n²) per pick - scarcity calculations",
            'regret_space': "O(n) - storing player list + caching",
            'notes': "n = number of players, p = number of picks per team"
        }
    
    def generate_performance_report(self, results: Dict[str, Any]) -> str:
        """Generate a formatted performance report"""
        if not results:
            return "No performance data available"
        
        report = []
        report.append(" PERFORMANCE ANALYSIS")
        report.append("=" * 40)
        report.append(f"Test Dataset: {results['dataset_size']} players")
        report.append("")
        
        report.append("⏱️  RUNTIME PERFORMANCE:")
        report.append(f"   Greedy Algorithm:  {results['greedy_time']*1000:.2f} ms")
        report.append(f"   Regret Algorithm:  {results['regret_time']*1000:.2f} ms")
        report.append(f"   Performance Ratio: {results['performance_ratio']:.1f}x slower")
        report.append("")
        
        report.append("💾 MEMORY USAGE:")
        report.append(f"   Player Objects:    ~{results['player_memory']/1024:.1f} KB")
        report.append(f"   Team Objects:      ~{results['team_memory']/1024:.1f} KB")
        report.append(f"   Total Estimated:   ~{results['memory_estimate']:.1f} KB")
        report.append("")
        
        complexity = self.analyze_complexity()
        report.append("🎯 COMPLEXITY ANALYSIS:")
        report.append("   Greedy Algorithm:")
        report.append(f"     Time:  {complexity['greedy_time']}")
        report.append(f"     Space: {complexity['greedy_space']}")
        report.append("   Regret Algorithm:")
        report.append(f"     Time:  {complexity['regret_time']}")
        report.append(f"     Space: {complexity['regret_space']}")
        
        return "\n".join(report)