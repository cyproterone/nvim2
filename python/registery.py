from typing import Sequence, Tuple

from pynvim import Nvim
from pynvim_pp.atomic import Atomic
from pynvim_pp.autocmd import AutoCMD
from pynvim_pp.keymap import Keymap
from pynvim_pp.rpc import RPC, RpcSpec
from pynvim_pp.settings import Settings

from .components.pkgs import inst

atomic = Atomic()
autocmd = AutoCMD()
keymap = Keymap()
rpc = RPC()
settings = Settings()


def drain(nvim: Nvim) -> Tuple[Atomic, Sequence[RpcSpec]]:
    _atomic = Atomic()
    _atomic.set_var("mapleader", " ")
    _atomic.set_var("maplocalleader", " ")

    a0 = inst(nvim)
    a1 = autocmd.drain()
    a2 = keymap.drain(buf=None)
    a3, s0 = rpc.drain(nvim.channel_id)
    a4 = settings.drain()
    return _atomic + a0 + a1 + a2 + a3 + a4 + atomic, s0
