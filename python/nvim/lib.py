from asyncio import Future
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Optional, Sequence, Tuple, TypeVar, cast

from pynvim import Nvim, NvimError
from pynvim.api import Buffer, Window

T = TypeVar("T")

AtomicInstruction = Tuple[str, Sequence[Any]]


def atomic(nvim: Nvim, *instructions: AtomicInstruction) -> Sequence[Any]:
    inst = tuple((f"nvim_{instruction}", args) for instruction, args in instructions)
    out, err = nvim.api.call_atomic(inst)
    if err:
        idx, _, err_msg = err
        raise NvimError(err_msg, instructions[idx])
    else:
        return cast(Sequence[Any], out)


class LockBroken(Exception):
    ...


@contextmanager
def buffer_lock(nvim: Nvim, b1: Optional[Buffer] = None) -> Iterator[Buffer]:
    if b1 is None:
        b1 = nvim.api.get_current_buf()
    c1 = nvim.api.buf_get_var(b1, "changetick")
    try:
        yield b1
    finally:
        b2, c2 = atomic(
            nvim, ("get_current_buf", ()), ("buf_get_var", (b1, "changetick"))
        )
        if not (b2 == b1 and c2 == c1):
            raise LockBroken()


@contextmanager
def window_lock(nvim: Nvim, w1: Optional[Window] = None) -> Iterator[Window]:
    if w1 is None:
        w1 = nvim.get_current_win()
    try:
        yield cast(Window, w1)
    finally:
        w2: Window = nvim.get_current_win()
        if w2 != w1:
            raise LockBroken()


async def async_call(nvim: Nvim, fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    fut = Future[T]()

    def cont() -> None:
        try:
            ret = fn(*args, **kwargs)
        except LockBroken:
            pass
        except Exception as e:
            if not fut.cancelled():
                fut.set_exception(e)
        else:
            if not fut.cancelled():
                fut.set_result(ret)

    nvim.async_call(cont)
    return await fut
