from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence, Set

from std2.pickle import decode
from yaml import safe_load

from ..consts import CONF_PKGS
from ..nvim.keymap import KeymapOpts


@dataclass(frozen=True)
class KeymapSpec:
    modes: Set[str]
    maps: Mapping[str, str]
    opts: KeymapOpts = field(default_factory=lambda: KeymapOpts())


@dataclass(frozen=True)
class PkgAttrs:
    uri: str
    keys: Sequence[KeymapSpec] = ()
    vals: Mapping[str, Any] = field(default_factory=dict)


PkgSpecs = Sequence[PkgAttrs]
pkg_specs: PkgSpecs = decode(PkgSpecs, safe_load(CONF_PKGS.open()))
