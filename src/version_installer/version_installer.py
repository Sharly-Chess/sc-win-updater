import json
import os
import re
import shutil
import tempfile
import zipfile
import subprocess
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Callable

from packaging.version import Version
from requests import get
from requests.exceptions import RequestException  # pylint: disable=redefined-builtin

from common.exception import SCInstallerException
from common.i18n import _
from version_installer.installer_status import InstallerStatus


class VersionInstaller:
    @classmethod
    def install_version(
        cls,
        install_dir: Path,
        status: InstallerStatus,
        version: Version | None = None,
        check_beta: bool = False,
        avoid_file: Path | None = None,
        add_windows_firewall_rule: bool = False,
    ) -> Version:
        """Install a version at the provided install directory.
        If no version is provided, search for the latest one.
        raises a SCInstallerException if it fails."""

        def set_progress(progress: float):
            status.progress = progress
            status.modified = True

        def set_label(label: str):
            status.label = label
            status.modified = True
            print(label)

        set_progress(0)
        if not version:
            set_label(_('Searching for the latest version...'))
            version = cls._search_for_latest_version(check_beta)
            set_progress(5)
        with tempfile.TemporaryDirectory() as _tmp_dir:
            tmp_dir = Path(_tmp_dir)
            set_label(
                _('Downloading version [{version}] from GitHub...').format(
                    version=version
                )
            )
            zip_file = tmp_dir / cls._get_asset_name(version)
            cls._download_version_zip_file(version, zip_file, set_progress, 5, 20)
            extract_dir = tmp_dir / f'sharly-chess-{version}'
            set_label(_('Extracting archive...'))
            cls._extract_zip_file(zip_file, extract_dir, set_progress, 20, 60)
            set_label(_('Checking files integrity...'))
            cls._check_missing_files(extract_dir)
            set_progress(63)
            set_label(_('Unblocking files...'))
            cls._check_missing_files(extract_dir)
            set_progress(66)
            set_label(_('Uninstalling previous version...'))
            cls._uninstall_previous_version(install_dir, version)
            set_progress(70)

            set_label(_('Copying files to install directory...'))
            cls._copy_dir_files(
                src_dir=extract_dir,
                dst_dir=install_dir,
                set_progress=set_progress,
                progress_start=70,
                progress_end=99,
                avoid_file=avoid_file,
            )
            if add_windows_firewall_rule:
                set_label(_('Adding firewall rule...'))
                cls._add_firewall_rule(install_dir / cls.exe_file(version))
            return version

    @classmethod
    def _search_for_latest_version(cls, check_beta: bool) -> Version:
        """Retrieves the latest version from the GitHub repository."""

        fake_latest = os.getenv('FAKE_LATEST_VERSION')
        if fake_latest:
            return Version(fake_latest)

        entries = cls._get_github_releases()

        assets_by_version: dict[Version, list[dict]] = {}
        for entry in entries:
            tag_name: str = entry['tag_name']
            if matches := re.match(r'^(\d+\.\d+\.\d+)$', tag_name):
                version = Version(matches.group(1))
            elif matches := re.match(
                r'^(\d+.\d+.\d+(a\d+|b\d+|rc\d+))$',
                tag_name,
            ):
                if check_beta:
                    version = Version(matches.group(1))
                else:
                    continue
            else:
                continue
            if entry.get('draft'):
                continue
            assets_by_version[version] = entry.get('assets', [])

        return next(
            version
            for version in sorted(assets_by_version, reverse=True)
            if cls._get_asset_name(version)
            in [asset.get('name') for asset in assets_by_version[version]]
        )

    @classmethod
    def _download_version_zip_file(
        cls,
        version: Version,
        download_path: Path,
        set_progress: Callable[[float], None],
        progress_start: int,
        progress_end: int,
    ):
        local_zip = os.getenv('ZIP_FILE_PATH')
        if local_zip:
            shutil.copy(local_zip, download_path)
            set_progress(progress_end)
            return
        download_url = cls._get_asset_url(version)
        response = get(download_url, allow_redirects=True, stream=True, timeout=10)
        if response.status_code != 200:
            raise SCInstallerException(
                _('Downloading failed with code [{code}].').format(
                    code=response.status_code
                )
            )
        total_size = int(response.headers.get('content-length', 1))
        progress = 5.0
        progress_rate = progress_end - progress_start
        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                progress += (len(chunk) / total_size) * progress_rate
                set_progress(progress)

    @classmethod
    def _extract_zip_file(
        cls,
        zip_file: Path,
        extract_dir: Path,
        set_progress: Callable[[float], None],
        progress_start: int,
        progress_end: int,
    ):
        progress = float(progress_start)
        progress_rate = progress_end - progress_start
        step = 100
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            step_progress = progress_rate * step / len(zip_ref.infolist())
            for index, file in enumerate(zip_ref.infolist(), 1):
                zip_ref.extract(file, extract_dir)
                if index % step == 0:
                    progress += step_progress
                    set_progress(progress)

    @staticmethod
    def _check_missing_files(version_dir: Path):
        control_file = version_dir / 'tmp' / 'control_file.json'
        if not control_file.exists():
            return
        with open(control_file, 'r', encoding='utf8') as infile:
            control_data: dict[str, Any] = json.loads(infile.read())
        file_paths: list[str] = control_data['file_paths']
        missing_files = [
            file_path
            for file_path in file_paths
            if not (version_dir / file_path).is_file()
        ]
        if missing_files:
            error = _('Some files are missing from the downloading:')
            for file in missing_files:
                error += f'\n  - {file}'
            raise SCInstallerException(error)

    @staticmethod
    def _unblock_files(version_dir: Path):
        for root_, __, files in os.walk(version_dir):
            for name in files:
                path = os.path.join(root_, name)
                # Remove Zone.Identifier ADS if it exists
                ads_path = path + ':Zone.Identifier'
                try:
                    os.remove(ads_path)
                    print(f'Unblocked: {path}')
                except FileNotFoundError:
                    pass  # not blocked or already unblocked
                except Exception as e:
                    print(f'Failed to unblock {path}: {e}')

    @classmethod
    def _uninstall_previous_version(cls, install_dir: Path, version: Version):
        try:
            exe_path = install_dir / cls.exe_file(version)
            exe_path.unlink(missing_ok=True)
            internal = install_dir / '_internal'
            if internal.exists():
                shutil.rmtree(internal)
        except PermissionError:
            raise SCInstallerException(
                _('Sharly Chess is already running, stop it then try again.')
            )

    @staticmethod
    def exe_file(version: Version) -> str:
        if version.major < 5:
            return f'sharly-chess-{version}.exe'
        return 'sharly-chess.exe'

    @staticmethod
    def _copy_dir_files(
        src_dir: Path,
        dst_dir: Path,
        set_progress: Callable[[float], None],
        progress_start: int,
        progress_end: int,
        avoid_file: Path | None = None,
    ):
        progress = float(progress_start)
        progress_rate = progress_end - progress_start
        step = 100
        src_files = list(src_dir.glob('**/*'))
        step_progress = progress_rate * step / len(src_files)
        if avoid_file:
            if dst_dir in avoid_file.parents:
                src_avoid = src_dir / avoid_file.relative_to(dst_dir)
                src_avoid.unlink(missing_ok=True)
        for index, src_file in enumerate(src_files, start=1):
            if index % step == 0:
                progress += step_progress
                set_progress(progress)
            if not src_file.is_file():
                continue
            dst_file = dst_dir / src_file.relative_to(src_dir)
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
        set_progress(progress_end)

    @staticmethod
    def _add_firewall_rule(exe_path: Path):
        command = (
            'netsh advfirewall firewall add rule name="Sharly Chess" dir=in '
            f'action=allow program="{exe_path.absolute()}" enable=yes profile=any'
        )
        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError:
            raise SCInstallerException(_('Error while adding firewall rule.'))

    @classmethod
    def _get_github_releases(cls) -> list[dict[str, Any]]:
        url = 'https://api.github.com/repos/sharly-chess/sharly-chess/releases'
        try:
            response = get(url, allow_redirects=True, timeout=5)
            response.raise_for_status()
            data = response.content.decode()
            return json.loads(data)
        except (RequestException, JSONDecodeError):
            raise SCInstallerException(_('An error occurred while requesting GitHub.'))

    @classmethod
    def _get_asset_name(cls, version: Version) -> str:
        """Name of the asset to download in order to install a new version."""
        return f'sharly-chess-{version}-windows.zip'

    @classmethod
    def _get_asset_url(cls, version: Version):
        """URL of the asset to download in order to install a new version."""
        base_url = 'https://github.com/Sharly-Chess/sharly-chess/releases/download'
        asset = cls._get_asset_name(version)
        return f'{base_url}/{version}/{asset}'
