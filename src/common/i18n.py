import gettext as gettext_lib
import sys
import threading
from gettext import GNUTranslations
from pathlib import Path

from common import DEVEL_ENV

DEFAULT_LOCALE: str = 'en'
if DEVEL_ENV:
    print(f'Default locale: {DEFAULT_LOCALE}')

# The directory where to find the i18n files.
locales_dir: Path = Path(__file__).resolve().parents[2] / 'locale'
if not locales_dir.is_dir():
    print(f'Locales directory [{locales_dir}] not found, exiting.')
    sys.exit(1)
if DEVEL_ENV:
    print(f'Locale folder: {locales_dir}')

# Build a dict of all the translations with the available locales retrieved from the filesystem.
locales: list[str] = []
for l_entry in locales_dir.iterdir():
    if l_entry.is_dir():
        mo_file: Path = l_entry / 'LC_MESSAGES' / f'messages.mo'
        if mo_file.is_file():
            locales.append(l_entry.name)


# load the translations.
_all_translations: dict[str, GNUTranslations] = {}
for loc in locales:
    try:
        _all_translations[loc] = gettext_lib.translation(
            'messages',
            locales_dir,
            [
                loc,
            ],
        )
    except Exception as ex:
        print(f'Could not load locale [{loc}]: {ex}.')
        sys.exit(1)
if DEVEL_ENV:
    print(f'Locales found: {', '.join(locales)}')


# Initialize the current thread with the default locale.
_thread_local_data = threading.local()


def get_locale() -> str:
    """Returns the locale of the current thread."""
    try:
        return _thread_local_data.locale
    except AttributeError:
        return DEFAULT_LOCALE


def set_locale(locale: str):
    """Sets the locale for the current thread."""
    if hasattr(_thread_local_data, 'locale') and _thread_local_data.locale == locale:
        return
    if locale not in locales:
        print(f'Unknown locale [{locale}], exiting.')
        sys.exit(1)
    _thread_local_data.locale = locale
    if DEVEL_ENV:
        print(f'Locale set to [{locale}].')


def gettext(message: str, locale: str | None = None):
    """Overrides the gettext.gettext() function to use the locale of the current thread."""
    if locales:
        return _all_translations[locale or get_locale()].gettext(message)
    else:
        return gettext_lib.gettext(message)


def _(message: str, locale: str | None = None):
    """An alias for gettext()."""
    return gettext(message, locale)


def ngettext(singular: str, plural: str, n: int, locale: str | None = None):
    """Overrides the gettext.ngettext() function to use the locale of the current thread."""
    if locales:
        return _all_translations[locale or get_locale()].ngettext(singular, plural, n)
    else:
        return gettext_lib.ngettext(singular, plural, n)
