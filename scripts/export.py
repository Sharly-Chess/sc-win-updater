import shutil
from pathlib import Path

from PyInstaller.__main__ import run as run_pyinstaller

from common import APP_NAME, APP_VERSION, ICON_FILE, BASE_DIR

BASE_NAME = f'{APP_NAME}-{APP_VERSION}'


def pre_cleanup():
    exe_path = BASE_DIR / 'dist' / f'{BASE_NAME}.exe'
    exe_path.unlink(missing_ok=True)


def post_cleanup():
    build_dir = BASE_DIR / 'build' / BASE_NAME
    shutil.rmtree(build_dir)
    spec_file = BASE_DIR / f'{BASE_NAME}.spec'
    spec_file.unlink(missing_ok=True)


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
        '--uac-admin',
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


pre_cleanup()
pyinstaller_params = generate_pyinstaller_params()
run_pyinstaller(pyinstaller_params)
post_cleanup()
