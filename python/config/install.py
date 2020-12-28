from dataclasses import dataclass, field
from typing import Optional, Sequence


@dataclass(frozen=True)
class InstallSpec:
    pip: Sequence[str] = field(default_factory=tuple)
    npm: Sequence[str] = field(default_factory=tuple)
    bash: Optional[str] = None