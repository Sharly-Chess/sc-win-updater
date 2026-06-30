# sharly-chess-installer

Simple GUI to install or update the [Sharly Chess](https://github.com/Sharly-Chess/sharly-chess) application.  
Works for both windows and MacOS. The project is split into 2 distinct applications: 
- The Updater, which simply installs a version of the application  
- The Installer, an install wizard which additionally provides extra parameters (Windows-only)

## Getting started 

Install dependencies:  
```sh
pip install -e .
```

Running the applications: 
```sh
python src/updater.py # The Updater
python src/installer.py # The Installer
```
