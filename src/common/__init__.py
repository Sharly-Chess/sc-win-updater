import importlib.metadata
import sys
from pathlib import Path

from packaging.version import Version

APP_NAME = 'sc-win-updater'
APP_VERSION = Version(importlib.metadata.version(APP_NAME))

DEV_ENV = not getattr(sys, 'frozen', False)
UPDATER_FILE = Path(sys.executable).resolve()
ICON_FILE = Path('images') / 'sharly-chess.ico'
