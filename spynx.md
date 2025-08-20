# Documentation Generation

This project uses Sphinx for documentation generation.

## Requirements

- Python 3.x
- Sphinx

## Installation

Install Sphinx if not already available:
```bash
pip install sphinx
```

## Generating Documentation

### 1. Generate API documentation indices

Generate the API documentation structure from the source code:
```bash
sphinx-apidoc -f -o docs/source src/ --separate --module-first
```

This command:
- `-f`: Force overwrite of existing files
- `-o docs/source`: Output directory for generated .rst files
- `src/`: Source directory to document
- `--separate`: Create separate pages for each module
- `--module-first`: Put module documentation before submodules

### 2. Build HTML documentation

Navigate to the docs directory and build the documentation:
```bash
cd docs && make clean html
```

On Windows, you can also use:
```bash
cd docs && make.bat clean html
```

### 3. View documentation

Open the generated documentation in your browser:
```
docs/build/html/index.html
```

## Documentation Structure

The documentation is organized as follows:
- `docs/source/`: Sphinx source files (.rst)
- `docs/build/`: Generated documentation output
- `docs/build/html/`: HTML documentation files

## Notes

- Pre-generated documentation is already available in the repository
- The documentation is automatically generated from docstrings in the source code
- Configuration is managed in `docs/source/conf.py`

## Cleaning Documentation

To clean previously built documentation:
```bash
cd docs && make clean
```

## Advanced Usage

For more advanced Sphinx features and configuration options, refer to the [official Sphinx documentation](https://www.sphinx-doc.org/).
