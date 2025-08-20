# PMCSN Project

A Performance Modeling and Computer System Networks simulation project implementing discrete event simulation.

## Quick Start

To run the simulation:
```bash
python3 src/main.py
```

## Features

### Simulation Analysis Tools

1. **Queue Statistics Analysis**: Generate comprehensive visualizations of queue performance
   ```bash
   python3 src/analyze_queue_stats.py
   ```

2. **Large Dataset Analysis**: Optimized analysis for 3-4 months of simulation data
   ```bash
   python3 src/analyze_queue_stats_large.py
   ```

3. **Pareto Distribution Fitting**: Find and test Pareto distribution approximations
   ```bash
   python3 src/findPareto.py
   ```

### Generated Analysis

The analysis tools automatically create visualizations in the `queue_analysis_graphs/` directory:

- **Individual queue analysis**: Distribution plots, temporal trends, and performance metrics
- **Comparative analysis**: Cross-queue performance comparison and system efficiency
- **Temporal analysis**: Daily, weekly, and monthly trends
- **Performance heatmaps**: Queue utilization and wait time patterns over time

## Documentation

See [DOCUMENTATION.md](DOCUMENTATION.md) for Sphinx documentation generation instructions.

## Project Structure

```
PMCSN_Project/
├── conf/                    # Configuration files
│   └── request.json
├── docs/                    # Sphinx documentation
├── drawio-Model/           # System model diagrams
├── src/                    # Source code
│   ├── analyze_queue_stats.py      # Standard queue analysis tool
│   ├── analyze_queue_stats_large.py # Large dataset analysis tool
│   ├── findPareto.py              # Pareto distribution fitting
│   ├── daily_stats.json           # Generated simulation statistics
│   ├── desPython/                  # Discrete event simulation library
│   ├── interfaces/                 # Abstract interfaces
│   ├── models/                     # Data models (person, request)
│   ├── simulation/                 # Simulation engine and components
│   │   ├── blocks/                 # Simulation blocks
│   │   └── states/                 # System states
│   ├── queue_analysis_graphs/      # Generated analysis visualizations
│   └── main.py                     # Main entry point
├── DOCUMENTATION.md         # Sphinx documentation guide
└── README.md
```

## Analysis Output

The analysis tools generate various types of visualizations:

### Queue Performance Analysis
- **Distribution plots**: Wait time and execution time distributions for each queue
- **Temporal trends**: Queue performance over time
- **Correlation analysis**: Relationship between wait and execution times
- **Queue length analysis**: Queue capacity utilization patterns

### System-wide Analysis
- **Efficiency metrics**: System throughput and performance indicators
- **Comparative analysis**: Cross-queue performance comparison
- **Heatmaps**: Performance patterns across time and queues
- **Trend analysis**: Daily, weekly, and monthly patterns

### Pareto Distribution Analysis
The `findPareto.py` tool helps identify optimal Pareto distribution parameters for modeling arrival patterns and service times by testing various parameter combinations and providing statistical fits.

## Requirements

- Python 3.x
- matplotlib
- numpy
- pandas

For documentation generation, see [DOCUMENTATION.md](DOCUMENTATION.md).