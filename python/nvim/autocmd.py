from dataclasses import dataclass
from python.nvim.lib import AtomicInstruction
from typing import (
    Callable,
    Iterable,
    Iterator,
    MutableMapping,
    Sequence,
    Tuple,
    TypeVar,
    Any,
)

from .rpc import RPC_FUNCTION, RPC_SPEC, lua_rpc_literal

T = TypeVar("T")


@dataclass(frozen=True)
class _AuParams:
    blocking: bool
    events: Iterable[str]
    filters: Iterable[str]
    modifiers: Iterable[str]
    args: Iterable[str]


class AutoCMD:
    def __init__(self) -> None:
        self._autocmds: MutableMapping[str, Tuple[_AuParams, RPC_FUNCTION[Any]]] = {}

    def __call__(
        self,
        name: str,
        *,
        events: Iterable[str],
        filters: Iterable[str] = ("*",),
        modifiers: Iterable[str] = (),
        args: Iterable[str] = (),
        blocking: bool = False,
    ) -> Callable[[RPC_FUNCTION[T]], RPC_FUNCTION[T]]:
        param = _AuParams(
            blocking=blocking,
            events=events,
            filters=filters,
            modifiers=modifiers,
            args=args,
        )

        def decor(rpc_f: RPC_FUNCTION[T]) -> RPC_FUNCTION[T]:
            self._autocmds[name] = (param, rpc_f)
            return rpc_f

        return decor

    def drain(
        self, chan: int
    ) -> Tuple[Sequence[AtomicInstruction], Sequence[RPC_SPEC]]:
        def it() -> Iterator[Tuple[Sequence[AtomicInstruction], RPC_SPEC]]:
            while self._autocmds:
                name, (param, func) = self._autocmds.popitem()
                events = ",".join(param.events)
                filters = " ".join(param.filters)
                modifiers = " ".join(param.modifiers)
                lua = lua_rpc_literal(
                    chan, blocking=param.blocking, name=name, args=param.args
                )

                yield (
                    ("command", (f"augroup ch_{chan}_{name}",)),
                    ("command", ("autocmd!",)),
                    ("command", (f"autocmd {events} {filters} {modifiers} {lua}",)),
                    ("command", ("augroup END",)),
                ), (name, func)

        instructions, specs = zip(*it())
        return instructions, specs
