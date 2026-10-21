# Contributing to rms-pdstable

Thank you for your interest in contributing to rms-pdstable! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

We expect all contributors to follow our Code of Conduct, which ensures a welcoming and inclusive environment for everyone.
See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:

   ```bash
   git clone https://github.com/your-username/rms-pdstable.git
   cd rms-pdstable
   ```

3. Create the virtual environment and install the package with its dev and docs dependencies. The script is safe to re-run, and `scripts/run-all-checks.sh` expects the environment it creates:

   ```bash
   ./scripts/setup-venv.sh
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

## Development Workflow

1. Create a new branch from `main`, named `<initials>_<YYMMDD>_<topic>`:

   ```bash
   git checkout -b ms_261021_label_cache
   ```

2. Make your changes, following our coding standards
3. Write or update tests as necessary
4. Run the tests, lint, and docs build to ensure they pass:

   ```bash
   ./scripts/run-all-checks.sh
   ```

5. Commit your changes with a subject written as a plain imperative sentence, with no type prefix:

   ```bash
   git commit -m "Report the column name when a value cannot be parsed"
   ```

6. Push your branch to your fork:

   ```bash
   git push origin ms_261021_label_cache
   ```

7. Open a Pull Request on GitHub

## Coding Standards

We follow these standards for all code contributions:

* **Python Style**: Follow PEP 8, with a maximum line length of 90. `ruff check` is the linter of record; do not run `ruff format`, because it removes the column alignment the code uses deliberately
* **Type Hints**: Do not annotate code under `src/`; give parameter and return types in the docstrings instead. Annotate every test function
* **Docstrings**: Document all modules, classes, and methods with docstrings following the Google style, using `Parameters:` rather than `Args:`
* **Testing**: Include unit tests for new functionality
* **Compatibility**: Ensure compatibility with Python 3.11+

Example of a well-formatted method:

```python
def get_column(self, name, *, masked=False):
    """Return the values in a column of this table.

    Parameters:
        name (str): The name of the column to retrieve.
        masked (bool, optional): True to replace each invalid value with None.

    Returns:
        numpy.ndarray | list[tuple]: The values in the column, one per row of the table.
    """
```

## Pull Request Process

1. Ensure all checks in `scripts/run-all-checks.sh` pass
2. Update documentation if necessary
3. Request a review from a maintainer
4. Address any feedback from reviewers

The maintainers will squash-merge your PR once it meets all requirements.

## Testing

We use pytest for testing. To run the tests:

```bash
pytest
```

For more verbose output:

```bash
pytest -v
```

To run a specific test file:

```bash
pytest tests/test_specific_file.py
```

## Documentation

We use Sphinx for documentation. To build the docs and open them in a browser:

```bash
./scripts/read-docs.sh
```

The generated documentation will be in `docs/_build/html`.

When adding new features, please update the relevant documentation:

* Update docstrings for new functions and classes
* Add examples if appropriate
* Update the user guide or developer guide if necessary

## Reporting Issues

If you find a bug or have a suggestion for improvement:

1. Check if the issue already exists in the GitHub issue tracker
2. If not, create a new issue with:
   * A clear, descriptive title
   * A detailed description of the issue
   * Steps to reproduce (for bugs)
   * Your environment information (Python version, OS, etc.)
   * Any relevant logs or screenshots

Thank you for contributing to rms-pdstable!
