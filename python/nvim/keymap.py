from __future__ import annotations

from dataclasses import asdict, dataclass
from string import Template
from typing import (
    Iterable,
    MutableMapping,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

from pynvim.api import Buffer

from .atomic import Atomic

T = TypeVar("T")


@dataclass(frozen=True)
class KeymapOpts:
    noremap: bool
    silent: bool
    expr: bool
    nowait: bool
    unique: bool


_KEY_MODES = {"n", "o", "v", "i", "c", "t"}


class _K:
    def __init__(
        self,
        lhs: str,
        modes: Iterable[str],
        options: KeymapOpts,
        parent: Keymap,
    ) -> None:
        self._lhs, self._modes = lhs, modes
        self._opts, self._parent = options, parent

    def __lshift__(self, rhs: Union[str, Template]) -> None:
        for mode in self._modes:
            self._parent._mappings[(mode, self._lhs)] = (self._opts, rhs)


class _KM:
    def __init__(self, modes: Iterable[str], parent: Keymap) -> None:
        self._modes, self._parent = modes, parent

    def __call__(
        self,
        lhs: str,
        noremap: bool = True,
        silent: bool = True,
        expr: bool = False,
        nowait: bool = False,
        unique: bool = False,
    ) -> _K:
        opts = KeymapOpts(
            noremap=noremap,
            silent=silent,
            expr=expr,
            nowait=nowait,
            unique=unique,
        )

        return _K(
            lhs=lhs,
            modes=self._modes,
            options=opts,
            parent=self._parent,
        )


class Keymap:
    def __init__(self) -> None:
        self._mappings: MutableMapping[
            Tuple[str, str],
            Tuple[KeymapOpts, Union[str, Template]],
        ] = {}

    def __getattr__(self, modes: str) -> _KM:
        for mode in modes:
            if mode not in _KEY_MODES:
                raise AttributeError()
        else:
            return _KM(modes=modes, parent=self)

    def drain(self, chan: int, buf: Optional[Buffer]) -> Atomic:
        atomic = Atomic()
        while self._mappings:
            (mode, lhs), (opts, rhs) = self._mappings.popitem()
            if type(rhs) is str and buf is None:
                atomic.set_keymap(mode, lhs, rhs, asdict(opts))

            elif type(rhs) is str and buf is not None:
                atomic.buf_set_keymap(buf, mode, lhs, rhs, asdict(opts))

            elif isinstance(rhs, Template) and buf is None:
                call = rhs.substitute(chan=chan)
                atomic.set_keymap(mode, lhs, call, asdict(opts))

            elif isinstance(rhs, Template) and buf is not None:
                call = rhs.substitute(chan=chan)
                atomic.buf_set_keymap(buf, mode, lhs, call, asdict(opts))
            else:
                assert False

        return atomic
