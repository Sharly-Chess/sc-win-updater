from babel.messages.frontend import CommandLineInterface
import sys
from pathlib import Path


def run_babel_command(
    babel_command: str,
    babel_args: list,
    verbose: bool = False,
):
    """Run a Babel command using the command-line interface."""
    argv: list[str] = [
        sys.argv[0],
    ]
    if not verbose:
        argv += [
            '-q',
        ]
    argv += [
        babel_command,
    ] + list(map(str, babel_args))  # map to ensure all args are passed as strings
    if return_code := CommandLineInterface().run(argv):
        print(f'Babel command returned {return_code}, exiting.\nArguments:{'\n- '.join(argv)}')
        sys.exit(1)


def main():
    """Update the i18n files."""
    locales_dir: Path = Path(__file__).resolve().parents[1] / 'locale'
    print(f'Locale folder: {locales_dir}')
    pot_file: Path = locales_dir / 'messages.pot'
    config_file: Path = locales_dir / 'babel.cfg'
    print('Extracting strings to POT file...')
    run_babel_command(
        'extract',
        [
            f'--mapping-file={config_file}',
            f'--output-file={pot_file}',
            '--sort-output',
            '--add-location=never',
            '--no-wrap',
            '--omit-header',
            '--ignore-dirs="**/static"',
            f'{Path(__file__).resolve().parents[1]}',
        ],
    )
    locales: list[str] = []
    for l_entry in locales_dir.iterdir():
        if l_entry.is_dir():
            locales.append(l_entry.name)
    for locale in locales:
        locale_dir: Path = locales_dir / locale / 'LC_MESSAGES'
        po_file: Path = locale_dir / 'messages.po'
        if not po_file.is_file():
            print(f'Initializing PO file for locale [{locale}]...')
            po_file.parent.mkdir(parents=True, exist_ok=True)
            run_babel_command(
                'init',
                [
                    f'--locale={locale}',
                    f'--input-file={pot_file}',
                    f'--output-file={po_file}',
                ],
            )
        print(f'Updating PO file for locale [{locale}]...')
        run_babel_command(
            'update',
            [
                f'--locale={locale}',
                f'--output-dir={locale_dir}',
                f'--input-file={pot_file}',
                f'--output-file={po_file}',
                '--no-fuzzy-matching',
                '--no-wrap',
                '--omit-header',
            ],
        )
        mo_file: Path = locale_dir / 'messages.mo'
        print(f'Updating MO file for locale [{locale}]...')
        run_babel_command(
            'compile',
            [
                '--use-fuzzy',
                f'--domain=messages',
                f'--directory={locales_dir}',
                f'--locale={locale}',
            ],
        )


if __name__ == '__main__':
    main()
