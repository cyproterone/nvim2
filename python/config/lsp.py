from dataclasses import dataclass
from typing import Any, FrozenSet, Optional, Sequence

from std2.pickle import decode
from yaml import safe_load

from ..consts import CONF_LSP
from .install import InstallSpec


@dataclass(frozen=True)
class RootPattern:
    exact: Sequence[str] = ()
    globs: Sequence[str] = ()
    version_control: bool = True


@dataclass(frozen=True)
class LspAttrs:
    server: str
    bin: str
    filetypes: FrozenSet[str]
    args: Sequence[str] = ()
    root: RootPattern = RootPattern()
    settings: Optional[Any] = None
    install: Optional[InstallSpec] = None


LspSpecs = Sequence[LspAttrs]
lsp_specs: LspSpecs = decode(LspSpecs, safe_load(CONF_LSP.open()))
