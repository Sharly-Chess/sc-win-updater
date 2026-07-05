import shutil
from argparse import ArgumentParser, Namespace
from pathlib import Path

from PyInstaller.__main__ import run as run_pyinstaller


from common import APP_NAME, APP_VERSION, ICON_FILE, BASE_DIR

from i18n_update import update_i18n_files
from sign import sign_file

BASE_NAME = f'{APP_NAME}-{APP_VERSION}'


def clean():
    print('Cleaning folders...')
    for folder_name in ('dist', 'build'):
        folder: Path = BASE_DIR / folder_name
        if folder.is_dir():
            shutil.rmtree(folder)


def generate_pyinstaller_params():
    params = [
        'src/main.py',
        f'--name={BASE_NAME}',
        f'--icon={ICON_FILE}',
        '--clean',
        '--noconfirm',
        '--copy-metadata',
        'sc_win_updater',
        '--paths=.',
        '--windowed',
        '--onefile',
        '--optimize',
        '1',
    ]
    hidden_imports = ['common', 'gui', 'version_installer']
    for import_ in hidden_imports:
        params.append(f'--hiddenimport={import_}')
    files: list[Path] = [
        ICON_FILE,
    ]
    files += list((BASE_DIR / 'locale').glob('**/*.mo'))
    for file in files:
        if not file.is_file():
            continue
        relative_path = file.parent.relative_to(BASE_DIR)
        params.append(f'--add-data={file};{relative_path}')
    return params

def main():
    parser = ArgumentParser(description='Export Sharly Chess updater.')
    parser.add_argument(
        '--windows-signtool-cert-fingerprint',
        type=str,
        help='The user.',
    )
    args: Namespace = parser.parse_args()
    clean()
    update_i18n_files()
    pyinstaller_params = generate_pyinstaller_params()
    run_pyinstaller(pyinstaller_params)
    sign_file(
        BASE_DIR / 'dist' / f'{BASE_NAME}.exe',
        args.windows_signtool_cert_fingerprint,
    )


if __name__ == '__main__':
    main()
