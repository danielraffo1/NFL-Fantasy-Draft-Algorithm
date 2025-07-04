# Fantasy Football Draft Algorithm Comparison

A comprehensive comparison between traditional ADP-based (Greedy) and advanced Regret-based draft algorithms for fantasy football.

## Project Overview

This project implements and compares two fantasy football draft algorithms:

1. **Greedy Algorithm**: Traditional approach using Average Draft Position (ADP) rankings
2. **Regret Algorithm**: Advanced approach considering positional scarcity, value dropoff, and pick timing

## Quick Start

### Prerequisites

pip install pandas numpy matplotlib seaborn openpyxl


### Required Data Files

Ensure these files are in the data folder:

**ESPN Draft Rankings:**
- `fantasy_rankings_2020.xlsx`
- `fantasy_rankings_2021.xlsx`
- `fantasy_rankings_2022.xlsx`
- `fantasy_rankings_2023.xlsx`
- `fantasy_rankings_2024.xlsx`

**Actual Season Performance:**
- `2020.xlsx`
- `2021.xlsx`
- `2022.xlsx`
- `2023.xlsx`
- `2024.xlsx`

### Running the Analysis

# Run complete analysis
python main.py

# Run tests
python test_suite.py

# Test specific algorithm
python -c "from main import *; # your custom test code"


## File Structure

├── main.py                 # Main execution file
├── models.py              # Data models (Player, Team)
├── algorithms.py          # Draft algorithms implementation
├── data_loader.py         # Data loading utilities
├── draft_simulator.py     # Draft simulation engine
├── performance_analyzer.py # Performance benchmarking
├── visualizer.py          # Chart generation
├── test_suite.py          # Automated tests
└── README.md              # This file

## Algorithm Details

### Greedy Algorithm
- **Time Complexity**: O(n log n)
- **Space Complexity**: O(n)
- **Strategy**: Pick best available player by ADP for needed positions

### Regret Algorithm
- **Time Complexity**: O(n²) per pick
- **Space Complexity**: O(n)
- **Strategy**: Calculate regret scores based on:
  - Player value (normalized auction value)
  - Positional scarcity (quality players remaining)
  - Value dropoff (gap to next best player)
  - Pick urgency (time until next turn)

**Regret Score Formula:**
```
regret = value_score + (scarcity × dropoff × 0.4) + (urgency × 0.3) - bye_penalty
```

## Draft Configuration

- **Teams**: 10 (snake draft)
- **Draft Position**: 5th
- **Roster**: 1 QB, 2 RB, 2 WR, 1 TE, 1 FLEX, 1 K
- **Total Picks**: 8 per team

## Contributing

To extend the algorithm:

1. Add new factors to regret score calculation
2. Implement alternative draft strategies
3. Add new performance metrics
4. Expand test coverage

## License

This project is for educational and research purposes.

## Contact

For questions about implementation or results, please refer to the test outputs and performance analysis included in the codebase.