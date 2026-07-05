import importlib.metadata
import sys
from pathlib import Path

from packaging.version import Version

APP_NAME = 'sc-win-updater'
APP_VERSION = Version(importlib.metadata.version(APP_NAME))

DEVEL_ENV = not getattr(sys, 'frozen', False)


def _app_base_dir():
    # PyInstaller onefile
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        return Path(meipass)
    return Path(__file__).resolve().parents[2]


BASE_DIR = _app_base_dir()
ICON_FILE = BASE_DIR / 'images' / 'sharly-chess.ico'
