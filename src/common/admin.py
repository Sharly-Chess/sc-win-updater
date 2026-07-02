import ctypes
import sys


def _is_windows_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def ensure_admin_privileges():
    if not _is_windows_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, 'runas', sys.executable, ' '.join(sys.argv), None, 1
        )
        sys.exit()
