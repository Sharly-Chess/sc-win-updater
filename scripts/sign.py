from pathlib import Path


# SignTool location
SIGNTOOL_RELEASE: int = 26100
SIGNTOOL_VERSION: str = f'10.0.{SIGNTOOL_RELEASE}.0'
SIGNTOOL_DIR: Path = Path(f'C:/Program Files (x86)/Windows Kits/10/bin/{SIGNTOOL_VERSION}/x64')
SIGNTOOL_EXE: Path = SIGNTOOL_DIR / 'signtool.exe'

# The URL where to get the timestamp of the signature
SIGNTOOL_TIMESTAMP_URL = 'http://time.certum.pl'


def compact_command_output(
    output: str,
) -> str:
    """Compact the output of a command to save space in the logs."""
    return '\n'.join(
        line for line in map(lambda s: s.rstrip(), output.split('\n')) if line
    )


def signtool_run_command(
    params: list[str],
) -> tuple[int, str, str]:
    """Run SignTool and return the result code, stdout and stderr as strings"""
    # windows_tools.signtool has no sha1 parameter, needed to sign with
    # a cloud certificate, so the module can not be used.
    # from windows_tools.signtool import SignTool
    # signer: SignTool = SignTool(authority_timestamp_url='http://time.certum.pl')
    # signer.sign(EXE, bitness=64)


    import subprocess

    cmd: list[str] = [
        str(SIGNTOOL_EXE),
    ] + params
    print(f'Running command [{' '.join(cmd)}]...')
    process = subprocess.run(cmd, capture_output=True, text=True)
    print(f'Command returned [{process.returncode}].')

    return (
        process.returncode,
        compact_command_output(process.stdout),
        compact_command_output(process.stderr),
    )


def signtool_verify_file(
    file: Path,
    signed: bool,
) -> bool:
    """Verify if a file is signed or not signed, return True if as expected.
    Cf https://learn.microsoft.com/en-us/windows/win32/seccrypto/using-signtool-to-verify-a-file-signature"""
    print(f'Verifying that file [{file}] is {'signed' if signed else 'not signed'}...')
    result, out, err = signtool_run_command(
        [
            'verify',
            '-pa',
            '-v',
            str(file),
        ],
    )
    correct: bool
    if signed:
        correct = result == 0
    else:
        correct = result != 0
    if correct:
        print(f'STDOUT:\n{out}')
        print(f'SUCCESS: File [{file}] is {'signed' if signed else 'not signed'}.')
    else:
        print(f'STDOUT:\n{out}')
        print(f'STDERR:\n{err}')
        print(f'ERROR: File [{file}] is {'not signed.' if signed else 'already signed.'}.')
    return correct


def signtool_sign_file(
    file: Path,
    signtool_cert_fingerprint: str,
) -> bool:
    """Sign a file, return True if no error while signing."""
    print(f'Signing file [{file}]...')
    result, out, err = signtool_run_command(
        [
            'sign',
            '-sha1',
            signtool_cert_fingerprint,
            '-tr',
            SIGNTOOL_TIMESTAMP_URL,
            '-td',
            'sha256',
            '-fd',
            'sha256',
            str(file),
        ]
    )
    correct: bool = result == 0
    if correct:
        print(f'STDOUT:\n{out}')
        print(f'SUCCESS: File [{file}] has been successfully signed.')
    else:
        print(f'STDOUT:\n{out}')
        print(f'STDERR:\n{err}')
        print(f'ERROR: Signing file [{file}] failed.')
    return correct


def sign_file(
    file: Path,
    signtool_cert_fingerprint: str,
) -> bool:
    # Verify that the file is not already signed
    if not signtool_verify_file(file, signed=False):
        return True
    # Sign the file
    if not signtool_sign_file(file, signtool_cert_fingerprint):
        return False
    # Verify that it has been signed
    if not signtool_verify_file(file, signed=True):
        return False
    return True
