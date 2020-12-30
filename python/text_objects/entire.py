from pynvim import Nvim
from pynvim.api import Buffer

from ..registery import keymap, rpc


@rpc(blocking=True)
def _entire(nvim: Nvim) -> None:
    buf: Buffer = nvim.api.get_current_buf()
    count: int = nvim.api.buf_line_count(buf)
    last_line: str = nvim.api.buf_get_lines(buf, -2, -1, True)
    nvim.funcs.setpos("'<", (buf.number, 1, 1, 0))
    nvim.funcs.setpos("'>", (buf.number, count, len(last_line), 0))
    nvim.command("norm! `<V`>")


keymap.o("ie") << f"<cmd>lua {_entire.lua_name}()<cr>"
keymap.o("ae") << f"<cmd>lua {_entire.lua_name}()<cr>"
keymap.v("ie") << f"<esc><cmd>lua {_entire.lua_name}()<cr>"
keymap.v("ae") << f"<esc><cmd>lua {_entire.lua_name}()<cr>"
