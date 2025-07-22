# PMCSN Project

A Performance Modeling and Computer System Networks simulation project implementing discrete event simulation.

## Quick Start

To run the application:
```bash
python3 src/main.py
```

## Documentation

This project uses Sphinx for documentation generation.

### Generating Documentation

1. **Generate API documentation indices:**
   ```bash
   sphinx-apidoc -f -o docs/source src/ --separate --module-first
   ```

2. **Build HTML documentation:**
   ```bash
   cd docs && make clean html
   ```

3. **View documentation:**
   Open `docs/build/html/index.html` in your browser

> **Note:** Pre-generated documentation is already available in the repository.

## Project Structure

```
PMCSN_Project/
├── conf/                    # Configuration files
│   └── request.json
├── docs/                    # Sphinx documentation
├── drawio-Model/           # System model diagrams
├── src/                    # Source code
│   ├── desPython/          # Discrete event simulation library
│   ├── interfaces/         # Abstract interfaces
│   ├── models/             # Data models (person, request)
│   ├── simulation/         # Simulation engine and components
│   │   ├── blocks/         # Simulation blocks
│   │   └── states/         # System states
│   └── main.py            # Main entry point
└── README.md
```

## Requirements

- Python 3.x
- Sphinx (for documentation)
(for now)