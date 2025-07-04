#!/usr/bin/env python3
"""
Visualization utilities for Fantasy Football Draft Algorithm
Creates charts and graphs for analysis results
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Any, Optional

def create_comparison_charts(results: Dict[int, Dict], performance_results: Optional[Dict[str, Any]] = None):
    """Create comprehensive comparison charts"""
    
    if not results:
        print("❌ No results data to visualize")
        return
    
    # Prepare data
    years = sorted(results.keys())
    greedy_scores = [results[year]['greedy'] for year in years]
    regret_scores = [results[year]['regret'] for year in years]
    improvements = [results[year]['improvement'] for year in years]
    
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # 1. Yearly Performance Comparison
    x = np.arange(len(years))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, greedy_scores, width, label='Greedy Algorithm', 
                    color='#e74c3c', alpha=0.8)
    bars2 = ax1.bar(x + width/2, regret_scores, width, label='Regret Algorithm', 
                    color='#27ae60', alpha=0.8)
    
    ax1.set_xlabel('Season')
    ax1.set_ylabel('Fantasy Points')
    ax1.set_title('Algorithm Performance Comparison by Season')
    ax1.set_xticks(x)
    ax1.set_xticklabels(years)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for i, (greedy, regret) in enumerate(zip(greedy_scores, regret_scores)):
        ax1.text(i - width/2, greedy + 20, f'{greedy:.0f}', ha='center', va='bottom', fontsize=9)
        ax1.text(i + width/2, regret + 20, f'{regret:.0f}', ha='center', va='bottom', fontsize=9)
    
    # 2. Yearly Improvements
    colors = ['green' if imp > 0 else 'red' for imp in improvements]
    bars3 = ax2.bar(years, improvements, color=colors, alpha=0.7)
    ax2.set_xlabel('Season')
    ax2.set_ylabel('Point Difference (Regret - Greedy)')
    ax2.set_title('Yearly Performance Improvements')
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax2.grid(True, alpha=0.3)
    
    # Add value labels
    for i, (year, imp) in enumerate(zip(years, improvements)):
        ax2.text(year, imp + (5 if imp > 0 else -15), f'{imp:+.0f}', 
                ha='center', va='bottom' if imp > 0 else 'top', fontsize=9, fontweight='bold')
    
    # 3. Cumulative Performance
    cumulative_greedy = np.cumsum(greedy_scores)
    cumulative_regret = np.cumsum(regret_scores)
    
    ax3.plot(years, cumulative_greedy, 'o-', color='#e74c3c', linewidth=3, 
             markersize=8, label='Greedy (Cumulative)')
    ax3.plot(years, cumulative_regret, 'o-', color='#27ae60', linewidth=3, 
             markersize=8, label='Regret (Cumulative)')
    
    ax3.set_xlabel('Season')
    ax3.set_ylabel('Cumulative Fantasy Points')
    ax3.set_title('Cumulative Performance Over Time')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Fill area between lines
    ax3.fill_between(years, cumulative_greedy, cumulative_regret, 
                     where=(np.array(cumulative_regret) >= np.array(cumulative_greedy)),
                     color='green', alpha=0.2, label='Regret Advantage')
    ax3.fill_between(years, cumulative_greedy, cumulative_regret, 
                     where=(np.array(cumulative_regret) < np.array(cumulative_greedy)),
                     color='red', alpha=0.2, label='Greedy Advantage')
    
    # 4. Summary Statistics and Performance Metrics
    ax4.axis('off')
    
    # Calculate summary stats
    total_improvement = sum(improvements)
    avg_improvement = np.mean(improvements)
    regret_wins = sum(1 for imp in improvements if imp > 0)
    win_rate = (regret_wins / len(improvements)) * 100
    
    summary_text = f"""
🏆 ALGORITHM COMPARISON SUMMARY

📊 Overall Performance:
    Total Seasons: {len(years)}
    Regret Wins: {regret_wins}/{len(years)} ({win_rate:.0f}%)
    
    Point Analysis:
    Total Improvement: {total_improvement:+.0f} points
    Average per Season: {avg_improvement:+.1f} points
    Best Single Season: {max(improvements):+.0f} points
    Worst Single Season: {min(improvements):+.0f} points

📈 Consistency:
    Winning Seasons: {regret_wins}
    Losing Seasons: {len(years) - regret_wins}
    """
    
    if performance_results:
        perf_text = f"""
⚡ Performance Metrics:
    Runtime Ratio: {performance_results.get('performance_ratio', 0):.1f}x slower
    Memory Usage: ~{performance_results.get('memory_estimate', 0):.0f} KB
    """
        summary_text += perf_text
    
    # Determine overall conclusion
    if total_improvement > 0:
        conclusion = "✅ REGRET ALGORITHM SUPERIOR"
        conclusion_color = 'green'
    else:
        conclusion = "❌ HYPOTHESIS NOT CONFIRMED"
        conclusion_color = 'red'
    
    summary_text += f"\n CONCLUSION: {conclusion}"
    
    ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, 
             fontsize=11, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))
    
    # Add conclusion box
    ax4.text(0.5, 0.05, conclusion, transform=ax4.transAxes, 
             fontsize=14, fontweight='bold', ha='center', va='bottom',
             bbox=dict(boxstyle="round,pad=0.5", facecolor=conclusion_color, alpha=0.7, edgecolor='black'))
    
    plt.tight_layout()
    plt.savefig('algorithm_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("📊 Comprehensive visualization saved as 'algorithm_comparison.png'")

def create_position_breakdown_chart(greedy_team, regret_team, year: int):
    """Create position-by-position breakdown chart"""
    
    positions = ['QB', 'RB', 'WR', 'TE', 'FLEX', 'K']
    greedy_pos = []
    regret_pos = []
    
    for pos in positions:
        greedy_points = sum(p.actual_points for p in greedy_team.roster[pos])
        regret_points = sum(p.actual_points for p in regret_team.roster[pos])
        greedy_pos.append(greedy_points)
        regret_pos.append(regret_points)
    
    # Create chart
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(positions))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, greedy_pos, width, label='Greedy', color='#e74c3c', alpha=0.8)
    bars2 = ax.bar(x + width/2, regret_pos, width, label='Regret', color='#27ae60', alpha=0.8)
    
    ax.set_xlabel('Position')
    ax.set_ylabel('Fantasy Points')
    ax.set_title(f'Position Breakdown Comparison - {year} Season')
    ax.set_xticks(x)
    ax.set_xticklabels(positions)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Add difference annotations
    for i, (greedy, regret) in enumerate(zip(greedy_pos, regret_pos)):
        diff = regret - greedy
        if abs(diff) > 1:  # Only show significant differences
            ax.annotate(f'{diff:+.0f}', 
                       xy=(i, max(greedy, regret) + 10),
                       ha='center', va='bottom', fontweight='bold',
                       color='green' if diff > 0 else 'red')
    
    plt.tight_layout()
    plt.savefig(f'position_breakdown_{year}.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"📊 Position breakdown chart saved as 'position_breakdown_{year}.png'")

def create_performance_metrics_chart(performance_results: Dict[str, Any]):
    """Create performance metrics visualization"""
    
    if not performance_results:
        print("❌ No performance data to visualize")
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Runtime comparison
    algorithms = ['Greedy', 'Regret']
    runtimes = [performance_results['greedy_time'] * 1000, 
                performance_results['regret_time'] * 1000]
    colors = ['#e74c3c', '#27ae60']
    
    bars1 = ax1.bar(algorithms, runtimes, color=colors, alpha=0.8)
    ax1.set_ylabel('Runtime (ms)')
    ax1.set_title('Algorithm Runtime Comparison')
    ax1.grid(True, alpha=0.3)
    
    # Add value labels
    for bar, runtime in zip(bars1, runtimes):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{runtime:.2f}ms', ha='center', va='bottom', fontweight='bold')
    
    # Memory usage breakdown
    memory_categories = ['Players', 'Teams', 'Algorithm']
    memory_values = [
        performance_results['player_memory'] / 1024,
        performance_results['team_memory'] * 10 / 1024,  # 10 teams
        (performance_results['regret_memory'] - performance_results['greedy_memory']) / 1024
    ]
    
    ax2.pie(memory_values, labels=memory_categories, autopct='%1.1f%%', startangle=90)
    ax2.set_title('Memory Usage Distribution')
    
    plt.tight_layout()
    plt.savefig('performance_metrics.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("Performance metrics chart saved as 'performance_metrics.png'")