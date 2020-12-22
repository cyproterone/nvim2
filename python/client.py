from asyncio.tasks import gather
from typing import AsyncIterator

from pynvim import Nvim

from .lib.go import go
from .nvim.client import ARPC_MSG, RPC_MSG
from .nvim.lib import async_call
from .registery import finalize


async def client(
    nvim: Nvim, arpcs: AsyncIterator[ARPC_MSG], rpcs: AsyncIterator[RPC_MSG]
) -> None:
    async def poll_arpc() -> None:
        async for event, args in arpcs:

            def cont() -> None:
                nvim.api.out_write(f"{event} - {args}\n")

            await async_call(nvim, cont)

    async def poll_rpc() -> None:
        async for fut, (event, args) in rpcs:

            def cont() -> None:
                nvim.api.out_write(f"{event}\n")

            await async_call(nvim, cont)
            fut.set_result(None)

    await gather(go(poll_arpc()), go(poll_rpc()))
    await finalize(nvim)
