import argparse
import sys
from pathlib import Path

from packaging.version import InvalidVersion, Version

from common import DEVEL_ENV
from common.admin import ensure_admin_privileges
from common.i18n import set_locale
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
    default=(Path('dev-output') if DEVEL_ENV else Path(sys.executable).resolve().parent),
)
parser.add_argument(
    '-b',
    '--beta',
    action='store_true',
    help='When looking for the latest version, also include beta versions.',
)
parser.add_argument(
    '-s',
    '--skip-admin',
    action='store_true',
    help='Skip the admin elevation.',
)
parser.add_argument(
    '-l',
    '--locale',
    type=str,
    help='The locale to use.',
)
args = parser.parse_args()

if args.locale:
    set_locale(args.locale)

if not args.skip_admin:
    ensure_admin_privileges()

version: Version | None = None
if args.version:
    try:
        version = Version(args.version)
    except InvalidVersion:
        print(f'Invalid version [{args.version}], falling back to latest version.')

app = UpdaterApp(
    version=version,
    check_beta=args.beta,
    install_dir=Path(args.output),
)
app.mainloop()
