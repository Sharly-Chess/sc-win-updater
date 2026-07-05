import ctypes
import gettext as gettext_lib
import locale
import threading
from gettext import GNUTranslations
from pathlib import Path

from common import DEVEL_ENV, BASE_DIR
from common.exception import SCUpdaterException

DEFAULT_LOCALE = 'en'

# The directory where to find the i18n files.
locales_dir: Path = BASE_DIR / 'locale'
if not locales_dir.is_dir():
    raise SCUpdaterException(f'Locales directory [{locales_dir}] not found.')
if DEVEL_ENV:
    print(f'Locale folder: {locales_dir}')

# Build a dict of all the translations with the available locales retrieved from the filesystem.
locales: list[str] = []
for l_entry in locales_dir.iterdir():
    if not l_entry.is_dir():
        continue
    mo_file: Path = l_entry / 'LC_MESSAGES' / 'messages.mo'
    if mo_file.is_file():
        locales.append(l_entry.name)

if not locales:
    raise SCUpdaterException(f'No locales found in [{locales_dir}].')

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
        raise SCUpdaterException(f'Could not load locale [{loc}]: {ex}.')
if DEVEL_ENV:
    print(f'Locales found: {", ".join(locales)}')


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
        raise SCUpdaterException(
            f'Unknown locale {locale} (expected: {", ".join(locales)})'
        )
    _thread_local_data.locale = locale
    if DEVEL_ENV:
        print(f'Locale set to [{locale}].')


def get_default_locale() -> str:
    system_user_locale = _get_system_user_locale()
    if system_user_locale:
        user_locale = system_user_locale[:2]
        if user_locale in locales:
            return user_locale
    return DEFAULT_LOCALE


def _get_system_user_locale() -> str | None:
    windll = ctypes.windll.kernel32
    try:
        # Locale ID → Windows locale name → Python locale key
        # locale.windows_locale maps LCIDs to names like 'en_GB'
        system_user_locale = locale.windows_locale[windll.GetUserDefaultUILanguage()]
        print('System user locale:', system_user_locale)
        return system_user_locale
    except Exception as e:
        print('System locale not found: ', e)
        return None


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
