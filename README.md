# Sharly Chess Windows updater

Simple GUI to update the [Sharly Chess](https://github.com/Sharly-Chess/sharly-chess) application on windows.

## Getting started

```sh
# Create virtual environment
python -m venv venv
venv/Scripts/activate

# Install dependencies
pip install -e .[lint, dev]

# Setup pre-commit hook
pre-commit install
```

Running the applications:
```sh
python src/main.py
usage: main.py [-h] [-v VERSION] [-o OUTPUT] [-b] [-s]

options:
  -h, --help            show this help message and exit
  -v, --version VERSION
                        Version to install. Defaults to the latest version.
  -o, --output OUTPUT   Path to the directory in which the new version will be installed.
  -b, --beta            When looking for the latest version, also include beta versions.
  -s, --skip-admin      Skip the admin elevation.
```
