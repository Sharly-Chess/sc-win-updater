import os
from threading import Thread
import tkinter as tk
from pathlib import Path
from tkinter import ttk
import tkinter.messagebox

from packaging.version import Version

from common import ICON_FILE
from common.exception import SCUpdaterException
from common.i18n import _
from version_installer.installer_status import InstallerStatus
from version_installer.version_installer import VersionInstaller


class UpdaterApp(tk.Tk):
    def __init__(
        self,
        check_beta: bool,
        install_dir: Path,
        locale: str,
        version: Version | None = None,
    ):
        super().__init__()
        self.check_beta = check_beta
        self.install_dir = install_dir
        self.version = version
        self.locale = locale

        # Set window in the middle of the screen
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        window_w = 400
        window_h = 100
        x = (screen_w // 2) - (window_w // 2)
        y = (screen_h // 2) - (window_h // 2) - 100
        self.geometry(f'{window_w}x{window_h}+{x}+{y}')

        self.title(_('Sharly Chess update'))
        self.iconbitmap(ICON_FILE)
        self.resizable(False, False)

        # Widgets
        self.label = ttk.Label(self)
        self.label.pack(pady=(20, 3), padx=20, anchor='nw')
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100)
        progress_bar.pack(padx=20, fill='x', anchor='n')

        self.after(100, self._start_installer_thread)

    def _set_progress_and_label(self, progress: float, label: str):
        self.progress_var.set(progress)
        self.label.config(text=label)
        self.update_idletasks()

    def _start_installer_thread(self):
        status = InstallerStatus(_('Starting installer...'))

        def run_installer():
            try:
                self.version = VersionInstaller.install_version(
                    version=self.version,
                    check_beta=self.check_beta,
                    install_dir=self.install_dir,
                    status=status,
                    locale=self.locale,
                )
            except Exception as e:
                if isinstance(e, SCUpdaterException):
                    error = str(e)
                else:
                    error = _('An unexpected error occurred:')
                    error += f'\n\n{e}'
                status.error = error

        thread = Thread(target=run_installer)
        thread.start()
        self._check_install_status(status, thread)

    def _check_install_status(self, status: InstallerStatus, thread: Thread):
        if thread.is_alive():
            if status.modified:
                self._set_progress_and_label(status.progress, status.label)
            self.after(100, self._check_install_status, status, thread)
        elif status.error:
            self._show_retry_dialog(status.error)
        else:
            self._set_progress_and_label(100, _('Done.'))
            self._show_succes_dialog()

    def _show_retry_dialog(self, error: str):
        retry = tk.messagebox.askretrycancel(
            title=_('Update error'),
            message=error,
        )
        if retry:
            self._start_installer_thread()
        else:
            self.quit()

    def _show_succes_dialog(self):
        tk.messagebox.showinfo(
            title=_('Update complete'),
            message=_(
                'The new version has successfully been '
                'installed. Close to restart Sharly Chess.'
            ),
        )

        self.destroy()
        self.quit()
        assert self.version is not None
        exe_path = self.install_dir / VersionInstaller.exe_file(self.version)
        os.execl(exe_path, exe_path)
