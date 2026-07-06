import argparse
import sys
from pathlib import Path

from packaging.version import InvalidVersion, Version

from common import DEVEL_ENV, BASE_DIR
from common.i18n import get_default_locale, set_locale, locales
from gui.updater_app import UpdaterApp

if DEVEL_ENV:
    from dotenv import load_dotenv

    load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument(
    '-v',
    '--version',
    type=str,
    help='Version to install. Defaults to the latest version.',
)
parser.add_argument(
    '-o',
    '--output',
    type=str,
    help='Path to the directory in which the new version will be installed.',
)
parser.add_argument(
    '-b',
    '--beta',
    action='store_true',
    help='When looking for the latest version, also include beta versions.',
)
parser.add_argument(
    '-l',
    '--locale',
    type=str,
    help='The locale to use.',
)
args = parser.parse_args()

version: Version | None = None
if args.version:
    try:
        version = Version(args.version)
    except InvalidVersion:
        print(f'Invalid version [{args.version}], falling back to latest version.')

locale = get_default_locale()
if args.locale and args.locale not in locales:
    print('Unknown locale [%s] (expected: %s), falling back to [%s].')
elif args.locale:
    locale = args.locale
set_locale(locale)

if args.output:
    install_dir = Path(args.output)
elif DEVEL_ENV:
    install_dir = BASE_DIR / 'dev-output'
else:
    exe_path = Path(sys.executable).resolve()
    install_dir = exe_path.parent / 'output'
    for parent in exe_path.parents:
        if (parent / 'sharly-chess.exe').exists():
            install_dir = parent
            break

app = UpdaterApp(
    check_beta=args.beta,
    install_dir=install_dir,
    version=version,
    locale=locale,
)
app.mainloop()
