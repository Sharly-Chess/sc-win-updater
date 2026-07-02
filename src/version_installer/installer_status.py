from dataclasses import dataclass


@dataclass
class InstallerStatus:
    label: str
    progress: float = 0
    modified: bool = False
    error: str | None = None
