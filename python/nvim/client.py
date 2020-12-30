from abc import abstractmethod
from asyncio.coroutines import iscoroutine
from asyncio.tasks import run_coroutine_threadsafe, sleep
from logging import WARN
from math import inf
from os import linesep
from threading import Thread
from typing import Any, Protocol, Sequence, TypeVar

from pynvim import Nvim

from .logging import log, nvim_handler
from .rpc import RpcSpec, nil_handler

T = TypeVar("T")

from .rpc import RpcMsg


class Client(Protocol):
    @abstractmethod
    def on_msg(self, nvim: Nvim, msg: RpcMsg) -> Any:
        ...

    @abstractmethod
    async def wait(self, nvim: Nvim) -> None:
        ...


class DefaultClient(Client):
    def __init__(self, *specs: RpcSpec[Any]) -> None:
        self._handlers = {k: v for k, v in specs}

    def on_msg(self, nvim: Nvim, msg: RpcMsg) -> Any:
        name, args = msg
        handler = self._handlers.get(name, nil_handler(name))
        ret = handler(nvim, *args)
        return None if iscoroutine(ret) else ret

    async def wait(self, nvim: Nvim) -> None:
        await sleep(inf)


def _on_err(error: str) -> None:
    log.error("%s", error)


def run_client(nvim: Nvim, client: Client, log_level: int = WARN) -> None:
    def on_rpc(name: str, evt_args: Sequence[Sequence[Any]]) -> Any:
        args, *_ = evt_args
        try:
            return client.on_msg(nvim, (name, args))
        except Exception as e:
            fmt = f"ERROR IN RPC FOR: %s - %s{linesep}%s"
            log.exception(fmt, name, args, e)
            raise

    def main() -> None:
        try:
            fut = run_coroutine_threadsafe(client.wait(nvim), loop=nvim.loop)
            fut.result()
        except Exception as e:
            log.exception(e)

    def forever() -> None:
        nvim.run_loop(
            err_cb=_on_err,
            notification_cb=on_rpc,
            request_cb=on_rpc,
        )

    th1 = Thread(target=main)
    th2 = Thread(target=forever, daemon=True)

    log.addHandler(nvim_handler(nvim))
    log.setLevel(log_level)
    th2.start()
    th1.start()
    th1.join()
