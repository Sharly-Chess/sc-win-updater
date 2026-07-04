from pathlib import Path

from PyInstaller.__main__ import run as run_pyinstaller

from common import APP_NAME, APP_VERSION, ICON_FILE, BASE_DIR

basename = f'{APP_NAME}-{APP_VERSION}'


def generate_pyinstaller_params():
    params = [
        'src/main.py',
        f'--name={basename}',
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
    for file in files:
        if not file.is_file():
            continue
        relative_path = file.relative_to(BASE_DIR)
        params.append(f'--add-data={file};{relative_path}')
    return params


params = generate_pyinstaller_params()
run_pyinstaller(params)
