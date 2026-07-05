import ctypes
import sys
from pathlib import Path

from common import DEVEL_ENV


def _is_windows_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def ensure_admin_privileges():
    if _is_windows_admin():
        return
    exe_path = Path(sys.executable).absolute()
    params = sys.argv
    if not DEVEL_ENV:
        params.pop(0)
    ctypes.windll.shell32.ShellExecuteW(
        None, 'runas', str(exe_path), ' '.join(params), None, 1
    )
    sys.exit()
