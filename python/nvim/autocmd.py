from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, MutableMapping, Optional, TypeVar
from uuid import uuid4

from .atomic import Atomic

T = TypeVar("T")


@dataclass(frozen=True)
class _AuParams:
    events: Iterable[str]
    modifiers: Iterable[str]
    rhs: str


class _A:
    def __init__(
        self,
        name: str,
        events: Iterable[str],
        modifiers: Iterable[str],
        parent: AutoCMD,
    ) -> None:
        self._name, self._events, self._modifiers = name, events, modifiers
        self._parent = parent

    def __lshift__(self, rhs: str) -> None:
        self._parent._autocmds[self._name] = _AuParams(
            events=self._events, modifiers=self._modifiers, rhs=rhs
        )


class AutoCMD:
    def __init__(self) -> None:
        self._autocmds: MutableMapping[str, _AuParams] = {}

    def __call__(
        self,
        event: str,
        *events: str,
        name: Optional[str] = None,
        modifiers: Iterable[str] = ("*",),
    ) -> _A:
        cmd_name = name or uuid4().hex
        return _A(
            name=cmd_name, events=(event, *events), modifiers=modifiers, parent=self
        )

    def drain(self, chan: int) -> Atomic:
        atomic = Atomic()
        while self._autocmds:
            name, param = self._autocmds.popitem()
            events = ",".join(param.events)
            modifiers = " ".join(param.modifiers)
            atomic.command(f"augroup ch_{chan}.{name}")
            atomic.command("autocmd!")
            atomic.command(f"autocmd {events} {modifiers} {param.rhs}")
            atomic.command("augroup END")

        return atomic
