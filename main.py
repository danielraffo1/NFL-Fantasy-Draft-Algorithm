#!/usr/bin/env python3
"""
Fantasy Football Draft Algorithm Comparison
Main execution file for testing Greedy vs Regret-based algorithms
FIXED VERSION: Handles division by zero and player shortage issues
"""

import sys
import os
from data_loader import DataLoader
from algorithms import GreedyDraftAlgorithm, RegretDraftAlgorithm
from draft_simulator import DraftSimulator
from performance_analyzer import PerformanceAnalyzer
from visualizer import create_comparison_charts

def main():
    """Main execution function"""
    print("🏈 Fantasy Football Draft Algorithm Comparison")
    print("=" * 50)
    
    # Initialize data loader
    loader = DataLoader()
    
    # Load all data
    print("\n📊 Loading data...")
    espn_data = loader.load_espn_rankings()
    actual_data = loader.load_actual_points()
    
    if not espn_data or not actual_data:
        print("❌ Failed to load required data files")
        sys.exit(1)
    
    # Initialize simulator
    simulator = DraftSimulator()
    
    # Test single year first (2023)
    test_year = 2023
    print(f"\n Running test case: {test_year}")
    
    # Run simulations
    greedy_result = simulator.simulate_draft(
        test_year, GreedyDraftAlgorithm, espn_data, actual_data
    )
    
    regret_result = simulator.simulate_draft(
        test_year, RegretDraftAlgorithm, espn_data, actual_data
    )
    
    if not greedy_result or not regret_result:
        print("❌ Simulation failed")
        sys.exit(1)
    
    greedy_team, _ = greedy_result
    regret_team, _ = regret_result
    
    # Display results
    print(f"\n📈 TEST RESULTS:")
    print(f"   Greedy Algorithm:  {greedy_team.total_points:.1f} points")
    print(f"   Regret Algorithm:  {regret_team.total_points:.1f} points")
    print(f"   Improvement:       {regret_team.total_points - greedy_team.total_points:+.1f} points")
    
    winner = "REGRET" if regret_team.total_points > greedy_team.total_points else "GREEDY"
    print(f"   Winner: {winner} Algorithm")
    
    # Detailed roster comparison
    print(f"\n🏆 ROSTER COMPARISON:")
    print("-" * 30)
    
    for position in ['QB', 'RB', 'WR', 'TE', 'FLEX', 'K']:
        greedy_pos = sum(p.actual_points for p in greedy_team.roster[position])
        regret_pos = sum(p.actual_points for p in regret_team.roster[position])
        diff = regret_pos - greedy_pos
        
        print(f"{position:4s}: Greedy={greedy_pos:6.1f}, Regret={regret_pos:6.1f}, Diff={diff:+6.1f}")
    
    # Performance analysis
    print(f"\n⚡ Running performance analysis...")
    analyzer = PerformanceAnalyzer()
    perf_results = analyzer.analyze_algorithms(espn_data, actual_data, test_year)
    
    if perf_results:
        print(f"\n⏱️  RUNTIME PERFORMANCE:")
        print(f"   Greedy Algorithm:  {perf_results['greedy_time']*1000:.2f} ms")
        print(f"   Regret Algorithm:  {perf_results['regret_time']*1000:.2f} ms")
        
        # FIXED: Handle division by zero
        if perf_results['greedy_time'] > 0:
            ratio = perf_results['regret_time'] / perf_results['greedy_time']
            print(f"   Performance Ratio: {ratio:.1f}x slower")
        else:
            print(f"   Performance Ratio: Regret is significantly slower (Greedy < 0.001ms)")
        
        print(f"\n💾 MEMORY USAGE:")
        print(f"   Estimated Total:   ~{perf_results['memory_estimate']:.1f} KB")
    
    # Run multi-year analysis
    print(f"\n🔄 Running multi-year analysis...")
    all_results = {}
    
    for year in [2020, 2021, 2022, 2023, 2024]:
        if year in espn_data and year in actual_data:
            print(f"   Testing {year}...")
            
            greedy_result = simulator.simulate_draft(
                year, GreedyDraftAlgorithm, espn_data, actual_data
            )
            regret_result = simulator.simulate_draft(
                year, RegretDraftAlgorithm, espn_data, actual_data
            )
            
            if greedy_result and regret_result:
                greedy_team, _ = greedy_result
                regret_team, _ = regret_result
                
                all_results[year] = {
                    'greedy': greedy_team.total_points,
                    'regret': regret_team.total_points,
                    'improvement': regret_team.total_points - greedy_team.total_points
                }
    
    # Summary of all years
    if all_results:
        print(f"\n📊 MULTI-YEAR SUMMARY:")
        print("-" * 40)
        total_greedy = 0
        total_regret = 0
        regret_wins = 0
        
        for year, results in all_results.items():
            improvement = results['improvement']
            winner = "Regret" if improvement > 0 else "Greedy"
            if improvement > 0:
                regret_wins += 1
            
            print(f"{year}: Greedy={results['greedy']:.1f}, Regret={results['regret']:.1f}, "
                  f"Diff={improvement:+.1f} ({winner})")
            
            total_greedy += results['greedy']
            total_regret += results['regret']
        
        total_improvement = total_regret - total_greedy
        win_rate = (regret_wins / len(all_results)) * 100
        
        print(f"\nOVERALL RESULTS:")
        print(f"   Total Improvement: {total_improvement:+.1f} points")
        print(f"   Average per Season: {total_improvement/len(all_results):+.1f} points")
        print(f"   Regret Win Rate: {win_rate:.1f}% ({regret_wins}/{len(all_results)})")
        
        overall_winner = "REGRET ALGORITHM" if total_improvement > 0 else "GREEDY ALGORITHM"
        print(f"   OVERALL WINNER: {overall_winner}")
    
    # Create visualizations
    print(f"\n📈 Creating visualizations...")
    try:
        create_comparison_charts(all_results, perf_results)
        print("✅ Visualizations saved successfully!")
    except Exception as e:
        print(f"⚠️  Warning: Could not create visualizations: {e}")
    
    print(f"\n Analysis complete!")

if __name__ == "__main__":
    main()